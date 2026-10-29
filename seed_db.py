# -*- coding: utf-8 -*-
"""
seed_db.py - Create the SQLite schema and seed sample evaluation criteria.

What it is for:
    Reproducibly initialize the local `rfp.db` with the five default RFP
    evaluation criteria from the mini-project brief. Run this before
    starting the Streamlit app, or run it once as part of setup.

What it does:
    ✅ Creates the three tables (via db.init_db()).
    ✅ Inserts the default criteria only if the table is empty (idempotent).
    ✅ Prints a short confirmation of what was seeded.

Usage:
    python seed_db.py

Requires: none beyond the Python standard library + db.py.
"""

from db import get_connection, init_db

# Default criteria from the mini-project brief. Weights are expressed as
# fractions and total exactly 1.0 (100%).
DEFAULT_CRITERIA = [
    {
        "name": "Technical Capability",
        "description": "Architecture, integrations, scalability, technical fit",
        "weight": 0.30,
        "max_score": 10,
        "is_active": 1,
    },
    {
        "name": "Implementation Plan",
        "description": "Timeline, milestones, staffing, risk plan",
        "weight": 0.20,
        "max_score": 10,
        "is_active": 1,
    },
    {
        "name": "Commercial Value",
        "description": "Pricing clarity, total cost, assumptions",
        "weight": 0.20,
        "max_score": 10,
        "is_active": 1,
    },
    {
        "name": "Security & Compliance",
        "description": "Controls, certifications, privacy, auditability",
        "weight": 0.20,
        "max_score": 10,
        "is_active": 1,
    },
    {
        "name": "Support & Experience",
        "description": "Support model, similar projects, references",
        "weight": 0.10,
        "max_score": 10,
        "is_active": 1,
    },
]


def seed() -> None:
    """Create tables and insert default criteria if none exist yet."""
    init_db()
    with get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM evaluation_criteria"
        ).fetchone()["n"]

        if count > 0:
            print(f"Criteria table already has {count} row(s); skipping seed.")
            return

        conn.executemany(
            "INSERT INTO evaluation_criteria "
            "(name, description, weight, max_score, is_active) "
            "VALUES (:name, :description, :weight, :max_score, :is_active)",
            DEFAULT_CRITERIA,
        )
    print(f"Seeded {len(DEFAULT_CRITERIA)} evaluation criteria.")


if __name__ == "__main__":
    seed()
