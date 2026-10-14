"""Acceptance tests for Step 15 Final Submission Bundle and Repository Integrity."""

import importlib.util
import json
from pathlib import Path
from typing import Any, Optional
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_root_files_present_and_non_empty() -> None:
    """Verify all essential project root files exist and are populated."""
    essential_root_files = [
        "pyproject.toml",
        "README.md",
        "LICENSE",
        "pytest.ini",
        "STATE.md",
        ".gitignore",
        ".env.example",
        "app.py",
    ]
    for filename in essential_root_files:
        p = ROOT_DIR / filename
        assert p.exists(), f"Essential root file missing: {filename}"
        assert p.stat().st_size > 10, f"File appears unexpectedly empty: {filename}"


def test_documentation_deliverables_present() -> None:
    """Verify all documentation artifacts in docs/ exist and exceed minimum length."""
    docs = [
        "DEMO_SCRIPT.md",
        "SLIDES_OUTLINE.md",
        "SUBMISSION_TEXT.md",
        "SUBMISSION_CHECKLIST.md",
    ]
    for doc in docs:
        p = ROOT_DIR / "docs" / doc
        assert p.exists(), f"Documentation file missing: docs/{doc}"
        assert p.stat().st_size > 500, f"Documentation file too brief: docs/{doc}"


def test_all_core_modules_importable() -> None:
    """Verify that all core testtrace package modules are importable."""
    modules = [
        "testtrace.schemas",
        "testtrace.datagen",
        "testtrace.analytics",
        "testtrace.rules",
        "testtrace.kb",
        "testtrace.retrieval",
        "testtrace.reasoner",
        "testtrace.validator",
        "testtrace.storage",
        "testtrace.pipeline",
        "testtrace.api",
        "testtrace.evolus",
    ]
    for mod in modules:
        spec = importlib.util.find_spec(mod)
        assert spec is not None, f"Module '{mod}' could not be located in environment"


def test_knowledge_base_sop_manuals_present() -> None:
    """Verify that all 6 Standard Operating Procedure manuals are present in data/kb/."""
    expected_sops = [
        "MAN-401_station_configuration.md",
        "MAN-501_fixture_contact.md",
        "MAN-601_dut_rf_defects.md",
        "MAN-701_instrument_calibration.md",
        "MAN-801_revision_limits.md",
        "MAN-901_ambiguity_data_gaps.md",
    ]
    kb_dir = ROOT_DIR / "data" / "kb"
    for sop in expected_sops:
        p = kb_dir / sop
        assert p.exists(), f"SOP manual missing: data/kb/{sop}"
        assert p.stat().st_size > 200, f"SOP manual unexpectedly short: data/kb/{sop}"


def _find_key_recursive(obj: Any, key: str) -> Optional[Any]:
    """Search for a key in a nested dict/list structure."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            res = _find_key_recursive(v, key)
            if res is not None:
                return res
    elif isinstance(obj, list):
        for item in obj:
            res = _find_key_recursive(item, key)
            if res is not None:
                return res
    return None


def test_synthetic_packages_and_benchmark_artifacts() -> None:
    """Verify that all 43 synthetic packages and benchmark results exist."""
    synthetic_dir = ROOT_DIR / "data" / "synthetic"
    assert synthetic_dir.exists(), "data/synthetic directory is missing"

    for case_id in ["CASE_A", "CASE_B", "CASE_C"]:
        assert (synthetic_dir / case_id).is_dir(), f"Missing canonical case: {case_id}"

    packages = [d.name for d in synthetic_dir.iterdir() if d.is_dir()]
    assert len(packages) >= 43, f"Expected at least 43 test packages, found {len(packages)}"

    bench_json_path = ROOT_DIR / "data" / "benchmark_results.json"
    bench_md_path = ROOT_DIR / "data" / "benchmark_summary.md"
    assert bench_json_path.exists(), "data/benchmark_results.json is missing"
    assert bench_md_path.exists(), "data/benchmark_summary.md is missing"

    summary_md = bench_md_path.read_text(encoding="utf-8")
    assert "95.3%" in summary_md, "Benchmark summary markdown missing 95.3% accuracy indicator"

    telemetry = json.loads(bench_json_path.read_text(encoding="utf-8"))
    cat_acc = _find_key_recursive(telemetry, "category_accuracy")
    assert cat_acc is not None, "category_accuracy not found in benchmark telemetry"
    assert cat_acc >= 0.90 or cat_acc >= 90.0, f"Category accuracy below target: {cat_acc}"

    dom_acc = _find_key_recursive(telemetry, "domain_accuracy") or _find_key_recursive(
        telemetry, "domain_side_accuracy"
    )
    assert dom_acc is not None, "domain_accuracy not found in benchmark telemetry"
    assert dom_acc >= 0.90 or dom_acc >= 90.0, f"Domain accuracy below target: {dom_acc}"
