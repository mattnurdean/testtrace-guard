"""Deterministic guardrail validator for LLM-generated diagnostic reports."""

from typing import Any, Union
from testtrace.schemas import (
    AnalyticsResult,
    DiagnosticReport,
    RetrievalResult,
    RuleEvaluationResult,
    ValidationResult,
)

VALID_DOMAINS = {
    "STATION_CONFIGURATION": "MEASUREMENT_SYSTEM",
    "DUT_DEFECT": "DUT",
    "FIXTURE_CONTACT": "MEASUREMENT_SYSTEM",
    "INSTRUMENT_CALIBRATION": "MEASUREMENT_SYSTEM",
    "SPEC_OR_REVISION_MISMATCH": "SPECIFICATION",
    "INSUFFICIENT_EVIDENCE": "UNDETERMINED",
}


def validate_and_sanitize_report(
    raw_input: Union[dict[str, Any], DiagnosticReport],
    analytics: AnalyticsResult,
    rule_res: RuleEvaluationResult,
    retrieval: RetrievalResult,
) -> ValidationResult:
    """Validate, ground, and sanitize diagnostic reports against deterministic ground truth."""
    discrepancies: list[str] = []
    overrides: list[str] = []

    # 1. Cast to DiagnosticReport or construct robust fallback if structure is malformed
    if isinstance(raw_input, DiagnosticReport):
        report_dict = raw_input.model_dump()
    elif isinstance(raw_input, dict):
        report_dict = dict(raw_input)
    else:
        discrepancies.append("MALFORMED_INPUT: Input is neither dict nor DiagnosticReport; using deterministic fallback.")
        report_dict = {}

    # Safe field extractions with fallbacks
    case_id = report_dict.get("case_id") or analytics.case_id
    category = report_dict.get("category") or rule_res.recommended_category
    target_side = report_dict.get("target_side") or rule_res.recommended_side
    status = report_dict.get("status") or rule_res.status
    confidence = float(report_dict.get("confidence", rule_res.confidence))
    primary_kb_doc = report_dict.get("primary_kb_doc") or retrieval.primary_doc.doc_id
    root_cause = report_dict.get("root_cause_summary") or f"Identified issue within category {category}."
    supporting_facts = list(report_dict.get("supporting_fact_ids", rule_res.supporting_fact_ids))
    recommended_actions = list(report_dict.get("recommended_actions") or retrieval.primary_doc.action_items[:3])
    preventative_actions = list(report_dict.get("preventative_actions") or [])

    # 2. Fact Grounding Verification (Hallucination Guard)
    valid_fact_ids = {f.fact_id for f in analytics.facts}
    sanitized_fact_ids: list[str] = []
    for fid in supporting_facts:
        if fid in valid_fact_ids:
            sanitized_fact_ids.append(fid)
        else:
            discrepancies.append(f"HALLUCINATED_FACT_ID: Removed fact ID '{fid}' not present in deterministic analytics.")

    if not sanitized_fact_ids:
        # Fallback to verified rule facts
        sanitized_fact_ids = [fid for fid in rule_res.supporting_fact_ids if fid in valid_fact_ids]
        discrepancies.append("EMPTY_FACTS: Restored supporting fact IDs from deterministic rule engine.")

    # 3. Category & Side Consistency Check
    if category != rule_res.recommended_category:
        if rule_res.confidence >= 0.80:
            overrides.append(
                f"CATEGORY_CONFLICT: Overriding LLM category '{category}' with high-confidence rule engine category '{rule_res.recommended_category}' (conf {rule_res.confidence:.2f})."
            )
            category = rule_res.recommended_category
            target_side = rule_res.recommended_side
        else:
            discrepancies.append(
                f"CATEGORY_DRIFT: LLM category '{category}' differs from low-confidence rule recommendation '{rule_res.recommended_category}'."
            )

    # Enforce standard architectural domain
    expected_domain = VALID_DOMAINS.get(category, target_side)
    if target_side != expected_domain:
        overrides.append(f"DOMAIN_MISMATCH: Corrected target side from '{target_side}' to standard domain '{expected_domain}'.")
        target_side = expected_domain

    # 4. Standard Operating Procedure Alignment
    if not primary_kb_doc.startswith(retrieval.primary_doc.prefix):
        discrepancies.append(
            f"KB_MISMATCH: Aligning primary KB doc '{primary_kb_doc}' to retrieved reference '{retrieval.primary_doc.doc_id}'."
        )
        primary_kb_doc = retrieval.primary_doc.doc_id

    # 5. Status & Ambiguity Protocol Check
    if category == "INSUFFICIENT_EVIDENCE" and status != "NEEDS_MORE_DATA":
        overrides.append("STATUS_ENFORCEMENT: Enforcing status 'NEEDS_MORE_DATA' for INSUFFICIENT_EVIDENCE triage.")
        status = "NEEDS_MORE_DATA"
    elif category != "INSUFFICIENT_EVIDENCE" and status == "NEEDS_MORE_DATA" and rule_res.status == "PLAN_READY_FOR_REVIEW":
        overrides.append("STATUS_ENFORCEMENT: Setting status 'PLAN_READY_FOR_REVIEW' for definitive triage finding.")
        status = "PLAN_READY_FOR_REVIEW"

    # 6. Action Grounding Check
    if not recommended_actions:
        recommended_actions = retrieval.primary_doc.action_items[:3] or [rule_res.suggested_action]
        discrepancies.append("ACTION_RESTORED: Injected mandatory action items from retrieved standard operating procedure.")

    # Determine final validator verdict
    if overrides:
        verdict = "CORRECTED"
    elif discrepancies:
        verdict = "FLAGGED"
    else:
        verdict = "PASS"

    sanitized_report = DiagnosticReport(
        case_id=case_id,
        category=category,
        target_side=target_side,
        status=status,
        confidence=round(confidence, 2),
        primary_kb_doc=primary_kb_doc,
        root_cause_summary=root_cause,
        supporting_fact_ids=sanitized_fact_ids,
        recommended_actions=recommended_actions,
        preventative_actions=preventative_actions,
        validator_verdict=verdict,
        discrepancies=discrepancies + overrides,
        execution_time_ms=report_dict.get("execution_time_ms", 0.0),
    )

    return ValidationResult(
        is_valid=True,
        verdict=verdict,
        sanitized_report=sanitized_report,
        discrepancies=discrepancies,
        overrides_applied=overrides,
    )