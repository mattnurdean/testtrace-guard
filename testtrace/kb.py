"""Knowledge Base (KB) loading, metadata extraction, and pure-Python BM25 search engine."""

import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, Field


class KBDocument(BaseModel):
    """Structured representation of an engineering SOP document."""
    doc_id: str
    prefix: str
    title: str
    category: str
    fault_family: str
    target_side: str
    keywords: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    content: str
    file_path: str


class BM25Okapi:
    """Zero-dependency, pure-Python implementation of BM25Okapi."""

    def __init__(self, corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.avgdl = sum(len(doc) for doc in corpus) / self.corpus_size if self.corpus_size > 0 else 0.0
        self.doc_freqs: list[Counter] = []
        self.doc_lens: list[int] = [len(doc) for doc in corpus]
        self.idf: dict[str, float] = {}

        df: Counter = Counter()
        for doc in corpus:
            counts = Counter(doc)
            self.doc_freqs.append(counts)
            for word in counts.keys():
                df[word] += 1

        for word, freq in df.items():
            # Standard Robertson-Spärck Jones smoothed IDF
            self.idf[word] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        scores = [0.0] * self.corpus_size
        for token in query_tokens:
            if token not in self.idf:
                continue
            idf_val = self.idf[token]
            for i, doc_freq in enumerate(self.doc_freqs):
                tf = doc_freq.get(token, 0)
                if tf > 0:
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (self.doc_lens[i] / self.avgdl))
                    scores[i] += idf_val * (numerator / denominator)
        return scores


def tokenize(text: str) -> list[str]:
    """Tokenize and normalize text for BM25 retrieval."""
    cleaned = re.sub(r"[^a-zA-Z0-9_\-\.]", " ", text.lower())
    return [tok for tok in cleaned.split() if len(tok) > 1]


class KBIndexer:
    """Manages markdown engineering manuals and performs ranked BM25 search."""

    def __init__(self, kb_dir: Path = Path("data/kb")):
        self.kb_dir = kb_dir
        self.documents: list[KBDocument] = []
        self._doc_by_id: dict[str, KBDocument] = {}
        self._doc_by_prefix: dict[str, KBDocument] = {}
        self.bm25: Optional[BM25Okapi] = None
        self._tokenized_corpus: list[list[str]] = []
        self.load_corpus()

    def parse_markdown(self, file_path: Path) -> KBDocument:
        text = file_path.read_text(encoding="utf-8")
        lines = text.splitlines()

        doc_id = ""
        prefix = ""
        category = ""
        fault_family = ""
        target_side = ""
        keywords: list[str] = []
        action_items: list[str] = []
        title = file_path.stem

        # Extract title from first H1 if present
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Parse bullet metadata
        in_action_protocol = False
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("- **Manual ID**:"):
                doc_id = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("- **Prefix**:"):
                prefix = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("- **Category**:"):
                category = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("- **Fault Family**:"):
                fault_family = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("- **Target Side**:"):
                target_side = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("- **Keywords**:"):
                kw_str = line_str.split(":", 1)[1].strip()
                keywords = [k.strip() for k in kw_str.split(",") if k.strip()]

            # Track action items
            if line_str.startswith("## 4. Mandatory Corrective Action Protocol"):
                in_action_protocol = True
                continue
            elif in_action_protocol and line_str.startswith("## "):
                in_action_protocol = False

            if in_action_protocol and re.match(r"^\d+\.\s+\*\*", line_str):
                action_items.append(line_str)

        return KBDocument(
            doc_id=doc_id or file_path.stem,
            prefix=prefix or (doc_id.split("-")[0] + "-" + doc_id.split("-")[1][0] if "-" in doc_id else "MAN-0"),
            title=title,
            category=category,
            fault_family=fault_family,
            target_side=target_side,
            keywords=keywords,
            action_items=action_items,
            content=text,
            file_path=str(file_path.as_posix()),
        )

    def load_corpus(self) -> None:
        """Scan directory and index all SOP markdown files."""
        self.documents.clear()
        self._doc_by_id.clear()
        self._doc_by_prefix.clear()
        self._tokenized_corpus.clear()

        md_files = sorted(list(self.kb_dir.glob("*.md")))
        for p in md_files:
            if p.name.startswith("KB_INDEX"):
                continue
            doc = self.parse_markdown(p)
            self.documents.append(doc)
            self._doc_by_id[doc.doc_id] = doc
            self._doc_by_prefix[doc.prefix] = doc

            # Combine title, keywords, category, and text for indexing
            doc_index_text = f"{doc.title} {' '.join(doc.keywords)} {doc.category} {doc.fault_family} {doc.content}"
            self._tokenized_corpus.append(tokenize(doc_index_text))

        if self._tokenized_corpus:
            self.bm25 = BM25Okapi(self._tokenized_corpus)

    def search(self, query: str, top_k: int = 3) -> list[tuple[KBDocument, float]]:
        """Rank documents using BM25 given a freeform query string."""
        if not self.bm25 or not self.documents:
            return []

        tokens = tokenize(query)
        if not tokens:
            return [(doc, 0.0) for doc in self.documents[:top_k]]

        scores = self.bm25.get_scores(tokens)
        scored_pairs = list(zip(self.documents, scores))
        scored_pairs.sort(key=lambda pair: pair[1], reverse=True)
        return scored_pairs[:top_k]

    def get_document_by_prefix(self, prefix: str) -> Optional[KBDocument]:
        """Fetch manual by standard prefix (e.g., 'MAN-4')."""
        return self._doc_by_prefix.get(prefix)

    def get_document_by_id(self, doc_id: str) -> Optional[KBDocument]:
        """Fetch manual by exact ID (e.g., 'MAN-401')."""
        return self._doc_by_id.get(doc_id)