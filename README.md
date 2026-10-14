# 📡 TestTrace Guard

> **Automated RF Test Fault Triage & Measurement Integrity Assurance**  
> *Deterministic RF Analytics, Heuristic Rule Triage, Hybrid BM25 Retrieval, and AMD vLLM Guardrails.*

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io)
[![Tests Passing](https://img.shields.io/badge/Tests-43%2F43%20Passing-brightgreen.svg)]()

---

## 1. Executive Summary & Problem Statement

In high-volume semiconductor and RF module automated test environments (ATE), intermittent test failures and line yield drops present a costly engineering dilemma: **Is the Device Under Test (DUT) defective, or has the measurement system drifted?**

Test technicians routinely spend hours re-seating devices, swapping cables, and questioning instrument calibration. Traditional triage relies on subjective tribal knowledge, risking two major operational pitfalls:
1. **False Rejections (Type I Error):** Scrapping healthy units ($100s–$1,000s each) due to uncalibrated test fixtures or corrupted station cable-loss tables.
2. **False Passes (Type II Error):** Masking intrinsic DUT component failures through repeated re-testing on misaligned stations.

**TestTrace Guard** solves this challenge with an automated, multi-tiered triage pipeline that processes raw RF parametric measurements, station maintenance logs, and golden reference standards in **under 35 milliseconds**, delivering hallucination-free, standard operating procedure (SOP) aligned diagnostic action plans.

---

## 2. System Architecture
```
TestTrace Guard operates as a deterministic-first, LLM-augmented audit pipeline. Every finding is mathematically grounded before entering the reasoning tier.
┌───────────────────────────────────┐
                          │     Raw Investigation Package     │
                          │ (measurements, limits, history)   │
                          └─────────────────┬─────────────────┘
                                            │
                                            ▼
                          ┌───────────────────────────────────┐
                          │  Deterministic Analytics Engine   │
                          │  - Golden standard offset check   │
                          │  - Welch's t-test station delta   │
                          │  - Reconnect repeatability sigma  │
                          └─────────────────┬─────────────────┘
                                            │ Facts (E-001...E-n)
                                            ▼
                          ┌───────────────────────────────────┐
                          │   Heuristic Triage Rule Engine    │
                          │  - Fault family isolation (F1-F5) │
                          │  - Architectural domain routing   │
                          │  - Ambiguity protocol detection   │
                          └─────────────────┬─────────────────┘
                                            │ Anchor + Keywords
                                            ▼
                          ┌───────────────────────────────────┐
                          │      Hybrid BM25 Retrieval        │
                          │  - Priority SOP anchor routing    │
                          │  - Lexical token scoring (k1, b)  │
                          │  - Action protocol extraction     │
                          └─────────────────┬─────────────────┘
                                            │ Grounded Context
                                            ▼
                          ┌───────────────────────────────────┐
                          │   Dual-Mode LLM Reasoner Tier     │
                          │  - Offline Deterministic Mock     │
                          │  - Remote AMD ROCm / vLLM Server  │
                          └─────────────────┬─────────────────┘
                                            │ Raw Report JSON
                                            ▼
                          ┌───────────────────────────────────┐
                          │   Deterministic Guardrail Guard   │
                          │  - Anti-hallucination fact filter │
                          │  - High-confidence rule override  │
                          │  - Status protocol enforcement    │
                          └─────────────────┬─────────────────┘
                                            │ Verified Verdict
                                            ▼
                ┌───────────────────────────┴───────────────────────────┐
                │                                                       │
                ▼                                                       ▼
  ┌───────────────────────────┐                           ┌───────────────────────────┐
  │   Interactive Streamlit   │                           │     FastAPI & Storage     │
  │   Triage Console (UI)     │                           │  (SQLite & JSON Traces)   │
  └───────────────────────────┘                           └───────────────────────────┘
```
---
### Core Architecture Stages
1. **Deterministic Analytics (`testtrace.analytics`):** Computes Welch's t-statistics, S21 golden standard deviations, delta-to-limit margins, and fixture re-seat contact variance without network or LLM dependencies ($<1\text{ ms}$).
2. **Heuristic Rule Engine (`testtrace.rules`):** Categorizes signatures into fault families (F1: Station Config, F2: DUT Defect, F3: Fixture Contact, F4: Instrument Cal, F5: Revision Mismatch, AMB: Inconclusive Gap).
3. **Hybrid BM25 Retrieval (`testtrace.kb`, `testtrace.retrieval`):** Combines rule-anchor promotion with Okapi BM25 scoring across curated engineering manuals (`MAN-401` to `MAN-901`).
4. **LLM Reasoner (`testtrace.reasoner`):** Synthesizes grounded diagnostic root-cause reports via an offline mock synthesizer or remote AMD vLLM endpoint.
5. **Deterministic Guardrail Validator (`testtrace.validator`):** Enforces 100% citation grounding, strips hallucinated fact IDs, and guarantees that rule verdicts override low-confidence LLM drift.
6. **Dual-Layer Audit Storage (`testtrace.storage`):** Saves full JSON run telemetry while indexing operational metrics in a queryable SQLite database.

---

## 3. Benchmark & Verification Results

Evaluated across **43 synthetic investigation packages** (Canonical Demos, 20 Development cases, and 20 Blinded Test cases) generated via production RF physics models:

| Evaluation Metric | Target Benchmark | Measured Performance | Verdict |
|---|---|---|---|
| **Triage Category Accuracy** | $\ge 90.0\%$ | **95.3%** | ✅ PASS |
| **Architectural Domain (Side)** | $\ge 95.0\%$ | **95.3%** | ✅ PASS |
| **Triage Status Accuracy** | $\ge 95.0\%$ | **95.3%** | ✅ PASS |
| **Top-1 SOP Manual Accuracy** | $\ge 95.0\%$ | **95.3%** | ✅ PASS |
| **Action Keyword Grounding** | $\ge 80.0\%$ | **97.2%** | ✅ PASS |
| **Pipeline Latency (Mean)** | $< 100.0\text{ ms}$ | **30.51 ms** | ✅ PASS |
| **Pipeline Latency (Median p50)**| $< 50.0\text{ ms}$ | **28.68 ms** | ✅ PASS |
| **Pipeline Latency (95th %ile)** | $< 200.0\text{ ms}$ | **47.77 ms** | ✅ PASS |
| **Throughput (Mock Mode)** | $\ge 10\text{ cases/s}$ | **16.5–19.7 cases/s** | ✅ PASS |

*Full evaluation reports and raw telemetry are preserved in `data/benchmark_summary.md` and `data/benchmark_results.json`.*

---

## 4. Quick Start Guide

### Prerequisites
* Python 3.11, 3.12, 3.13, or 3.14
* Git

### Installation
bash
# Clone the repository
git clone [https://github.com/your-username/testtrace-guard.git](https://github.com/your-username/testtrace-guard.git)
cd testtrace-guard

# Create and activate virtual environment
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install package with development dependencies
pip install -e ".[dev]"

### Running the System

1. **Command Line Interface (CLI):**

    python -m testtrace.pipeline --case CASE_A --mode mock
    testtrace --case CASE_B --mode mock

2. **Interactive Streamlit Dashboard:**

    streamlit run app.py

3. **REST API Service:**

    uvicorn testtrace.api:app --host 0.0.0.0 --port 8000 --reload

4. **Automated Benchmark Suite:**

    python scripts/run_benchmark.py --split all --mode mock

---

## 5. AMD Infrastructure & Fallback Protocol

TestTrace Guard is built to run on **AMD Developer Cloud** utilizing ROCm and vLLM acceleration:

* **Target Hardware:** AMD Instinct MI300X or Radeon Pro with ROCm 6.x.
* **Target Model:** Qwen/Qwen2.5-7B-Instruct served via vllm.entrypoints.openai.api_server.
* **Zero-Downtime Mock Fallback:** To maintain high availability during network latency or token factory outages, TestTrace Guard features an offline deterministic mock fallback (LLM_MODE=mock). The fallback executes in under 35 ms while preserving 100% schema compliance and strict fact grounding.

To configure a live AMD vLLM endpoint, copy .env.example to .env and set LLM_MODE=vllm along with your LLM_BASE_URL and LLM_API_KEY.

---

## 6. Project Structure

    testtrace-guard/
    ├── app.py                     # Streamlit 5-tab interactive triage dashboard
    ├── pyproject.toml             # Standard PEP 517/518 build specification
    ├── pytest.ini                 # Pytest configuration and pythonpath resolver
    ├── README.md                  # System overview and operational guide
    ├── LICENSE                    # MIT License
    ├── STATE.md                   # Real-time hackathon execution ledger
    ├── data/                      # Audit SQLite index, KB manuals, and synthetic cases
    ├── scripts/                   # Benchmark runner and LLM smoke tests
    ├── testtrace/                 # Core analytics, rules, BM25, reasoner, validator, API
    └── tests/                     # Comprehensive pytest acceptance test suites

---

## 7. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
