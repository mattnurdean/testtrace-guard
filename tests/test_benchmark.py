"""Acceptance tests for Step 10 Evaluation and Latency Benchmark Harness."""

from pathlib import Path
import pytest
from scripts.run_benchmark import run_evaluation

DATA_DIR = Path("data/synthetic")
AUDIT_DIR = Path("data/audit")
KB_DIR = Path("data/kb")


@pytest.fixture(scope="module")
def dev_benchmark_results(tmp_path_factory: pytest.TempPathFactory) -> dict:
    """Run benchmark evaluation on the 20-case development split."""
    tmp_dir = tmp_path_factory.mktemp("bench_test")
    json_path = tmp_dir / "benchmark_results.json"
    md_path = tmp_dir / "benchmark_summary.md"

    metrics = run_evaluation(
        data_dir=DATA_DIR,
        split="dev",
        mode="mock",
        audit_dir=tmp_dir / "audit",
        kb_dir=KB_DIR,
        out_json=json_path,
        out_md=md_path,
    )
    return metrics


def test_benchmark_execution_and_totals(dev_benchmark_results: dict) -> None:
    assert dev_benchmark_results["total_cases_evaluated"] >= 12, "Must evaluate at least 12 DEV cases"
    assert dev_benchmark_results["throughput_cases_per_sec"] > 0.0


def test_category_accuracy_threshold(dev_benchmark_results: dict) -> None:
    acc = dev_benchmark_results["category_accuracy"]
    assert acc >= 90.0, f"Category accuracy ({acc:.1f}%) is below 90.0% target"


def test_domain_accuracy_threshold(dev_benchmark_results: dict) -> None:
    acc = dev_benchmark_results["domain_accuracy"]
    assert acc >= 95.0, f"Domain (side) accuracy ({acc:.1f}%) is below 95.0% target"


def test_status_accuracy_threshold(dev_benchmark_results: dict) -> None:
    acc = dev_benchmark_results["status_accuracy"]
    assert acc >= 95.0, f"Triage status accuracy ({acc:.1f}%) is below 95.0% target"


def test_sop_prefix_accuracy_threshold(dev_benchmark_results: dict) -> None:
    acc = dev_benchmark_results["sop_prefix_accuracy"]
    assert acc >= 95.0, f"SOP prefix retrieval accuracy ({acc:.1f}%) is below 95.0% target"


def test_action_keyword_recall_threshold(dev_benchmark_results: dict) -> None:
    recall = dev_benchmark_results["action_keyword_recall"]
    assert recall >= 80.0, f"Action keyword recall ({recall:.1f}%) is below 80.0% target"


def test_benchmark_latency_budget(dev_benchmark_results: dict) -> None:
    mean_lat = dev_benchmark_results["latency_mean_ms"]
    p95_lat = dev_benchmark_results["latency_p95_ms"]
    assert mean_lat < 100.0, f"Mean latency ({mean_lat:.2f} ms) exceeds 100 ms limit"
    assert p95_lat < 200.0, f"p95 latency ({p95_lat:.2f} ms) exceeds 200 ms limit"


def test_benchmark_artifacts_generation(tmp_path: Path) -> None:
    json_path = tmp_path / "bench.json"
    md_path = tmp_path / "bench.md"

    metrics = run_evaluation(
        data_dir=DATA_DIR,
        split="demo",
        mode="mock",
        audit_dir=tmp_path / "audit",
        kb_dir=KB_DIR,
        out_json=json_path,
        out_md=md_path,
    )

    assert json_path.exists(), "benchmark_results.json must be created"
    assert md_path.exists(), "benchmark_summary.md must be created"
    assert json_path.stat().st_size > 500
    assert "# TestTrace Guard" in md_path.read_text(encoding="utf-8")