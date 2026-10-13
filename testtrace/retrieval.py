"""Hybrid retrieval engine combining rule anchors and BM25 lexical ranking."""

import time
from pathlib import Path
from typing import Optional

from testtrace.kb import KBIndexer, KBDocument
from testtrace.schemas import (
    AnalyticsResult,
    RetrievalResult,
    RetrievedDocument,
    RuleEvaluationResult,
)


def build_retrieval_query(analytics: AnalyticsResult, rule_res: RuleEvaluationResult) -> str:
    """Synthesize evidence facts and rule triage context into an expressive BM25 query."""
    tokens: list[str] = [
        rule_res.recommended_category.replace("_", " "),
        rule_res.suggested_action,
    ]

    # Incorporate failed test parameter names
    for ft in analytics.failed_tests:
        tokens.append(ft.replace("_", " "))

    # Incorporate supporting or critical evidence facts
    for f in analytics.facts:
        if f.fact_id in rule_res.supporting_fact_ids or f.severity == "CRITICAL":
            tokens.append(f.description)

    # Incorporate station context
    for st in analytics.affected_stations:
        tokens.append(st)

    return " ".join(tokens)


def extract_document_excerpt(doc: KBDocument, max_chars: int = 400) -> str:
    """Extract a concise summary excerpt from document markdown content."""
    lines = doc.content.splitlines()
    body_lines: list[str] = []
    capture = False

    for line in lines:
        if line.startswith("## 2. Measurement Signatures") or line.startswith("## 3. Root Cause Analysis"):
            capture = True
            continue
        elif line.startswith("## 4. Mandatory Corrective Action Protocol"):
            break

        if capture and line.strip() and not line.startswith("#"):
            body_lines.append(line.strip())

    excerpt = " ".join(body_lines)
    if len(excerpt) > max_chars:
        excerpt = excerpt[:max_chars].rsplit(" ", 1)[0] + "..."
    return excerpt or doc.content[:max_chars] + "..."


def format_llm_context(
    primary: RetrievedDocument,
    secondary: list[RetrievedDocument],
    rule_res: RuleEvaluationResult,
) -> str:
    """Format structured standard operating procedure context for prompt injection."""
    lines: list[str] = [
        "=== RETRIEVED STANDARD OPERATING PROCEDURE (PRIMARY AUDIT REFERENCE) ===",
        f"Manual ID: {primary.doc_id} ({primary.title})",
        f"Category: {primary.category} | Architectural Domain: {primary.target_side}",
        f"Source Specification: {primary.file_path}",
        "",
        "Mandatory Corrective Action Protocol:",
    ]

    if primary.action_items:
        for item in primary.action_items:
            lines.append(f"  {item}")
    else:
        lines.append(f"  - {rule_res.suggested_action}")

    lines.extend([
        "",
        "Diagnostic Signatures & Root Cause Context:",
        f"  {primary.excerpt}",
    ])

    if secondary:
        lines.extend([
            "",
            "=== SUPPLEMENTARY CROSS-REFERENCE MANUALS ===",
        ])
        for s_doc in secondary:
            lines.append(f"- {s_doc.doc_id}: {s_doc.title} (Category: {s_doc.category})")

    return "\n".join(lines)


def retrieve_context(
    analytics: AnalyticsResult,
    rule_res: RuleEvaluationResult,
    kb_indexer: Optional[KBIndexer] = None,
    kb_dir: Path = Path("data/kb"),
    top_k: int = 3,
) -> RetrievalResult:
    """Perform hybrid retrieval integrating deterministic rule anchor and BM25 ranking."""
    start_time = time.perf_counter()

    if kb_indexer is None:
        kb_indexer = KBIndexer(kb_dir=kb_dir)

    query_text = build_retrieval_query(analytics, rule_res)
    bm25_matches = kb_indexer.search(query_text, top_k=max(top_k, 4))

    # Deterministic anchor lookup based on rule engine recommendation
    anchor_doc = kb_indexer.get_document_by_prefix(rule_res.suggested_kb_prefix)

    ranked_docs: list[RetrievedDocument] = []
    seen_ids: set[str] = set()

    # Priority 1: Direct anchor promotion
    if anchor_doc:
        anchor_bm25_score = next((score for doc, score in bm25_matches if doc.doc_id == anchor_doc.doc_id), 0.0)
        # Apply deterministic routing boost
        hybrid_score = anchor_bm25_score + 100.0
        retrieved_anchor = RetrievedDocument(
            doc_id=anchor_doc.doc_id,
            prefix=anchor_doc.prefix,
            title=anchor_doc.title,
            category=anchor_doc.category,
            target_side=anchor_doc.target_side,
            score=round(hybrid_score, 3),
            retrieval_method="ANCHOR_MATCH" if anchor_bm25_score == 0.0 else "HYBRID",
            action_items=anchor_doc.action_items,
            excerpt=extract_document_excerpt(anchor_doc),
            file_path=anchor_doc.file_path,
        )
        ranked_docs.append(retrieved_anchor)
        seen_ids.add(anchor_doc.doc_id)

    # Priority 2: BM25 ranked documents
    for doc, score in bm25_matches:
        if doc.doc_id in seen_ids:
            continue
        ranked_docs.append(
            RetrievedDocument(
                doc_id=doc.doc_id,
                prefix=doc.prefix,
                title=doc.title,
                category=doc.category,
                target_side=doc.target_side,
                score=round(score, 3),
                retrieval_method="BM25_LEXICAL",
                action_items=doc.action_items,
                excerpt=extract_document_excerpt(doc),
                file_path=doc.file_path,
            )
        )
        seen_ids.add(doc.doc_id)

    if not ranked_docs:
        raise RuntimeError(f"Retrieval yielded zero documents for case {analytics.case_id}")

    primary_doc = ranked_docs[0]
    secondary_docs = ranked_docs[1:top_k]
    formatted_context = format_llm_context(primary_doc, secondary_docs, rule_res)

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return RetrievalResult(
        case_id=analytics.case_id,
        query_text=query_text,
        primary_doc=primary_doc,
        secondary_docs=secondary_docs,
        formatted_context=formatted_context,
        execution_time_ms=round(elapsed_ms, 3),
    )