"""Acceptance tests for Step 5 Knowledge Base Curation and Indexing."""

import time
from pathlib import Path
import pytest
from testtrace.kb import KBIndexer, KBDocument

KB_DIR = Path("data/kb")


@pytest.fixture(scope="module")
def indexer() -> KBIndexer:
    idx = KBIndexer(kb_dir=KB_DIR)
    assert len(idx.documents) >= 6, "Knowledge base must contain at least 6 manuals"
    return idx


def test_kb_manuals_exist_and_loaded(indexer: KBIndexer) -> None:
    expected_manual_ids = {"MAN-401", "MAN-501", "MAN-601", "MAN-701", "MAN-801", "MAN-901"}
    loaded_ids = {doc.doc_id for doc in indexer.documents}
    assert expected_manual_ids.issubset(loaded_ids), f"Missing manuals: {expected_manual_ids - loaded_ids}"


def test_kb_document_metadata_integrity(indexer: KBIndexer) -> None:
    for doc in indexer.documents:
        assert doc.doc_id.startswith("MAN-")
        assert doc.prefix.startswith("MAN-")
        assert len(doc.title) > 5
        assert doc.category in {
            "STATION_CONFIGURATION",
            "FIXTURE_CONTACT",
            "DUT_DEFECT",
            "INSTRUMENT_CALIBRATION",
            "SPEC_OR_REVISION_MISMATCH",
            "INSUFFICIENT_EVIDENCE",
        }
        assert len(doc.keywords) >= 4
        assert len(doc.action_items) >= 3
        assert len(doc.content) > 200


def test_prefix_lookups(indexer: KBIndexer) -> None:
    assert indexer.get_document_by_prefix("MAN-4") is not None
    assert indexer.get_document_by_prefix("MAN-5") is not None
    assert indexer.get_document_by_prefix("MAN-6") is not None
    assert indexer.get_document_by_prefix("MAN-7") is not None
    assert indexer.get_document_by_prefix("MAN-8") is not None
    assert indexer.get_document_by_prefix("MAN-9") is not None


@pytest.mark.parametrize(
    "query, expected_prefix",
    [
        ("cable loss compensation table reference path configuration offset", "MAN-4"),
        ("DUT isolation shield LO leakage internal mixer defect", "MAN-6"),
        ("fixture contact pin repeatability re-seat mechanical alignment", "MAN-5"),
        ("instrument calibration overdue drift reference standard metrology", "MAN-7"),
        ("product revision test limits mismatch REV_A REV_B sequence", "MAN-8"),
        ("missing golden baseline unrecorded calibration gap inconclusive", "MAN-9"),
    ],
)
def test_bm25_retrieval_accuracy(indexer: KBIndexer, query: str, expected_prefix: str) -> None:
    results = indexer.search(query, top_k=3)
    assert len(results) > 0, f"Query '{query}' returned no results"
    top_doc, top_score = results[0]
    assert top_doc.prefix == expected_prefix, (
        f"Query '{query}' retrieved {top_doc.prefix} ({top_doc.doc_id}) instead of {expected_prefix}. Score: {top_score}"
    )
    assert top_score > 0.0, "Top BM25 score must be non-zero"


def test_retrieval_speed_benchmark(indexer: KBIndexer) -> None:
    query = "golden reference check cable loss compensation ST-A"

    # Warmup
    _ = indexer.search(query, top_k=3)

    start = time.perf_counter()
    iterations = 50
    for _ in range(iterations):
        _ = indexer.search(query, top_k=3)
    elapsed_ms = ((time.perf_counter() - start) / iterations) * 1000.0

    assert elapsed_ms < 50.0, f"Average BM25 search latency ({elapsed_ms:.3f} ms) exceeds 50 ms budget"