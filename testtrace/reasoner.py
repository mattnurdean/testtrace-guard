"""Evidence-grounded LLM reasoner and diagnostic report generator for TestTrace Guard."""

import json
import logging
import os
import sys
import time
from typing import Any, Optional
from openai import OpenAI, OpenAIError

from testtrace.schemas import (
    AnalyticsResult,
    DiagnosticReport,
    RetrievalResult,
    RuleEvaluationResult,
)
from testtrace.validator import validate_and_sanitize_report

logger = logging.getLogger("testtrace.reasoner")


def build_system_prompt() -> str:
    """Return strict system instruction guiding evidence-grounded RF diagnostics."""
    return (
        "You are TestTrace Guard, an expert RF test engineering diagnostics assistant for automated hardware manufacturing. "
        "Your task is to review deterministic analytical facts, rule engine recommendations, and standard operating procedures (SOP), "
        "and produce a strictly grounded, hallucination-free root-cause triage report.\n\n"
        "RULES:\n"
        "1. Output ONLY valid JSON. No conversational preamble, no markdown backticks (no ```json).\n"
        "2. You may ONLY cite fact IDs that exist in the provided Evidence Facts list. Do not invent facts.\n"
        "3. Your root_cause_summary must directly reference numerical measurements, station IDs, and frequencies.\n"
        "4. Your recommended_actions must align with the retrieved SOP protocol.\n"
        "5. The JSON must match the following schema:\n"
        "{\n"
        '  "case_id": str,\n'
        '  "category": str,\n'
        '  "target_side": str,\n'
        '  "status": "PLAN_READY_FOR_REVIEW" | "NEEDS_MORE_DATA",\n'
        '  "confidence": float,\n'
        '  "primary_kb_doc": str,\n'
        '  "root_cause_summary": str,\n'
        '  "supporting_fact_ids": list[str],\n'
        '  "recommended_actions": list[str],\n'
        '  "preventative_actions": list[str]\n'
        "}"
    )


def build_user_prompt(
    analytics: AnalyticsResult,
    rule_res: RuleEvaluationResult,
    retrieval: RetrievalResult,
) -> str:
    """Construct structured prompt including evidence facts, rule matches, and retrieved SOP."""
    facts_block = "\n".join(
        f"- [{f.fact_id}] ({f.category}, {f.severity}) {f.description}" for f in analytics.facts
    )

    rules_block = "\n".join(
        f"- {r.rule_id} ({r.name}): {r.description} [Matched: {', '.join(r.matched_fact_ids)}]"
        for r in rule_res.fired_rules
    )

    return (
        f"INVESTIGATION CASE: {analytics.case_id}\n"
        f"TARGET UNIT: DUT_017\n"
        f"FAILED TESTS: {', '.join(analytics.failed_tests) or 'None'}\n"
        f"AFFECTED STATIONS: {', '.join(analytics.affected_stations) or 'None'}\n\n"
        f"=== DETERMINISTIC EVIDENCE FACTS ===\n{facts_block}\n\n"
        f"=== RULE ENGINE ASSESSMENT ===\n"
        f"Recommended Category: {rule_res.recommended_category}\n"
        f"Target Domain: {rule_res.recommended_side}\n"
        f"Confidence: {rule_res.confidence:.2f}\n"
        f"Fired Rules:\n{rules_block}\n\n"
        f"=== RETRIEVED SOP CONTEXT ===\n{retrieval.formatted_context}\n\n"
        "Generate the diagnostic JSON report now."
    )


def generate_mock_report_data(
    analytics: AnalyticsResult,
    rule_res: RuleEvaluationResult,
    retrieval: RetrievalResult,
) -> dict[str, Any]:
    """Deterministically synthesize a schema-compliant diagnostic report without external LLM calls."""
    doc = retrieval.primary_doc

    if rule_res.recommended_category == "STATION_CONFIGURATION":
        summary = (
            f"Automated analysis identified systematic insertion loss offset on Station ST-A following recent "
            f"configuration changes. Golden reference verification confirms {doc.title} failure on ST-A while ST-B remains within tolerance."
        )
    elif rule_res.recommended_category == "DUT_DEFECT":
        summary = (
            f"Target unit DUT_017 consistently violated RF specification limits across multiple independent test stations (ST-A and ST-B) "
            f"while golden verification units passed, isolating the root cause to intrinsic DUT hardware failure."
        )
    elif rule_res.recommended_category == "FIXTURE_CONTACT":
        summary = (
            f"Large reconnect delta shifts and elevated intra-run repeatability sigma indicate mechanical contact instability "
            f"or pogo pin interface wear on fixture {doc.doc_id}."
        )
    elif rule_res.recommended_category == "INSTRUMENT_CALIBRATION":
        summary = (
            f"Station instrumentation calibration interval is overdue, producing systematic measurement drift across multiple parametric tests."
        )
    elif rule_res.recommended_category == "SPEC_OR_REVISION_MISMATCH":
        summary = (
            f"Parametric measurements reflect design parameters of updated product revision evaluated against legacy specification limits."
        )
    else:
        summary = (
            f"Investigation package lacks essential golden reference verification baselines and maintenance records. "
            f"Triage status set to NEEDS_MORE_DATA pending verification sweep."
        )

    # Pass all action items from the retrieved standard operating procedure
    actions = list(doc.action_items) if doc.action_items else [rule_res.suggested_action]
    preventative = [
        "Enforce automated pre-flight golden standard checks at start of each shift.",
        "Integrate automated configuration change audit logging with continuous limit tracking.",
    ]

    return {
        "case_id": analytics.case_id,
        "category": rule_res.recommended_category,
        "target_side": rule_res.recommended_side,
        "status": rule_res.status,
        "confidence": rule_res.confidence,
        "primary_kb_doc": doc.doc_id,
        "root_cause_summary": summary,
        "supporting_fact_ids": rule_res.supporting_fact_ids,
        "recommended_actions": actions,
        "preventative_actions": preventative,
    }


def generate_report(
    analytics: AnalyticsResult,
    rule_res: RuleEvaluationResult,
    retrieval: RetrievalResult,
    mode: Optional[str] = None,
    client: Optional[OpenAI] = None,
) -> DiagnosticReport:
    """Execute LLM diagnostic reasoning with validation and fallback guarantees."""
    start_time = time.perf_counter()

    if mode is None:
        mode = os.getenv("LLM_MODE", "mock").lower()

    raw_data: dict[str, Any]

    if mode == "vllm":
        base_url = os.getenv("LLM_BASE_URL", "http://localhost:8000/v1")
        api_key = os.getenv("LLM_API_KEY", "mock-key")
        model = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")

        if client is None:
            client = OpenAI(base_url=base_url, api_key=api_key)

        sys_prompt = build_system_prompt()
        user_prompt = build_user_prompt(analytics, rule_res, retrieval)

        for attempt in range(2):
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.0,
                    max_tokens=800,
                )
                raw_json_str = completion.choices[0].message.content or ""
                cleaned = raw_json_str.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()

                raw_data = json.loads(cleaned)
                break
            except (OpenAIError, json.JSONDecodeError, Exception) as exc:
                logger.warning("vLLM attempt %d failed (%s); retrying...", attempt + 1, str(exc))
                if attempt == 1:
                    logger.error("vLLM reasoning failed; reverting to mock deterministic synthesizer.")
                    raw_data = generate_mock_report_data(analytics, rule_res, retrieval)
    else:
        raw_data = generate_mock_report_data(analytics, rule_res, retrieval)

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    raw_data["execution_time_ms"] = round(elapsed_ms, 2)

    val_res = validate_and_sanitize_report(raw_data, analytics, rule_res, retrieval)
    return val_res.sanitized_report