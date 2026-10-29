# -*- coding: utf-8 -*-
"""
validation.py - Pydantic schema for the LLM scorecard response.

What it is for:
    Define the expected shape of the LLM's structured JSON output, then
    validate and normalize the LLM result before scoring (FR5).

What it does:
    ✅ Declares the criterion-level and top-level LLM response schema.
    ✅ Fills missing criteria, clips out-of-range scores, coerces types,
       and records a warning for every normalization action.
"""

import json

from pydantic import BaseModel


class CriterionResult(BaseModel):
    criterion_id: int
    score: float
    max_score: int
    justification: str
    evidence: str


class LLMResponse(BaseModel):
    supplier_name: str
    criteria: list[CriterionResult]
    risks: list[str] = []
    overall_summary: str = ""


def _coerce_score(value, criterion_id, warnings):
    """Coerce a score to float, recording a warning on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        warnings.append(f"Criterion {criterion_id} has an invalid score; set to 0.")
        return 0.0


def validate_and_normalize(raw_json, criteria):
    """Validate an LLM scorecard and return (normalized, warnings).

    The normalized scorecard always contains exactly one entry per active
    criterion, in active-criterion order. Missing results are filled with a
    zero score, and out-of-range scores are clipped to [0, max_score]. Every
    normalization action produces a human-readable warning.
    """
    warnings = []

    if isinstance(raw_json, str):
        try:
            raw_json = json.loads(raw_json)
        except Exception:
            warnings.append("Malformed JSON response; treating all criteria as missing.")
            raw_json = {}
    if not isinstance(raw_json, dict):
        warnings.append("Invalid LLM response type; treating all criteria as missing.")
        raw_json = {}

    raw_criteria = raw_json.get("criteria") or []
    if not isinstance(raw_criteria, list):
        warnings.append(
            "LLM 'criteria' field is missing or not a list; treating all criteria as missing."
        )
        raw_criteria = []

    by_id = {}
    for item in raw_criteria:
        if isinstance(item, dict) and "criterion_id" in item:
            by_id[item["criterion_id"]] = item

    normalized_criteria = []
    for criterion in criteria:
        cid = criterion["criterion_id"]
        max_score = criterion["max_score"]
        item = by_id.get(cid)

        if item is None:
            warnings.append(f"Criterion {cid} ({criterion['name']}) missing; score set to 0.")
            normalized_criteria.append(
                {
                    "criterion_id": cid,
                    "score": 0.0,
                    "max_score": max_score,
                    "justification": "",
                    "evidence": "",
                }
            )
            continue

        score = _coerce_score(item.get("score"), cid, warnings)
        clipped = max(0.0, min(score, max_score))
        if clipped != score:
            warnings.append(
                f"Criterion {cid} ({criterion['name']}) score {score} clipped to {clipped}."
            )

        normalized_criteria.append(
            {
                "criterion_id": cid,
                "score": clipped,
                "max_score": max_score,
                "justification": str(item.get("justification", "")),
                "evidence": str(item.get("evidence", "")),
            }
        )

    risks = raw_json.get("risks")
    if not isinstance(risks, list):
        risks = []

    return {
        "supplier_name": str(raw_json.get("supplier_name", "")),
        "criteria": normalized_criteria,
        "risks": risks,
        "overall_summary": str(raw_json.get("overall_summary", "")),
    }, warnings
