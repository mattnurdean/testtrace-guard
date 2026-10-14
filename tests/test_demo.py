"""Acceptance tests for Step 12 Demo Script documentation and CLI walkthrough."""

from pathlib import Path
import pytest

from scripts.demo_walkthrough import run_demo_walkthrough

ROOT_DIR = Path(__file__).resolve().parent.parent
DEMO_DOC_PATH = ROOT_DIR / "docs" / "DEMO_SCRIPT.md"


def test_demo_script_exists_and_non_empty() -> None:
    """Verify docs/DEMO_SCRIPT.md exists and is populated."""
    assert DEMO_DOC_PATH.exists(), "docs/DEMO_SCRIPT.md does not exist"
    content = DEMO_DOC_PATH.read_text(encoding="utf-8")
    assert len(content) > 1500, "docs/DEMO_SCRIPT.md is unexpectedly short"


def test_demo_script_covers_all_scenes_and_cases() -> None:
    """Verify time-coded scenes, canonical cases, and SOPs are documented."""
    content = DEMO_DOC_PATH.read_text(encoding="utf-8")

    required_markers = [
        "Pre-Flight Recording Checklist",
        "Scene 1",
        "Scene 2",
        "Scene 3",
        "Scene 4",
        "Scene 5",
        "Scene 6",
        "CASE_A",
        "Case B",
        "Case C",
        "MAN-401",
        "MAN-601",
        "MAN-901",
        "NEEDS_MORE_DATA",
        "95.3%",
    ]
    for marker in required_markers:
        assert marker in content, f"Required demo script element '{marker}' missing from docs/DEMO_SCRIPT.md"


def test_demo_walkthrough_execution(tmp_path: Path) -> None:
    """Verify scripts/demo_walkthrough.py executes all 3 canonical cases cleanly."""
    summaries = run_demo_walkthrough(
        data_dir=ROOT_DIR / "data" / "synthetic",
        audit_dir=tmp_path / "audit",
        kb_dir=ROOT_DIR / "data" / "kb",
        mode="mock",
    )

    assert len(summaries) == 3

    # Case A checks
    assert summaries[0]["case_id"] == "CASE_A"
    assert summaries[0]["category"] == "STATION_CONFIGURATION"
    assert summaries[0]["primary_kb_doc"] == "MAN-401"

    # Case B checks
    assert summaries[1]["case_id"] == "CASE_B"
    assert summaries[1]["category"] == "DUT_DEFECT"
    assert summaries[1]["primary_kb_doc"] == "MAN-601"

    # Case C checks
    assert summaries[2]["case_id"] == "CASE_C"
    assert summaries[2]["category"] == "INSUFFICIENT_EVIDENCE"
    assert summaries[2]["status"] == "NEEDS_MORE_DATA"
    assert summaries[2]["primary_kb_doc"] == "MAN-901"