# STATE
## Environment (real values only)
GPU: UNVERIFIED | ROCm: UNVERIFIED | vLLM: UNVERIFIED | Model + license: UNVERIFIED | Endpoint: UNVERIFIED | Hourly price: UNVERIFIED | Credits left: $100.00

## Steps
| Step | Status | Commit | Notes |
|---|---      |---       |---|
| 0 | DONE    | <your_latest_commit_hash> | Repo created, venv active tree initialized |
| 1 | PAUSED  | — | Token Factory 404; paused for Discord clarification. Fallback to MOCK mode per Playbook §5 |
| 2 | DONE    | <paste_step2_commit_hash> | Synthetic dataset generator complete and verified (6/6 tests pass) |
| 3 | IN_PROGRESS | — | Deterministic analytics (testtrace/schemas.py, testtrace/analytics.py) |
| 4 | PENDING | — | Rule engine |
| 5 | PENDING | — | Knowledge base |
| 6 | PENDING | — | Retrieval |
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
- scripts/smoke_llm.py — connectivity and TTFT smoke script
- scripts/json_smoke.py — JSON schema smoke script

## Decisions / overrides
- Initialized project tracking per Playbook v1.0 specifications.
- Paused Step 1 live endpoint verification due to 404 route error; activated Playbook §5 mock mode fallback to safeguard internal freeze schedule (Oct 15).

## Assumptions
- Python 3.11+ is locally installed and available.
- Synthetic data generation and deterministic analytics can be built and validated offline.

## Open issues
- AMD Developer Cloud instance pending launch and verification in Step 1.
- Need exact Token Factory API endpoint structure from Discord/organizers.
## Next step
Step 1 — AMD vLLM endpoint verification (Gate G0).
Step 2 — Synthetic data generator (testtrace/datagen.py).