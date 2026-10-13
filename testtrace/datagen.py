"""Synthetic RF test dataset generator for TestTrace Guard."""

import argparse
import csv
import json
import logging
import math
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("testtrace.datagen")

# Parameter definitions per Playbook App. C.1
# (test_name, unit, freq_list, nominal_fn, unit_sigma, repeat_sigma, lower_limit, upper_limit, meas_uncertainty)
PARAM_SPECS = [
    (
        "insertion_loss",
        "dB",
        [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        lambda f: -2.5 - 0.15 * (f - 1.0),
        0.12,
        0.03,
        -4.0,
        -2.0,
        0.10,
    ),
    (
        "return_loss",
        "dB",
        [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        lambda f: -18.0,
        1.2,
        0.15,
        None,
        -10.0,
        0.50,
    ),
    (
        "lo_leakage",
        "dBm",
        [2.4],
        lambda f: -52.0,
        1.5,
        0.15,
        None,
        -40.0,
        0.50,
    ),
    (
        "phase_noise_10k",
        "dBc/Hz",
        [2.4],
        lambda f: -110.0,
        0.8,
        0.15,
        None,
        -105.0,
        0.30,
    ),
    (
        "harmonic_h2",
        "dBc",
        [2.4],
        lambda f: -38.0,
        1.5,
        0.20,
        None,
        -30.0,
        0.50,
    ),
]

ACTION_KEYWORDS = {
    "F1": ["golden", "reference path", "cable loss", "compensation", "configuration"],
    "F2": ["isolation", "shield", "LO"],
    "F3": ["reconnect", "re-seat", "repeatability", "contact"],
    "F4": ["calibration", "golden", "reference check"],
    "F5": ["limits", "revision"],
    "AMB": ["golden", "repeat", "configuration revision"],
}

CATEGORY_MAP = {
    "F1": "STATION_CONFIGURATION",
    "F2": "DUT_DEFECT",
    "F3": "FIXTURE_CONTACT",
    "F4": "INSTRUMENT_CALIBRATION",
    "F5": "SPEC_OR_REVISION_MISMATCH",
    "AMB": "INSUFFICIENT_EVIDENCE",
}

SIDE_MAP = {
    "F1": "MEASUREMENT_SYSTEM",
    "F2": "DUT",
    "F3": "MEASUREMENT_SYSTEM",
    "F4": "MEASUREMENT_SYSTEM",
    "F5": "SPECIFICATION",
    "AMB": "UNDETERMINED",
}

KB_PREFIX_MAP = {
    "F1": "MAN-4",
    "F2": "MAN-6",
    "F3": "MAN-5",
    "F4": "MAN-7",
    "F5": "MAN-8",
    "AMB": "MAN-9",
}


def create_limits_rows(limits_version: str = "LIM_V1.0", product_revision: str = "REV_A") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for test_name, unit, freqs, _, _, _, lower, upper, uncertainty in PARAM_SPECS:
        for f in freqs:
            rows.append({
                "limits_version": limits_version,
                "product_revision": product_revision,
                "test_name": test_name,
                "freq_ghz": f"{f:.1f}",
                "lower_limit": f"{lower:.2f}" if lower is not None else "",
                "upper_limit": f"{upper:.2f}" if upper is not None else "",
                "unit": unit,
                "meas_uncertainty": f"{uncertainty:.2f}",
            })
    return rows


def create_golden_ref_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for test_name, unit, freqs, nominal_fn, _, _, _, _, _ in PARAM_SPECS:
        for f in freqs:
            ref_val = nominal_fn(f)
            tol = 0.30 if "phase_noise" in test_name else 0.50
            rows.append({
                "unit_id": "GOLDEN_01",
                "test_name": test_name,
                "freq_ghz": f"{f:.1f}",
                "ref_value": f"{ref_val:.3f}",
                "tol": f"{tol:.2f}",
                "unit": unit,
            })
    return rows


def generate_package(
    case_id: str,
    split: str,
    family: str,
    difficulty: str,
    out_dir: Path,
    rng: random.Random,
) -> None:
    case_dir = out_dir / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    base_time = datetime(2026, 10, 10, 8, 0, 0, tzinfo=timezone.utc)
    change_time = base_time + timedelta(days=1, hours=4)  # ST-A config change timestamp

    # 1. Station History setup
    st_a_change = "none"
    st_a_change_at = ""
    st_b_cal_due = "2027-01-15"
    st_a_cal_due = "2027-02-01"
    st_b_last_ref = "2026-10-09"
    st_a_last_ref = "2026-10-09"
    st_a_cfg = "CFG-2.2"

    if family == "F1":
        st_a_change = "cable_loss_compensation_table updated"
        st_a_change_at = change_time.strftime("%Y-%m-%d %H:%M:%S")
        st_a_cfg = "CFG-2.3"
    elif family == "F4":
        st_b_cal_due = "2026-09-01"  # > 30 days overdue relative to test window
    elif family == "AMB":
        st_a_cal_due = ""
        st_b_cal_due = ""
        st_a_last_ref = ""
        st_b_last_ref = ""

    # Hard variant injection: conflicting change or near-duplicate
    if difficulty == "hard" and family == "F2":
        st_a_change = "station ground cable inspected"
        st_a_change_at = (base_time + timedelta(hours=10)).strftime("%Y-%m-%d %H:%M:%S")

    station_history_rows = [
        {
            "station_id": "ST-A",
            "instrument_id": "INSTR-A1",
            "fixture_id": "FX-1",
            "calibration_due_date": st_a_cal_due,
            "last_reference_check": st_a_last_ref,
            "software_version": "SW-4.1.0",
            "configuration_version": st_a_cfg,
            "recent_change": st_a_change,
            "recent_change_at": st_a_change_at,
            "historical_failure_rate": "0.012",
        },
        {
            "station_id": "ST-B",
            "instrument_id": "INSTR-B1",
            "fixture_id": "FX-2",
            "calibration_due_date": st_b_cal_due,
            "last_reference_check": st_b_last_ref,
            "software_version": "SW-4.1.0",
            "configuration_version": "CFG-1.9",
            "recent_change": "none",
            "recent_change_at": "",
            "historical_failure_rate": "0.015",
        },
    ]

    # 2. Limits and Golden Reference setup
    limits_rows = create_limits_rows("LIM_V1.0", "REV_A")
    golden_ref_rows = create_golden_ref_rows()

    # 3. Measurement campaigns (~24 DUTs + Golden runs)
    measurements: list[dict[str, Any]] = []
    run_seq = 1

    unit_ids = [f"DUT_{i:03d}" for i in range(1, 25)]
    target_dut_id = "DUT_017"

    # Pre-generate unit intrinsic biases
    unit_biases: dict[str, dict[str, float]] = {}
    for uid in unit_ids:
        unit_biases[uid] = {}
        for test_name, _, _, _, unit_sig, _, _, _, _ in PARAM_SPECS:
            unit_biases[uid][test_name] = rng.gauss(0.0, unit_sig)

    # In F5: target DUT is product revision REV_B
    unit_revs = {uid: "REV_A" for uid in unit_ids}
    if family == "F5":
        unit_revs[target_dut_id] = "REV_B"

    curr_time = base_time

    def record_run(
        u_id: str,
        u_type: str,
        rev: str,
        station: str,
        reconnect_idx: int,
        sweeps: int,
        timestamp: datetime,
    ) -> None:
        nonlocal run_seq
        fixt = "FX-1" if station == "ST-A" else "FX-2"
        instr = "INSTR-A1" if station == "ST-A" else "INSTR-B1"

        for sweep_idx in range(1, sweeps + 1):
            for test_name, unit_str, freqs, nominal_fn, _, rep_sig, _, _, _ in PARAM_SPECS:
                for f in freqs:
                    nom = nominal_fn(f)

                    # REV_B nominal adjustments in F5
                    if rev == "REV_B":
                        if test_name == "insertion_loss":
                            nom = -1.40  # Deliberately fails REV_A upper limit of -2.0 dB
                        elif test_name == "return_loss":
                            nom = -16.0

                    # Intrinsic DUT bias or exact golden reference
                    if u_type == "GOLDEN":
                        val = nom
                    else:
                        val = nom + unit_biases[u_id][test_name]

                    # Station ST-B baseline offset (+0.05 dB IL)
                    if station == "ST-B" and test_name == "insertion_loss":
                        val += 0.05

                    # Repeatability noise
                    sigma = rep_sig

                    # --- FAULT INJECTIONS ---
                    # F1: Station config offset on ST-A after change
                    if family == "F1" and station == "ST-A" and timestamp >= change_time:
                        if test_name == "insertion_loss":
                            f1_offset = -2.40 if difficulty == "easy" else -0.80
                            val += f1_offset

                    # F2: Target DUT LO leakage defect on both stations
                    if family == "F2" and u_id == target_dut_id and test_name == "lo_leakage":
                        val = -34.0 if difficulty == "easy" else -37.5

                    # F3: Target DUT Fixture contact issue on ST-A at reconnect 0
                    if family == "F3" and u_id == target_dut_id and reconnect_idx == 0:
                        if test_name in ("insertion_loss", "return_loss") and f >= 4.0:
                            sigma *= 8.0
                            val += rng.uniform(0.9, 1.5)

                    # F4: Instrument calibration drift on ST-B
                    if family == "F4" and station == "ST-B":
                        if test_name == "insertion_loss":
                            val += 0.40
                        elif test_name == "lo_leakage":
                            val += 2.50
                        elif test_name == "phase_noise_10k":
                            val += 0.50

                    # AMB: Marginal phase noise on target DUT on 1 of 5 sweeps
                    if family == "AMB" and u_id == target_dut_id and test_name == "phase_noise_10k":
                        if sweep_idx == 3:
                            val = -104.70  # Exceeds -105.00 dBc/Hz limit by 0.30 dB

                    # Add Gaussian noise
                    noise = rng.gauss(0.0, sigma)
                    measured = val + noise

                    measurements.append({
                        "run_id": f"RUN_{run_seq:05d}",
                        "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "unit_id": u_id,
                        "unit_type": u_type,
                        "product_revision": rev,
                        "station_id": station,
                        "fixture_id": fixt,
                        "instrument_id": instr,
                        "test_name": test_name,
                        "freq_ghz": f"{f:.1f}",
                        "sweep_idx": sweep_idx,
                        "reconnect_idx": reconnect_idx,
                        "measured_value": f"{measured:.3f}",
                        "unit": unit_str,
                        "temperature_c": f"{25.0 + rng.uniform(-1.5, 1.5):.1f}",
                        "operator_id": "OP_104",
                        "test_sequence_version": "SEQ_2.0",
                        "limits_version": "LIM_V1.0",
                    })
                    run_seq += 1

    # First half of DUTs (tested before ST-A change timestamp)
    for uid in unit_ids[:10]:
        st = "ST-A" if rng.random() > 0.5 else "ST-B"
        record_run(uid, "DUT", unit_revs[uid], st, 0, 3, curr_time)
        curr_time += timedelta(minutes=25)

    # Advance time past ST-A configuration update
    if curr_time < change_time + timedelta(hours=1):
        curr_time = change_time + timedelta(hours=1)

    # Golden verification runs on active station configurations
    include_golden = family != "AMB"
    if difficulty == "hard" and family in ("F1", "F2") and case_id not in ("CASE_A", "CASE_B"):
        include_golden = False  # Hard variant: missing golden rows

    if include_golden:
        record_run("GOLDEN_01", "GOLDEN", "REV_A", "ST-A", 0, 3, curr_time)
        curr_time += timedelta(minutes=15)
        record_run("GOLDEN_01", "GOLDEN", "REV_A", "ST-B", 0, 3, curr_time)
        curr_time += timedelta(minutes=15)

    # Target DUT run on ST-A (or ST-B for F4 calibration fault)
    target_station = "ST-B" if family == "F4" else "ST-A"
    sweeps_target = 5 if family == "AMB" else 3

    record_run(target_dut_id, "DUT", unit_revs[target_dut_id], target_station, 0, sweeps_target, curr_time)
    curr_time += timedelta(minutes=20)

    # F3 includes a re-seat reconnect run
    if family == "F3":
        record_run(target_dut_id, "DUT", unit_revs[target_dut_id], target_station, 1, 3, curr_time)
        curr_time += timedelta(minutes=20)

    # Target DUT cross-check run on other station (except AMB or F3)
    if family in ("F1", "F2", "F4", "F5"):
        alt_station = "ST-B" if target_station == "ST-A" else "ST-A"
        record_run(target_dut_id, "DUT", unit_revs[target_dut_id], alt_station, 0, 3, curr_time)
        curr_time += timedelta(minutes=20)

    # Remaining DUTs after the incident
    for uid in unit_ids[10:]:
        if uid == target_dut_id:
            continue
        st = "ST-A" if rng.random() > 0.5 else "ST-B"
        record_run(uid, "DUT", unit_revs[uid], st, 0, 3, curr_time)
        curr_time += timedelta(minutes=25)

    # 4. Write CSV files
    def write_csv(filename: str, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
        with open(case_dir / filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    write_csv(
        "measurements.csv",
        measurements,
        [
            "run_id", "timestamp", "unit_id", "unit_type", "product_revision",
            "station_id", "fixture_id", "instrument_id", "test_name", "freq_ghz",
            "sweep_idx", "reconnect_idx", "measured_value", "unit", "temperature_c",
            "operator_id", "test_sequence_version", "limits_version",
        ],
    )
    write_csv(
        "limits.csv",
        limits_rows,
        [
            "limits_version", "product_revision", "test_name", "freq_ghz",
            "lower_limit", "upper_limit", "unit", "meas_uncertainty",
        ],
    )
    write_csv(
        "golden_reference.csv",
        golden_ref_rows,
        ["unit_id", "test_name", "freq_ghz", "ref_value", "tol", "unit"],
    )
    write_csv(
        "station_history.csv",
        station_history_rows,
        [
            "station_id", "instrument_id", "fixture_id", "calibration_due_date",
            "last_reference_check", "software_version", "configuration_version",
            "recent_change", "recent_change_at", "historical_failure_rate",
        ],
    )

    # 5. Write truth.json
    expected_status = "NEEDS_MORE_DATA" if family == "AMB" else "PLAN_READY_FOR_REVIEW"
    truth_payload = {
        "case_id": case_id,
        "split": split,
        "family": family,
        "difficulty": difficulty,
        "true_category": CATEGORY_MAP[family],
        "true_side": SIDE_MAP[family],
        "expected_status": expected_status,
        "expected_kb_prefix": KB_PREFIX_MAP[family],
        "expected_action_keywords": ACTION_KEYWORDS[family],
        "notes": f"Synthetic case {case_id} ({family}, difficulty: {difficulty}) generated deterministically.",
    }
    with open(case_dir / "truth.json", "w", encoding="utf-8") as f:
        json.dump(truth_payload, f, indent=2)


def generate_all(seed: int = 42, out_dir: Path = Path("data/synthetic"), eval_mode: str = "standard") -> None:
    rng = random.Random(seed)
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Generating canonical demo packages (CASE_A, CASE_B, CASE_C)...")
    generate_package("CASE_A", "demo", "F1", "easy", out_dir, rng)
    generate_package("CASE_B", "demo", "F2", "easy", out_dir, rng)
    generate_package("CASE_C", "demo", "AMB", "easy", out_dir, rng)

    if eval_mode == "turbo":
        families_per_split = ["F1", "F2", "F3", "F4", "F5"] * 2 + ["AMB"] * 2
    else:
        families_per_split = ["F1", "F2", "F3", "F4", "F5"] * 3 + ["AMB"] * 5

    for split in ("dev", "test"):
        logger.info("Generating %s split packages (%d cases)...", split, len(families_per_split))
        for idx, fam in enumerate(families_per_split, start=1):
            case_id = f"{split.upper()}_{idx:03d}"
            difficulty = "hard" if (idx % 3 == 0) else "easy"
            generate_package(case_id, split, fam, difficulty, out_dir, rng)

    logger.info("Synthetic dataset generation complete at: %s", out_dir.resolve())


def main() -> None:
    parser = argparse.ArgumentParser(description="TestTrace Guard Synthetic Dataset Generator")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    parser.add_argument("--out", type=Path, default=Path("data/synthetic"), help="Target output directory")
    parser.add_argument("--eval-mode", choices=["standard", "turbo"], default="standard", help="Eval dataset size")
    args = parser.parse_args()

    generate_all(seed=args.seed, out_dir=args.out, eval_mode=args.eval_mode)


if __name__ == "__main__":
    main()