"""TestTrace Guard - Interactive RF Test Failure Triage Dashboard."""

import json
import os
from pathlib import Path
from typing import Any, Optional
import pandas as pd
import streamlit as st

from testtrace.kb import KBIndexer
from testtrace.pipeline import run_pipeline
from testtrace.schemas import PipelineRunResult
from testtrace.storage import AuditStorage

# --- Page Configuration & Styling ---
st.set_page_config(
    page_title="TestTrace Guard | RF Test Failure Triage",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path("data/synthetic")
AUDIT_DIR = Path("data/audit")
KB_DIR = Path("data/kb")

# --- Initialize Application Singletons ---
@st.cache_resource
def get_audit_storage() -> AuditStorage:
    return AuditStorage(base_dir=AUDIT_DIR)

@st.cache_resource
def get_kb_indexer() -> KBIndexer:
    return KBIndexer(kb_dir=KB_DIR)

storage = get_audit_storage()
kb_indexer = get_kb_indexer()


def get_available_cases() -> list[str]:
    """Scan synthetic data directory for available test packages."""
    if not DATA_DIR.exists():
        return ["CASE_A", "CASE_B", "CASE_C"]
    dirs = sorted([p.name for p in DATA_DIR.iterdir() if p.is_dir()])
    return dirs if dirs else ["CASE_A", "CASE_B", "CASE_C"]


def render_sidebar() -> tuple[str, str, bool]:
    """Render sidebar controls and return selected case, mode, and trigger flag."""
    st.sidebar.title("📡 TestTrace Guard")
    st.sidebar.caption("Automated RF Test Failure Triage")
    st.sidebar.markdown("---")

    # Environment Status
    mode_env = os.getenv("LLM_MODE", "mock").upper()
    st.sidebar.markdown(f"**Inference Mode:** `{mode_env}`")
    st.sidebar.markdown("**Engine:** Pure Python Deterministic + AMD vLLM Guardrail")
    st.sidebar.markdown(f"**Indexed SOPs:** `{len(kb_indexer.documents)} manuals`")
    st.sidebar.markdown("---")

    st.sidebar.subheader("🎯 Quick Demo Presets")
    col_a, col_b, col_c = st.sidebar.columns(3)
    preset_selected = None
    if col_a.button("Case A", help="Station Config Offset (F1)"):
        preset_selected = "CASE_A"
    if col_b.button("Case B", help="DUT Intrinsic LO Defect (F2)"):
        preset_selected = "CASE_B"
    if col_c.button("Case C", help="Data Gap / Ambiguity (AMB)"):
        preset_selected = "CASE_C"

    all_cases = get_available_cases()
    default_idx = 0
    if preset_selected and preset_selected in all_cases:
        default_idx = all_cases.index(preset_selected)
    elif "selected_case" in st.session_state and st.session_state["selected_case"] in all_cases:
        default_idx = all_cases.index(st.session_state["selected_case"])

    selected_case = st.sidebar.selectbox("Select Test Package:", all_cases, index=default_idx)
    st.session_state["selected_case"] = selected_case

    run_mode = st.sidebar.radio("Inference Execution Mode:", ["mock", "vllm"], index=0, horizontal=True)

    st.sidebar.markdown("---")
    trigger = st.sidebar.button("🚀 Run Automated Triage", type="primary", use_container_width=True)

    return selected_case, run_mode, trigger


def display_executive_summary(res: PipelineRunResult) -> None:
    """Display high-level triage findings, confidence, and guardrail verdicts."""
    rep = res.report

    # Top KPI Metrics Row
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Investigation Case", res.case_id)
    m2.metric("Triage Category", rep.category)
    m3.metric("Architectural Domain", rep.target_side)
    m4.metric("Confidence", f"{rep.confidence * 100:.1f}%")
    m5.metric("Latency", f"{res.total_execution_time_ms:.1f} ms")

    # Status & Guardrail Banner
    status_color = "green" if rep.status == "PLAN_READY_FOR_REVIEW" else "orange"
    verdict_badge = "🛡️ PASS" if rep.validator_verdict == "PASS" else f"⚠️ {rep.validator_verdict}"

    st.markdown(
        f"""
        <div style="background-color: #f0f2f6; padding: 14px 20px; border-radius: 8px; border-left: 6px solid {status_color}; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 1.15rem; font-weight: 600;">Status: <span style="color: {status_color};">{rep.status}</span></span>
                <span style="font-size: 0.95rem; font-weight: 600;">Guardrail Validator: <code>{verdict_badge}</code></span>
            </div>
            <p style="margin: 8px 0 0 0; color: #31333F;"><b>Primary Manual:</b> <code>{rep.primary_kb_doc}</code> | <b>Target Unit:</b> <code>DUT_017</code> | <b>Run ID:</b> <code>{res.run_id}</code></p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def display_tabs(res: PipelineRunResult) -> None:
    """Render tabbed deep dive into evidence, rules, retrieval, report, and audit history."""
    tab_evidence, tab_rules, tab_sop, tab_report, tab_audit = st.tabs(
        [
            "📊 Deterministic Evidence",
            "⚙️ Rule Engine",
            "📖 Retrieved SOP",
            "📝 Diagnostic Report",
            "🗄️ Audit Ledger",
        ]
    )

    # --- TAB 1: EVIDENCE FACTS ---
    with tab_evidence:
        st.subheader("Deterministic Evidence Facts")
        st.caption("Extracted via parametric statistical analysis and cross-station delta evaluation.")

        facts_data = []
        for f in res.analytics.facts:
            facts_data.append(
                {
                    "Fact ID": f.fact_id,
                    "Category": f.category,
                    "Severity": f.severity,
                    "Station": f.station_id or "ALL",
                    "Metric": f.metric_name,
                    "Freq (GHz)": f"{f.freq_ghz:.1f}" if f.freq_ghz else "—",
                    "Measured": f"{f.measured_value:.3f}" if f.measured_value is not None else "—",
                    "Delta": f"{f.delta:+.3f}" if f.delta is not None else "—",
                    "Threshold": f"{f.threshold:.3f}" if f.threshold is not None else "—",
                    "p-value": f"{f.p_value:.4f}" if f.p_value is not None else "—",
                    "Description": f.description,
                }
            )

        if facts_data:
            df_facts = pd.DataFrame(facts_data)
            st.dataframe(df_facts, use_container_width=True, hide_index=True)
        else:
            st.info("No significant evidence facts detected.")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Failed Tests:** `{', '.join(res.analytics.failed_tests) or 'None'}`")
            st.markdown(f"**Affected Stations:** `{', '.join(res.analytics.affected_stations) or 'None'}`")
        with col2:
            st.markdown(f"**Golden Verification Runs Present:** `{'Yes' if res.analytics.has_golden_data else 'No (DATA GAP)'}`")
            st.markdown(f"**Station Calibration Valid:** `{'Yes' if res.analytics.has_valid_cal else 'No (OVERDUE / GAP)'}`")

    # --- TAB 2: RULE ENGINE ---
    with tab_rules:
        st.subheader("Heuristic Rule Engine Evaluation")
        r_eval = res.rule_evaluation

        st.markdown(f"**Recommended Category:** `{r_eval.recommended_category}` (Confidence: `{r_eval.confidence:.2f}`)")
        st.markdown(f"**Suggested Standard Operating Procedure:** `{r_eval.suggested_kb_prefix}`")
        st.markdown(f"**Execution Latency:** `{r_eval.execution_time_ms:.3f} ms`")

        st.markdown("#### Fired Rules")
        if r_eval.fired_rules:
            for rule in r_eval.fired_rules:
                with st.expander(f"🔹 {rule.rule_id}: {rule.name} (Weight: {rule.weight:.1f})"):
                    st.write(f"**Description:** {rule.description}")
                    st.write(f"**Target Domain:** `{rule.target_side}` | **Category:** `{rule.target_category}`")
                    st.write(f"**Matched Evidence Fact IDs:** `{', '.join(rule.matched_fact_ids) or 'None'}`")
        else:
            st.info("No specific deterministic rules triggered.")

    # --- TAB 3: RETRIEVED SOP ---
    with tab_sop:
        st.subheader(f"Retrieved SOP: {res.retrieval.primary_doc.doc_id}")
        p_doc = res.retrieval.primary_doc
        st.markdown(f"### {p_doc.title}")
        st.markdown(f"**Category:** `{p_doc.category}` | **Domain:** `{p_doc.target_side}` | **Retrieval Method:** `{p_doc.retrieval_method}` (Score: `{p_doc.score:.2f}`)")

        st.markdown("#### Mandatory Corrective Action Protocol")
        if p_doc.action_items:
            for act in p_doc.action_items:
                st.markdown(f"- {act}")
        else:
            st.info("No specific action items listed.")

        st.markdown("#### Diagnostic Signatures & Root Cause")
        st.info(p_doc.excerpt)

        if res.retrieval.secondary_docs:
            st.markdown("#### Supplementary Cross-Reference Manuals")
            for s_doc in res.retrieval.secondary_docs:
                st.markdown(f"- **{s_doc.doc_id}**: {s_doc.title} (`{s_doc.category}`)")

    # --- TAB 4: DIAGNOSTIC REPORT ---
    with tab_report:
        st.subheader("Validated Root Cause Triage Report")
        rep = res.report

        st.markdown("#### Root Cause Summary")
        st.success(rep.root_cause_summary)

        st.markdown("#### Recommended Immediate Actions")
        for i, act in enumerate(rep.recommended_actions, 1):
            st.markdown(f"**{i}.** {act}")

        if rep.preventative_actions:
            st.markdown("#### Preventative Measures")
            for p_act in rep.preventative_actions:
                st.markdown(f"- {p_act}")

        if rep.discrepancies:
            st.markdown("#### Guardrail Discrepancies & Sanitization Log")
            for disc in rep.discrepancies:
                st.warning(f"⚠️ {disc}")

    # --- TAB 5: AUDIT LEDGER ---
    with tab_audit:
        st.subheader("Audit Ledger & Run History")
        records = storage.list_records(limit=20)

        if records:
            audit_table = [
                {
                    "Run ID": r.run_id,
                    "Case ID": r.case_id,
                    "Timestamp": r.timestamp,
                    "Category": r.category,
                    "Domain": r.target_side,
                    "Status": r.status,
                    "Conf": f"{r.confidence:.2f}",
                    "Verdict": r.validator_verdict,
                    "Time (ms)": f"{r.total_execution_time_ms:.1f}",
                }
                for r in records
            ]
            st.dataframe(pd.DataFrame(audit_table), use_container_width=True, hide_index=True)
        else:
            st.info("Audit index is currently empty.")

        st.markdown("#### Raw Audit Trace JSON")
        st.download_button(
            label="💾 Download Full Audit JSON",
            data=json.dumps(res.model_dump(), indent=2),
            file_name=f"{res.case_id}_{res.run_id}_audit.json",
            mime="application/json",
        )
        with st.expander("Inspect Raw JSON Payload"):
            st.json(res.model_dump())


def main() -> None:
    selected_case, run_mode, trigger = render_sidebar()

    st.title("📡 TestTrace Guard")
    st.markdown("#### Automated RF Test Fault Triage & Measurement Integrity Assurance")

    # Manage Active Result in Session State
    if trigger or "active_result" not in st.session_state:
        target_path = DATA_DIR / selected_case
        if not target_path.exists():
            st.error(f"Selected case directory `{selected_case}` not found under `{DATA_DIR}`.")
            return

        with st.spinner(f"Analyzing {selected_case} via {run_mode.upper()} pipeline..."):
            result = run_pipeline(
                case_path=target_path,
                mode=run_mode,
                audit_storage=storage,
                kb_indexer=kb_indexer,
            )
            st.session_state["active_result"] = result

    # Display Current Active Investigation
    if "active_result" in st.session_state:
        res: PipelineRunResult = st.session_state["active_result"]
        display_executive_summary(res)
        display_tabs(res)


if __name__ == "__main__":
    main()