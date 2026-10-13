"""Acceptance tests for Step 7 LLM Reasoner and Guardrail Validator."""

import time
from pathlib import Path
import pytest

from testtrace.analytics import load_package, run_analytics
from testtrace.kb import KBIndexer
from testtrace.reasoner import generate_report
from testtrace.retrieval import retrieve_context
from testtrace.rules import evaluate_rules
from testtrace.schemas import DiagnosticReport
from testtrace.validator import validate_and_sanitize_report

DATA_DIR = Path("data/synthetic")
KB_DIR = Path("data/kb")


@pytest.fixture(scope="module")
def shared_kb() -> KBIndexer:
    return KBIndexer(kb_dir=KB_DIR)


def test_reasoner_canonical_case_a(shared_kb: KBIndexer) -> None:
    pkg = load_package(DATA_DIR / "CASE_A")
    analytics = run_analytics(pkg)
    rule_res = evaluate_rules(analytics, pkg)
    retrieval = retrieve_context(analytics, rule_res, kb_indexer=shared_kb)

    report = generate_report(analytics, rule_res, retrieval, mode="mock")

    assert isinstance(report, DiagnosticReport)
    assert report.case_id == "CASE_A"
    assert report.category == "STATION_CONFIGURATION"
    assert report.target_side == "MEASUREMENT_SYSTEM"
    assert report.status == "PLAN_READY_FOR_REVIEW"
    assert report.primary_kb_doc == "MAN-401"
    assert report.validator_verdict in ("PASS", "CORRECTED")
    assert len(report.supporting_fact_ids) > 0
    assert len(report.recommended_actions) >= 2

    # Verify fact grounding (all cited facts exist in analytics.facts)
    valid_ids = {f.fact_id for f in analytics.facts}
    for fid in report.supporting_fact_ids:
        assert fid in valid_ids, f"Fact ID {fid} is not grounded in deterministic analytics"


def test_reasoner_canonical_case_b(shared_kb: KBIndexer) -> None:
    pkg = load_package(DATA_DIR / "CASE_B")
    analytics = run_analytics(pkg)
    rule_res = evaluate_rules(analytics, pkg)
    retrieval = retrieve_context(analytics, rule_res, kb_indexer=shared_kb)

    report = generate_report(analytics, rule_res, retrieval, mode="mock")

    assert report.case_id == "CASE_B"
    assert report.category == "DUT_DEFECT"
    assert report.target_side == "DUT"
    assert report.status == "PLAN_READY_FOR_REVIEW"
    assert report.primary_kb_doc == "MAN-601"
    assert "DUT_017" in report.root_cause_summary


def test_reasoner_canonical_case_c_ambiguity(shared_kb: KBIndexer) -> None:
    pkg = load_package(DATA_DIR / "CASE_C")
    analytics = run_analytics(pkg)
    rule_res = evaluate_rules(analytics, pkg)
    retrieval = retrieve_context(analytics, rule_res, kb_indexer=shared_kb)

    report = generate_report(analytics, rule_res, retrieval, mode="mock")

    assert report.case_id == "CASE_C"
    assert report.category == "INSUFFICIENT_EVIDENCE"
    assert report.target_side == "UNDETERMINED"
    assert report.status == "NEEDS_MORE_DATA"
    assert report.primary_kb_doc == "MAN-901"


def test_validator_strips_hallucinated_facts(shared_kb: KBIndexer) -> None:
    pkg = load_package(DATA_DIR / "CASE_A")
    analytics = run_analytics(pkg)
    rule_res = evaluate_rules(analytics, pkg)
    retrieval = retrieve_context(analytics, rule_res, kb_indexer=shared_kb)

    # Craft payload containing fake hallucinated fact IDs
    hallucinated_payload = {
        "case_id": "CASE_A",
        "category": "STATION_CONFIGURATION",
        "target_side": "MEASUREMENT_SYSTEM",
        "status": "PLAN_READY_FOR_REVIEW",
        "confidence": 0.90,
        "primary_kb_doc": "MAN-401",
        "root_cause_summary": "Test summary",
        "supporting_fact_ids": ["E-001", "E-999_HALLUCINATED", "E-888_FAKE"],
        "recommended_actions": ["Action 1"],
    }

    val_res = validate_and_sanitize_report(hallucinated_payload, analytics, rule_res, retrieval)

    assert "E-999_HALLUCINATED" not in val_res.sanitized_report.supporting_fact_ids
    assert "E-888_FAKE" not in val_res.sanitized_report.supporting_fact_ids
    assert any("HALLUCINATED_FACT_ID" in d for d in val_res.discrepancies)


def test_validator_overrides_contradictory_category(shared_kb: KBIndexer) -> None:
    pkg = load_package(DATA_DIR / "CASE_A")
    analytics = run_analytics(pkg)
    rule_res = evaluate_rules(analytics, pkg)
    retrieval = retrieve_context(analytics, rule_res, kb_indexer=shared_kb)

    # Simulate LLM erroneously claiming DUT defect when rules prove station configuration
    contradictory_payload = {
        "case_id": "CASE_A",
        "category": "DUT_DEFECT",
        "target_side": "DUT",
        "status": "PLAN_READY_FOR_REVIEW",
        "confidence": 0.60,
        "primary_kb_doc": "MAN-601",
        "root_cause_summary": "Erroneously blaming the DUT.",
        "supporting_fact_ids": ["E-001"],
        "recommended_actions": ["Quarantine DUT."],
    }

    val_res = validate_and_sanitize_report(contradictory_payload, analytics, rule_res, retrieval)

    assert val_res.sanitized_report.category == "STATION_CONFIGURATION"
    assert val_res.sanitized_report.target_side == "MEASUREMENT_SYSTEM"
    assert val_res.sanitized_report.validator_verdict == "CORRECTED"
    assert any("CATEGORY_CONFLICT" in o for o in val_res.overrides_applied)


def test_validator_enforces_ambiguity_status(shared_kb: KBIndexer) -> None:
    pkg = load_package(DATA_DIR / "CASE_C")
    analytics = run_analytics(pkg)
    rule_res = evaluate_rules(analytics, pkg)
    retrieval = retrieve_context(analytics, rule_res, kb_indexer=shared_kb)

    invalid_status_payload = {
        "case_id": "CASE_C",
        "category": "INSUFFICIENT_EVIDENCE",
        "target_side": "UNDETERMINED",
        "status": "PLAN_READY_FOR_REVIEW",  # Contradiction: INSUFFICIENT_EVIDENCE must be NEEDS_MORE_DATA
        "confidence": 0.80,
        "primary_kb_doc": "MAN-901",
        "root_cause_summary": "Missing golden baseline.",
        "supporting_fact_ids": rule_res.supporting_fact_ids,
        "recommended_actions": ["Repeat golden check."],
    }

    val_res = validate_and_sanitize_report(invalid_status_payload, analytics, rule_res, retrieval)

    assert val_res.sanitized_report.status == "NEEDS_MORE_DATA"
    assert any("STATUS_ENFORCEMENT" in o for o in val_res.overrides_applied)


def test_reasoner_execution_benchmark(shared_kb: KBIndexer) -> None:
    pkg = load_package(DATA_DIR / "CASE_A")
    analytics = run_analytics(pkg)
    rule_res = evaluate_rules(analytics, pkg)
    retrieval = retrieve_context(analytics, rule_res, kb_indexer=shared_kb)

    # Warmup
    _ = generate_report(analytics, rule_res, retrieval, mode="mock")

    start = time.perf_counter()
    iterations = 20
    for _ in range(iterations):
        _ = generate_report(analytics, rule_res, retrieval, mode="mock")
    avg_latency_ms = ((time.perf_counter() - start) / iterations) * 1000.0

    assert avg_latency_ms < 100.0, f"Average mock reasoner latency ({avg_latency_ms:.2f} ms) exceeds 100 ms limit"