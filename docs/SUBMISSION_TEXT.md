# TestTrace Guard — Hackathon Submission Details

## 1. Project Title & Tagline
- **Project Title:** TestTrace Guard
- **Elevator Pitch / Tagline:** Automated RF test fault triage and measurement integrity assurance system powered by deterministic analytics, hybrid BM25 SOP retrieval, and AMD vLLM guardrails.

---

## 2. Inspiration & Problem Statement
In high-volume automated test environments (ATE) for RF semiconductors and wireless communications hardware, intermittent failures present an urgent dilemma: **Did the Device Under Test (DUT) fail, or has the test station drifted?**

When an RF parameter—such as S21 insertion loss or local oscillator (LO) leakage—violates tolerance limits, manufacturing lines suffer from two costly failure modes:
1. **False Rejections (Type I Error):** Scrapping or reworking good devices due to uncalibrated test stations, worn fixture pogo pins, or corrupted cable-loss compensation tables.
2. **False Passes (Type II Error):** Re-testing marginal units on misaligned stations until they pass, letting defective hardware escape to customers.

Traditional triage relies on slow, manual troubleshooting and tribal knowledge. TestTrace Guard automates this entire decision chain in under 35 milliseconds, deterministically isolating the root cause and delivering standard operating procedure (SOP) action plans with zero hallucinations.

---

## 3. What TestTrace Guard Does
TestTrace Guard ingests raw test campaign packages (RF measurements, upper/lower limits, multi-station runs, golden verification baselines, and station maintenance ledgers) and delivers:
- **Instant Fault Categorization:** Classifies failures into six core families:
  - F1: Station Configuration Offset
  - F2: Intrinsic DUT Defect
  - F3: Fixture Contact & Pogo Pin Repeatability
  - F4: Instrument Calibration Expiry & Drift
  - F5: Hardware Revision & Limit Mismatch
  - AMB: Inconclusive Evidence & Data Completeness Gaps
- **Architectural Domain Routing:** Directs actions to the correct side: `MEASUREMENT_SYSTEM`, `DUT`, `SPECIFICATION`, or `UNDETERMINED`.
- **SOP Action Protocol Retrieval:** Hybrid BM25 Okapi retrieval pinpoints the exact standard operating manual (`MAN-401` through `MAN-901`) and injects mandatory corrective protocols.
- **Safety Invariant Enforcement:** When critical baseline runs are missing, the system automatically halts automated disposition and enforces status `NEEDS_MORE_DATA`.
- **Canonical Scenarios Verified:**
  - **Case A (`CASE_A`):** Station Configuration Shift (Fault Family F1) — triaged to `MAN-401` in 35 ms to halt station drift and restore baseline loss tables.
  - **Case B (`CASE_B`):** Intrinsic DUT Defect (Fault Family F2) — triaged to `MAN-601` in 24 ms to quarantine DUT for LO leakage and X-ray shield analysis.
  - **Case C (`CASE_C`):** Inconclusive Data Gap (Guardrail AMB) — triaged to `MAN-901` in 23 ms, enforcing `NEEDS_MORE_DATA` to prevent scrapping good units without baseline data.
- **Dual-Layer Audit Persistence:** Writes human-readable JSON traces and indexes metrics into SQLite for enterprise MES integration.

---

## 4. How We Built It (Technical Architecture)
TestTrace Guard is built from the ground up on a **deterministic-first, LLM-augmented** principle:

1. **Deterministic Analytics Engine (`testtrace.analytics`):**
   - Implemented in pure Python with zero external ML dependencies.
   - Computes parametric deltas, limit margins, Welch's t-test statistics, Gaussian error function p-values, and fixture re-seat variance in <1 ms.
   - Emits structured evidence facts (`E-001` through `E-n`).

2. **Heuristic Expert Rule Engine (`testtrace.rules`):**
   - Applies deterministic rules matching evidence fact combinations.
   - Calculates domain confidence scores and promotes target SOP anchor prefixes.

3. **Hybrid BM25 Retrieval Engine (`testtrace.kb`, `testtrace.retrieval`):**
   - Pure-Python implementation of BM25Okapi with smoothed Robertson-Spärck Jones IDF.
   - Indexes markdown-based Standard Operating Procedures (`MAN-401` to `MAN-901`).
   - Prioritizes rule-promoted anchors backed by lexical token relevance.

4. **Dual-Mode LLM Reasoner & Guardrail Validator (`testtrace.reasoner`, `testtrace.validator`):**
   - Supports both remote AMD vLLM OpenAI-compatible endpoints and an offline deterministic mock synthesizer.
   - The Guardrail Validator verifies that every cited fact ID exists in analytical telemetry, strips ungrounded hallucinations, and enforces rule overrides when deterministic confidence >= 0.80.

5. **Operator Interfaces & Deployment:**
   - **Streamlit Console (`app.py`):** Interactive 5-tab dashboard featuring one-click Canonical Case presets (Case A, Case B, Case C), live telemetry, evidence fact tables, and audit logs.
   - **FastAPI Service (`testtrace.api`):** Production REST API providing asynchronous triage endpoints and SQLite audit query routes.

---

## 5. Benchmarks & Verification
We validated TestTrace Guard across **43 synthetic investigation packages** (Canonical Demos Case A, Case B, and Case C, 20 Development packages, and 20 Blinded Test packages) modeling real RF physical impairments:

- **Triage Category Accuracy:** **95.3%** (Target: >=90.0%)
- **Architectural Domain Accuracy:** **95.3%** (Target: >=95.0%)
- **Triage Status Accuracy:** **95.3%** (Target: >=95.0%)
- **Top-1 SOP Manual Accuracy:** **95.3%** (Target: >=95.0%)
- **Action Keyword Recall Rate:** **97.2%** (Target: >=80.0%)
- **Mean Pipeline Latency:** **30.51 ms** (Target: <100.0 ms)
- **p95 Latency:** **47.77 ms**
- **Throughput:** **16.5–21.6 cases/second**

---

## 6. AMD Technology Stack & Hardware Acceleration
- **Target Platform:** AMD Developer Cloud instances equipped with AMD Instinct™ MI300X or Radeon™ Pro GPUs running ROCm 6.x.
- **Serving Framework:** vLLM (`vllm.entrypoints.openai.api_server`) serving `Qwen/Qwen2.5-7B-Instruct` with PagedAttention and continuous batching.
- **Zero-Downtime Resilience:** Designed with an integrated offline deterministic fallback mode (`LLM_MODE=mock`), allowing test cells to triage failures locally in <35 ms even if network connectivity to cloud GPUs is interrupted.

---

## 7. What's Next
- **Evolus Integration:** Connect triage outputs directly into Evolus manufacturing planning and workflow scheduling.
- **SCPI Instrument Self-Test Loops:** Automatically trigger automated loop-back diagnostics on Keysight and Rohde & Schwarz signal analyzers when measurement system drift is flagged.
- **Closed-Loop Limit Synchronization:** Implement bi-directional limit ledger updates to prevent revision mismatch rejections.
