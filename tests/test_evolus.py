"""Acceptance tests for Step 14 Evolus MES and Work Order Integration."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from testtrace.api import app
from testtrace.evolus import (
    create_evolus_ticket,
    dispatch_evolus_ticket,
    list_dispatched_tickets,
)
from testtrace.kb import KBIndexer
from testtrace.pipeline import run_pipeline
from testtrace.schemas import EvolusTicket
from testtrace.storage import AuditStorage

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "synthetic"
KB_DIR = ROOT_DIR / "data" / "kb"


@pytest.fixture
def test_pipeline_results(tmp_path: Path):
    """Run Canonical Cases A, B, and C to produce test PipelineRunResults."""
    storage = AuditStorage(base_dir=tmp_path / "audit")
    kb = KBIndexer(kb_dir=KB_DIR)

    res_a = run_pipeline(DATA_DIR / "CASE_A", mode="mock", audit_storage=storage, kb_indexer=kb)
    res_b = run_pipeline(DATA_DIR / "CASE_B", mode="mock", audit_storage=storage, kb_indexer=kb)
    res_c = run_pipeline(DATA_DIR / "CASE_C", mode="mock", audit_storage=storage, kb_indexer=kb)
    return res_a, res_b, res_c, storage


def test_evolus_ticket_mapping_case_a(test_pipeline_results):
    res_a, _, _, _ = test_pipeline_results
    ticket = create_evolus_ticket(res_a)

    assert isinstance(ticket, EvolusTicket)
    assert ticket.ticket_type == "STATION_MAINTENANCE_HALT"
    assert "Station_ST-A" in ticket.target_entity
    assert ticket.priority == "CRITICAL"
    assert ticket.sop_reference == "MAN-401"
    assert len(ticket.action_items) > 0


def test_evolus_ticket_mapping_case_b(test_pipeline_results):
    _, res_b, _, _ = test_pipeline_results
    ticket = create_evolus_ticket(res_b)

    assert ticket.ticket_type == "DUT_FAILURE_ANALYSIS_QUARANTINE"
    assert ticket.target_entity == "DUT_017"
    assert ticket.priority == "HIGH"
    assert ticket.sop_reference == "MAN-601"


def test_evolus_ticket_mapping_case_c(test_pipeline_results):
    _, _, res_c, _ = test_pipeline_results
    ticket = create_evolus_ticket(res_c)

    assert ticket.ticket_type == "VERIFICATION_SWEEP_DISPATCH"
    assert ticket.priority == "HIGH"
    assert ticket.sop_reference == "MAN-901"


def test_evolus_ticket_persistence(tmp_path: Path, test_pipeline_results):
    res_a, _, _, _ = test_pipeline_results
    ticket = create_evolus_ticket(res_a)
    evolus_dir = tmp_path / "evolus"

    dispatched = dispatch_evolus_ticket(ticket, evolus_dir=evolus_dir)
    assert dispatched.status == "DISPATCHED"

    tickets_on_disk = list_dispatched_tickets(evolus_dir=evolus_dir)
    assert len(tickets_on_disk) == 1
    assert tickets_on_disk[0].ticket_id == ticket.ticket_id
    assert tickets_on_disk[0].title == ticket.title


def test_api_evolus_dispatch_flow(tmp_path: Path):
    with TestClient(app) as client:
        # 1. Trigger triage on CASE_A to index an audit record
        triage_resp = client.post("/triage/CASE_A?mode=mock")
        assert triage_resp.status_code == 200
        run_id = triage_resp.json()["run_id"]

        # 2. Dispatch Evolus ticket via API
        disp_resp = client.post(f"/evolus/dispatch/{run_id}")
        assert disp_resp.status_code == 200
        ticket_data = disp_resp.json()
        assert ticket_data["run_id"] == run_id
        assert ticket_data["sop_reference"] == "MAN-401"

        # 3. Query dispatched tickets list
        list_resp = client.get("/evolus/tickets")
        assert list_resp.status_code == 200
        all_tickets = list_resp.json()
        assert any(t["ticket_id"] == ticket_data["ticket_id"] for t in all_tickets)
