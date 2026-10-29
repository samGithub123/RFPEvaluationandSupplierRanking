# -*- coding: utf-8 -*-
"""
db.py - SQLite persistence layer for the RFP Evaluation project.

What it is for:
    Own all database access in one place. The rest of the application
    (scoring, ranking, UI) never writes SQL directly; it calls the helpers
    in this module.

    Tables:
        evaluation_criteria  - active/weighted criteria used for scoring
        rfp_runs             - one row per evaluation batch (RFP_RUN_ID)
        supplier_results     - one row per supplier within a run

What it does:
    ✅ Opens (and creates) the local `rfp.db`.
    ✅ Creates the three tables if they do not exist.
    ✅ Loads active criteria, ordered by criterion_id.
    ✅ Creates a run and stores supplier results under one RFP_RUN_ID.
    ✅ Loads a completed run back for display / JSON download.

Design note (SOLID - Single Responsibility):
    This module only talks to SQLite. Prompt building, LLM calls, scoring,
    and ranking live in their own modules.
"""

import json
import os
import sqlite3

# The database lives next to this module so the app and seed script always
# agree on the same file regardless of the current working directory.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rfp.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS evaluation_criteria (
    criterion_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL,
    description  TEXT    NOT NULL,
    weight       REAL    NOT NULL,
    max_score    INTEGER NOT NULL,
    is_active    INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS rfp_runs (
    rfp_run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    status     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS supplier_results (
    rfp_run_id        TEXT    NOT NULL,
    supplier_name     TEXT    NOT NULL,
    submission_date   TEXT    NOT NULL,
    experience_rating REAL    NOT NULL,
    absolute_score    REAL    NOT NULL,
    ppi               REAL    NOT NULL,
    final_rank        INTEGER NOT NULL,
    result_json       TEXT    NOT NULL,
    PRIMARY KEY (rfp_run_id, supplier_name),
    FOREIGN KEY (rfp_run_id) REFERENCES rfp_runs (rfp_run_id)
);
"""


def get_connection() -> sqlite3.Connection:
    """Open a connection to the local SQLite database.

    sqlite3 connections do not work well across threads by default, so we
    return a fresh connection per call and enable row factory for
    dict-style access. Callers are responsible for closing it (or using it
    as a context manager).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create all tables if they do not already exist."""
    with get_connection() as conn:
        conn.executescript(_SCHEMA)


def load_active_criteria() -> list[dict]:
    """Return every active criterion as a list of dicts.

    Ordering by criterion_id keeps the prompt and scorecards stable across
    runs. Each dict contains criterion_id, name, description, weight and
    max_score.
    """
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT criterion_id, name, description, weight, max_score "
            "FROM evaluation_criteria "
            "WHERE is_active = 1 "
            "ORDER BY criterion_id"
        ).fetchall()
    return [dict(row) for row in rows]


def load_all_criteria() -> list[dict]:
    """Return every criterion (active and inactive) ordered by criterion_id.

    Includes the is_active flag so the criteria-management screen can show
    and edit the current state of each criterion.
    """
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT criterion_id, name, description, weight, max_score, is_active "
            "FROM evaluation_criteria "
            "ORDER BY criterion_id"
        ).fetchall()
    return [dict(row) for row in rows]


def set_criterion_active(criterion_id: int, is_active: bool) -> None:
    """Activate or deactivate a single criterion."""
    init_db()
    with get_connection() as conn:
        conn.execute(
            "UPDATE evaluation_criteria SET is_active = ? WHERE criterion_id = ?",
            (1 if is_active else 0, criterion_id),
        )


def set_criterion_weight(criterion_id: int, weight: float) -> None:
    """Update the weight of a single criterion (stored as a fraction)."""
    init_db()
    with get_connection() as conn:
        conn.execute(
            "UPDATE evaluation_criteria SET weight = ? WHERE criterion_id = ?",
            (weight, criterion_id),
        )


def create_run(rfp_run_id: str, created_at: str, status: str = "in_progress") -> None:
    """Insert a new run row keyed by RFP_RUN_ID."""
    init_db()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO rfp_runs (rfp_run_id, created_at, status) VALUES (?, ?, ?)",
            (rfp_run_id, created_at, status),
        )


def update_run_status(rfp_run_id: str, status: str) -> None:
    """Update the status of an existing run (e.g. to 'completed')."""
    init_db()
    with get_connection() as conn:
        conn.execute(
            "UPDATE rfp_runs SET status = ? WHERE rfp_run_id = ?",
            (status, rfp_run_id),
        )


def save_supplier_result(
    rfp_run_id: str,
    supplier_name: str,
    submission_date: str,
    experience_rating: float,
    absolute_score: float,
    ppi: float,
    final_rank: int,
    result_json: dict,
) -> None:
    """Insert (or replace) one supplier's complete result for a run.

    result_json is stored as a JSON string so the full scorecard can be
    reconstructed later without re-running the LLM.
    """
    init_db()
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO supplier_results "
            "(rfp_run_id, supplier_name, submission_date, experience_rating, "
            " absolute_score, ppi, final_rank, result_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                rfp_run_id,
                supplier_name,
                submission_date,
                experience_rating,
                absolute_score,
                ppi,
                final_rank,
                json.dumps(result_json),
            ),
        )


def load_run(rfp_run_id: str) -> dict:
    """Load a run and all of its supplier results.

    Returns:
        {
            "run": {"rfp_run_id": ..., "created_at": ..., "status": ...},
            "suppliers": [ {..., "result_json": <decoded dict>}, ... ]
        }
    """
    init_db()
    with get_connection() as conn:
        run_row = conn.execute(
            "SELECT rfp_run_id, created_at, status FROM rfp_runs WHERE rfp_run_id = ?",
            (rfp_run_id,),
        ).fetchone()
        rows = conn.execute(
            "SELECT rfp_run_id, supplier_name, submission_date, experience_rating, "
            "       absolute_score, ppi, final_rank, result_json "
            "FROM supplier_results "
            "WHERE rfp_run_id = ?",
            (rfp_run_id,),
        ).fetchall()

    suppliers = []
    for row in rows:
        item = dict(row)
        item["result_json"] = json.loads(item["result_json"])
        suppliers.append(item)

    return {
        "run": dict(run_row) if run_row else None,
        "suppliers": suppliers,
    }
