# TestTrace Guard — Presentation Slide Deck Outline

## Slide 1: Title & Executive Tagline
- **Slide Title:** TestTrace Guard: Automated RF Test Fault Triage & Measurement Integrity Assurance
- **Subtitle:** Deterministic RF Statistical Analytics, Heuristic Rule Triage, Hybrid BM25 Retrieval, and AMD vLLM Guardrails
- **Presenter:** Din (Muhammad Nuruddin) — AMD Lab Hackathon 2026
- **Key Visuals:** High-tech RF ATE dashboard header, system architecture flow, AMD ROCm & vLLM compatibility badges.
- **Presenter Bullet Points:**
  - Automated triage for high-volume RF manufacturing and automated test equipment (ATE).
  - Sub-35 ms root-cause determination isolating DUT defects from measurement drift.
  - Zero-downtime hybrid architecture: pure-Python deterministic core with AMD ROCm LLM augmentation.

---

## Slide 2: The Manufacturing Dilemma (Problem Statement)
- **Slide Title:** The Cost of Uncertainty: Defective DUT or Drifted Station?
- **Key Problem Visuals:**
  - Split graphic: "Device Under Test (DUT)" vs. "Automated Test Station (ATE)".
  - Two operational failure modes:
    1. **Type I Error (False Rejection):** Scrapping high-value RF modules ($100s–$1,000s) caused by degraded fixture pogo pins or uncompensated cable loss.
    2. **Type II Error (False Acceptance):** Passing defective units through repeated station re-testing, risking catastrophic field failures.
- **Presenter Bullet Points:**
  - In manual triage, technicians spend hours swapping cables, re-seating fixtures, and second-guessing calibration.
  - Reliance on tribal knowledge creates production bottlenecks and yield loss.
  - Manufacturing lines need automated, mathematically grounded, and SOP-compliant triage in milliseconds.

---

## Slide 3: Multi-Tiered Architecture & Guardrail Philosophy
- **Slide Title:** Deterministic-First Architecture with Hallucination-Proof Guardrails
- **Key Diagram:** 5-Stage Sequential Pipeline Diagram
  1. *Deterministic Analytics:* Welch's t-test, S21 golden standard deltas, p-value calculation (<1 ms).
  2. *Heuristic Rule Engine:* Fault family classification (F1–F5, AMB) and SOP anchor promotion (<10 ms).
  3. *Hybrid BM25 Retrieval:* Okapi BM25 ranked search across curated manuals MAN-401 to MAN-901 (<2 ms).
  4. *Dual-Mode LLM Reasoner:* AMD vLLM (Qwen2.5-7B) on ROCm with offline deterministic mock fallback.
  5. *Deterministic Guardrail Validator:* 100% citation grounding, hallucinated fact stripping, rule overrides.
- **Presenter Bullet Points:**
  - Unlike naive LLM wrappers, TestTrace Guard guarantees that no finding is emitted without mathematical evidence.
  - High-confidence rule engine classifications (>=0.80) strictly override low-confidence LLM drift.
  - Ambiguous cases with missing data automatically enforce a `NEEDS_MORE_DATA` disposition.

---

## Slide 4: Canonical Demonstration Scenarios
- **Slide Title:** Verifiable Root Cause Isolation Across Canonical Cases
- **Comparison Table / Visual:**
  - **Case A (Station Config Offset - F1):**
    - *Signature:* Systematic -2.4 dB insertion loss on Station ST-A across 1–6 GHz; ST-B passes.
    - *Verdict:* `STATION_CONFIGURATION` (Measurement System) | Confidence: 96% | Latency: 35 ms.
    - *Action:* SOP `MAN-401` — Quarantine Station ST-A, audit cable loss table, restore baseline.
  - **Case B (Intrinsic DUT Defect - F2):**
    - *Signature:* Excessive LO leakage (-34 dBm vs -40 dBm limit) on both ST-A and ST-B; golden units pass.
    - *Verdict:* `DUT_DEFECT` (DUT) | Confidence: 96% | Latency: 24 ms.
    - *Action:* SOP `MAN-601` — Quarantine DUT_017, route to X-ray shield inspection; leave stations active.
  - **Case C (Inconclusive Data Gap - AMB):**
    - *Signature:* Marginal phase noise exceedance, missing golden verification runs, unrecorded calibration dates.
    - *Verdict:* `INSUFFICIENT_EVIDENCE` (Undetermined) | Status: `NEEDS_MORE_DATA` | Primary SOP: `MAN-901`.
    - *Action:* Guardrail halt — Prevent scrapping; mandate immediate golden reference sweep.

---

## Slide 5: Quantitative Benchmark & Verification
- **Slide Title:** Benchmark Results Across 43 Production Investigation Packages
- **Key Data Table:**
  - Category Classification Accuracy: **95.3%** (Target: >=90%)
  - Architectural Domain (Side) Accuracy: **95.3%** (Target: >=95%)
  - Triage Status Accuracy: **95.3%** (Target: >=95%)
  - SOP Manual Prefix Top-1 Accuracy: **95.3%** (Target: >=95%)
  - Action Keyword Grounding Recall: **97.2%** (Target: >=80%)
  - End-to-End Pipeline Mean Latency: **30.51 ms** (Budget: <100 ms)
  - Throughput: **16.5–21.6 cases/second**
- **Presenter Bullet Points:**
  - Evaluated on comprehensive synthetic dataset modeling real S-parameter physics and measurement noise.
  - 100% of generated actions directly cite verified standard operating procedures.
  - Sub-35 ms execution enables inline, real-time test cell disposition without slowing line throughput.

---

## Slide 6: Enterprise Ready: REST API & Streamlit Console
- **Slide Title:** Production-Grade Operator & Factory Integration
- **Key Screenshots:**
  - *FastAPI Backend (`:8000`):* OpenAPI endpoints (`/health`, `/cases`, `/triage/{case_id}`, `/audit`).
  - *Streamlit Triage Console (`:8501`):* 5-tab deep-dive interface:
    - Tab 1: Deterministic Evidence Facts (statistical deltas, p-values).
    - Tab 2: Rule Engine Evaluation (fired rules, matched fact IDs).
    - Tab 3: Retrieved SOP (verbatim corrective action protocols).
    - Tab 4: Diagnostic Report (validated root cause, immediate & preventative actions).
    - Tab 5: Audit Ledger (queryable SQLite run history, one-click raw JSON telemetry export).
- **Presenter Bullet Points:**
  - Dual-layer audit architecture: full JSON diagnostic traces on disk with high-speed SQLite indexing.
  - Seamlessly integrates with factory Manufacturing Execution Systems (MES) and test executives.

---

## Slide 7: AMD Infrastructure & The Road Ahead
- **Slide Title:** Scalable Hardware Acceleration & Next Steps
- **Key Architecture Graphic:** AMD Instinct™ MI300X / Radeon™ Pro running ROCm 6.x & vLLM OpenAI-compatible server.
- **Presenter Bullet Points:**
  - **AMD Deployment:** High-throughput batch inference with vLLM PagedAttention and FP8/FP16 acceleration.
  - **High-Availability Fallback:** Offline deterministic mock engine ensures 100% uptime during network disconnects.
  - **Future Roadmap:**
    - Integration with Evolus manufacturing scheduling platform.
    - Automated SCPI instrument loop-back self-test triggers.
    - Closed-loop automated limits synchronization and calibration dispatch.
