"""Acceptance tests for Step 2 Synthetic Data Generator."""

import csv
import json
from pathlib import Path
import pytest
from testtrace.datagen import generate_all

DATA_DIR = Path("data/synthetic")


@pytest.fixture(scope="module", autouse=True)
def run_generator() -> None:
    generate_all(seed=42, out_dir=DATA_DIR, eval_mode="standard")


def test_packages_exist() -> None:
    assert (DATA_DIR / "CASE_A" / "measurements.csv").exists()
    assert (DATA_DIR / "CASE_B" / "measurements.csv").exists()
    assert (DATA_DIR / "CASE_C" / "measurements.csv").exists()
    assert (DATA_DIR / "DEV_001" / "measurements.csv").exists()
    assert (DATA_DIR / "TEST_001" / "measurements.csv").exists()


def test_package_schema_integrity() -> None:
    for case_id in ("CASE_A", "CASE_B", "CASE_C"):
        p_dir = DATA_DIR / case_id
        for fname in ("measurements.csv", "limits.csv", "golden_reference.csv", "station_history.csv", "truth.json"):
            assert (p_dir / fname).exists(), f"Missing {fname} in {case_id}"

        with open(p_dir / "truth.json", encoding="utf-8") as f:
            truth = json.load(f)
            assert "case_id" in truth
            assert "true_category" in truth
            assert "true_side" in truth
            assert "expected_kb_prefix" in truth
            assert len(truth["expected_action_keywords"]) >= 1


def test_non_fault_units_pass_rate() -> None:
    # Load limits
    case_dir = DATA_DIR / "CASE_B"
    limits: dict[tuple[str, str], tuple[float | None, float | None]] = {}
    with open(case_dir / "limits.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lower = float(row["lower_limit"]) if row["lower_limit"] else None
            upper = float(row["upper_limit"]) if row["upper_limit"] else None
            limits[(row["test_name"], row["freq_ghz"])] = (lower, upper)

    non_fault_total = 0
    non_fault_passed = 0

    with open(case_dir / "measurements.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["unit_id"] in ("DUT_017", "GOLDEN_01"):
                continue  # Skip target injected unit and golden
            non_fault_total += 1
            val = float(row["measured_value"])
            lower, upper = limits[(row["test_name"], row["freq_ghz"])]
            is_pass = True
            if lower is not None and val < lower:
                is_pass = False
            if upper is not None and val > upper:
                is_pass = False
            if is_pass:
                non_fault_passed += 1

    pass_rate = non_fault_passed / non_fault_total
    assert pass_rate >= 0.95, f"Non-fault pass rate {pass_rate:.4f} is below 95%"


def test_case_a_golden_offset_st_a_only() -> None:
    st_a_devs: list[float] = []
    st_b_devs: list[float] = []

    with open(DATA_DIR / "CASE_A" / "measurements.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["unit_type"] == "GOLDEN" and row["test_name"] == "insertion_loss":
                val = float(row["measured_value"])
                freq = float(row["freq_ghz"])
                nominal = -2.5 - 0.15 * (freq - 1.0)
                dev = val - nominal
                if row["station_id"] == "ST-A":
                    st_a_devs.append(dev)
                elif row["station_id"] == "ST-B":
                    st_b_devs.append(dev)

    assert len(st_a_devs) > 0
    assert len(st_b_devs) > 0
    mean_a_dev = sum(st_a_devs) / len(st_a_devs)
    mean_b_dev = sum(st_b_devs) / len(st_b_devs)

    # ST-A has ~ -2.4 dB offset; ST-B has normal ~ +0.05 dB offset
    assert mean_a_dev < -1.8, f"Expected large negative offset on ST-A, got {mean_a_dev:.3f}"
    assert abs(mean_b_dev) < 0.2, f"ST-B golden should be within normal tolerance, got {mean_b_dev:.3f}"


def test_case_c_amb_missing_golden() -> None:
    with open(DATA_DIR / "CASE_C" / "measurements.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        golden_rows = [r for r in reader if r["unit_type"] == "GOLDEN"]
        assert len(golden_rows) == 0, "CASE_C must contain no golden rows"

    with open(DATA_DIR / "CASE_C" / "station_history.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            assert r["calibration_due_date"] == "", "CASE_C cal due date must be blank"
            assert r["last_reference_check"] == "", "CASE_C last ref check must be blank"


def test_hard_difficulty_ratio() -> None:
    hard_count = 0
    total_eval = 0
    for split in ("DEV", "TEST"):
        for path in DATA_DIR.glob(f"{split}_*"):
            if path.is_dir():
                total_eval += 1
                with open(path / "truth.json", encoding="utf-8") as f:
                    t = json.load(f)
                    if t["difficulty"] == "hard":
                        hard_count += 1

    ratio = hard_count / total_eval if total_eval > 0 else 0
    assert ratio >= 0.30, f"Hard cases ratio {ratio:.2f} is below 30%"