"""Acceptance tests for Step 6 Hybrid Retrieval Pipeline."""

import json
import time
from pathlib import Path
import pytest

from testtrace.analytics import load_package, run_analytics
from testtrace.kb import KBIndexer
from testtrace.retrieval import build_retrieval_query, retrieve_context
from testtrace.rules import evaluate_rules
from testtrace.schemas import RetrievalResult

DATA_DIR = Path("data/synthetic")
KB_DIR = Path("data/kb")


@pytest.fixture(scope="module")
def shared_kb() -> KBIndexer:
    return KBIndexer(kb_dir=KB_DIR)


def find_dev_case_by_family(family: str) -> Path:
    for p in sorted(DATA_DIR.glob("DEV_*")):
        truth_file = p / "truth.json"
        if truth_file.exists():
            with open(truth_file, encoding="utf-8") as f:
                data = json.load(f)
                if data.get("family") == family:
                    return p
    raise FileNotFoundError(f"No DEV package found for family {family}")


def test_retrieval_case_a(shared_kb: KBIndexer) -> None:
    pkg = load_package(DATA_DIR / "CASE_A")
    analytics = run_analytics(pkg)
    rule_res = evaluate_rules(analytics, pkg)
    retrieval = retrieve_context(analytics, rule_res, kb_indexer=shared_kb)

    assert retrieval.case_id == "CASE_A"
    assert retrieval.primary_doc.prefix == "MAN-4"
    assert retrieval.primary_doc.doc_id == "MAN-401"
    assert retrieval.primary_doc.category == "STATION_CONFIGURATION"
    assert retrieval.primary_doc.target_side == "MEASUREMENT_SYSTEM"
    assert len(retrieval.primary_doc.action_items) >= 3

    # Normalize text to check keywords
    action_text = " ".join(retrieval.primary_doc.action_items).lower().replace("_", " ")
    for kw in ["golden", "cable loss", "compensation"]:
        assert kw in action_text, f"Expected keyword '{kw}' in retrieved action protocol"

    assert "MAN-401" in retrieval.formatted_context
    assert "Mandatory Corrective Action Protocol" in retrieval.formatted_context


def test_retrieval_case_b(shared_kb: KBIndexer) -> None:
    pkg = load_package(DATA_DIR / "CASE_B")
    analytics = run_analytics(pkg)
    rule_res = evaluate_rules(analytics, pkg)
    retrieval = retrieve_context(analytics, rule_res, kb_indexer=shared_kb)

    assert retrieval.case_id == "CASE_B"
    assert retrieval.primary_doc.prefix == "MAN-6"
    assert retrieval.primary_doc.doc_id == "MAN-601"
    assert retrieval.primary_doc.category == "DUT_DEFECT"
    assert retrieval.primary_doc.target_side == "DUT"

    action_text = " ".join(retrieval.primary_doc.action_items).lower()
    assert "quarantine" in action_text or "shield" in action_text or "isolation" in action_text


def test_retrieval_case_c(shared_kb: KBIndexer) -> None:
    pkg = load_package(DATA_DIR / "CASE_C")
    analytics = run_analytics(pkg)
    rule_res = evaluate_rules(analytics, pkg)
    retrieval = retrieve_context(analytics, rule_res, kb_indexer=shared_kb)

    assert retrieval.case_id == "CASE_C"
    assert retrieval.primary_doc.prefix == "MAN-9"
    assert retrieval.primary_doc.doc_id == "MAN-901"
    assert retrieval.primary_doc.category == "INSUFFICIENT_EVIDENCE"
    assert retrieval.primary_doc.target_side == "UNDETERMINED"


@pytest.mark.parametrize(
    "family, expected_prefix, expected_doc_id",
    [
        ("F3", "MAN-5", "MAN-501"),
        ("F4", "MAN-7", "MAN-701"),
        ("F5", "MAN-8", "MAN-801"),
    ],
)
def test_retrieval_dev_families(
    shared_kb: KBIndexer,
    family: str,
    expected_prefix: str,
    expected_doc_id: str,
) -> None:
    case_path = find_dev_case_by_family(family)
    pkg = load_package(case_path)
    analytics = run_analytics(pkg)
    rule_res = evaluate_rules(analytics, pkg)
    retrieval = retrieve_context(analytics, rule_res, kb_indexer=shared_kb)

    assert retrieval.primary_doc.prefix == expected_prefix
    assert retrieval.primary_doc.doc_id == expected_doc_id


def test_query_formulation_content(shared_kb: KBIndexer) -> None:
    pkg = load_package(DATA_DIR / "CASE_A")
    analytics = run_analytics(pkg)
    rule_res = evaluate_rules(analytics, pkg)
    query = build_retrieval_query(analytics, rule_res)

    assert len(query) > 20
    assert "STATION CONFIGURATION" in query or "station configuration" in query.lower()
    assert "ST-A" in query


def test_retrieval_speed_benchmark(shared_kb: KBIndexer) -> None:
    pkg = load_package(DATA_DIR / "CASE_A")
    analytics = run_analytics(pkg)
    rule_res = evaluate_rules(analytics, pkg)

    # Warmup
    _ = retrieve_context(analytics, rule_res, kb_indexer=shared_kb)

    start = time.perf_counter()
    iterations = 50
    for _ in range(iterations):
        _ = retrieve_context(analytics, rule_res, kb_indexer=shared_kb)
    avg_latency_ms = ((time.perf_counter() - start) / iterations) * 1000.0

    assert avg_latency_ms < 20.0, f"Average hybrid retrieval latency ({avg_latency_ms:.3f} ms) exceeds 20 ms budget"