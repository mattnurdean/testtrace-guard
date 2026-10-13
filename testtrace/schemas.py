"""Pydantic v2 schemas for TestTrace Guard data, evidence facts, triage rules, retrieval, reports, and pipeline runs."""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class MeasurementRow(BaseModel):
    run_id: str
    timestamp: str
    unit_id: str
    unit_type: str  # "DUT" or "GOLDEN"
    product_revision: str
    station_id: str
    fixture_id: str
    instrument_id: str
    test_name: str
    freq_ghz: float
    sweep_idx: int
    reconnect_idx: int
    measured_value: float
    unit: str
    temperature_c: float
    operator_id: str
    test_sequence_version: str
    limits_version: str

    @field_validator("freq_ghz", "measured_value", "temperature_c", mode="before")
    @classmethod
    def parse_float(cls, v: Any) -> float:
        return float(v)

    @field_validator("sweep_idx", "reconnect_idx", mode="before")
    @classmethod
    def parse_int(cls, v: Any) -> int:
        return int(v)


class LimitRow(BaseModel):
    limits_version: str
    product_revision: str
    test_name: str
    freq_ghz: float
    lower_limit: Optional[float] = None
    upper_limit: Optional[float] = None
    unit: str
    meas_uncertainty: float

    @field_validator("freq_ghz", "meas_uncertainty", mode="before")
    @classmethod
    def parse_float(cls, v: Any) -> float:
        return float(v)

    @field_validator("lower_limit", "upper_limit", mode="before")
    @classmethod
    def parse_optional_float(cls, v: Any) -> Optional[float]:
        if v is None or v == "":
            return None
        return float(v)


class GoldenRefRow(BaseModel):
    unit_id: str
    test_name: str
    freq_ghz: float
    ref_value: float
    tol: float
    unit: str

    @field_validator("freq_ghz", "ref_value", "tol", mode="before")
    @classmethod
    def parse_float(cls, v: Any) -> float:
        return float(v)


class StationHistoryRow(BaseModel):
    station_id: str
    instrument_id: str
    fixture_id: str
    calibration_due_date: Optional[str] = None
    last_reference_check: Optional[str] = None
    software_version: str
    configuration_version: str
    recent_change: str
    recent_change_at: Optional[str] = None
    historical_failure_rate: float

    @field_validator("historical_failure_rate", mode="before")
    @classmethod
    def parse_float(cls, v: Any) -> float:
        return float(v)

    @field_validator("calibration_due_date", "last_reference_check", "recent_change_at", mode="before")
    @classmethod
    def empty_to_none(cls, v: Any) -> Optional[str]:
        if not v or v == "":
            return None
        return str(v)


class InvestigationPackage(BaseModel):
    case_id: str
    measurements: list[MeasurementRow]
    limits: list[LimitRow]
    golden_reference: list[GoldenRefRow]
    station_history: list[StationHistoryRow]
    target_unit_id: str = "DUT_017"


class EvidenceFact(BaseModel):
    fact_id: str
    category: str  # GOLDEN_DEVIATION, STATION_DELTA, DUT_SPEC_VIOLATION, REPEATABILITY_VARIANCE, CALIBRATION_STATUS, CONFIG_CHANGE, DATA_GAP
    description: str
    metric_name: str
    station_id: Optional[str] = None
    unit_id: Optional[str] = None
    freq_ghz: Optional[float] = None
    measured_value: Optional[float] = None
    reference_value: Optional[float] = None
    delta: Optional[float] = None
    threshold: Optional[float] = None
    p_value: Optional[float] = None
    severity: str = "INFO"  # INFO, WARNING, CRITICAL
    source_trace: str


class AnalyticsResult(BaseModel):
    case_id: str
    facts: list[EvidenceFact]
    failed_tests: list[str]
    affected_stations: list[str]
    has_golden_data: bool
    has_valid_cal: bool
    total_measurements: int
    execution_time_ms: float


class RuleMatch(BaseModel):
    rule_id: str
    name: str
    description: str
    target_category: str
    target_side: str
    weight: float
    matched_fact_ids: list[str] = Field(default_factory=list)


class RuleEvaluationResult(BaseModel):
    case_id: str
    recommended_category: str
    recommended_side: str
    status: str  # "PLAN_READY_FOR_REVIEW" or "NEEDS_MORE_DATA"
    confidence: float
    fired_rules: list[RuleMatch]
    supporting_fact_ids: list[str]
    suggested_action: str
    suggested_kb_prefix: str
    execution_time_ms: float


class RetrievedDocument(BaseModel):
    doc_id: str
    prefix: str
    title: str
    category: str
    target_side: str
    score: float
    retrieval_method: str  # "ANCHOR_MATCH", "BM25_LEXICAL", "HYBRID"
    action_items: list[str] = Field(default_factory=list)
    excerpt: str
    file_path: str


class RetrievalResult(BaseModel):
    case_id: str
    query_text: str
    primary_doc: RetrievedDocument
    secondary_docs: list[RetrievedDocument] = Field(default_factory=list)
    formatted_context: str
    execution_time_ms: float


class DiagnosticReport(BaseModel):
    case_id: str
    category: str
    target_side: str
    status: str  # "PLAN_READY_FOR_REVIEW" or "NEEDS_MORE_DATA"
    confidence: float
    primary_kb_doc: str
    root_cause_summary: str
    supporting_fact_ids: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    preventative_actions: list[str] = Field(default_factory=list)
    validator_verdict: str = "PASS"  # "PASS", "CORRECTED", "FLAGGED"
    discrepancies: list[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0


class ValidationResult(BaseModel):
    is_valid: bool
    verdict: str  # "PASS", "CORRECTED", "FLAGGED"
    sanitized_report: DiagnosticReport
    discrepancies: list[str] = Field(default_factory=list)
    overrides_applied: list[str] = Field(default_factory=list)


class PipelineRunResult(BaseModel):
    run_id: str
    case_id: str
    timestamp: str
    mode: str
    analytics: AnalyticsResult
    rule_evaluation: RuleEvaluationResult
    retrieval: RetrievalResult
    report: DiagnosticReport
    total_execution_time_ms: float
    audit_file_path: Optional[str] = None


class AuditRecord(BaseModel):
    run_id: str
    case_id: str
    timestamp: str
    category: str
    target_side: str
    status: str
    confidence: float
    primary_kb_doc: str
    validator_verdict: str
    total_execution_time_ms: float
    audit_file_path: str