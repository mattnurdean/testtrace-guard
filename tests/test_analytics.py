"""Acceptance tests for Step 3 Deterministic Analytics."""

import time
from pathlib import Path
import pytest
from testtrace.analytics import load_package, run_analytics
from testtrace.schemas import AnalyticsResult, InvestigationPackage

DATA_DIR = Path("data/synthetic")


@pytest.fixture(scope="module")
def case_a_package() -> InvestigationPackage:
    return load_package(DATA_DIR / "CASE_A")


@pytest.fixture(scope="module")
def case_b_package() -> InvestigationPackage:
    return load_package(DATA_DIR / "CASE_B")


@pytest.fixture(scope="module")
def case_c_package() -> InvestigationPackage:
    return load_package(DATA_DIR / "CASE_C")


def test_package_loading_and_pydantic_validation(case_a_package: InvestigationPackage) -> None:
    assert case_a_package.case_id == "CASE_A"
    assert len(case_a_package.measurements) > 0
    assert len(case_a_package.limits) > 0
    assert len(case_a_package.golden_reference) > 0
    assert len(case_a_package.station_history) == 2


def test_case_a_station_configuration_evidence(case_a_package: InvestigationPackage) -> None:
    result = run_analytics(case_a_package)
    categories = [f.category for f in result.facts]

    # CASE_A must detect config change, golden deviation on ST-A, and station delta
    assert "CONFIG_CHANGE" in categories, "Must flag ST-A configuration table change"
    assert "GOLDEN_DEVIATION" in categories, "Must flag ST-A golden reference failure"
    assert "STATION_DELTA" in categories, "Must detect significant station discrepancy"

    # Verify golden deviation details
    st_a_golden_facts = [
        f for f in result.facts if f.category == "GOLDEN_DEVIATION" and f.station_id == "ST-A"
    ]
    assert len(st_a_golden_facts) > 0
    assert st_a_golden_facts[0].delta is not None
    assert st_a_golden_facts[0].delta < -1.5, f"Expected offset < -1.5 dB, got {st_a_golden_facts[0].delta}"

    # Golden deviation should NOT be present on ST-B
    st_b_golden_facts = [
        f for f in result.facts if f.category == "GOLDEN_DEVIATION" and f.station_id == "ST-B"
    ]
    assert len(st_b_golden_facts) == 0, "ST-B golden baseline must be within tolerance"


def test_case_b_dut_defect_evidence(case_b_package: InvestigationPackage) -> None:
    result = run_analytics(case_b_package)

    # CASE_B target unit fails LO leakage on both stations
    lo_violations = [
        f for f in result.facts if f.category == "DUT_SPEC_VIOLATION" and f.metric_name == "lo_leakage"
    ]
    assert len(lo_violations) > 0, "Must detect LO leakage spec violation"

    violated_stations = {f.station_id for f in lo_violations}
    assert "ST-A" in violated_stations and "ST-B" in violated_stations, "DUT defect must fail on both stations"

    # Golden runs must pass without deviations
    golden_facts = [f for f in result.facts if f.category == "GOLDEN_DEVIATION"]
    assert len(golden_facts) == 0, "No golden deviations expected in CASE_B"


def test_case_c_ambiguity_and_missing_baseline(case_c_package: InvestigationPackage) -> None:
    result = run_analytics(case_c_package)

    assert result.has_golden_data is False
    assert result.has_valid_cal is False

    data_gap_facts = [f for f in result.facts if f.category == "DATA_GAP"]
    assert len(data_gap_facts) >= 2, "Must detect missing golden runs and missing calibration records"


def test_analytics_execution_speed_benchmark(case_a_package: InvestigationPackage) -> None:
    # Warm-up run
    _ = run_analytics(case_a_package)

    # Timed run
    start = time.perf_counter()
    res = run_analytics(case_a_package)
    duration_ms = (time.perf_counter() - start) * 1000.0

    assert duration_ms < 500.0, f"Analytics execution ({duration_ms:.2f} ms) exceeds 500 ms limit"
    assert isinstance(res, AnalyticsResult)