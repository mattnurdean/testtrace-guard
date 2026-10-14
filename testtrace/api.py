"""FastAPI REST service exposing TestTrace Guard triage pipeline and audit history."""

import os
from pathlib import Path
from typing import Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from testtrace.kb import KBIndexer
from testtrace.pipeline import run_pipeline
from testtrace.schemas import AuditRecord, PipelineRunResult
from testtrace.storage import AuditStorage

app = FastAPI(
    title="TestTrace Guard API",
    version="0.1.0",
    description="Automated RF test fault triage and root-cause audit system.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Application singletons
DATA_DIR = Path("data/synthetic")
AUDIT_DIR = Path("data/audit")
KB_DIR = Path("data/kb")

storage = AuditStorage(base_dir=AUDIT_DIR)
kb_indexer = KBIndexer(kb_dir=KB_DIR)


@app.get("/health")
def health_check() -> dict[str, Any]:
    """Check service health and active LLM inference mode."""
    mode = os.getenv("LLM_MODE", "mock").lower()
    return {
        "status": "healthy",
        "service": "testtrace-guard",
        "version": "0.1.0",
        "inference_mode": mode,
        "kb_documents_loaded": len(kb_indexer.documents),
    }


@app.get("/cases")
def list_available_cases() -> list[str]:
    """List all available synthetic investigation package directories."""
    if not DATA_DIR.exists():
        return []
    return sorted([p.name for p in DATA_DIR.iterdir() if p.is_dir()])


@app.post("/triage/{case_id}", response_model=PipelineRunResult)
def triage_case(
    case_id: str,
    mode: Optional[str] = Query(None, description="Override LLM mode: 'mock' or 'vllm'"),
) -> PipelineRunResult:
    """Execute automated triage on an investigation package."""
    target_path = DATA_DIR / case_id
    if not target_path.exists():
        raise HTTPException(status_code=404, detail=f"Case package '{case_id}' not found.")

    inf_mode = mode or os.getenv("LLM_MODE", "mock").lower()

    try:
        result = run_pipeline(
            case_path=target_path,
            mode=inf_mode,
            audit_storage=storage,
            kb_indexer=kb_indexer,
            audit_dir=AUDIT_DIR,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline failure: {str(exc)}")


@app.get("/audit", response_model=list[AuditRecord])
def list_audit_history(limit: int = Query(50, ge=1, le=200)) -> list[AuditRecord]:
    """Retrieve indexed triage run records from the audit ledger."""
    return storage.list_records(limit=limit)


@app.get("/audit/{run_id}", response_model=PipelineRunResult)
def get_audit_record(run_id: str) -> PipelineRunResult:
    """Retrieve full trace and telemetry for a specific investigation run."""
    record = storage.load_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Audit run '{run_id}' not found.")
    return record

from testtrace.evolus import (
    create_evolus_ticket,
    dispatch_evolus_ticket,
    list_dispatched_tickets,
)
from testtrace.schemas import EvolusTicket, PipelineRunResult


@app.post("/evolus/dispatch/{run_id}", response_model=EvolusTicket, tags=["Evolus Integration"])
def dispatch_to_evolus(run_id: str) -> EvolusTicket:
    """Generate and dispatch an Evolus MES work order or FA quarantine ticket for a completed run."""
    import json

    audit_dir = Path("data/audit")
    matches = list(audit_dir.glob(f"*{run_id}*.json"))
    if not matches:
        raise HTTPException(status_code=404, detail=f"Triage run '{run_id}' not found in audit trace directory.")

    raw_run = json.loads(matches[0].read_text(encoding="utf-8"))
    run_res = PipelineRunResult.model_validate(raw_run)
    ticket = create_evolus_ticket(run_res)
    return dispatch_evolus_ticket(ticket)


@app.get("/evolus/tickets", response_model=list[EvolusTicket], tags=["Evolus Integration"])
def get_evolus_tickets() -> list[EvolusTicket]:
    """Retrieve all dispatched Evolus work orders and failure analysis tickets."""
    return list_dispatched_tickets()
