"""
SQLite persistence layer for LegacyLens jobs and pipeline results.

Uses Python's built-in ``sqlite3`` module (sync). FastAPI runs sync handlers
in a threadpool automatically, so there is no blocking penalty.

Schema is designed for direct migration to Turso (LibSQL) — no
SQLite-specific features are used.
"""

from __future__ import annotations

import json
import sqlite3
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent / "legacylens.db"

# Only these artifact filenames may be served via the artifact endpoint.
ALLOWED_ARTIFACTS = frozenset({
    "logic_map.json",
    "logic_map.md",
    "modernized.py",
    "test_modernized.py",
    "review_report.json",
    "confidence.json",
    "errors.json",
    "pipeline_result.json",
})


# ---------------------------------------------------------------------------
# Connection & schema init
# ---------------------------------------------------------------------------

USE_TURSO = os.environ.get("USE_TURSO", "false").lower() == "true"
TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

class _DictRow(dict):
    def __init__(self, cols, vals):
        super().__init__(zip(cols, vals))
        self._vals = vals
    def __getitem__(self, key):
        if isinstance(key, int):
            return self._vals[key]
        return super().__getitem__(key)

class _TursoCursor:
    def __init__(self, rs):
        self.rs = rs
        self.idx = 0
    def fetchone(self):
        if not self.rs or self.idx >= len(self.rs.rows):
            return None
        row = self.rs.rows[self.idx]
        self.idx += 1
        return _DictRow(self.rs.columns, row)
    def fetchall(self):
        if not self.rs:
            return []
        return [_DictRow(self.rs.columns, row) for row in self.rs.rows]

class _TursoWrapper:
    def __init__(self, client):
        self.client = client
        self._closed = False
        
    def execute(self, sql, params=()):
        if self._closed:
            raise sqlite3.ProgrammingError("Cannot operate on a closed database.")
        try:
            rs = self.client.execute(sql, params)
            return _TursoCursor(rs)
        except Exception as e:
            err_str = str(e).lower()
            if "unique constraint failed" in err_str:
                raise sqlite3.IntegrityError(str(e))
            if "duplicate column name" in err_str or "already exists" in err_str:
                raise sqlite3.OperationalError(str(e))
            raise

    def executescript(self, sql):
        stmts = [s.strip() for s in sql.split(";") if s.strip()]
        if stmts:
            self.client.batch(stmts)
        return self

    def commit(self):
        pass
        
    def close(self):
        if not self._closed:
            self.client.close()
            self._closed = True

def _get_connection(db_path: Path | str = DB_PATH):
    """Open a connection using either Turso or local SQLite with fallback."""
    if USE_TURSO:
        if not TURSO_DATABASE_URL:
            # We explicitly want Turso, but URL is missing -> fail fast
            raise ValueError("USE_TURSO is true but TURSO_DATABASE_URL is not set.")
        
        import libsql_client
        try:
            client = libsql_client.create_client_sync(
                url=TURSO_DATABASE_URL,
                auth_token=TURSO_AUTH_TOKEN
            )
            # Test connection
            client.execute("SELECT 1")
            return _TursoWrapper(client)
        except Exception as e:
            # Deliberate failure: if USE_TURSO=true and it fails, DO NOT MUTELY FALL-BACK TO REST. Fail fast.
            raise RuntimeError(f"Failed to connect to Turso database: {e}")

    # Fallback / Local mode
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: Path | str = DB_PATH) -> None:
    """Create tables if they don't already exist."""
    conn = _get_connection(db_path)
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id              TEXT PRIMARY KEY,
                username        TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS jobs (
                id              TEXT PRIMARY KEY,
                file_name       TEXT NOT NULL,
                source_code     TEXT NOT NULL,
                status          TEXT NOT NULL DEFAULT 'pending',
                current_node    TEXT,
                iteration       INTEGER NOT NULL DEFAULT 0,
                error           TEXT,
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL,
                run_dir         TEXT
            );
        """)
        
        # Additive migration for Phase 6: Multi-File Projects
        try:
            conn.execute("ALTER TABLE jobs ADD COLUMN submitted_files TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Additive migration for Phase 7: Lineage & Versioning
        try:
            conn.execute("ALTER TABLE jobs ADD COLUMN parent_job_id TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE jobs ADD COLUMN run_version INTEGER NOT NULL DEFAULT 1")
        except sqlite3.OperationalError:
            pass

        # Additive migration for Phase 8: Authentication
        try:
            conn.execute("ALTER TABLE jobs ADD COLUMN user_id TEXT REFERENCES users(id)")
        except sqlite3.OperationalError:
            pass

        conn.executescript("""
            CREATE TABLE IF NOT EXISTS pipeline_results (
                job_id           TEXT PRIMARY KEY REFERENCES jobs(id),
                result_json      TEXT NOT NULL,
                confidence_level TEXT,
                iterations       INTEGER,
                has_errors       INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS pipeline_errors (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id          TEXT NOT NULL REFERENCES jobs(id),
                stage           TEXT NOT NULL,
                error_type      TEXT NOT NULL,
                message         TEXT NOT NULL,
                recoverable     INTEGER NOT NULL,
                iteration       INTEGER
            );
        """)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Users CRUD
# ---------------------------------------------------------------------------

def create_user(user_id: str, username: str, hashed_password: str, *, db_path: Path | str = DB_PATH) -> dict[str, Any]:
    now = _now_iso()
    conn = _get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO users (id, username, hashed_password, created_at) VALUES (?, ?, ?, ?)",
            (user_id, username, hashed_password, now)
        )
        conn.commit()
        return get_user_by_username(username, db_path=db_path)
    except sqlite3.IntegrityError:
        raise ValueError("Username already exists")
    finally:
        conn.close()

def get_user_by_username(username: str, *, db_path: Path | str = DB_PATH) -> dict[str, Any] | None:
    conn = _get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Jobs CRUD
# ---------------------------------------------------------------------------

def create_job(
    job_id: str,
    file_name: str,
    source_code: str,
    user_id: str,
    submitted_files: list[str] | None = None,
    parent_job_id: str | None = None,
    *,
    db_path: Path | str = DB_PATH,
) -> dict[str, Any]:
    """Insert a new job row with status='pending'. Returns the row as a dict."""
    if submitted_files is None:
        submitted_files = [file_name]
    
    now = _now_iso()
    conn = _get_connection(db_path)
    try:
        run_version = 1
        if parent_job_id:
            parent_row = conn.execute("SELECT parent_job_id FROM jobs WHERE id = ?", (parent_job_id,)).fetchone()
            if not parent_row:
                raise ValueError(f"Parent job {parent_job_id} not found")
            
            resolved_root = parent_row["parent_job_id"] or parent_job_id
            parent_job_id = resolved_root
            
            max_ver_row = conn.execute(
                "SELECT MAX(run_version) as max_v FROM jobs WHERE id = ? OR parent_job_id = ?", 
                (resolved_root, resolved_root)
            ).fetchone()
            run_version = (max_ver_row["max_v"] or 0) + 1

        conn.execute(
            """INSERT INTO jobs (id, file_name, source_code, status, created_at, updated_at, submitted_files, parent_job_id, run_version, user_id)
               VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?)""",
            (job_id, file_name, source_code, now, now, json.dumps(submitted_files), parent_job_id, run_version, user_id),
        )
        conn.commit()
        return get_job(job_id, user_id, db_path=db_path)
    finally:
        conn.close()


def get_job(job_id: str, user_id: str, *, db_path: Path | str = DB_PATH) -> dict[str, Any] | None:
    """Fetch a single job row as a dict, or None if not found or unauthorized."""
    conn = _get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM jobs WHERE id = ? AND user_id = ?", (job_id, user_id)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_jobs(
    user_id: str,
    page: int = 1,
    limit: int = 20,
    *,
    db_path: Path | str = DB_PATH,
) -> dict[str, Any]:
    """Return a paginated, newest-first list of jobs with metadata.

    Returns::

        {
            "jobs": [{"id": ..., "file_name": ..., ...}, ...],
            "total": 42,
            "page": 1,
            "limit": 20,
            "total_pages": 3,
        }
    """
    import math

    limit = max(1, min(limit, 100))
    page = max(1, page)
    offset = (page - 1) * limit

    conn = _get_connection(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM jobs WHERE user_id = ?", (user_id,)).fetchone()[0]
        rows = conn.execute(
            """SELECT j.id, j.file_name, j.status, j.iteration, j.created_at, j.updated_at,
                      j.parent_job_id, j.run_version,
                      pr.confidence_level, pr.has_errors
               FROM jobs j
               LEFT JOIN pipeline_results pr ON pr.job_id = j.id
               WHERE j.user_id = ?
               ORDER BY j.created_at DESC
               LIMIT ? OFFSET ?""",
            (user_id, limit, offset),
        ).fetchall()

        jobs = []
        for r in rows:
            jobs.append({
                "job_id": r["id"],
                "file_name": r["file_name"],
                "status": r["status"],
                "confidence_level": r["confidence_level"],
                "iterations": r["iteration"],
                "has_errors": bool(r["has_errors"]) if r["has_errors"] is not None else False,
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
                "parent_job_id": r["parent_job_id"],
                "run_version": r["run_version"],
            })

        return {
            "jobs": jobs,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": max(1, math.ceil(total / limit)),
        }
    finally:
        conn.close()


def update_job(
    job_id: str,
    *,
    db_path: Path | str = DB_PATH,
    **fields: Any,
) -> None:
    """Update arbitrary columns on a job row."""
    if not fields:
        return
    fields["updated_at"] = _now_iso()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [job_id]
    conn = _get_connection(db_path)
    try:
        conn.execute(f"UPDATE jobs SET {set_clause} WHERE id = ?", values)
        conn.commit()
    finally:
        conn.close()


def get_job_history(
    job_id: str,
    user_id: str,
    *,
    db_path: Path | str = DB_PATH,
) -> list[dict[str, Any]]:
    """Return all jobs in a given lineage, ordered by run_version ASC."""
    conn = _get_connection(db_path)
    try:
        row = conn.execute("SELECT id, parent_job_id FROM jobs WHERE id = ? AND user_id = ?", (job_id, user_id)).fetchone()
        if not row:
            return []
            
        root_id = row["parent_job_id"] or row["id"]
        
        rows = conn.execute(
            """SELECT j.id as job_id, j.file_name, j.status, j.iteration, j.created_at, j.updated_at,
                      j.parent_job_id, j.run_version,
                      pr.confidence_level, pr.has_errors
               FROM jobs j
               LEFT JOIN pipeline_results pr ON pr.job_id = j.id
               WHERE (j.id = ? OR j.parent_job_id = ?) AND j.user_id = ?
               ORDER BY j.run_version ASC""",
            (root_id, root_id, user_id)
        ).fetchall()
        
        jobs = []
        for r in rows:
            jobs.append({
                "job_id": r["job_id"],
                "file_name": r["file_name"],
                "status": r["status"],
                "confidence_level": r["confidence_level"],
                "iterations": r["iteration"],
                "has_errors": bool(r["has_errors"]) if r["has_errors"] is not None else False,
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
                "parent_job_id": r["parent_job_id"],
                "run_version": r["run_version"],
            })
        return jobs
    finally:
        conn.close()

# ---------------------------------------------------------------------------
# Pipeline results
# ---------------------------------------------------------------------------


def save_pipeline_result(
    job_id: str,
    result_dict: dict[str, Any],
    *,
    db_path: Path | str = DB_PATH,
) -> None:
    """Persist a PipelineResult (as a dict) and denormalized errors."""
    result_json = json.dumps(result_dict, default=str)

    # Extract denormalized fields
    confidence_level = None
    final_conf = result_dict.get("final_confidence")
    if final_conf and isinstance(final_conf, dict):
        confidence_level = final_conf.get("level")

    iterations = result_dict.get("iterations", 0)
    errors = result_dict.get("errors", [])
    has_errors = 1 if errors else 0

    conn = _get_connection(db_path)
    try:
        conn.execute(
            """INSERT OR REPLACE INTO pipeline_results
               (job_id, result_json, confidence_level, iterations, has_errors)
               VALUES (?, ?, ?, ?, ?)""",
            (job_id, result_json, confidence_level, iterations, has_errors),
        )

        # Denormalize errors for queryability
        conn.execute("DELETE FROM pipeline_errors WHERE job_id = ?", (job_id,))
        for err in errors:
            conn.execute(
                """INSERT INTO pipeline_errors
                   (job_id, stage, error_type, message, recoverable, iteration)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    job_id,
                    err.get("stage", ""),
                    err.get("error_type", ""),
                    err.get("message", ""),
                    1 if err.get("recoverable") else 0,
                    err.get("iteration"),
                ),
            )

        conn.commit()
    finally:
        conn.close()


def get_pipeline_result(
    job_id: str,
    *,
    db_path: Path | str = DB_PATH,
) -> dict[str, Any] | None:
    """Fetch the full PipelineResult dict for a job, or None."""
    conn = _get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT result_json FROM pipeline_results WHERE job_id = ?",
            (job_id,),
        ).fetchone()
        if row:
            return json.loads(row["result_json"])
        return None
    finally:
        conn.close()
