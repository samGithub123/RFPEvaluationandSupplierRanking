# Agentic RFP Evaluation & Supplier Ranking

## Technical Specification (Low-Level Design)

---

## 1. Overview

This document specifies the technical design for the RFP Evaluation and
Supplier Ranking mini project. The system is a Streamlit application backed
by SQLite and an LLM, following an agentic workflow split into clear,
deterministic components.

---

## 2. Technology Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| Database | SQLite (`sqlite3` standard library) |
| AI layer | Any JSON-capable LLM (default: OpenAI via `langchain-openai`) |
| PDF extraction | `pypdf` |
| Validation | `pydantic` (plus custom normalization) |
| Optional local public tunnel | `pyngrok` |
| Language | Python 3.x |

---

## 3. System Architecture

```
                    ┌─────────────────────────────┐
                    │        Streamlit UI         │
                    │   (app.py — orchestrator)   │
                    └───────┬──────────┬──────────┘
                            │          │
              ┌─────────────▼──┐   ┌───▼──────────────┐
              │   Document     │   │  Evaluation      │
              │   Tool         │   │  Agent (LLM)     │
              │  documents.py  │   │  evaluation_agent│
              └───────┬────────┘   └───┬──────────────┘
                      │                 │
                      │  Validation     │
                      │  Tool           │
                      │  validation.py  │
                      └───────┬─────────┘
                              │
              ┌───────────────▼──────────────┐
              │  Scoring + Benchmark + Rank  │
              │  scoring.py / ranking.py     │
              └───────────────┬──────────────┘
                              │
              ┌───────────────▼──────────────┐
              │   SQLite (db.py)             │
              └──────────────────────────────┘
```

For optional public access to a local run, `tunnel.py` connects ngrok to the
Streamlit server on port 8501. The tunnel runs independently from the app.

### 3.1 Component Responsibilities

| Component | Module | Responsibility |
|---|---|---|
| Orchestrator | `app.py` | Controls workflow order, drives UI |
| Document Tool | `documents.py` | Extracts clean text from PDFs |
| Evaluation Agent | `evaluation_agent.py` | Builds prompt, calls LLM, returns JSON |
| Validation Tool | `validation.py` | Schema check + normalization + warnings |
| Scoring/Ranking Tool | `scoring.py`, `ranking.py` | Deterministic formulas and ordering |
| Persistence | `db.py` | SQLite schema, seed, load, save |

---

## 4. Folder Structure

```
RFPEvaluationandSupplierRanking/
├── app.py                 # Streamlit UI + orchestration
├── db.py                  # SQLite schema, seed, load/save helpers
├── documents.py           # PDF text extraction
├── evaluation_agent.py    # Prompt builder + LLM structured call
├── validation.py          # Pydantic schema + normalization
├── scoring.py             # Absolute score, benchmark, gap, relative %, PPI
├── ranking.py             # Tie-break sort + rank assignment
├── keys.py                # API key loading from .env
├── tunnel.py              # Optional ngrok tunnel for the local Streamlit app
├── logger.py              # Central logging config (file + console)
├── seed_db.py             # Create schema + seed criteria
├── requirements.txt
├── README.md
├── FUNCTIONAL.md
├── TECHNICAL.md
├── data/                  # Synthetic supplier PDFs
│   ├── Apex_Systems.pdf
│   ├── BrightPath_Tech.pdf
│   ├── NexaWorks.pdf
│   └── Orbit_Digital.pdf
├── rfp.db                 # Generated SQLite (gitignored)
├── sample_output/
│   └── sample_run.json
├── .env.example
└── .gitignore
```

---

## 5. Database Design (SQLite)

### 5.1 Tables

**`evaluation_criteria`**

| Field | Type | Notes |
|---|---|---|
| criterion_id | INTEGER PK | |
| name | TEXT | e.g. "Technical Capability" |
| description | TEXT | what the LLM should inspect |
| weight | REAL | e.g. 0.30 (as a fraction) |
| max_score | INTEGER | e.g. 10 |
| is_active | INTEGER | 0/1 flag |

**`rfp_runs`**

| Field | Type | Notes |
|---|---|---|
| rfp_run_id | TEXT PK | UUID / timestamp-based |
| created_at | TEXT | ISO timestamp |
| status | TEXT | e.g. "completed" |

**`supplier_results`**

| Field | Type | Notes |
|---|---|---|
| rfp_run_id | TEXT FK | links to `rfp_runs` |
| supplier_name | TEXT | |
| submission_date | TEXT | |
| experience_rating | REAL | historical rating |
| absolute_score | REAL | weighted score |
| ppi | REAL | peer performance index |
| final_rank | INTEGER | 1..N |
| result_json | TEXT | full serialized scorecard |

### 5.2 Seed Criteria (default)

| Name | Weight | Max score | Inspect |
|---|---|---|---|
| Technical Capability | 30% | 10 | Architecture, integrations, scalability, fit |
| Implementation Plan | 20% | 10 | Timeline, milestones, staffing, risk plan |
| Commercial Value | 20% | 10 | Pricing clarity, total cost, assumptions |
| Security & Compliance | 20% | 10 | Controls, certifications, privacy, auditability |
| Support & Experience | 10% | 10 | Support model, similar projects, references |

---

## 6. Module Design

### 6.1 `db.py`

- Create tables if not present.
- `load_active_criteria()` → list of active criteria dicts.
- `load_all_criteria()` → all criteria dicts (with `is_active`) for the management form.
- `set_criterion_active(criterion_id, is_active)` → activate/deactivate a criterion.
- `set_criterion_weight(criterion_id, weight)` → re-weight a criterion.
- `create_run(rfp_run_id, status)` → new run row.
- `save_supplier_result(...)` → insert one result row.
- `load_run(rfp_run_id)` → retrieve complete run for display.

### 6.2 `documents.py`

- `extract_text(pdf_bytes) -> str`.
- Uses `pypdf.PdfReader` over a byte stream.
- Joins page text, normalizes whitespace.

### 6.3 `evaluation_agent.py`

- `build_prompt(criteria, document_text) -> str`.
- `evaluate_supplier(criteria, document_text) -> dict`.
- Uses a structured-output LLM call (`ChatOpenAI` with `gpt-4o-mini`).
- Prompt instructs: JSON only, one result per active criterion,
  stay within `[0, max_score]`, use only document evidence.

### 6.4 `validation.py`

- Pydantic models for expected JSON (`CriterionResult`, `LLMResponse`).
- `validate_and_normalize(raw_json, criteria) -> (normalized, warnings)`.
- Handles missing criteria, out-of-range clipping, malformed JSON retry.

### 6.5 `scoring.py`

- `absolute_score(criteria_results, criteria) -> float`.
- `benchmark(suppliers_criteria) -> dict`.
- `gap(supplier_score, benchmark_score) -> float`.
- `relative_percent(supplier_score, benchmark_score) -> float`.
- `ppi(relative_percents, weights) -> float`.

### 6.6 `ranking.py`

- `rank_suppliers(suppliers) -> list` with assigned ranks.
- Implements the mandatory stable tie-break sort.
- `tie_break_explanation()` -> str explaining the tie-break order.

### 6.7 `tunnel.py`

- Reads `NGROK_AUTH_TOKEN` from the project `.env` file via `keys.py`.
- Connects an ngrok public URL to the local Streamlit server on port 8501.
- Prints the public URL and keeps the tunnel alive until Enter is pressed.
- Requires `pyngrok` and a configured ngrok auth token; run it in a second
  terminal after starting `streamlit run app.py`.

### 6.8 `app.py`

- Streamlit UI.
- Seeds the database on first run (idempotent).
- Logging: records each pipeline step and exceptions via `logger.py`.
- Criteria screen: displays active criteria and validates that active weights total 100%.
- Criteria management sidebar form: activate/deactivate and re-weight criteria.
- Supplier input: multiple PDF upload with per-supplier name, submission date, and experience rating; validation messages and an Evaluate button.
- Batch creation: on Evaluate, generates an `RFP_RUN_ID` and inserts an `in_progress` run; snapshots suppliers in session state.
- Evaluation: on Evaluate, loops suppliers, extracts PDF text, calls the LLM, and stores raw scorecards in session state.
- Validation: normalizes each raw scorecard (missing/out-of-range/wrong-type) and records warnings.
- Scoring: calculates each supplier's absolute weighted score and stores scored suppliers in session state.
- Benchmarking: computes per-criterion best scores, gaps, and relative percentages across suppliers.
- Ranking: computes PPI and assigns final ranks via the tie-break order.
- Persistence: saves each supplier result under the RFP_RUN_ID and marks the run `completed`.
- Presentation: renders the leaderboard, per-supplier scorecards, run details, and JSON download.
- Session state for supplier uploads and results.
- Renders Criteria, Supplier input, Leaderboard, Scorecards, Run details.
- Provides JSON download.

---

## 7. End-to-End Data Flow

Each step is broken into **input → what it does → output**.

### Step 1 — Load criteria
- **Input:** SQLite database.
- **What it does:** reads active criteria (weight, max_score, description).
- **Output:** ordered list of active criteria.

### Step 2 — Upload PDFs + metadata
- **Input:** user file uploads + form fields.
- **What it does:** validates files and metadata.
- **Output:** list of `{name, date, experience_rating, pdf_bytes}`.

### Step 3 — Create batch
- **Input:** supplier list.
- **What it does:** generates `RFP_RUN_ID`.
- **Output:** new run identifier.

### Step 4 — Extract text
- **Input:** one PDF (bytes).
- **What it does:** extracts and normalizes text.
- **Output:** plain-text proposal string.

### Step 5 — LLM scores (JSON)
- **Input:** document text + active criteria + prompt.
- **What it does:** calls the LLM for structured JSON.
- **Output:** raw scorecard JSON (scores, justifications, evidence).

### Step 6 — Validate
- **Input:** raw LLM JSON + criteria.
- **What it does:** schema check + fill/clip/normalize.
- **Output:** normalized scorecard + warnings.

### Step 7 — Score
- **Input:** validated criterion scores.
- **What it does:** computes absolute weighted score.
- **Output:** one weighted score per supplier.

### Step 8 — Benchmark
- **Input:** all suppliers' validated scores.
- **What it does:** per-criterion best score, gap, relative %, PPI.
- **Output:** benchmark table + PPI per supplier.

### Step 9 — Rank
- **Input:** PPI, date, experience, name.
- **What it does:** stable sort + rank assignment.
- **Output:** final ranks + tie-break explanation.

### Step 10 — Persist
- **Input:** complete run results.
- **What it does:** writes to SQLite under one `RFP_RUN_ID`.
- **Output:** durable run record.

### Step 11 — Display
- **Input:** persisted run data.
- **What it does:** renders leaderboard, scorecards, run details.
- **Output:** interactive UI + JSON download.

---

## 8. LLM Integration

### 8.1 Prompt Requirements

The prompt must instruct the model to:

- Use only evidence present in the supplier document.
- Return one result for **every active criterion**.
- Stay within the score range `[0, max_score]`.
- Output **JSON only** (no prose wrapper).

### 8.2 Expected LLM Output

```json
{
  "supplier_name": "Apex Systems",
  "criteria": [
    {
      "criterion_id": 1,
      "score": 8,
      "max_score": 10,
      "justification": "...",
      "evidence": "..."
    }
  ],
  "risks": ["..."],
  "overall_summary": "..."
}
```

### 8.3 Structured Output Strategy

- Prefer a structured-output mechanism (e.g. OpenAI JSON mode or
  `with_structured_output`) backed by a Pydantic model.
- On parse failure, retry once; if still invalid, record a warning and
  apply normalization.

---

## 9. Validation & Normalization Rules

- **Missing criterion:** fill score = 0, add warning.
- **Out-of-range score:** clip to `[0, max_score]`, add warning.
- **Malformed JSON:** retry; else mark criterion results invalid and warn.
- **Wrong type / unknown field:** ignore unknown fields; coerce known fields.
- Every normalization produces a human-readable warning stored in the run.

---

## 10. Scoring Formulas

### 10.1 Absolute Weighted Score

```
absolute_score = Σ (criterion_score / max_score) × weight
```

### 10.2 Criterion Benchmark

```
benchmark(c) = max(valid score for criterion c across all suppliers)
```

### 10.3 Criterion Gap

```
gap = supplier_score(c) - benchmark(c)
# zero for the benchmark leader, otherwise negative
```

### 10.4 Relative Performance %

```
relative% = (supplier_score(c) / benchmark(c)) × 100
# if benchmark == 0, define safe handling (e.g. relative% = 0)
```

### 10.5 Peer Performance Index (PPI)

```
PPI = Σ (relative%(c) × weight(c))
```

where `Σ weight(c) = 100%`.

---

## 11. Ranking & Tie-Break Algorithm

Stable sort in this exact priority order:

1. Higher PPI first
2. Earlier submission date
3. Higher historical experience rating
4. Supplier name in ascending order

Assign ranks `1, 2, 3, …` only **after** this stable sort.

The app must produce and display a tie-break explanation showing which
rules were applied.

---

## 12. Persistence Design

- One `RFP_RUN_ID` ties together the run row and all supplier result rows.
- `result_json` stores the full serialized scorecard so it can be
  reconstructed without re-running the LLM.
- Downloadable JSON is generated from `result_json` (or the in-memory run).

---

## 13. Streamlit UI Design

| Section | Data shown |
|---|---|
| Criteria | name, weight, max_score (read from DB); activate/deactivate and re-weight form |
| Supplier input | multiple PDF upload, per-supplier name/date/experience rating, validation messages, Evaluate button |
| Leaderboard | rank, supplier, absolute score, PPI, date, experience |
| Scorecard | score, benchmark, gap, relative %, weight, evidence, justification |
| Run details | RFP_RUN_ID, warnings, tie-break explanation, JSON download |

---

## 14. Error Handling & Edge Cases

- Benchmark = 0 (all zero scores) → safe division handling.
- Empty/missing supplier metadata → validation message before evaluate.
- Unreadable PDF → warning; skip or mark supplier.
- LLM timeout/API error → retry once, then surface error.
- Duplicate supplier names → preserve distinct entries via metadata.

---

## 15. Testing Plan

- **Unit tests** for `scoring.py` and `ranking.py` (deterministic).
- **Validation tests** for missing/out-of-range/malformed JSON.
- **DB tests** for seed, save, and load round-trip.
- **Integration test:** run a full pipeline with a stub LLM response.
- **Manual demo:** one successful run + one validation/error case.

---

## 16. Deployment (Streamlit Community Cloud)

- Provide `requirements.txt` with all dependencies.
- Set the LLM API key as a Streamlit secret / environment variable.
- `app.py` is the entry point.
- Seed criteria on first run or via `seed_db.py`.

### 16.1 Optional local ngrok tunnel

- Install the project dependencies, including `pyngrok` from `requirements.txt`.
- Set `NGROK_AUTH_TOKEN` in the root `.env` file; keep the token out of source
  control.
- Start the app with `streamlit run app.py`, then run `python tunnel.py` in a
  second terminal.
- The tunnel prints a public URL for port 8501. Keep both processes running
  while the URL is in use; press Enter in the tunnel terminal to stop it.

---

## 17. Deliverables Checklist

- [ ] Source code + folder structure + `requirements.txt`
- [ ] SQLite seed script + sample criteria
- [ ] Four synthetic supplier PDFs
- [ ] Public Streamlit Community Cloud URL
- [ ] README (setup, architecture, formulas, assumptions, screenshots)
- [ ] Sample exported JSON for one run
- [ ] Demo (success case + validation/error case)
