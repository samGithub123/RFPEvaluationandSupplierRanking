# -*- coding: utf-8 -*-
"""
evaluation_agent.py - LLM evaluation agent for the RFP Evaluation project.

What it is for:
    Score one supplier document against the active criteria using an LLM with
    structured JSON output. The LLM may judge proposal content, but it never
    decides arithmetic, benchmarks, tie-breaks, or ranks.

What it does:
    ✅ Builds a dynamic prompt from the active criteria.
    ✅ Calls an OpenAI model via langchain-openai with structured output.
    ✅ Returns the scorecard as a plain dict for downstream validation.
"""

import keys
from validation import LLMResponse

from langchain_openai import ChatOpenAI

MODEL_NAME = "gpt-4o-mini"


def _get_llm():
    """Build a ChatOpenAI client, failing clearly if no API key is set."""
    api_key = keys.require("OPENAI_API_KEY", keys.OPENAI_API_KEY)
    return ChatOpenAI(model=MODEL_NAME, temperature=0, api_key=api_key)


def build_prompt(criteria, document_text):
    """Build the evaluation prompt from active criteria and document text."""
    lines = [
        "You are evaluating a supplier RFP response.",
        "Evaluate the supplier against EVERY criterion below, using only "
        "evidence present in the document.",
        "",
    ]
    for c in criteria:
        lines.append(
            f"- criterion_id={c['criterion_id']} | {c['name']} "
            f"(max {c['max_score']}): {c['description']}"
        )
    lines.extend(
        [
            "",
            "Return valid JSON only, with this shape:",
            '{"supplier_name": "...", "criteria": [{"criterion_id": 1, '
            '"score": 8, "max_score": 10, "justification": "...", '
            '"evidence": "..."}], "risks": ["..."], "overall_summary": "..."}',
            "Every criterion must appear once and score must stay within "
            "[0, max_score].",
            "",
            "DOCUMENT:",
            document_text,
        ]
    )
    return "\n".join(lines)


def evaluate_supplier(criteria, document_text):
    """Return the LLM scorecard for one supplier as a plain dict."""
    llm = _get_llm().with_structured_output(LLMResponse)
    result = llm.invoke(build_prompt(criteria, document_text))
    return result.model_dump()
