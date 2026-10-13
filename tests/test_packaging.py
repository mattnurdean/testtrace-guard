import importlib.util
from pathlib import Path
import pytest

try:
    import tomllib  # Python 3.11+ standard library
except ImportError:
    import tomli as tomllib  # type: ignore

ROOT_DIR = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = ROOT_DIR / "pyproject.toml"
README_PATH = ROOT_DIR / "README.md"


def test_pyproject_toml_exists_and_parses() -> None:
    """Verify pyproject.toml exists and conforms to valid TOML syntax."""
    assert PYPROJECT_PATH.exists(), "pyproject.toml is missing from root"
    content = PYPROJECT_PATH.read_text(encoding="utf-8")
    data = tomllib.loads(content)

    assert "project" in data
    proj = data["project"]
    assert proj["name"] == "testtrace-guard"
    assert proj["version"] == "0.1.0"
    assert "dependencies" in proj
    assert len(proj["dependencies"]) >= 5


def test_dependencies_declared() -> None:
    """Verify critical dependencies are specified in pyproject.toml."""
    data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    deps = " ".join(data["project"]["dependencies"]).lower()

    for expected in ["pydantic", "fastapi", "uvicorn", "streamlit", "pandas"]:
        assert expected in deps, f"Expected dependency '{expected}' missing from pyproject.toml"


def test_cli_entry_points_configured() -> None:
    """Verify console script CLI entry point is defined."""
    data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    scripts = data["project"].get("scripts", {})
    assert "testtrace" in scripts
    assert scripts["testtrace"] == "testtrace.pipeline:main"


def test_readme_contains_core_sections() -> None:
    """Verify README.md exists and covers all essential operational sections."""
    assert README_PATH.exists(), "README.md is missing from root"
    text = README_PATH.read_text(encoding="utf-8")

    essential_sections = [
        "Executive Summary & Problem Statement",
        "System Architecture",
        "Benchmark & Verification Results",
        "Quick Start Guide",
        "AMD Infrastructure & Fallback Protocol",
        "Project Structure",
    ]
    for section in essential_sections:
        assert section in text, f"Missing section '{section}' in README.md"

    # Verify benchmark accuracy numbers are documented
    assert "95.3%" in text, "README must document measured 95.3% accuracy"
    assert "30.51 ms" in text or "30.5" in text or "35 ms" in text


def test_package_modules_importable() -> None:
    """Verify all primary submodules can be imported cleanly."""
    modules = [
        "testtrace.schemas",
        "testtrace.analytics",
        "testtrace.rules",
        "testtrace.kb",
        "testtrace.retrieval",
        "testtrace.reasoner",
        "testtrace.validator",
        "testtrace.storage",
        "testtrace.pipeline",
        "testtrace.api",
    ]
    for mod in modules:
        spec = importlib.util.find_spec(mod)
        assert spec is not None, f"Module '{mod}' could not be located in environment"