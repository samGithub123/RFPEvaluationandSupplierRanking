# RFP Evaluation and Supplier Ranking

## Overview

This project is an AI-assisted application for evaluating supplier RFP responses as PDF documents. It combines document extraction, LLM-based scoring, validation, deterministic business rules, database persistence, and a Streamlit user interface.

The system reads supplier proposals, scores them against configurable criteria, benchmarks each supplier against its peers, and produces an explainable final leaderboard.

## Purpose

The business goal is to reduce manual effort and subjectivity in supplier evaluation. Procurement teams often receive several proposals in PDF form and need a repeatable, defensible process that can compare suppliers consistently.

This application solves that by:

- extracting text from supplier PDFs
- evaluating each response against active criteria
- validating and normalizing LLM output
- calculating weighted absolute scores
- benchmarking scorecards across suppliers
- ranking suppliers using deterministic tie-break rules
- persisting all run data locally for auditability

## Business Problem

A procurement team receives many supplier RFP responses. Reviewing each proposal manually is slow, inconsistent, and difficult to justify later. The system introduces a repeatable workflow using AI for subjective judgment and Python for transparent, deterministic scoring and ranking.

## Actors and Stakeholders

- Procurement user: uploads proposals, enters metadata, triggers evaluation, reviews finalists
- Administrator or instructor: defines active criteria and weights in the database
- Supplier: provides the RFP response being evaluated indirectly through the uploaded PDF
- System: orchestrates extraction, LLM scoring, validation, ranking, and persistence

## Scope

### In scope

- Loading active evaluation criteria and weights from SQLite
- Uploading multiple supplier RFP PDFs with metadata
- Creating a batch or run for each evaluation cycle
- Extracting PDF text and asking an LLM for criterion-wise scoring
- Validating and normalizing malformed or incomplete LLM output
- Calculating weighted scores, benchmarks, gaps, and relative percentages
- Ranking suppliers with a deterministic tie-break order
- Writing results to SQLite
- Rendering a leaderboard and detailed scorecards
- Downloading the complete run as JSON

### Out of scope

- Real-time collaborative editing
- Role-based user authentication
- Non-PDF document formats
- Negotiation or contract generation
- Storing confidential supplier data beyond local demo use

## Functional Requirements

### FR1 — Criteria Management

- Load active evaluation criteria and weights from SQLite.
- Display active criteria, weights, and maximum scores in the UI.
- Ensure all active criteria total 100%.
- Allow activation, deactivation, or re-weighting without changing prompt logic.

### FR2 — Supplier Input

- Allow uploading multiple supplier RFP PDFs.
- Capture supplier metadata for each submission:
  - supplier name
  - submission date
  - historical experience rating
- Show validation messages when required inputs are missing.

### FR3 — Batch Creation

- Create a supplier set and generate a run identifier.
- Track each evaluation cycle as a unique RFP run.

### FR4 — Evaluation

- Load the newest active criteria.
- Extract text from each uploaded PDF.
- Build a prompt dynamically from the active criteria.
- Ask the LLM to return valid JSON containing:
  - criterion-wise scores
  - justification per criterion
  - evidence per criterion
- Ensure every active criterion is evaluated once.

### FR5 — Validation and Normalization

- Parse the LLM JSON response.
- Validate the schema.
- Fill missing criterion results.
- Clip invalid out-of-range scores.
- Record warnings for every normalization action.

### FR6 — Scoring

- Calculate the absolute weighted score for every supplier.

### FR7 — Benchmarking

- Find the best score per criterion across suppliers.
- Compute benchmark gaps and relative percentages.

### FR8 — Ranking

- Calculate the Peer Performance Index (PPI).
- Apply the required deterministic tie-break order.
- Assign sequential ordinal ranks.

### FR9 — Persistence

- Save the complete result under one RFP run ID in SQLite.

### FR10 — Presentation

- Show a leaderboard.
- Show detailed per-criterion scorecards with evidence.
- Show run details and tie-break explanation.
- Allow the complete run to be downloaded as JSON.

## Agentic Design Overview

The workflow is split into clear components so the LLM handles judgment and Python handles deterministic logic.

- Orchestrator: manages workflow order and invokes tools in sequence
- Document tool: extracts clean text from supplier PDFs
- Evaluation agent: scores one supplier using active criteria and evidence from the document
- Validation tool: checks schema, fills missing data, clips invalid scores, records warnings
- Ranking tool: performs benchmark computations, scoring formulas, and final ordering

The LLM is allowed to judge proposal quality, but it does not decide arithmetic, benchmarks, tie-break rules, or final ranks.

## Technology Stack

- UI: Streamlit
- Database: SQLite using Python standard library sqlite3
- AI layer: JSON-capable LLM, default OpenAI via langchain-openai
- PDF extraction: pypdf
- Validation: pydantic and custom normalization logic
- Optional public access for local runs: pyngrok
- Language: Python 3.x

## System Architecture

The application follows a simple layered flow:

- Streamlit UI
- Document extraction
- Evaluation agent
- Validation and normalization
- Scoring, benchmarking, ranking
- SQLite persistence

## Project Structure

- app.py — Streamlit UI and orchestration
- db.py — SQLite schema and persistence layer
- documents.py — PDF text extraction
- evaluation_agent.py — prompt building and LLM evaluation
- validation.py — Pydantic schema and normalization
- scoring.py — absolute score, benchmark, gap, relative percentage, and PPI logic
- ranking.py — deterministic sorting and ranking rules
- tunnel.py — exposes the running local Streamlit app through ngrok
- seed_db.py — database creation and initial seed data
- keys.py — environment variable loading for API credentials and optional ngrok token
- logger.py — logging configuration
- requirements.txt — Python dependencies
- data/ — sample supplier PDFs
- sample_output/ — example run output
- FUNCTIONAL.md — high-level business and functional specification
- TECHNICAL.md — low-level technical design notes

## Database Design

The app stores data locally in SQLite in a small schema:

### evaluation_criteria

- criterion_id: integer primary key
- name: criterion name
- description: assessment description
- weight: fractional value such as 0.30
- max_score: maximum score for the criterion
- is_active: Boolean-style flag for active criteria

### rfp_runs

- rfp_run_id: unique run ID
- created_at: ISO timestamp
- status: progress state such as in_progress or completed

### supplier_results

- rfp_run_id: foreign key to the run
- supplier_name: supplier name
- submission_date: date of submission
- experience_rating: supplier rating
- absolute_score: weighted score
- ppi: peer performance index
- final_rank: ranked position
- result_json: serialized full scorecard payload

### Default seed criteria

- Technical Capability — 30% — max 10
- Implementation Plan — 20% — max 10
- Commercial Value — 20% — max 10
- Security & Compliance — 20% — max 10
- Support & Experience — 10% — max 10

## Module Design

### app.py

- Handles the Streamlit UI and workflow orchestration
- Seeds the database on first run
- Validates active total weight
- Uploads supplier PDFs and metadata
- Creates a run and triggers evaluation
- Displays leaderboard, scorecards, warnings, and export options

### db.py

- Creates tables when missing
- Loads active and inactive criteria
- Updates criteria activation and weights
- Creates runs
- Saves supplier results
- Loads a completed run for display

### documents.py

- Expects PDF bytes
- Extracts readable text using pypdf
- Normalizes whitespace and joins page text

### evaluation_agent.py

- Builds the LLM prompt from active criteria and document text
- Calls the OpenAI-backed model using structured output
- Returns a scorecard dictionary

### validation.py

- Defines schema models for the evaluation response
- Validates and normalizes raw LLM output
- Adds warnings for missing or invalid fields
- Clips out-of-range criterion values

### scoring.py

- Computes absolute weighted score
- Finds the best score per criterion across suppliers
- Computes gap and relative percentage
- Calculates PPI based on weighted relative performance

### ranking.py

- Sorts suppliers in deterministic order using:
  1. higher PPI
  2. earlier submission date
  3. higher experience rating
  4. supplier name ascending
- Assigns final ranks sequentially

## End-to-End Data Flow

1. Load criteria from SQLite.
2. Upload supplier PDFs and metadata.
3. Create a run ID for the batch.
4. Extract text from each PDF.
5. Send the text and criteria to the LLM.
6. Validate and normalize the LLM output.
7. Compute absolute scores.
8. Benchmark across suppliers.
9. Calculate PPI and final ranks.
10. Persist the results.
11. Display the leaderboard and detailed scorecards.
12. Export JSON output for the run.

## User Workflow

1. Open the app and review active criteria.
2. Adjust criteria weights or active status in the sidebar if needed.
3. Upload supplier PDF files and provide metadata.
4. Click Evaluate.
5. Review supplier rankings and detailed evidence.
6. Download the final JSON result.

## Success Criteria

- Each incoming proposal is evaluated against every active criterion.
- Scores remain traceable to criteria, weight, evidence, and business rules.
- Ranking is deterministic and reproducible.
- Output can be persisted and exported as JSON.
- The app can be run locally with Streamlit and an OpenAI API key.

## Setup and Run

### 1. Create a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variables

Create a .env file in the project root with your API key:

```env
OPENAI_API_KEY=your_api_key_here
NGROK_AUTH_TOKEN=your_ngrok_auth_token  # Optional; only needed for a public tunnel
```

### 4. Initialize the database

```bash
python seed_db.py
```

### 5. Start the application

```bash
streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal, typically:

```text
http://localhost:8501
```

To expose the running app with a public ngrok URL, start a second terminal in
the project folder and run:

```bash
python tunnel.py
```

The public URL is printed in that terminal. Keep both terminals running while
using the tunnel; press Enter in the tunnel terminal to stop it. Get an ngrok
auth token from https://dashboard.ngrok.com/get-started/your-authtoken and
store it only in `.env`, not in source control.

## Notes

- The app uses a local SQLite database named rfp.db.
- The .env file is ignored by Git for security.
- The project intentionally keeps scoring and ranking deterministic, while using the LLM only for proposal analysis and evidence-backed scoring.

## Assumptions and Constraints

- Supplier proposals are demo or synthetic sample PDFs.
- A JSON-capable LLM is available via API key.
- Active criteria weights should sum to 100%.
- Results are not real legal or procurement decisions; they are for evaluation and demonstration purposes.

## License

This project is intended for educational and internal evaluation use unless otherwise specified by the repository owner.
