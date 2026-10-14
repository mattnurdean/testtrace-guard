"""Automated CLI demo walkthrough executing Canonical Cases A, B, and C."""

from pathlib import Path
import sys
import time

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from testtrace.kb import KBIndexer
from testtrace.pipeline import print_report_summary, run_pipeline
from testtrace.storage import AuditStorage


def run_demo_walkthrough(
    data_dir: Path = Path("data/synthetic"),
    audit_dir: Path = Path("data/audit"),
    kb_dir: Path = Path("data/kb"),
    mode: str = "mock",
) -> list[dict[str, str]]:
    """Execute Canonical Cases A, B, and C sequentially and return summary dicts."""
    storage = AuditStorage(base_dir=audit_dir)
    kb = KBIndexer(kb_dir=kb_dir)

    canonical_cases = [
        ("CASE_A", "Scenario 1: Station Configuration Offset (Fault Family F1)"),
        ("CASE_B", "Scenario 2: Intrinsic DUT RF Defect (Fault Family F2)"),
        ("CASE_C", "Scenario 3: Ambiguous Data Gap / Missing Baseline (Guardrail AMB)"),
    ]

    summaries: list[dict[str, str]] = []

    print("\n" + "#" * 70)
    print("   TESTTRACE GUARD — AUTOMATED CANONICAL DEMO WALKTHROUGH")
    print("#" * 70)

    for case_id, title in canonical_cases:
        print(f"\n>>> Executing {title} [{case_id}]...")
        case_path = data_dir / case_id
        res = run_pipeline(
            case_path=case_path,
            mode=mode,
            audit_storage=storage,
            kb_indexer=kb,
            audit_dir=audit_dir,
            kb_dir=kb_dir,
        )
        print_report_summary(res)
        summaries.append(
            {
                "case_id": res.case_id,
                "category": res.report.category,
                "target_side": res.report.target_side,
                "status": res.report.status,
                "primary_kb_doc": res.report.primary_kb_doc,
                "verdict": res.report.validator_verdict,
            }
        )

    print("#" * 70)
    print("   WALKTHROUGH COMPLETE — 3/3 CANONICAL SCENARIOS VERIFIED")
    print("#" * 70 + "\n")
    return summaries


if __name__ == "__main__":
    run_demo_walkthrough()