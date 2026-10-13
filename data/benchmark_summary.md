# TestTrace Guard - Evaluation & Benchmark Report

- **Timestamp:** `2026-10-13T21:36:12Z`
- **Evaluation Split:** `all` (43 cases)
- **Inference Execution Mode:** `mock`
- **Overall Throughput:** `16.54 cases/sec`

## 1. Key Performance Indicators (KPIs)

| Evaluation Metric | Target Spec | Measured Result | Status |
|---|---|---|---|
| **Triage Category Accuracy** | $\ge 90.0\%$ | **95.3%** | ✅ PASS |
| **Architectural Domain (Side)** | $\ge 95.0\%$ | **95.3%** | ✅ PASS |
| **Triage Status Accuracy** | $\ge 95.0\%$ | **95.3%** | ✅ PASS |
| **Top-1 SOP Prefix Accuracy** | $\ge 95.0\%$ | **95.3%** | ✅ PASS |
| **Action Keyword Recall** | $\ge 80.0\%$ | **97.2%** | ✅ PASS |
| **Mean Latency per Case** | $< 100.0\text{ ms}$ | **30.51 ms** | ✅ PASS |

## 2. Latency Percentiles (End-to-End Pipeline)

| Latency Percentile | Measured Latency | Budget Limit |
|---|---|---|
| **Mean** | 30.51 ms | 100.00 ms |
| **p50 (Median)** | 28.68 ms | 50.00 ms |
| **p90** | 41.68 ms | 150.00 ms |
| **p95** | 47.77 ms | 200.00 ms |
| **p99** | 64.18 ms | 500.00 ms |

## 3. Guardrail Validator Verdicts

- **Clean Pass (`PASS`):** 37
- **Sanitized / Overridden (`CORRECTED`):** 0
- **Flagged Discrepancies (`FLAGGED`):** 6

## 4. Fault Family Breakdown

| Fault Family | Description | Cases Tested | Category Acc | Domain Acc |
|---|---|---|---|---|
| **AMB** | Inconclusive Data Gap | 11 | 100.0% | 100.0% |
| **F1** | Station Configuration Offset | 7 | 71.4% | 71.4% |
| **F2** | Intrinsic DUT Defect | 7 | 100.0% | 100.0% |
| **F3** | Fixture Contact Instability | 6 | 100.0% | 100.0% |
| **F4** | Calibration Overdue | 6 | 100.0% | 100.0% |
| **F5** | Spec / Revision Mismatch | 6 | 100.0% | 100.0% |
