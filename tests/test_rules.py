"""Acceptance tests for Step 4 Deterministic Rule Engine."""

import json
import time
from pathlib import Path
import pytest
from testtrace.analytics import load_package, run_analytics
from testtrace.rules import evaluate_rules
from testtrace.schemas import RuleEvaluationResult

DATA_DIR = Path("data/synthetic")


def find_dev_case_by_family(family: str) -> Path:
    """Find the first synthetic DEV package matching the requested fault family."""
    for p in sorted(DATA_DIR.glob("DEV_*")):
        truth_file = p / "truth.json"
        if truth_file.exists():
            with open(truth_file, encoding="utf-8") as f:
                data = json.load(f)
                if data.get("family") == family:
                    return p
    raise FileNotFoundError(f"No DEV package found for family {family}")


def test_case_a_station_configuration_triage() -> None:
    pkg = load_package(DATA_DIR / "CASE_A")
    analytics = run_analytics(pkg)
    rule_res = evaluate_rules(analytics, pkg)

    assert rule_res.case_id == "CASE_A"
    assert rule_res.recommended_category == "STATION_CONFIGURATION"
    assert rule_res.recommended_side == "MEASUREMENT_SYSTEM"
    assert rule_res.status == "PLAN_READY_FOR_REVIEW"
    assert rule_res.suggested_kb_prefix == "MAN-4"
    assert rule_res.confidence >= 0.80
    assert any(r.rule_id == "R-CFG-001" for r in rule_res.fired_rules)
    assert len(rule_res.supporting_fact_ids) > 0


def test_case_b_dut_defect_triage() -> None:
    pkg = load_package(DATA_DIR / "CASE_B")
    analytics = run_analytics(pkg)
    rule_res = evaluate_rules(analytics, pkg)

    assert rule_res.case_id == "CASE_B"
    assert rule_res.recommended_category == "DUT_DEFECT"
    assert rule_res.recommended_side == "DUT"
    assert rule_res.status == "PLAN_READY_FOR_REVIEW"
    assert rule_res.suggested_kb_prefix == "MAN-6"
    assert rule_res.confidence >= 0.80
    assert any(r.rule_id == "R-DUT-001" for r in rule_res.fired_rules)
    assert len(rule_res.supporting_fact_ids) > 0


def test_case_c_ambiguity_triage() -> None:
    pkg = load_package(DATA_DIR / "CASE_C")
    analytics = run_analytics(pkg)
    rule_res = evaluate_rules(analytics, pkg)

    assert rule_res.case_id == "CASE_C"
    assert rule_res.recommended_category == "INSUFFICIENT_EVIDENCE"
    assert rule_res.recommended_side == "UNDETERMINED"
    assert rule_res.status == "NEEDS_MORE_DATA"
    assert rule_res.suggested_kb_prefix == "MAN-9"
    assert rule_res.confidence >= 0.75
    assert any(r.rule_id == "R-GAP-001" for r in rule_res.fired_rules)
    assert len(rule_res.supporting_fact_ids) > 0


def test_fault_family_f3_fixture_contact() -> None:
    f3_path = find_dev_case_by_family("F3")
    pkg = load_package(f3_path)
    analytics = run_analytics(pkg)
    rule_res = evaluate_rules(analytics, pkg)

    assert rule_res.recommended_category == "FIXTURE_CONTACT"
    assert rule_res.recommended_side == "MEASUREMENT_SYSTEM"
    assert rule_res.suggested_kb_prefix == "MAN-5"
    assert any(r.rule_id == "R-FIX-001" for r in rule_res.fired_rules)


def test_fault_family_f4_instrument_calibration() -> None:
    f4_path = find_dev_case_by_family("F4")
    pkg = load_package(f4_path)
    analytics = run_analytics(pkg)
    rule_res = evaluate_rules(analytics, pkg)

    assert rule_res.recommended_category == "INSTRUMENT_CALIBRATION"
    assert rule_res.recommended_side == "MEASUREMENT_SYSTEM"
    assert rule_res.suggested_kb_prefix == "MAN-7"
    assert any(r.rule_id == "R-CAL-001" for r in rule_res.fired_rules)


def test_fault_family_f5_revision_mismatch() -> None:
    f5_path = find_dev_case_by_family("F5")
    pkg = load_package(f5_path)
    analytics = run_analytics(pkg)
    rule_res = evaluate_rules(analytics, pkg)

    assert rule_res.recommended_category == "SPEC_OR_REVISION_MISMATCH"
    assert rule_res.recommended_side == "SPECIFICATION"
    assert rule_res.suggested_kb_prefix == "MAN-8"
    assert any(r.rule_id == "R-REV-001" for r in rule_res.fired_rules)


def test_rule_engine_execution_benchmark() -> None:
    pkg = load_package(DATA_DIR / "CASE_A")
    analytics = run_analytics(pkg)

    # Warmup
    _ = evaluate_rules(analytics, pkg)

    # Timed benchmark
    start = time.perf_counter()
    res = evaluate_rules(analytics, pkg)
    duration_ms = (time.perf_counter() - start) * 1000.0

    assert duration_ms < 10.0, f"Rule evaluation ({duration_ms:.3f} ms) exceeds 10 ms limit"
    assert isinstance(res, RuleEvaluationResult)