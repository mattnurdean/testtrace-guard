"""Audit storage and query engine for TestTrace Guard triage runs."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from testtrace.schemas import AuditRecord, PipelineRunResult


class AuditStorage:
    """Manages persistent JSON execution records and SQLite query indexing."""

    def __init__(self, base_dir: Path = Path("data/audit")):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.base_dir / "audit_index.db"
        self._init_sqlite()

    def _init_sqlite(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_runs (
                    run_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    category TEXT NOT NULL,
                    target_side TEXT NOT NULL,
                    status TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    primary_kb_doc TEXT NOT NULL,
                    validator_verdict TEXT NOT NULL,
                    total_execution_time_ms REAL NOT NULL,
                    audit_file_path TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_case_id ON audit_runs (case_id)")
            conn.commit()

    def save_run(self, result: PipelineRunResult) -> str:
        """Persist full run to JSON and index in SQLite ledger."""
        # Sanitize timestamp for filename
        ts_slug = result.timestamp.replace(":", "-").replace("T", "_").replace("Z", "")
        filename = f"{result.case_id}_{result.run_id}_{ts_slug}.json"
        target_file = self.base_dir / filename

        result.audit_file_path = str(target_file.as_posix())

        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, indent=2)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO audit_runs (
                    run_id, case_id, timestamp, category, target_side,
                    status, confidence, primary_kb_doc, validator_verdict,
                    total_execution_time_ms, audit_file_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.run_id,
                    result.case_id,
                    result.timestamp,
                    result.report.category,
                    result.report.target_side,
                    result.report.status,
                    result.report.confidence,
                    result.report.primary_kb_doc,
                    result.report.validator_verdict,
                    result.total_execution_time_ms,
                    result.audit_file_path,
                ),
            )
            conn.commit()

        return result.audit_file_path

    def list_records(self, limit: int = 50) -> list[AuditRecord]:
        """Query recent triage runs from SQLite ledger."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM audit_runs
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()

        records: list[AuditRecord] = []
        for r in rows:
            records.append(
                AuditRecord(
                    run_id=r["run_id"],
                    case_id=r["case_id"],
                    timestamp=r["timestamp"],
                    category=r["category"],
                    target_side=r["target_side"],
                    status=r["status"],
                    confidence=r["confidence"],
                    primary_kb_doc=r["primary_kb_doc"],
                    validator_verdict=r["validator_verdict"],
                    total_execution_time_ms=r["total_execution_time_ms"],
                    audit_file_path=r["audit_file_path"],
                )
            )
        return records

    def load_run(self, run_id: str) -> Optional[PipelineRunResult]:
        """Load full pipeline run payload from JSON file by run_id."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT audit_file_path FROM audit_runs WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()

        if not row:
            # Fallback search in directory
            for path in self.base_dir.glob(f"*_{run_id}_*.json"):
                with open(path, "r", encoding="utf-8") as f:
                    return PipelineRunResult.model_validate_json(f.read())
            return None

        audit_path = Path(row[0])
        if audit_path.exists():
            with open(audit_path, "r", encoding="utf-8") as f:
                return PipelineRunResult.model_validate_json(f.read())
        return None