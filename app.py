# -*- coding: utf-8 -*-
"""
app.py - Streamlit UI and orchestration for the RFP Evaluation project.

What it is for:
    Provide the interactive interface and drive the end-to-end workflow.
    This slice implements FR1 (Criteria Management), FR2 (Supplier Input),
    FR3 (Batch Creation), FR4 (Evaluation), FR5 (Validation &
    Normalization), FR6 (Scoring), FR7 (Benchmarking), FR8 (Ranking),
    FR9 (Persistence), and FR10 (Presentation): manage criteria, upload
    supplier PDFs, create a batch, evaluate with the LLM, normalize, score,
    benchmark, rank, persist, and present the results.

What it does:
    ✅ Seeds the database on first run (idempotent).
    ✅ Loads and displays active criteria with weights and max scores.
    ✅ Validates that active weights total 100%.
    ✅ Provides a sidebar form to activate/deactivate and re-weight criteria.
    ✅ Uploads multiple supplier RFP PDFs and collects metadata.
    ✅ Validates supplier input and stores it in session state.
    ✅ Creates a batch/run with a generated RFP_RUN_ID.
    ✅ Evaluates each supplier: extracts PDF text and calls the LLM.
    ✅ Validates and normalizes each LLM scorecard and records warnings.
    ✅ Calculates the absolute weighted score for every supplier.
    ✅ Computes per-criterion benchmarks, gaps, and relative percentages.
    ✅ Computes PPI and assigns final ranks via the tie-break order.
    ✅ Persists the complete run to SQLite under one RFP_RUN_ID.
    ✅ Shows a leaderboard, scorecards, run details, and JSON download.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

import db
import documents
import evaluation_agent
import ranking
import scoring
import validation
from logger import get_logger
from seed_db import seed

logger = get_logger("rfp.app")

# Weights are stored as fractions (e.g. 0.30). Anything within this tolerance
# of 100% is treated as valid to avoid floating-point false negatives.
WEIGHT_TOLERANCE = 1e-6


def active_weight_total(criteria):
    """Return the summed weight of the given (already active) criteria."""
    return sum(float(c["weight"]) for c in criteria)


def format_weight_pct(weight):
    """Format a fraction weight as a human-friendly percentage."""
    return round(float(weight) * 100, 1)


def validate_suppliers(suppliers):
    """Check supplier metadata and return (valid_suppliers, errors)."""
    errors = []
    valid = []
    for i, supplier in enumerate(suppliers, start=1):
        if not supplier["name"]:
            errors.append(f"Supplier {i}: supplier name is required.")
            continue
        valid.append(supplier)
    return valid, errors


def generate_run_id():
    """Generate a unique batch/run identifier."""
    return uuid.uuid4().hex


def main():
    # Idempotent: creates tables and seeds the default criteria if empty.
    seed()
    logger.info("App started; database seeded (idempotent).")

    st.title("Agentic RFP Evaluation & Supplier Ranking")

    # --- Criteria management (writes happen before the display reads) ---
    all_criteria = db.load_all_criteria()
    logger.info("Loaded %d criteria for management.", len(all_criteria))
    with st.sidebar:
        st.header("Manage Criteria")
        with st.form("criteria_form"):
            for c in all_criteria:
                cid = c["criterion_id"]
                st.checkbox(
                    c["name"],
                    value=bool(c["is_active"]),
                    key=f"active_{cid}",
                )
                st.number_input(
                    f"Weight (%) — {c['name']}",
                    min_value=0.0,
                    max_value=100.0,
                    value=format_weight_pct(c["weight"]),
                    step=1.0,
                    key=f"weight_{cid}",
                )
            submitted = st.form_submit_button("Save criteria changes")

        if submitted:
            changed = False
            for c in all_criteria:
                cid = c["criterion_id"]
                want_active = bool(st.session_state[f"active_{cid}"])
                want_weight = float(st.session_state[f"weight_{cid}"]) / 100.0
                if want_active != bool(c["is_active"]):
                    db.set_criterion_active(cid, want_active)
                    changed = True
                if abs(want_weight - float(c["weight"])) > WEIGHT_TOLERANCE:
                    db.set_criterion_weight(cid, want_weight)
                    changed = True
            if changed:
                logger.info("Criteria management changes saved.")
                st.sidebar.success("Criteria updated.")
            else:
                logger.info("Criteria management: no changes to save.")
                st.sidebar.info("No changes to save.")

    # --- Criteria display ---
    st.header("Criteria")
    active_criteria = db.load_active_criteria()
    logger.info("Loaded %d active criteria.", len(active_criteria))

    if not active_criteria:
        logger.warning("No active criteria found; aborting.")
        st.warning("No active criteria found. Activate at least one in the sidebar.")
        return

    total = active_weight_total(active_criteria)
    logger.info("Active criteria weight total: %.1f%%.", format_weight_pct(total))
    if abs(total - 1.0) < WEIGHT_TOLERANCE:
        st.success(f"Active weights total {format_weight_pct(total)}%.")
    else:
        st.error(
            f"Active weights total {format_weight_pct(total)}% — "
            "they must total 100% before evaluation."
        )

    st.dataframe(
        [
            {
                "Criterion": c["name"],
                "Weight (%)": format_weight_pct(c["weight"]),
                "Max Score": c["max_score"],
                "Description": c["description"],
            }
            for c in active_criteria
        ]
    )

    # --- Supplier input ---
    st.header("Supplier input")
    uploaded_files = st.file_uploader(
        "Upload supplier RFP PDFs",
        type="pdf",
        accept_multiple_files=True,
    ) or []

    suppliers = []
    for i, uploaded in enumerate(uploaded_files):
        st.subheader(f"Supplier {i + 1}")
        col_name, col_date, col_rating = st.columns(3)
        default_name = Path(uploaded.name).stem
        name = col_name.text_input(
            "Supplier name",
            value=default_name,
            key=f"supplier_name_{i}",
        )
        submission_date = col_date.date_input(
            "Submission date",
            key=f"supplier_date_{i}",
        )
        experience_rating = col_rating.number_input(
            "Experience rating (0–10)",
            min_value=0.0,
            max_value=10.0,
            value=5.0,
            step=0.5,
            key=f"supplier_rating_{i}",
        )
        suppliers.append(
            {
                "name": name.strip(),
                "submission_date": submission_date.isoformat(),
                "experience_rating": experience_rating,
                "pdf_bytes": uploaded.getvalue(),
            }
        )

    valid_suppliers, errors = validate_suppliers(suppliers)
    st.session_state["suppliers"] = valid_suppliers
    logger.info("Supplier input: %d uploaded, %d valid.", len(uploaded_files), len(valid_suppliers))

    if not uploaded_files:
        st.info("Upload at least one supplier RFP PDF to begin.")
    for error in errors:
        st.error(error)
    if valid_suppliers and not errors:
        st.success(f"{len(valid_suppliers)} supplier(s) ready for evaluation.")

    weights_valid = abs(active_weight_total(active_criteria) - 1.0) < WEIGHT_TOLERANCE
    if st.button(
        "Evaluate",
        type="primary",
        disabled=not valid_suppliers or bool(errors) or not weights_valid,
    ):
        rfp_run_id = generate_run_id()
        created_at = datetime.now(timezone.utc).isoformat()
        db.create_run(rfp_run_id, created_at, status="in_progress")
        logger.info("Created batch RFP_RUN_ID=%s with %d suppliers.", rfp_run_id, len(valid_suppliers))
        st.session_state["rfp_run_id"] = rfp_run_id
        st.session_state["run_suppliers"] = valid_suppliers

        raw_scorecards = []
        for supplier in valid_suppliers:
            try:
                document_text = documents.extract_text(supplier["pdf_bytes"])
            except Exception:
                logger.exception("Failed to extract text for supplier %s.", supplier["name"])
                st.warning(f"Could not read PDF for {supplier['name']}; skipping.")
                continue
            try:
                scorecard = evaluation_agent.evaluate_supplier(active_criteria, document_text)
            except Exception as exc:
                logger.exception("LLM evaluation failed for supplier %s.", supplier["name"])
                st.error(f"Evaluation failed for {supplier['name']}: {exc}")
                continue
            logger.info("Evaluated supplier %s successfully.", supplier["name"])
            raw_scorecards.append(
                {
                    "name": supplier["name"],
                    "submission_date": supplier["submission_date"],
                    "experience_rating": supplier["experience_rating"],
                    "scorecard": scorecard,
                }
            )
        st.session_state["raw_scorecards"] = raw_scorecards

        validated_scorecards = []
        all_warnings = []
        for entry in raw_scorecards:
            normalized, warnings = validation.validate_and_normalize(
                entry["scorecard"], active_criteria
            )
            validated_scorecards.append(
                {
                    "name": entry["name"],
                    "submission_date": entry["submission_date"],
                    "experience_rating": entry["experience_rating"],
                    "scorecard": normalized,
                }
            )
            all_warnings.extend([f"{entry['name']}: {w}" for w in warnings])

        st.session_state["validated_scorecards"] = validated_scorecards
        st.session_state["warnings"] = all_warnings
        logger.info("Validation/normalization produced %d warning(s).", len(all_warnings))

        for entry in validated_scorecards:
            entry["absolute_score"] = scoring.absolute_score(
                entry["scorecard"]["criteria"], active_criteria
            )
            logger.info("Supplier %s absolute_score=%.4f.", entry["name"], entry["absolute_score"])

        suppliers_criteria = [
            entry["scorecard"]["criteria"] for entry in validated_scorecards
        ]
        benchmarks = scoring.benchmark(suppliers_criteria)
        logger.info("Benchmarks computed: %s", benchmarks)
        weights = {c["criterion_id"]: c["weight"] for c in active_criteria}
        for entry in validated_scorecards:
            for result in entry["scorecard"]["criteria"]:
                cid = result["criterion_id"]
                b = benchmarks.get(cid, 0.0)
                result["benchmark"] = b
                result["gap"] = scoring.gap(result["score"], b)
                result["relative_percent"] = scoring.relative_percent(result["score"], b)
            entry["ppi"] = scoring.ppi(
                {r["criterion_id"]: r["relative_percent"] for r in entry["scorecard"]["criteria"]},
                weights,
            )

        ranked_suppliers = ranking.rank_suppliers(validated_scorecards)
        logger.info("Ranked suppliers: %s", [(s["name"], s["final_rank"]) for s in ranked_suppliers])

        st.session_state["benchmarks"] = benchmarks
        st.session_state["scored_suppliers"] = validated_scorecards
        st.session_state["ranked_suppliers"] = ranked_suppliers

        for entry in ranked_suppliers:
            result_json = {
                "name": entry["name"],
                "submission_date": entry["submission_date"],
                "experience_rating": entry["experience_rating"],
                "absolute_score": entry["absolute_score"],
                "ppi": entry["ppi"],
                "final_rank": entry["final_rank"],
                "scorecard": entry["scorecard"],
            }
            db.save_supplier_result(
                rfp_run_id,
                entry["name"],
                entry["submission_date"],
                entry["experience_rating"],
                entry["absolute_score"],
                entry["ppi"],
                entry["final_rank"],
                result_json,
            )
        db.update_run_status(rfp_run_id, "completed")
        logger.info("Persisted %d supplier results for run %s; status completed.", len(ranked_suppliers), rfp_run_id)
        st.session_state["run_status"] = "completed"
        st.session_state["loaded_run"] = db.load_run(rfp_run_id)

        st.success(
            f"Run completed (RFP_RUN_ID: {rfp_run_id}) — "
            f"evaluated, validated, scored, benchmarked, ranked, and persisted {len(validated_scorecards)}/{len(valid_suppliers)} supplier(s)."
        )

    # --- Presentation (FR10) ---
    ranked = st.session_state.get("ranked_suppliers")
    if ranked:
        logger.info("Rendering leaderboard and scorecards for %d suppliers.", len(ranked))
        criterion_names = {c["criterion_id"]: c["name"] for c in active_criteria}
        weights = {c["criterion_id"]: c["weight"] for c in active_criteria}

        st.header("Leaderboard")
        st.dataframe(
            [
                {
                    "Rank": s["final_rank"],
                    "Supplier": s["name"],
                    "Absolute Score": round(float(s["absolute_score"]), 4),
                    "PPI": round(float(s["ppi"]), 2),
                    "Submission Date": s["submission_date"],
                    "Experience": s["experience_rating"],
                }
                for s in ranked
            ]
        )

        st.header("Detailed Scorecards")
        for s in ranked:
            with st.expander(f"{s['final_rank']}. {s['name']}"):
                st.dataframe(
                    [
                        {
                            "Criterion": criterion_names.get(r["criterion_id"], r["criterion_id"]),
                            "Score": r["score"],
                            "Max": r["max_score"],
                            "Weight (%)": format_weight_pct(weights.get(r["criterion_id"], 0.0)),
                            "Benchmark": r["benchmark"],
                            "Gap": r["gap"],
                            "Relative %": round(r["relative_percent"], 2),
                            "Justification": r["justification"],
                            "Evidence": r["evidence"],
                        }
                        for r in s["scorecard"]["criteria"]
                    ]
                )
                st.markdown(f"**Summary:** {s['scorecard']['overall_summary']}")
                if s["scorecard"]["risks"]:
                    st.markdown("**Risks:** " + "; ".join(s["scorecard"]["risks"]))

        st.header("Run details")
        run_id = st.session_state.get("rfp_run_id", "")
        st.write(f"RFP_RUN_ID: {run_id}")
        st.write(ranking.tie_break_explanation())

        warnings = st.session_state.get("warnings") or []
        if warnings:
            for warning in warnings:
                st.warning(warning)
        else:
            st.info("No normalization warnings.")

        download_data = {
            "rfp_run_id": run_id,
            "status": st.session_state.get("run_status", "completed"),
            "criteria": [
                {
                    "criterion_id": c["criterion_id"],
                    "name": c["name"],
                    "weight": c["weight"],
                    "max_score": c["max_score"],
                }
                for c in active_criteria
            ],
            "warnings": warnings,
            "suppliers": [
                {
                    "name": s["name"],
                    "submission_date": s["submission_date"],
                    "experience_rating": s["experience_rating"],
                    "absolute_score": s["absolute_score"],
                    "ppi": s["ppi"],
                    "final_rank": s["final_rank"],
                    "scorecard": s["scorecard"],
                }
                for s in ranked
            ],
        }
        st.download_button(
            "Download JSON",
            data=json.dumps(download_data, indent=2),
            file_name=f"{run_id}.json",
            mime="application/json",
        )


if __name__ == "__main__":
    main()
