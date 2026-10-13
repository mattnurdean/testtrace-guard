"""Deterministic analytics engine for RF test failure triage."""

import csv
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from testtrace.schemas import (
    AnalyticsResult,
    EvidenceFact,
    GoldenRefRow,
    InvestigationPackage,
    LimitRow,
    MeasurementRow,
    StationHistoryRow,
)


def load_package(package_dir: Path, target_unit_id: str = "DUT_017") -> InvestigationPackage:
    """Load and parse an investigation package directory into Pydantic models."""
    case_id = package_dir.name

    def read_csv(filename: str) -> list[dict[str, Any]]:
        file_path = package_dir / filename
        if not file_path.exists():
            return []
        with open(file_path, mode="r", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    measurements = [MeasurementRow.model_validate(r) for r in read_csv("measurements.csv")]
    limits = [LimitRow.model_validate(r) for r in read_csv("limits.csv")]
    golden_ref = [GoldenRefRow.model_validate(r) for r in read_csv("golden_reference.csv")]
    station_hist = [StationHistoryRow.model_validate(r) for r in read_csv("station_history.csv")]

    return InvestigationPackage(
        case_id=case_id,
        measurements=measurements,
        limits=limits,
        golden_reference=golden_ref,
        station_history=station_hist,
        target_unit_id=target_unit_id,
    )


def calculate_welch_t_stat(sample1: list[float], sample2: list[float]) -> tuple[float, float]:
    """Compute Welch's t-statistic and approximate two-tailed p-value using erf."""
    n1, n2 = len(sample1), len(sample2)
    if n1 < 2 or n2 < 2:
        return 0.0, 1.0

    m1 = sum(sample1) / n1
    m2 = sum(sample2) / n2

    v1 = sum((x - m1) ** 2 for x in sample1) / (n1 - 1)
    v2 = sum((x - m2) ** 2 for x in sample2) / (n2 - 1)

    se = math.sqrt((v1 / n1) + (v2 / n2))
    if se == 0:
        return 0.0, 1.0

    t_stat = (m1 - m2) / se

    # Normal approximation for p-value
    p_val = math.erfc(abs(t_stat) / math.sqrt(2))
    return t_stat, p_val


def run_analytics(pkg: InvestigationPackage) -> AnalyticsResult:
    """Execute deterministic measurement analytics and emit evidence facts."""
    start_time = time.perf_counter()
    facts: list[EvidenceFact] = []
    fact_seq = 1

    def next_fact_id() -> str:
        nonlocal fact_seq
        fid = f"E-{fact_seq:03d}"
        fact_seq += 1
        return fid

    # Build lookup tables
    limits_lookup: dict[tuple[str, float, str], LimitRow] = {}
    for lim in pkg.limits:
        limits_lookup[(lim.test_name, lim.freq_ghz, lim.product_revision)] = lim

    golden_lookup: dict[tuple[str, float], GoldenRefRow] = {}
    for g in pkg.golden_reference:
        golden_lookup[(g.test_name, g.freq_ghz)] = g

    # 1. Analyze Station History (Changes & Calibration)
    has_valid_cal = True
    ref_timestamps: list[datetime] = []
    for m in pkg.measurements:
        try:
            ref_timestamps.append(datetime.fromisoformat(m.timestamp.replace("Z", "+00:00")))
        except ValueError:
            pass
    active_test_date = max(ref_timestamps) if ref_timestamps else datetime.now(timezone.utc)

    for hist in pkg.station_history:
        # Check configuration / hardware change
        if hist.recent_change and hist.recent_change.lower() != "none":
            facts.append(
                EvidenceFact(
                    fact_id=next_fact_id(),
                    category="CONFIG_CHANGE",
                    description=f"Station {hist.station_id} recorded change: {hist.recent_change} at {hist.recent_change_at or 'recent'}",
                    metric_name="station_configuration",
                    station_id=hist.station_id,
                    severity="WARNING",
                    source_trace=f"station_history.csv:{hist.station_id}",
                )
            )

        # Check calibration status
        if not hist.calibration_due_date:
            has_valid_cal = False
            facts.append(
                EvidenceFact(
                    fact_id=next_fact_id(),
                    category="DATA_GAP",
                    description=f"Station {hist.station_id} missing calibration due date in maintenance ledger.",
                    metric_name="calibration_due_date",
                    station_id=hist.station_id,
                    severity="WARNING",
                    source_trace=f"station_history.csv:{hist.station_id}",
                )
            )
        else:
            try:
                due_date = datetime.strptime(hist.calibration_due_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if due_date < active_test_date:
                    days_overdue = (active_test_date - due_date).days
                    facts.append(
                        EvidenceFact(
                            fact_id=next_fact_id(),
                            category="CALIBRATION_STATUS",
                            description=f"Station {hist.station_id} calibration overdue by {days_overdue} days (due {hist.calibration_due_date}).",
                            metric_name="calibration_overdue_days",
                            station_id=hist.station_id,
                            delta=float(days_overdue),
                            threshold=0.0,
                            severity="CRITICAL",
                            source_trace=f"station_history.csv:{hist.station_id}",
                        )
                    )
            except ValueError:
                pass

    # 2. Golden Reference Verification
    golden_measurements = [m for m in pkg.measurements if m.unit_type == "GOLDEN"]
    has_golden_data = len(golden_measurements) > 0

    if not has_golden_data:
        facts.append(
            EvidenceFact(
                fact_id=next_fact_id(),
                category="DATA_GAP",
                description="Zero golden reference verification runs present in test package.",
                metric_name="golden_verification",
                severity="WARNING",
                source_trace="measurements.csv:unit_type=GOLDEN",
            )
        )
    else:
        # Group golden measurements by (station_id, test_name, freq_ghz)
        golden_grouped: dict[tuple[str, str, float], list[float]] = {}
        for m in golden_measurements:
            golden_grouped.setdefault((m.station_id, m.test_name, m.freq_ghz), []).append(m.measured_value)

        for (st_id, t_name, freq), vals in golden_grouped.items():
            ref_entry = golden_lookup.get((t_name, freq))
            if not ref_entry:
                continue

            mean_val = sum(vals) / len(vals)
            deviation = mean_val - ref_entry.ref_value
            if abs(deviation) > ref_entry.tol:
                facts.append(
                    EvidenceFact(
                        fact_id=next_fact_id(),
                        category="GOLDEN_DEVIATION",
                        description=(
                            f"Station {st_id} golden reference check failed on {t_name} @ {freq} GHz: "
                            f"mean {mean_val:.3f} {ref_entry.unit} deviates by {deviation:+.3f} {ref_entry.unit} (tol +/-{ref_entry.tol:.2f})."
                        ),
                        metric_name=t_name,
                        station_id=st_id,
                        unit_id="GOLDEN_01",
                        freq_ghz=freq,
                        measured_value=round(mean_val, 3),
                        reference_value=round(ref_entry.ref_value, 3),
                        delta=round(deviation, 3),
                        threshold=ref_entry.tol,
                        severity="CRITICAL",
                        source_trace=f"measurements.csv:station_id={st_id}&unit_id=GOLDEN_01",
                    )
                )

    # 3. Limit Compliance & Violations on Target Unit
    target_measurements = [m for m in pkg.measurements if m.unit_id == pkg.target_unit_id]
    failed_tests: set[str] = set()
    affected_stations: set[str] = set()

    for m in target_measurements:
        lim = limits_lookup.get((m.test_name, m.freq_ghz, m.product_revision))
        if not lim:
            continue

        is_fail = False
        delta_lim = 0.0
        lim_val = None

        if lim.lower_limit is not None and m.measured_value < lim.lower_limit:
            is_fail = True
            delta_lim = m.measured_value - lim.lower_limit
            lim_val = lim.lower_limit
        elif lim.upper_limit is not None and m.measured_value > lim.upper_limit:
            is_fail = True
            delta_lim = m.measured_value - lim.upper_limit
            lim_val = lim.upper_limit

        if is_fail:
            failed_tests.add(m.test_name)
            affected_stations.add(m.station_id)
            facts.append(
                EvidenceFact(
                    fact_id=next_fact_id(),
                    category="DUT_SPEC_VIOLATION",
                    description=(
                        f"Unit {pkg.target_unit_id} failed limit on {m.test_name} @ {m.freq_ghz} GHz on {m.station_id}: "
                        f"{m.measured_value:.3f} {m.unit} (limit {lim_val}, delta {delta_lim:+.3f})."
                    ),
                    metric_name=m.test_name,
                    station_id=m.station_id,
                    unit_id=pkg.target_unit_id,
                    freq_ghz=m.freq_ghz,
                    measured_value=m.measured_value,
                    reference_value=lim_val,
                    delta=round(delta_lim, 3),
                    threshold=lim.meas_uncertainty,
                    severity="CRITICAL",
                    source_trace=f"measurements.csv:run_id={m.run_id}",
                )
            )

    # 4. Station Delta & Inter-Station Reproducibility on Target Unit
    st_grouped: dict[tuple[str, float], dict[str, list[float]]] = {}
    for m in target_measurements:
        st_grouped.setdefault((m.test_name, m.freq_ghz), {}).setdefault(m.station_id, []).append(m.measured_value)

    for (t_name, freq), stations_data in st_grouped.items():
        if "ST-A" in stations_data and "ST-B" in stations_data:
            vals_a = stations_data["ST-A"]
            vals_b = stations_data["ST-B"]
            mean_a = sum(vals_a) / len(vals_a)
            mean_b = sum(vals_b) / len(vals_b)
            diff = mean_a - mean_b

            # Welch's t-test
            t_stat, p_val = calculate_welch_t_stat(vals_a, vals_b)

            # Check significant station shift (> 0.5 dB for loss/gain or p < 0.01)
            lim_entry = limits_lookup.get((t_name, freq, "REV_A"))
            uncertainty = lim_entry.meas_uncertainty if lim_entry else 0.20
            if abs(diff) > 2.0 * uncertainty or p_val < 0.01:
                facts.append(
                    EvidenceFact(
                        fact_id=next_fact_id(),
                        category="STATION_DELTA",
                        description=(
                            f"Significant station delta on {t_name} @ {freq} GHz: "
                            f"ST-A mean {mean_a:.3f} vs ST-B mean {mean_b:.3f} (delta {diff:+.3f}, p={p_val:.4f})."
                        ),
                        metric_name=t_name,
                        unit_id=pkg.target_unit_id,
                        freq_ghz=freq,
                        delta=round(diff, 3),
                        threshold=round(2.0 * uncertainty, 3),
                        p_value=round(p_val, 5),
                        severity="WARNING" if abs(diff) < 1.5 else "CRITICAL",
                        source_trace=f"measurements.csv:unit_id={pkg.target_unit_id}&stations=ST-A,ST-B",
                    )
                )

    # 5. Repeatability & Fixture Contact Re-seat Analysis
    reconnect_groups: dict[tuple[str, str, float], dict[int, list[float]]] = {}
    for m in target_measurements:
        reconnect_groups.setdefault((m.station_id, m.test_name, m.freq_ghz), {}).setdefault(m.reconnect_idx, []).append(m.measured_value)

    for (st_id, t_name, freq), rec_data in reconnect_groups.items():
        # High sweep-to-sweep jitter within reconnect 0
        if 0 in rec_data and len(rec_data[0]) >= 3:
            s0 = rec_data[0]
            mean_s0 = sum(s0) / len(s0)
            variance = sum((x - mean_s0) ** 2 for x in s0) / (len(s0) - 1)
            sigma = math.sqrt(variance)

            # Compare against reconnect 1 if present
            if 1 in rec_data and len(rec_data[1]) >= 1:
                mean_s1 = sum(rec_data[1]) / len(rec_data[1])
                reconnect_shift = abs(mean_s0 - mean_s1)
                if reconnect_shift > 0.8 or sigma > 0.3:
                    facts.append(
                        EvidenceFact(
                            fact_id=next_fact_id(),
                            category="REPEATABILITY_VARIANCE",
                            description=(
                                f"Fixture contact instability detected on {st_id} for {t_name} @ {freq} GHz: "
                                f"reconnect shift {reconnect_shift:.3f} dB with intra-run sigma {sigma:.3f}."
                            ),
                            metric_name=t_name,
                            station_id=st_id,
                            unit_id=pkg.target_unit_id,
                            freq_ghz=freq,
                            delta=round(reconnect_shift, 3),
                            threshold=0.8,
                            severity="CRITICAL",
                            source_trace=f"measurements.csv:unit_id={pkg.target_unit_id}&reconnect_idx=0,1",
                        )
                    )

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return AnalyticsResult(
        case_id=pkg.case_id,
        facts=facts,
        failed_tests=sorted(list(failed_tests)),
        affected_stations=sorted(list(affected_stations)),
        has_golden_data=has_golden_data,
        has_valid_cal=has_valid_cal,
        total_measurements=len(pkg.measurements),
        execution_time_ms=round(elapsed_ms, 2),
    )