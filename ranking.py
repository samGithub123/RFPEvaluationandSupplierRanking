# -*- coding: utf-8 -*-
"""
ranking.py - Deterministic ranking for the RFP Evaluation project.

What it is for:
    Apply the mandatory tie-break order and assign final ranks. The LLM never
    decides ranks; this module sorts suppliers with a stable, reproducible
    order in Python.

What it does:
    ✅ Sorts suppliers by PPI, submission date, experience rating, and name.
    ✅ Assigns sequential ranks 1..N after the stable sort.
"""


def rank_suppliers(suppliers):
    """Return suppliers sorted and tagged with final_rank.

    Sort order (all deterministic):
        1. higher PPI
        2. earlier submission date
        3. higher experience rating
        4. supplier name ascending
    """
    ordered = sorted(
        suppliers,
        key=lambda s: (
            -float(s["ppi"]),
            s["submission_date"],
            -float(s["experience_rating"]),
            s["name"],
        ),
    )
    for rank, supplier in enumerate(ordered, start=1):
        supplier["final_rank"] = rank
    return ordered


def tie_break_explanation():
    """Return a human-readable explanation of the tie-break order."""
    return (
        "Sort order: 1) higher PPI, 2) earlier submission date, "
        "3) higher experience rating, 4) supplier name ascending."
    )
