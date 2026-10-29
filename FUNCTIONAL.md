# Agentic RFP Evaluation & Supplier Ranking

## Functional Specification (High-Level Design)

---

## 1. Purpose

Build an AI-assisted application that reads supplier RFP (Request for
Proposal) responses as PDF documents, scores them against configurable
criteria, benchmarks each supplier against its peers, and produces an
explainable final leaderboard.

The system combines:

- **Document reading** (PDF text extraction)
- **LLM reasoning** (criterion-wise scoring with evidence)
- **Deterministic business rules** (validation, scoring, ranking)
- **Database persistence** (SQLite)
- **An interactive UI** (Streamlit)

---

## 2. Business Problem

A procurement team receives several supplier RFP responses as PDF
documents. Reading every proposal manually and comparing them consistently
is slow, subjective, and hard to audit.

The system solves this by:

- Using **AI** to examine each proposal independently.
- Using **Python** to apply transparent scoring, peer comparison,
  tie-break rules, and final ranking.

The result is a repeatable, explainable, and auditable evaluation process.

---

## 3. Actors / Stakeholders

| Actor | Role |
|---|---|
| Procurement user | Uploads proposals, enters metadata, triggers evaluation, reviews results |
| Instructor / administrator | Defines/activates criteria and weights in the database |
| Supplier (indirect) | Provides the RFP PDF response that is evaluated |
| System | Orchestrates extraction, LLM scoring, validation, scoring, and ranking |

---

## 4. Scope

### 4.1 In Scope

- Loading active evaluation criteria and weights from SQLite.
- Uploading multiple supplier RFP PDFs with metadata.
- Creating a batch/run and evaluating every supplier.
- Extracting PDF text and asking an LLM for criterion-wise scores in JSON.
- Validating and normalizing missing, malformed, or out-of-range results.
- Calculating weighted scores, benchmarks, gaps, relative percentages, PPI.
- Ranking suppliers with a deterministic tie-break order.
- Persisting the complete result to SQLite.
- Displaying a leaderboard and detailed scorecards.
- Downloading the complete result as JSON.
- Optionally exposing a locally running Streamlit app through a public ngrok URL.

### 4.2 Out of Scope

- Real-time document editing or collaborative review.
- Storing/processing real confidential supplier data (synthetic data only).
- Automated negotiation or contract generation.
- Multi-user authentication / role-based access control.
- Non-PDF document formats (unless added later).

---

## 5. Functional Requirements

### FR1 — Criteria Management

- Load active evaluation criteria and weights from SQLite.
- Display active criteria, weights, and maximum scores in Streamlit.
- Weights of all active criteria must total 100%.
- Criteria can be activated, deactivated, or re-weighted **without**
  changing the prompt code.

### FR2 — Supplier Input

- Allow the user to upload multiple supplier RFP PDFs.
- Allow the user to enter, per supplier:
  - Supplier name
  - Submission date
  - Historical experience rating
- Show validation messages for missing/invalid input.

### FR3 — Batch Creation

- Create supplier entries.
- Generate a batch/run identifier (`RFP_RUN_ID`).

### FR4 — Evaluation

- Reload the latest active criteria.
- Extract text from each uploaded PDF.
- Build the LLM prompt dynamically from the active criteria.
- Ask the LLM to return, in valid JSON:
  - A criterion-wise score
  - A justification
  - Supporting evidence
- The LLM must evaluate **every active criterion**.

### FR5 — Validation & Normalization

- Parse the LLM JSON.
- Check the schema.
- Fill missing criterion results.
- Clip invalid (out-of-range) scores.
- Record warnings for every normalization action.

### FR6 — Scoring

- Calculate the absolute weighted score for every supplier.

### FR7 — Benchmarking

- Find the best (highest valid) score per criterion across all suppliers.
- Calculate peer metrics (gap, relative performance).

### FR8 — Ranking

- Calculate the Peer Performance Index (PPI).
- Apply the mandatory deterministic tie-break order.
- Assign sequential ranks (1, 2, 3, …).

### FR9 — Persistence

- Write the complete result to SQLite using one `RFP_RUN_ID`.

### FR10 — Presentation

- Show a leaderboard.
- Show detailed per-criterion scorecards with evidence.
- Show comparisons and tie-break explanation.
- Allow the complete result to be downloaded as JSON.

---

## 6. Agentic Design Overview

The workflow is decomposed into components with clear responsibilities.
The LLM is allowed to **judge proposal content**, but it must **not**
decide final arithmetic, benchmarks, tie-breaks, or ranks.

| Component | Responsibility | Suggested tools |
|---|---|---|
| Orchestrator Agent | Controls the workflow and calls tools in order | Python functions |
| Document Tool | Extracts clean text from each uploaded PDF | PyMuPDF / pypdf |
| Evaluation Agent | Scores one supplier using active criteria, cites evidence | LLM with structured JSON output |
| Validation Tool | Checks schema, fills missing criteria, clips scores, records warnings | Pydantic / custom Python |
| Ranking Tool | Performs formulas, peer comparison, tie-breaks, final ranking | Deterministic Python only |

---

## 7. User Workflow / Screens

| Screen / section | What it must show |
|---|---|
| Criteria | Active criteria, weights, and maximum score |
| Supplier input | Multiple PDF upload, supplier metadata, validation messages, Evaluate button |
| Leaderboard | Rank, supplier, absolute score, PPI, submission date, experience rating |
| Detailed scorecard | Criterion score, benchmark, gap, relative %, weight, evidence, justification |
| Run details | RFP_RUN_ID, warnings, tie-break explanation, JSON download |

### 7.1 Primary User Flow

1. Open the app; the active criteria load from SQLite.
2. Upload supplier PDFs and enter metadata.
3. Click **Evaluate**.
4. The system extracts, scores, validates, benchmarks, and ranks.
5. Review the leaderboard and drill into scorecards.
6. Download the full JSON result.
7. Optionally start the ngrok tunnel in a second terminal to share the local app.

---

## 8. High-Level Data Flow

```
Load criteria → Upload PDFs + metadata → Create batch (RFP_RUN_ID)
→ For each supplier: Extract text → LLM scores (JSON) → Validate
→ Score (absolute) → Benchmark → Rank (PPI + tie-breaks)
→ Persist → Display
```

---

## 9. Success Criteria / Acceptance Criteria

- The same inputs always produce the same formulas and ordering once the
  LLM scorecards have been validated.
- Every final score is traceable to:
  - A criterion
  - Its weight
  - Supplier evidence
  - A business rule
- The app deploys and runs publicly on Streamlit Community Cloud.
- A complete run can be exported as JSON and matches the SQLite record.

---

## 10. Assumptions & Constraints

- Proposals are short (2–4 pages), so full-document grounding is used
  instead of retrieval (RAG is not required).
- Supplier data is synthetic/fictional; no real confidential data is used.
- A JSON-capable LLM is available (default: OpenAI via an API key).
- Weights of active criteria total 100%.
- All ranking logic is deterministic and independent of the LLM.

---

## 11. Deliverables

- Complete source code with a clear folder structure and `requirements.txt`.
- SQLite database creation/seed script with sample evaluation criteria.
- At least four artificial supplier RFP PDFs.
- Deployed public application on Streamlit Community Cloud.
- README with setup steps, architecture, formulas, assumptions, screenshots.
- Sample exported JSON for one completed RFP run.
- A short demonstration of one successful run and one validation/error case.
