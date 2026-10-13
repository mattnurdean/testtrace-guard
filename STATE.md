# STATE
## Environment (real values only)
GPU: UNVERIFIED | ROCm: UNVERIFIED | vLLM: UNVERIFIED | Model + license: UNVERIFIED | Endpoint: UNVERIFIED | Hourly price: UNVERIFIED | Credits left: $100.00

## Steps
| Step | Status | Commit | Notes |
|---|---      |---       |---|
| 0 | DONE    | <your_latest_commit_hash> | Repo created, venv active tree initialized |
| 1 | PAUSED  | — | Token Factory 404; paused for Discord clarification. Fallback to MOCK mode per Playbook §5 |
| 2 | DONE    | <paste_step2_commit_hash> | Synthetic dataset generator complete and verified (6/6 tests pass) |
| 3 | DONE | <step3_commit_hash> | Deterministic analytics engine verified (5/5 tests pass, 0.44s execution) |
| 4 | DONE | pending | Rule engine complete and verified (7/7 tests pass, <10 ms evaluation) |
| 5 | DONE | pending | Knowledge base curated & BM25 engine verified (10/10 tests pass, <1 ms search) |
| 6 | IN_PROGRESS | — | Hybrid retrieval pipeline (testtrace/retrieval.py) |
| 7 | PENDING | — | LLM reasoner + validator |
| 8 | PENDING | — | Pipeline + API + storage |
| 9 | PENDING | — | Streamlit UI |
| 10 | PENDING | — | Evaluation + AMD benchmark |
| 11 | PENDING | — | Packaging & README |
| 12 | PENDING | — | Demo script & video |
| 13 | PENDING | — | Slides & descriptions |
| 14 | PENDING | — | Evolus integration (STRETCH) |
| 15 | PENDING | — | Final submission |

## Files added (path — purpose)
- .gitignore — ignore secrets, pycache, venv
- LICENSE — MIT License
- README.md — project root outline stub
- STATE.md — tracking sheet and environment facts
- pytest.ini — pytest root configuration and pythonpath resolver
- .env.example — AMD Droplet and Token Factory endpoint configuration template
- scripts/smoke_llm.py — connectivity, TTFT, and throughput smoke test
- scripts/json_smoke.py — 10-iteration JSON schema compliance test
- testtrace/__init__.py — package initialization
- data/synthetic/DATA_DISCLAIMER.md — synthetic data usage and non-confidentiality disclaimer
- testtrace/datagen.py — deterministic RF test campaign generator (Playbook App. C)
- tests/test_datagen.py — acceptance tests for synthetic dataset schema, pass rates, and fault physics
- testtrace/schemas.py — Pydantic v2 schemas for RF measurements, limits, golden ref, evidence facts, and rule outputs
- testtrace/analytics.py — pure Python deterministic RF analytics and evidence fact emitter
- tests/test_analytics.py — acceptance tests for canonical case triage facts and sub-500 ms benchmark
- testtrace/rules.py — deterministic RF failure triage heuristic rule engine
- tests/test_rules.py — acceptance tests for canonical cases, fault families F1–F5, and <10 ms execution benchmark
- data/kb/MAN-401_station_configuration.md — SOP for station configuration and cable loss compensation
- data/kb/MAN-501_fixture_contact.md — SOP for RF fixture interface, pin wear, and repeatability
- data/kb/MAN-601_dut_rf_defects.md — SOP for DUT LO leakage and internal RF shielding defects
- data/kb/MAN-701_instrument_calibration.md — SOP for instrumentation calibration expiry and drift
- data/kb/MAN-801_revision_limits.md — SOP for hardware revision and test limit synchronization
- data/kb/MAN-901_ambiguity_data_gaps.md — SOP for ambiguous data gaps and missing golden reference checks
- testtrace/kb.py — document parsing and pure-Python BM25Okapi search engine
- tests/test_kb.py — acceptance tests for KB ingestion, prefix lookups, and BM25 retrieval benchmark

## Decisions / overrides
- Paused Step 1 live endpoint verification due to 404 route error on Token Factory; activated Playbook §5 mock mode fallback to safeguard internal freeze schedule (Oct 15).
- Configured pytest.ini with `pythonpath = .` to ensure seamless module resolution across Windows/PowerShell environments.
- Positioned campaign golden verification runs after configuration change in datagen.py to reflect active station state (E-002: -2.4 dB offset on ST-A).
- Analytics engine implemented using closed-form Welch's t-test and Gaussian complementary error function (erfc) p-value approximation; zero external network or LLM dependencies.
- Rule engine prioritizes `INSUFFICIENT_EVIDENCE` / `NEEDS_MORE_DATA` whenever critical golden reference runs or calibration records are absent.
- Implemented pure-Python BM25Okapi with smoothed Robertson-Spärck Jones IDF; requires zero external C-extensions, ensuring deterministic local execution.
- Configured metadata extraction for manual prefixes (MAN-4 through MAN-9) to align with rule engine recommendations and truth specifications.

## Assumptions
- Python 3.14 virtual environment active.
- Synthetic dataset generated in `data/synthetic/` remains available locally.
- Development of Steps 2 through 6 continues in mock mode without requiring an active remote AMD GPU.
- Knowledge base markdown documents in data/kb/ remain read-only during search queries.

## Open issues
- AMD Developer Cloud instance pending launch and verification in Step 1.
- Need exact Token Factory API endpoint structure from Discord/organizers.

## Next step
Step 1 — AMD vLLM endpoint verification (Gate G0).
Step 2 — Synthetic data generator (testtrace/datagen.py).
Step 5 — Knowledge base curation and indexing (data/kb/*.md, testtrace/kb.py).
Step 6 — Hybrid retrieval pipeline (testtrace/retrieval.py, tests/test_retrieval.py).