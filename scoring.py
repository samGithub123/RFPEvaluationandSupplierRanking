# -*- coding: utf-8 -*-
"""
scoring.py - Deterministic scoring formulas for the RFP Evaluation project.

What it is for:
    Turn validated criterion scores into a single absolute weighted score per
    supplier. The LLM never does this arithmetic; it is computed in Python so
    results stay transparent and reproducible.

What it does:
    ✅ Calculates the absolute weighted score for one supplier.
    ✅ Computes per-criterion benchmarks, gaps, and relative percentages.
    ✅ Calculates the Peer Performance Index (PPI).
"""


def absolute_score(criteria_results, criteria):
    """Return the absolute weighted score for one supplier.

    Formula: sum over active criteria of (score / max_score) * weight.
    """
    weights = {c["criterion_id"]: c["weight"] for c in criteria}
    total = 0.0
    for result in criteria_results:
        cid = result["criterion_id"]
        weight = weights.get(cid, 0.0)
        max_score = result.get("max_score", 0)
        if max_score == 0:
            continue
        total += (float(result["score"]) / max_score) * weight
    return total


def benchmark(suppliers_criteria):
    """Return {criterion_id: best_score} across all suppliers."""
    best = {}
    for criteria_results in suppliers_criteria:
        for result in criteria_results:
            cid = result["criterion_id"]
            score = float(result["score"])
            if cid not in best or score > best[cid]:
                best[cid] = score
    return best


def gap(supplier_score, benchmark_score):
    """Return supplier score minus the peer benchmark."""
    return supplier_score - benchmark_score


def relative_percent(supplier_score, benchmark_score):
    """Return supplier score as a percentage of the peer benchmark."""
    if benchmark_score == 0:
        return 0.0
    return (supplier_score / benchmark_score) * 100


def ppi(relative_percents, weights):
    """Return the Peer Performance Index as a weighted average of relative %.

    relative_percents and weights are both {criterion_id: value} mappings.
    """
    total = 0.0
    for cid, rel in relative_percents.items():
        total += rel * weights.get(cid, 0.0)
    return total
