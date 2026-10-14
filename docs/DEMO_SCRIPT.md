# TestTrace Guard — 3-Minute Demo Video Script & Recording Plan

## 1. Pre-Flight Recording Checklist

- **Resolution & Frame Rate:** 1920x1080 (1080p) at 60 fps (OBS Studio or Windows Game Bar Win + Alt + R).
- **Audio:** Clear microphone input; disable desktop notification sounds (Focus Assist ON).
- **Browser Setup:**
  - Tab 1: Streamlit Triage Console running at http://localhost:8501 (Zoom set to 110% for readability).
  - Tab 2: FastAPI Swagger UI running at http://localhost:8000/docs (Zoom set to 110%).
  - Tab 3: GitHub Repository / README.md architecture diagram.
- **Terminal Setup:**
  - PowerShell window open at repository root with .venv active, font size 16pt, cleared screen (cls).

### Pre-Warmup Commands (Run Before Recording)

    # Terminal 1: Start FastAPI Service
    uvicorn testtrace.api:app --host 0.0.0.0 --port 8000

    # Terminal 2: Start Streamlit UI
    streamlit run app.py

    # Terminal 3: Ready for CLI Demo & Benchmark
    python scripts/demo_walkthrough.py

---

## 2. Time-Coded Storyboard & Narration Script (3:00 Total)

### Scene 1: Problem Statement & Hook (0:00 – 0:25)
- **Visual:** Start on GitHub README.md header and System Architecture diagram, then switch to the Streamlit dashboard landing view (http://localhost:8501).
- **Narration:**
  > "In high-volume semiconductor and RF module manufacturing, when an automated test station flags a failure, engineers face a critical question: Is the Device Under Test actually defective, or did the test station drift? Guessing wrong leads to false rejections—scrapping healthy hardware—or false passes that compromise quality. **TestTrace Guard** solves this in under 35 milliseconds by combining deterministic RF statistical analytics, heuristic rules, hybrid BM25 SOP retrieval, and guardrail-validated LLM reasoning."

---

### Scene 2: Architecture & Guardrail Philosophy (0:25 – 0:55)
- **Visual:** Highlight the sidebar in Streamlit showing Inference Mode, Engine: Pure Python Deterministic + AMD vLLM Guardrail, and Indexed SOPs: 6 manuals.
- **Narration:**
  > "Unlike raw LLM wrappers that hallucinate root causes from noisy logs, TestTrace Guard is deterministic-first. First, our pure-Python analytics engine computes Welch's t-tests, golden unit deviations, and fixture repeatability variance. Second, our rule engine isolates the fault family and promotes the exact Standard Operating Procedure anchor. Third, our hybrid BM25 retriever extracts verbatim corrective protocols. Finally, the reasoner and guardrail validator ensure 100% fact grounding—stripping any unverified citations and enforcing safety invariants."

---

### Scene 3: Live Triage — Canonical Case A: Station Configuration Shift (0:55 – 1:40)
- **Visual:**
  1. Click the **Case A** Quick Demo Preset button in the sidebar and click **Run Automated Triage**.
  2. Point to the top KPI row: `Investigation Case: CASE_A`, `Triage Category: STATION_CONFIGURATION`, `Architectural Domain: MEASUREMENT_SYSTEM`, `Confidence: 96.0%`, `Latency: ~35 ms`, and `Guardrail Validator: PASS`.
  3. Click **Tab 1: Deterministic Evidence** — highlight `E-001` (`CONFIG_CHANGE` on `ST-A`) and `E-002` through `E-007` (`GOLDEN_DEVIATION` showing `-2.4 dB` insertion loss offset across 1 to 6 GHz).
  4. Click **Tab 2: Rule Engine** — expand `R-CFG-001: Station Configuration Offset`.
  5. Click **Tab 3: Retrieved SOP** & **Tab 4: Diagnostic Report** — highlight `MAN-401` and the 5-step corrective protocol (Immediate Line Halt, Audit Configuration Delta, Reference Path Verification).
- **Narration:**
  > "Let's triage **CASE_A**. Unit `DUT_017` failed insertion loss limits on Station ST-A. Within 35 milliseconds, TestTrace Guard classifies this as a `STATION_CONFIGURATION` fault on the `MEASUREMENT_SYSTEM` side with 96% confidence. Looking at the Deterministic Evidence tab, we see why: Fact `E-001` caught a recent `cable_loss_compensation_table` update on ST-A, and Facts `E-002` to `E-007` prove the Golden Reference unit also shifted by minus 2.4 dB across all frequencies, while Station ST-B passed cleanly. The system routes directly to manual `MAN-401`, instructing operators to quarantine Station ST-A and restore the baseline compensation table rather than scrapping a healthy DUT."

---

### Scene 4: Live Contrast — Case B (DUT Defect) & Case C (Ambiguity Guardrail) (1:40 – 2:15)
- **Visual:**
  1. Click the **Case B** preset button in the sidebar. Show the top banner updating to `Triage Category: DUT_DEFECT`, `Architectural Domain: DUT`, `Primary Manual: MAN-601`.
  2. Briefly open **Tab 4: Diagnostic Report** showing the instruction to quarantine `DUT_017` for internal LO leakage and RF shielding inspection.
  3. Click the **Case C** preset button in the sidebar. Highlight the orange status banner: `Status: NEEDS_MORE_DATA`, `Triage Category: INSUFFICIENT_EVIDENCE`, `Architectural Domain: UNDETERMINED`, `Primary Manual: MAN-901`.
  4. Show **Tab 1: Deterministic Evidence** highlighting `DATA_GAP` facts (`E-001`, `E-002`, `E-003` — missing calibration due dates and zero golden verification runs).
- **Narration:**
  > "Now let's contrast this with **Case B**. Here, golden units pass on all stations, but `DUT_017` fails LO leakage identically on both Station A and Station B. TestTrace Guard isolates an intrinsic `DUT_DEFECT` and retrieves `MAN-601` to route the device to X-ray shield inspection.
  > What if the data is incomplete? In **Case C**, golden verification runs and calibration dates are missing. Instead of guessing, our guardrail enforces `INSUFFICIENT_EVIDENCE` and sets the status to `NEEDS_MORE_DATA` per `MAN-901`, halting automated disposition until a golden sweep is completed."

---

### Scene 5: Audit Ledger, FastAPI & 43-Case Benchmark Verification (2:15 – 2:45)
- **Visual:**
  1. Click **Tab 5: Audit Ledger** in Streamlit — show the indexed SQLite run history table and the **Download Full Audit JSON** button.
  2. Switch to Browser Tab 2 (`http://localhost:8000/docs`) — show the REST API endpoints (`/health`, `/cases`, `/triage/{case_id}`, `/audit`).
  3. Switch to PowerShell Terminal 3 and run `python scripts/run_benchmark.py --split all --mode mock`. Highlight the console summary table showing 43 cases evaluated, **95.3% Category, Domain, Status, and SOP accuracy**, **97.2% Action Keyword Recall**, and **~25 ms mean latency**.
- **Narration:**
  > "Every triage run is persisted in a dual-layer SQLite and JSON audit ledger and exposed via our FastAPI service for factory MES integration. Evaluating across our full 43-package benchmark suite—spanning all five fault families and ambiguous data gaps—TestTrace Guard achieves 95.3% accuracy across category, domain, status, and SOP retrieval, with 97.2% action keyword recall at an average latency under 30 milliseconds."

---

### Scene 6: Conclusion & AMD Readiness (2:45 – 3:00)
- **Visual:** Return to the Streamlit dashboard overview or CLI summary banner.
- **Narration:**
  > "Built with dual-mode support for AMD ROCm vLLM endpoints and a zero-downtime deterministic fallback, TestTrace Guard brings verifiable, hallucination-free measurement integrity to RF manufacturing. Thank you."
