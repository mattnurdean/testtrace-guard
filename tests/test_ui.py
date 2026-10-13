"""Acceptance tests for Step 9 Streamlit Dashboard logic and headless components."""

import py_compile
from pathlib import Path
import pytest

from testtrace.kb import KBIndexer
from testtrace.pipeline import run_pipeline
from testtrace.schemas import PipelineRunResult
from testtrace.storage import AuditStorage

APP_PATH = Path("app.py")
DATA_DIR = Path("data/synthetic")
KB_DIR = Path("data/kb")


def test_app_compilation_and_syntax() -> None:
    """Verify that app.py compiles cleanly without Python syntax errors."""
    assert APP_PATH.exists(), "app.py does not exist in root repository"
    compiled = py_compile.compile(str(APP_PATH), doraise=True)
    assert compiled is not None, "Failed to byte-compile app.py"


def test_case_listing_discovery() -> None:
    """Verify case discovery finds canonical cases CASE_A, CASE_B, and CASE_C."""
    import app

    cases = app.get_available_cases()
    assert isinstance(cases, list)
    assert len(cases) >= 3
    assert "CASE_A" in cases
    assert "CASE_B" in cases
    assert "CASE_C" in cases


def test_ui_pipeline_headless_run(tmp_path: Path) -> None:
    """Verify that the pipeline invocation executed by the UI executes successfully."""
    storage = AuditStorage(base_dir=tmp_path)
    kb = KBIndexer(kb_dir=KB_DIR)

    res = run_pipeline(
        case_path=DATA_DIR / "CASE_A",
        mode="mock",
        audit_storage=storage,
        kb_indexer=kb,
    )

    assert isinstance(res, PipelineRunResult)
    assert res.case_id == "CASE_A"
    assert res.report.category == "STATION_CONFIGURATION"
    assert res.report.confidence >= 0.80
    assert len(res.analytics.facts) > 0


def test_audit_ledger_ui_table(tmp_path: Path) -> None:
    """Verify that AuditStorage records can be converted to tabular format for Streamlit."""
    storage = AuditStorage(base_dir=tmp_path)
    kb = KBIndexer(kb_dir=KB_DIR)

    res = run_pipeline(DATA_DIR / "CASE_B", mode="mock", audit_storage=storage, kb_indexer=kb)
    records = storage.list_records(limit=10)

    assert len(records) > 0
    record_dicts = [
        {
            "Run ID": r.run_id,
            "Case ID": r.case_id,
            "Category": r.category,
            "Verdict": r.validator_verdict,
        }
        for r in records
    ]
    assert len(record_dicts) > 0
    assert record_dicts[0]["Case ID"] == "CASE_B"