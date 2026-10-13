"""End-to-end pipeline orchestrator and CLI for TestTrace Guard triage."""

import argparse
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from testtrace.analytics import load_package, run_analytics
from testtrace.kb import KBIndexer
from testtrace.reasoner import generate_report
from testtrace.retrieval import retrieve_context
from testtrace.rules import evaluate_rules
from testtrace.schemas import PipelineRunResult
from testtrace.storage import AuditStorage


def run_pipeline(
    case_path: Path,
    mode: str = "mock",
    audit_storage: Optional[AuditStorage] = None,
    kb_indexer: Optional[KBIndexer] = None,
    audit_dir: Path = Path("data/audit"),
    kb_dir: Path = Path("data/kb"),
) -> PipelineRunResult:
    """Execute end-to-end investigation pipeline on target package directory."""
    start_time = time.perf_counter()

    if not case_path.exists():
        raise FileNotFoundError(f"Investigation package path not found: {case_path}")

    case_id = case_path.name
    run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if audit_storage is None:
        audit_storage = AuditStorage(base_dir=audit_dir)

    if kb_indexer is None:
        kb_indexer = KBIndexer(kb_dir=kb_dir)

    # 1. Ingest package & run deterministic analytics
    pkg = load_package(case_path)
    analytics = run_analytics(pkg)

    # 2. Evaluate heuristic rule engine
    rule_res = evaluate_rules(analytics, pkg)

    # 3. Perform hybrid retrieval
    retrieval = retrieve_context(analytics, rule_res, kb_indexer=kb_indexer)

    # 4. Generate & validate diagnostic report
    report = generate_report(analytics, rule_res, retrieval, mode=mode)

    total_time_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

    result = PipelineRunResult(
        run_id=run_id,
        case_id=case_id,
        timestamp=now_iso,
        mode=mode,
        analytics=analytics,
        rule_evaluation=rule_res,
        retrieval=retrieval,
        report=report,
        total_execution_time_ms=total_time_ms,
    )

    # 5. Persist audit trace
    audit_storage.save_run(result)

    return result


def print_report_summary(res: PipelineRunResult) -> None:
    """Print an executive summary to stdout."""
    rep = res.report
    print("\n" + "=" * 65)
    print("      TESTTRACE GUARD - RF FAILURE TRIAGE REPORT")
    print("=" * 65)
    print(f" Run ID          : {res.run_id}")
    print(f" Case ID         : {res.case_id}")
    print(f" Execution Time  : {res.total_execution_time_ms:.2f} ms (Mode: {res.mode})")
    print(f" Verdict / Guard : {rep.validator_verdict}")
    print("-" * 65)
    print(f" Recommended Cat : {rep.category}")
    print(f" Target Domain   : {rep.target_side}")
    print(f" Triage Status   : {rep.status} (Confidence: {rep.confidence:.2f})")
    print(f" Primary SOP     : {rep.primary_kb_doc}")
    print("-" * 65)
    print(f" Root Cause Summary:")
    print(f"   {rep.root_cause_summary}")
    print("-" * 65)
    print(" Recommended Action Protocol:")
    for idx, act in enumerate(rep.recommended_actions, 1):
        print(f"   {idx}. {act}")
    print("-" * 65)
    print(f" Audit Trace     : {res.audit_file_path}")
    print("=" * 65 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="TestTrace Guard End-to-End Triage Pipeline")
    parser.add_argument("--case", type=str, default="CASE_A", help="Target case directory or ID")
    parser.add_argument("--data-dir", type=Path, default=Path("data/synthetic"), help="Base synthetic data directory")
    parser.add_argument("--audit-dir", type=Path, default=Path("data/audit"), help="Audit output directory")
    parser.add_argument("--mode", choices=["mock", "vllm"], default="mock", help="Inference mode")
    args = parser.parse_args()

    target_path = Path(args.case)
    if not target_path.exists():
        target_path = args.data_dir / args.case

    if not target_path.exists():
        print(f"Error: Investigation package '{args.case}' not found at {target_path}", file=sys.stderr)
        sys.exit(1)

    result = run_pipeline(
        case_path=target_path,
        mode=args.mode,
        audit_dir=args.audit_dir,
    )
    print_report_summary(result)


if __name__ == "__main__":
    main()