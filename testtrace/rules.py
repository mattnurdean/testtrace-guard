"""Deterministic RF triage rule engine for TestTrace Guard."""

import time
from typing import Any
from testtrace.schemas import (
    AnalyticsResult,
    EvidenceFact,
    InvestigationPackage,
    RuleEvaluationResult,
    RuleMatch,
)

ACTION_MAP = {
    "STATION_CONFIGURATION": (
        "Halt station testing. Audit recent configuration and cable loss compensation "
        "table changes. Restore verified baseline compensation table."
    ),
    "DUT_DEFECT": (
        "Quarantine unit for physical failure analysis. Inspect RF shielding, internal "
        "isolation, and active component solder joints."
    ),
    "FIXTURE_CONTACT": (
        "Inspect fixture RF launch pins and contact interfaces. Verify mechanical "
        "alignment, clamping pressure, and repeat test."
    ),
    "INSTRUMENT_CALIBRATION": (
        "Remove station from active line. Perform comprehensive instrument calibration "
        "and verify against certified reference standards."
    ),
    "SPEC_OR_REVISION_MISMATCH": (
        "Align test limits with unit product revision. Verify sequence version and "
        "prevent cross-revision test execution."
    ),
    "INSUFFICIENT_EVIDENCE": (
        "Perform golden unit verification check across both stations and update "
        "instrument calibration records before re-testing."
    ),
}

KB_PREFIX_MAP = {
    "STATION_CONFIGURATION": "MAN-4",
    "DUT_DEFECT": "MAN-6",
    "FIXTURE_CONTACT": "MAN-5",
    "INSTRUMENT_CALIBRATION": "MAN-7",
    "SPEC_OR_REVISION_MISMATCH": "MAN-8",
    "INSUFFICIENT_EVIDENCE": "MAN-9",
}

SIDE_MAP = {
    "STATION_CONFIGURATION": "MEASUREMENT_SYSTEM",
    "DUT_DEFECT": "DUT",
    "FIXTURE_CONTACT": "MEASUREMENT_SYSTEM",
    "INSTRUMENT_CALIBRATION": "MEASUREMENT_SYSTEM",
    "SPEC_OR_REVISION_MISMATCH": "SPECIFICATION",
    "INSUFFICIENT_EVIDENCE": "UNDETERMINED",
}


def evaluate_rules(analytics: AnalyticsResult, pkg: InvestigationPackage) -> RuleEvaluationResult:
    """Evaluate deterministic triage heuristics against analytical evidence facts."""
    start_time = time.perf_counter()
    fired_rules: list[RuleMatch] = []
    category_scores: dict[str, float] = {
        "STATION_CONFIGURATION": 0.0,
        "DUT_DEFECT": 0.0,
        "FIXTURE_CONTACT": 0.0,
        "INSTRUMENT_CALIBRATION": 0.0,
        "SPEC_OR_REVISION_MISMATCH": 0.0,
        "INSUFFICIENT_EVIDENCE": 0.0,
    }

    # Index facts by category and station
    facts_by_category: dict[str, list[EvidenceFact]] = {}
    for f in analytics.facts:
        facts_by_category.setdefault(f.category, []).append(f)

    # 1. Check Data Gaps & Ambiguity (Rule R-GAP-001)
    gap_facts = facts_by_category.get("DATA_GAP", [])
    if not analytics.has_golden_data or not analytics.has_valid_cal or gap_facts:
        gap_ids = [f.fact_id for f in gap_facts]
        fired_rules.append(
            RuleMatch(
                rule_id="R-GAP-001",
                name="Data Completeness Gap",
                description="Investigation package lacks golden reference verification or valid calibration data.",
                target_category="INSUFFICIENT_EVIDENCE",
                target_side="UNDETERMINED",
                weight=3.5,
                matched_fact_ids=gap_ids,
            )
        )
        category_scores["INSUFFICIENT_EVIDENCE"] += 3.5

    # 2. Check Station Configuration & Golden Deviation (Rule R-CFG-001 & R-GLD-001)
    config_facts = facts_by_category.get("CONFIG_CHANGE", [])
    golden_facts = facts_by_category.get("GOLDEN_DEVIATION", [])
    station_delta_facts = facts_by_category.get("STATION_DELTA", [])

    st_a_golden = [f for f in golden_facts if f.station_id == "ST-A"]
    st_b_golden = [f for f in golden_facts if f.station_id == "ST-B"]
    st_a_cfg = [f for f in config_facts if f.station_id == "ST-A"]

    if st_a_golden and st_a_cfg:
        matched_ids = [f.fact_id for f in st_a_golden] + [f.fact_id for f in st_a_cfg]
        fired_rules.append(
            RuleMatch(
                rule_id="R-CFG-001",
                name="Station Configuration Offset",
                description="Golden standard deviation coincides with recorded configuration change on Station ST-A.",
                target_category="STATION_CONFIGURATION",
                target_side="MEASUREMENT_SYSTEM",
                weight=5.0,
                matched_fact_ids=matched_ids,
            )
        )
        category_scores["STATION_CONFIGURATION"] += 5.0

    elif golden_facts and not (st_a_golden and st_b_golden):
        # Asymmetric golden failure on one station
        matched_ids = [f.fact_id for f in golden_facts]
        fired_rules.append(
            RuleMatch(
                rule_id="R-GLD-001",
                name="Isolated Station Golden Shift",
                description="Golden standard deviation detected on a single test station.",
                target_category="STATION_CONFIGURATION",
                target_side="MEASUREMENT_SYSTEM",
                weight=4.0,
                matched_fact_ids=matched_ids,
            )
        )
        category_scores["STATION_CONFIGURATION"] += 4.0

    if station_delta_facts and (st_a_golden or st_a_cfg):
        category_scores["STATION_CONFIGURATION"] += 1.5

    # 3. Check Multi-Station DUT Defect (Rule R-DUT-001)
    spec_violations = facts_by_category.get("DUT_SPEC_VIOLATION", [])
    violating_stations = {f.station_id for f in spec_violations if f.station_id}

    if len(violating_stations) >= 2 and not golden_facts:
        matched_ids = [f.fact_id for f in spec_violations]
        fired_rules.append(
            RuleMatch(
                rule_id="R-DUT-001",
                name="Cross-Station DUT Defect",
                description="Target unit fails specification limits across multiple stations while golden units pass.",
                target_category="DUT_DEFECT",
                target_side="DUT",
                weight=5.0,
                matched_fact_ids=matched_ids,
            )
        )
        category_scores["DUT_DEFECT"] += 5.0

    elif spec_violations and not golden_facts and not config_facts and not gap_facts:
        matched_ids = [f.fact_id for f in spec_violations]
        category_scores["DUT_DEFECT"] += 3.0

    # 4. Check Fixture Contact & Repeatability (Rule R-FIX-001)
    rep_facts = facts_by_category.get("REPEATABILITY_VARIANCE", [])
    if rep_facts:
        matched_ids = [f.fact_id for f in rep_facts]
        fired_rules.append(
            RuleMatch(
                rule_id="R-FIX-001",
                name="Fixture Contact Instability",
                description="High intra-run repeatability sigma or large reconnect shift detected upon re-seating.",
                target_category="FIXTURE_CONTACT",
                target_side="MEASUREMENT_SYSTEM",
                weight=5.0,
                matched_fact_ids=matched_ids,
            )
        )
        category_scores["FIXTURE_CONTACT"] += 5.0

    # 5. Check Instrument Calibration Overdue (Rule R-CAL-001)
    cal_facts = facts_by_category.get("CALIBRATION_STATUS", [])
    if cal_facts:
        matched_ids = [f.fact_id for f in cal_facts]
        fired_rules.append(
            RuleMatch(
                rule_id="R-CAL-001",
                name="Instrument Calibration Expired",
                description="Station instrument calibration is overdue by more than 30 days.",
                target_category="INSTRUMENT_CALIBRATION",
                target_side="MEASUREMENT_SYSTEM",
                weight=5.0,
                matched_fact_ids=matched_ids,
            )
        )
        category_scores["INSTRUMENT_CALIBRATION"] += 5.0

    # 6. Check Revision / Specification Mismatch (Rule R-REV-001)
    target_revs = {m.product_revision for m in pkg.measurements if m.unit_id == pkg.target_unit_id}
    limit_revs = {l.product_revision for l in pkg.limits}
    has_rev_mismatch = bool(target_revs and not target_revs.issubset(limit_revs))

    if has_rev_mismatch:
        rev_str = ", ".join(sorted(list(target_revs)))
        lim_str = ", ".join(sorted(list(limit_revs)))
        fired_rules.append(
            RuleMatch(
                rule_id="R-REV-001",
                name="Product Revision Mismatch",
                description=f"Unit revision ({rev_str}) does not match active specification limit revision ({lim_str}).",
                target_category="SPEC_OR_REVISION_MISMATCH",
                target_side="SPECIFICATION",
                weight=5.0,
                matched_fact_ids=[],
            )
        )
        category_scores["SPEC_OR_REVISION_MISMATCH"] += 5.0

    # Determine Winning Category
    # In ambiguous cases or heavy data gaps without confirmed hardware faults, prioritize INSUFFICIENT_EVIDENCE
    best_cat = "INSUFFICIENT_EVIDENCE"
    best_score = 0.0

    # If golden verification is completely missing and no multi-station hardware confirmation exists, force ambiguity
    if not analytics.has_golden_data and category_scores["DUT_DEFECT"] < 4.0:
        best_cat = "INSUFFICIENT_EVIDENCE"
        best_score = max(category_scores["INSUFFICIENT_EVIDENCE"], 3.5)
    else:
        for cat, score in category_scores.items():
            if score > best_score:
                best_score = score
                best_cat = cat

    # Confidence Calculation
    if best_cat == "INSUFFICIENT_EVIDENCE":
        status = "NEEDS_MORE_DATA"
        confidence = 0.88 if len(gap_facts) >= 2 else 0.78
    else:
        status = "PLAN_READY_FOR_REVIEW"
        total_score = sum(category_scores.values())
        raw_conf = best_score / total_score if total_score > 0 else 0.5
        confidence = min(0.96, max(0.80, round(raw_conf * 0.96, 2)))

    # Collect Supporting Fact IDs
    supporting_ids: set[str] = set()
    for r in fired_rules:
        if r.target_category == best_cat or (best_cat == "INSUFFICIENT_EVIDENCE" and r.rule_id == "R-GAP-001"):
            supporting_ids.update(r.matched_fact_ids)

    # If no specific rule facts were collected, provide all relevant category facts
    if not supporting_ids and best_cat in ("INSUFFICIENT_EVIDENCE", "SPEC_OR_REVISION_MISMATCH"):
        supporting_ids.update(f.fact_id for f in analytics.facts if f.category in ("DATA_GAP", "DUT_SPEC_VIOLATION"))

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return RuleEvaluationResult(
        case_id=pkg.case_id,
        recommended_category=best_cat,
        recommended_side=SIDE_MAP[best_cat],
        status=status,
        confidence=confidence,
        fired_rules=fired_rules,
        supporting_fact_ids=sorted(list(supporting_ids)),
        suggested_action=ACTION_MAP[best_cat],
        suggested_kb_prefix=KB_PREFIX_MAP[best_cat],
        execution_time_ms=round(elapsed_ms, 3),
    )