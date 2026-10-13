"""Acceptance tests for Step 8 Pipeline, Storage, and FastAPI Service."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from testtrace.api import app
from testtrace.kb import KBIndexer
from testtrace.pipeline import run_pipeline
from testtrace.schemas import PipelineRunResult
from testtrace.storage import AuditStorage

DATA_DIR = Path("data/synthetic")
KB_DIR = Path("data/kb")


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="module")
def shared_kb() -> KBIndexer:
    return KBIndexer(kb_dir=KB_DIR)


def test_pipeline_e2e_case_a(tmp_path: Path, shared_kb: KBIndexer) -> None:
    storage = AuditStorage(base_dir=tmp_path)
    res = run_pipeline(
        case_path=DATA_DIR / "CASE_A",
        mode="mock",
        audit_storage=storage,
        kb_indexer=shared_kb,
    )

    assert isinstance(res, PipelineRunResult)
    assert res.case_id == "CASE_A"
    assert res.report.category == "STATION_CONFIGURATION"
    assert res.report.target_side == "MEASUREMENT_SYSTEM"
    assert res.report.status == "PLAN_READY_FOR_REVIEW"
    assert res.report.primary_kb_doc == "MAN-401"
    assert res.report.validator_verdict in ("PASS", "CORRECTED")
    assert res.audit_file_path is not None
    assert Path(res.audit_file_path).exists()


def test_pipeline_e2e_case_b(tmp_path: Path, shared_kb: KBIndexer) -> None:
    storage = AuditStorage(base_dir=tmp_path)
    res = run_pipeline(
        case_path=DATA_DIR / "CASE_B",
        mode="mock",
        audit_storage=storage,
        kb_indexer=shared_kb,
    )

    assert res.case_id == "CASE_B"
    assert res.report.category == "DUT_DEFECT"
    assert res.report.target_side == "DUT"
    assert res.report.primary_kb_doc == "MAN-601"
    assert res.report.status == "PLAN_READY_FOR_REVIEW"


def test_pipeline_e2e_case_c(tmp_path: Path, shared_kb: KBIndexer) -> None:
    storage = AuditStorage(base_dir=tmp_path)
    res = run_pipeline(
        case_path=DATA_DIR / "CASE_C",
        mode="mock",
        audit_storage=storage,
        kb_indexer=shared_kb,
    )

    assert res.case_id == "CASE_C"
    assert res.report.category == "INSUFFICIENT_EVIDENCE"
    assert res.report.target_side == "UNDETERMINED"
    assert res.report.status == "NEEDS_MORE_DATA"
    assert res.report.primary_kb_doc == "MAN-901"


def test_storage_persistence_and_query(tmp_path: Path, shared_kb: KBIndexer) -> None:
    storage = AuditStorage(base_dir=tmp_path)
    res_a = run_pipeline(DATA_DIR / "CASE_A", mode="mock", audit_storage=storage, kb_indexer=shared_kb)
    res_b = run_pipeline(DATA_DIR / "CASE_B", mode="mock", audit_storage=storage, kb_indexer=shared_kb)

    # Verify listing
    records = storage.list_records(limit=10)
    assert len(records) >= 2
    run_ids = {r.run_id for r in records}
    assert res_a.run_id in run_ids
    assert res_b.run_id in run_ids

    # Verify retrieval
    loaded = storage.load_run(res_a.run_id)
    assert loaded is not None
    assert loaded.run_id == res_a.run_id
    assert loaded.case_id == "CASE_A"
    assert loaded.report.category == "STATION_CONFIGURATION"


def test_api_health_endpoint(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "testtrace-guard"
    assert data["kb_documents_loaded"] >= 6


def test_api_cases_endpoint(client: TestClient) -> None:
    resp = client.get("/cases")
    assert resp.status_code == 200
    cases = resp.json()
    assert "CASE_A" in cases
    assert "CASE_B" in cases
    assert "CASE_C" in cases


def test_api_triage_endpoint(client: TestClient) -> None:
    resp = client.post("/triage/CASE_A?mode=mock")
    assert resp.status_code == 200
    data = resp.json()
    assert data["case_id"] == "CASE_A"
    assert data["report"]["category"] == "STATION_CONFIGURATION"
    assert data["report"]["target_side"] == "MEASUREMENT_SYSTEM"
    assert "audit_file_path" in data


def test_api_audit_endpoints(client: TestClient) -> None:
    # Trigger triage
    post_resp = client.post("/triage/CASE_B?mode=mock")
    assert post_resp.status_code == 200
    run_id = post_resp.json()["run_id"]

    # Verify audit list
    list_resp = client.get("/audit")
    assert list_resp.status_code == 200
    records = list_resp.json()
    assert any(r["run_id"] == run_id for r in records)

    # Verify specific audit retrieval
    get_resp = client.get(f"/audit/{run_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["run_id"] == run_id
    assert get_resp.json()["case_id"] == "CASE_B"


def test_pipeline_latency_benchmark(tmp_path: Path, shared_kb: KBIndexer) -> None:
    storage = AuditStorage(base_dir=tmp_path)
    # Warmup
    _ = run_pipeline(DATA_DIR / "CASE_A", mode="mock", audit_storage=storage, kb_indexer=shared_kb)

    # Benchmark run
    res = run_pipeline(DATA_DIR / "CASE_A", mode="mock", audit_storage=storage, kb_indexer=shared_kb)
    assert res.total_execution_time_ms < 500.0, (
        f"End-to-end pipeline execution ({res.total_execution_time_ms:.2f} ms) exceeds 500 ms mock budget"
    )