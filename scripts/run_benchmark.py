"""Automated evaluation and latency benchmark harness for TestTrace Guard."""

import argparse
import json
import logging
import math
from pathlib import Path
import sys
import time
from typing import Any, Optional

# Ensure repository root is on sys.path for direct CLI script execution
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from testtrace.kb import KBIndexer
from testtrace.pipeline import run_pipeline
from testtrace.storage import AuditStorage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("testtrace.benchmark")


def percentile(data: list[float], q: float) -> float:
    """Calculate q-th percentile (0.0 <= q <= 1.0) using nearest rank."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    idx = int(math.ceil(q * len(sorted_data))) - 1
    return sorted_data[max(0, min(idx, len(sorted_data) - 1))]


def run_evaluation(
    data_dir: Path = Path("data/synthetic"),
    split: str = "all",
    mode: str = "mock",
    audit_dir: Path = Path("data/audit"),
    kb_dir: Path = Path("data/kb"),
    out_json: Optional[Path] = Path("data/benchmark_results.json"),
    out_md: Optional[Path] = Path("data/benchmark_summary.md"),
) -> dict[str, Any]:
    """Execute evaluation over test packages against ground-truth metadata."""
    if not data_dir.exists():
        raise FileNotFoundError(f"Synthetic dataset directory not found: {data_dir}")

    audit_storage = AuditStorage(base_dir=audit_dir)
    kb_indexer = KBIndexer(kb_dir=kb_dir)

    # 1. Discover target packages
    package_dirs: list[Path] = []
    for p in sorted(data_dir.iterdir()):
        if not p.is_dir():
            continue
        truth_file = p / "truth.json"
        if not truth_file.exists():
            continue

        try:
            with open(truth_file, "r", encoding="utf-8") as f:
                truth = json.load(f)
            pkg_split = truth.get("split", "unknown").lower()
            if split == "all" or pkg_split == split.lower() or p.name.lower().startswith(split.lower()):
                package_dirs.append(p)
        except Exception as exc:
            logger.warning("Skipping package %s: %s", p.name, exc)

    if not package_dirs:
        raise ValueError(f"No valid investigation packages found matching split '{split}' in {data_dir}")

    logger.info("Starting benchmark evaluation on %d packages (split='%s', mode='%s')...", len(package_dirs), split, mode)

    # 2. Benchmark execution loop
    results: list[dict[str, Any]] = []
    latencies: list[float] = []

    cat_matches = 0
    side_matches = 0
    status_matches = 0
    sop_matches = 0
    keyword_recalls: list[float] = []

    verdict_counts = {"PASS": 0, "CORRECTED": 0, "FLAGGED": 0}
    family_breakdown: dict[str, dict[str, int]] = {}

    start_bench_time = time.perf_counter()

    for p in package_dirs:
        with open(p / "truth.json", "r", encoding="utf-8") as f:
            truth = json.load(f)

        fam = truth.get("family", "UNKNOWN")
        if fam not in family_breakdown:
            family_breakdown[fam] = {"total": 0, "cat_correct": 0, "side_correct": 0}
        family_breakdown[fam]["total"] += 1

        run_res = run_pipeline(
            case_path=p,
            mode=mode,
            audit_storage=audit_storage,
            kb_indexer=kb_indexer,
            audit_dir=audit_dir,
            kb_dir=kb_dir,
        )

        rep = run_res.report
        latencies.append(run_res.total_execution_time_ms)

        # Match evaluations
        is_cat_correct = rep.category == truth["true_category"]
        is_side_correct = rep.target_side == truth["true_side"]
        is_status_correct = rep.status == truth["expected_status"]
        is_sop_correct = rep.primary_kb_doc.startswith(truth["expected_kb_prefix"])

        if is_cat_correct:
            cat_matches += 1
            family_breakdown[fam]["cat_correct"] += 1
        if is_side_correct:
            side_matches += 1
            family_breakdown[fam]["side_correct"] += 1
        if is_status_correct:
            status_matches += 1
        if is_sop_correct:
            sop_matches += 1

        # Action keyword grounding recall across recommended actions, preventative items, and summary
        expected_kws = truth.get("expected_action_keywords", [])
        combined_action_corpus = " ".join(
            rep.recommended_actions + rep.preventative_actions + [rep.root_cause_summary]
        ).lower().replace("_", " ")

        if expected_kws:
            hits = sum(1 for kw in expected_kws if kw.lower() in combined_action_corpus)
            kw_recall = hits / len(expected_kws)
        else:
            kw_recall = 1.0
        keyword_recalls.append(kw_recall)

        # Guardrail verdict distribution
        v = rep.validator_verdict if rep.validator_verdict in verdict_counts else "FLAGGED"
        verdict_counts[v] += 1

        results.append(
            {
                "case_id": run_res.case_id,
                "split": truth.get("split"),
                "family": fam,
                "difficulty": truth.get("difficulty"),
                "category_pred": rep.category,
                "category_truth": truth["true_category"],
                "category_match": is_cat_correct,
                "side_pred": rep.target_side,
                "side_truth": truth["true_side"],
                "side_match": is_side_correct,
                "status_pred": rep.status,
                "status_truth": truth["expected_status"],
                "status_match": is_status_correct,
                "sop_pred": rep.primary_kb_doc,
                "sop_expected_prefix": truth["expected_kb_prefix"],
                "sop_match": is_sop_correct,
                "keyword_recall": round(kw_recall, 3),
                "confidence": rep.confidence,
                "verdict": rep.validator_verdict,
                "latency_ms": run_res.total_execution_time_ms,
            }
        )

    total_bench_duration_s = time.perf_counter() - start_bench_time
    total_cases = len(package_dirs)

    # 3. Aggregate metrics
    cat_acc = (cat_matches / total_cases) * 100.0
    side_acc = (side_matches / total_cases) * 100.0
    status_acc = (status_matches / total_cases) * 100.0
    sop_acc = (sop_matches / total_cases) * 100.0
    avg_kw_recall = (sum(keyword_recalls) / len(keyword_recalls)) * 100.0 if keyword_recalls else 0.0

    mean_lat = sum(latencies) / len(latencies) if latencies else 0.0
    p50_lat = percentile(latencies, 0.50)
    p90_lat = percentile(latencies, 0.90)
    p95_lat = percentile(latencies, 0.95)
    p99_lat = percentile(latencies, 0.99)
    throughput_qps = total_cases / total_bench_duration_s if total_bench_duration_s > 0 else 0.0

    summary_metrics = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "split": split,
        "inference_mode": mode,
        "total_cases_evaluated": total_cases,
        "total_benchmark_duration_seconds": round(total_bench_duration_s, 3),
        "throughput_cases_per_sec": round(throughput_qps, 2),
        "category_accuracy": round(cat_acc, 2),
        "domain_accuracy": round(side_acc, 2),
        "status_accuracy": round(status_acc, 2),
        "sop_prefix_accuracy": round(sop_acc, 2),
        "action_keyword_recall": round(avg_kw_recall, 2),
        "latency_mean_ms": round(mean_lat, 2),
        "latency_p50_ms": round(p50_lat, 2),
        "latency_p90_ms": round(p90_lat, 2),
        "latency_p95_ms": round(p95_lat, 2),
        "latency_p99_ms": round(p99_lat, 2),
        "validator_verdicts": verdict_counts,
        "fault_family_breakdown": family_breakdown,
        "detailed_results": results,
    }

    # 4. Save artifacts
    if out_json:
        out_json.parent.mkdir(parents=True, exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(summary_metrics, f, indent=2)
        logger.info("Benchmark telemetry JSON saved to: %s", out_json.resolve())

    if out_md:
        out_md.parent.mkdir(parents=True, exist_ok=True)
        md_content = generate_markdown_report(summary_metrics)
        with open(out_md, "w", encoding="utf-8") as f:
            f.write(md_content)
        logger.info("Benchmark executive report saved to: %s", out_md.resolve())

    # 5. Print summary table to console
    print_console_summary(summary_metrics)

    return summary_metrics


def generate_markdown_report(metrics: dict[str, Any]) -> str:
    """Generate executive Markdown report comparing triage performance against targets."""
    lines = [
        "# TestTrace Guard - Evaluation & Benchmark Report",
        "",
        f"- **Timestamp:** `{metrics['timestamp']}`",
        f"- **Evaluation Split:** `{metrics['split']}` ({metrics['total_cases_evaluated']} cases)",
        f"- **Inference Execution Mode:** `{metrics['inference_mode']}`",
        f"- **Overall Throughput:** `{metrics['throughput_cases_per_sec']} cases/sec`",
        "",
        "## 1. Key Performance Indicators (KPIs)",
        "",
        "| Evaluation Metric | Target Spec | Measured Result | Status |",
        "|---|---|---|---|",
        f"| **Triage Category Accuracy** | $\\ge 90.0\\%$ | **{metrics['category_accuracy']:.1f}%** | {'✅ PASS' if metrics['category_accuracy'] >= 90.0 else '❌ FAIL'} |",
        f"| **Architectural Domain (Side)** | $\\ge 95.0\\%$ | **{metrics['domain_accuracy']:.1f}%** | {'✅ PASS' if metrics['domain_accuracy'] >= 95.0 else '❌ FAIL'} |",
        f"| **Triage Status Accuracy** | $\\ge 95.0\\%$ | **{metrics['status_accuracy']:.1f}%** | {'✅ PASS' if metrics['status_accuracy'] >= 95.0 else '❌ FAIL'} |",
        f"| **Top-1 SOP Prefix Accuracy** | $\\ge 95.0\\%$ | **{metrics['sop_prefix_accuracy']:.1f}%** | {'✅ PASS' if metrics['sop_prefix_accuracy'] >= 95.0 else '❌ FAIL'} |",
        f"| **Action Keyword Recall** | $\\ge 80.0\\%$ | **{metrics['action_keyword_recall']:.1f}%** | {'✅ PASS' if metrics['action_keyword_recall'] >= 80.0 else '❌ FAIL'} |",
        f"| **Mean Latency per Case** | $< 100.0\\text{{ ms}}$ | **{metrics['latency_mean_ms']:.2f} ms** | {'✅ PASS' if metrics['latency_mean_ms'] < 100.0 else '❌ FAIL'} |",
        "",
        "## 2. Latency Percentiles (End-to-End Pipeline)",
        "",
        "| Latency Percentile | Measured Latency | Budget Limit |",
        "|---|---|---|",
        f"| **Mean** | {metrics['latency_mean_ms']:.2f} ms | 100.00 ms |",
        f"| **p50 (Median)** | {metrics['latency_p50_ms']:.2f} ms | 50.00 ms |",
        f"| **p90** | {metrics['latency_p90_ms']:.2f} ms | 150.00 ms |",
        f"| **p95** | {metrics['latency_p95_ms']:.2f} ms | 200.00 ms |",
        f"| **p99** | {metrics['latency_p99_ms']:.2f} ms | 500.00 ms |",
        "",
        "## 3. Guardrail Validator Verdicts",
        "",
        f"- **Clean Pass (`PASS`):** {metrics['validator_verdicts'].get('PASS', 0)}",
        f"- **Sanitized / Overridden (`CORRECTED`):** {metrics['validator_verdicts'].get('CORRECTED', 0)}",
        f"- **Flagged Discrepancies (`FLAGGED`):** {metrics['validator_verdicts'].get('FLAGGED', 0)}",
        "",
        "## 4. Fault Family Breakdown",
        "",
        "| Fault Family | Description | Cases Tested | Category Acc | Domain Acc |",
        "|---|---|---|---|---|",
    ]

    names = {
        "F1": "Station Configuration Offset",
        "F2": "Intrinsic DUT Defect",
        "F3": "Fixture Contact Instability",
        "F4": "Calibration Overdue",
        "F5": "Spec / Revision Mismatch",
        "AMB": "Inconclusive Data Gap",
    }

    for fam, stats in sorted(metrics.get("fault_family_breakdown", {}).items()):
        tot = stats["total"]
        cat_pct = (stats["cat_correct"] / tot * 100.0) if tot > 0 else 0.0
        side_pct = (stats["side_correct"] / tot * 100.0) if tot > 0 else 0.0
        fname = names.get(fam, fam)
        lines.append(f"| **{fam}** | {fname} | {tot} | {cat_pct:.1f}% | {side_pct:.1f}% |")

    lines.append("")
    return "\n".join(lines)


def print_console_summary(m: dict[str, Any]) -> None:
    """Print clean executive summary to terminal."""
    print("\n" + "=" * 68)
    print("      TESTTRACE GUARD - BENCHMARK & EVALUATION SUMMARY")
    print("=" * 68)
    print(f" Evaluation Split : {m['split'].upper()} ({m['total_cases_evaluated']} cases evaluated)")
    print(f" Execution Mode   : {m['inference_mode'].upper()} (Throughput: {m['throughput_cases_per_sec']:.1f} cases/s)")
    print("-" * 68)
    print(f" Category Accuracy   : {m['category_accuracy']:.1f}% (Target: >=90%)")
    print(f" Domain / Side Acc   : {m['domain_accuracy']:.1f}% (Target: >=95%)")
    print(f" Triage Status Acc   : {m['status_accuracy']:.1f}% (Target: >=95%)")
    print(f" SOP Top-1 Accuracy  : {m['sop_prefix_accuracy']:.1f}% (Target: >=95%)")
    print(f" Keyword Recall Rate : {m['action_keyword_recall']:.1f}% (Target: >=80%)")
    print("-" * 68)
    print(f" Latency Mean / p50  : {m['latency_mean_ms']:.2f} ms / {m['latency_p50_ms']:.2f} ms")
    print(f" Latency p95 / p99   : {m['latency_p95_ms']:.2f} ms / {m['latency_p99_ms']:.2f} ms")
    print("-" * 68)
    print(f" Guardrail Verdicts  : PASS={m['validator_verdicts']['PASS']} | CORRECTED={m['validator_verdicts']['CORRECTED']} | FLAGGED={m['validator_verdicts']['FLAGGED']}")
    print("=" * 68 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="TestTrace Guard Automated Benchmark Runner")
    parser.add_argument("--data-dir", type=Path, default=Path("data/synthetic"), help="Dataset directory")
    parser.add_argument("--audit-dir", type=Path, default=Path("data/audit"), help="Audit directory")
    parser.add_argument("--kb-dir", type=Path, default=Path("data/kb"), help="Knowledge base directory")
    parser.add_argument("--split", choices=["demo", "dev", "test", "all"], default="all", help="Target split to evaluate")
    parser.add_argument("--mode", choices=["mock", "vllm"], default="mock", help="Inference mode")
    parser.add_argument("--out-json", type=Path, default=Path("data/benchmark_results.json"), help="Output JSON path")
    parser.add_argument("--out-md", type=Path, default=Path("data/benchmark_summary.md"), help="Output Markdown report path")
    args = parser.parse_args()

    run_evaluation(
        data_dir=args.data_dir,
        split=args.split,
        mode=args.mode,
        audit_dir=args.audit_dir,
        kb_dir=args.kb_dir,
        out_json=args.out_json,
        out_md=args.out_md,
    )


if __name__ == "__main__":
    main()