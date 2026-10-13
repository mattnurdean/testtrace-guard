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
| 6 | DONE | pending | Hybrid retrieval pipeline complete and verified (8/8 tests pass, <2 ms retrieval) |
| 7 | DONE | pending | LLM reasoner & guardrail validator verified (7/7 tests pass, <10 ms mock) |
| 8 | IN_PROGRESS | — | Pipeline + API + storage (testtrace/pipeline.py, testtrace/api.py) |
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
- testtrace/schemas.py — added RetrievedDocument and RetrievalResult models
- testtrace/retrieval.py — hybrid retrieval combining rule anchor routing, BM25 scoring, and context formatting
- tests/test_retrieval.py — acceptance tests for canonical case retrieval, fault families, and latency benchmark
- testtrace/schemas.py — added DiagnosticReport and ValidationResult models
- testtrace/validator.py — deterministic guardrail validator for fact grounding and category consistency
- testtrace/reasoner.py — LLM reasoning engine supporting mock and vLLM inference modes with retry logic
- tests/test_reasoner.py — acceptance tests for diagnostic reporting, hallucination guardrails, and latency

## Decisions / overrides
- Paused Step 1 live endpoint verification due to 404 route error on Token Factory; activated Playbook §5 mock mode fallback to safeguard internal freeze schedule (Oct 15).
- Configured pytest.ini with `pythonpath = .` to ensure seamless module resolution across Windows/PowerShell environments.
- Positioned campaign golden verification runs after configuration change in datagen.py to reflect active station state (E-002: -2.4 dB offset on ST-A).
- Analytics engine implemented using closed-form Welch's t-test and Gaussian complementary error function (erfc) p-value approximation; zero external network or LLM dependencies.
- Rule engine prioritizes `INSUFFICIENT_EVIDENCE` / `NEEDS_MORE_DATA` whenever critical golden reference runs or calibration records are absent.
- Implemented pure-Python BM25Okapi with smoothed Robertson-Spärck Jones IDF; requires zero external C-extensions, ensuring deterministic local execution.
- Configured metadata extraction for manual prefixes (MAN-4 through MAN-9) to align with rule engine recommendations and truth specifications.
- Implemented deterministic anchor promotion: rule engine's suggested_kb_prefix receives routing priority, backed by BM25 relevance scores.
- Formatted prompt context injects verbatim SOP corrective action protocol bullets to guarantee grounded recommendations in Step 7.
- Normalized underscores to spaces in keyword matching to robustly support snake_case parameter names within natural-language protocols.
- Implemented dual-mode reasoning: mock mode operates completely offline and deterministically, while vLLM mode routes to OpenAI-compatible endpoints with automated JSON recovery.
- Guardrail validator automatically strips ungrounded/hallucinated fact IDs and enforces rule engine overrides whenever deterministic rule confidence is >= 0.80.
- Enforced invariant: INSUFFICIENT_EVIDENCE triage must always map to status NEEDS_MORE_DATA.

## Assumptions
- Python 3.14 virtual environment active.
- Synthetic dataset generated in `data/synthetic/` remains available locally.
- Development of Steps 2 through 6 continues in mock mode without requiring an active remote AMD GPU.
- Knowledge base markdown documents in data/kb/ remain read-only during search queries.
- Knowledge base markdown corpus in data/kb/ is indexed and accessible.
- Synthetic dataset in data/synthetic/ and SOP corpus in data/kb/ remain available locally.

## Open issues
- AMD Developer Cloud instance pending launch and verification in Step 1.
- Need exact Token Factory API endpoint structure from Discord/organizers.

## Next step
Step 1 — AMD vLLM endpoint verification (Gate G0).
Step 2 — Synthetic data generator (testtrace/datagen.py).
Step 5 — Knowledge base curation and indexing (data/kb/*.md, testtrace/kb.py).
Step 6 — Hybrid retrieval pipeline (testtrace/retrieval.py, tests/test_retrieval.py).
Step 7 — LLM reasoner + validator (testtrace/reasoner.py, testtrace/validator.py, tests/test_reasoner.py).
Step 8 — End-to-end pipeline, CLI, and audit storage (testtrace/pipeline.py, testtrace/api.py, tests/test_pipeline.py).