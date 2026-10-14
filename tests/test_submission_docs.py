"""Acceptance tests for Step 13 Submission Documents and Slides Outline."""

from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
SLIDES_PATH = ROOT_DIR / "docs" / "SLIDES_OUTLINE.md"
SUBMISSION_PATH = ROOT_DIR / "docs" / "SUBMISSION_TEXT.md"


def test_slides_outline_exists_and_content() -> None:
    """Verify docs/SLIDES_OUTLINE.md exists, has proper length, and covers all 7 slides."""
    assert SLIDES_PATH.exists(), "docs/SLIDES_OUTLINE.md does not exist"
    content = SLIDES_PATH.read_text(encoding="utf-8")
    assert len(content) > 1800, "docs/SLIDES_OUTLINE.md is unexpectedly short"

    required_slides = [
        "Slide 1: Title & Executive Tagline",
        "Slide 2: The Manufacturing Dilemma",
        "Slide 3: Multi-Tiered Architecture",
        "Slide 4: Canonical Demonstration Scenarios",
        "Slide 5: Quantitative Benchmark & Verification",
        "Slide 6: Enterprise Ready: REST API & Streamlit Console",
        "Slide 7: AMD Infrastructure & The Road Ahead",
    ]
    for slide in required_slides:
        assert slide in content, f"Missing required slide section: '{slide}'"


def test_submission_text_exists_and_content() -> None:
    """Verify docs/SUBMISSION_TEXT.md exists, has proper length, and covers all portal fields."""
    assert SUBMISSION_PATH.exists(), "docs/SUBMISSION_TEXT.md does not exist"
    content = SUBMISSION_PATH.read_text(encoding="utf-8")
    assert len(content) > 2200, "docs/SUBMISSION_TEXT.md is unexpectedly short"

    required_sections = [
        "1. Project Title & Tagline",
        "2. Inspiration & Problem Statement",
        "3. What TestTrace Guard Does",
        "4. How We Built It (Technical Architecture)",
        "5. Benchmarks & Verification",
        "6. AMD Technology Stack & Hardware Acceleration",
        "7. What's Next",
    ]
    for sec in required_sections:
        assert sec in content, f"Missing required submission section: '{sec}'"


def test_documents_benchmark_consistency() -> None:
    """Verify that both documents accurately reflect the verified 95.3% benchmark results."""
    slides_content = SLIDES_PATH.read_text(encoding="utf-8")
    submission_content = SUBMISSION_PATH.read_text(encoding="utf-8")

    for doc_content, name in [(slides_content, "SLIDES_OUTLINE"), (submission_content, "SUBMISSION_TEXT")]:
        assert "95.3%" in doc_content, f"Missing 95.3% benchmark accuracy in {name}"
        assert "MAN-401" in doc_content, f"Missing MAN-401 reference in {name}"
        assert "CASE_A" in doc_content or "Case A" in doc_content, f"Missing Case A in {name}"
        assert "CASE_B" in doc_content or "Case B" in doc_content, f"Missing Case B in {name}"
        assert "CASE_C" in doc_content or "Case C" in doc_content, f"Missing Case C in {name}"
        assert "ROCm" in doc_content, f"Missing ROCm in {name}"
        assert "vLLM" in doc_content, f"Missing vLLM in {name}"