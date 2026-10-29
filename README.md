# RFP Evaluation and Supplier Ranking

This project is a Python Streamlit application that evaluates supplier RFP responses, validates the generated scorecards, computes weighted scores, benchmarks results, ranks suppliers, and stores the run in SQLite.

## Features

- Upload multiple supplier PDF proposals
- Extract text from uploaded PDFs
- Evaluate each proposal using an LLM
- Validate and normalize LLM output
- Calculate weighted absolute scores
- Benchmark supplier performance across criteria
- Compute PPI and final ranking with deterministic tie-break rules
- Persist evaluation runs locally in SQLite
- Download the final results as JSON

## Tech stack

- Python 3
- Streamlit
- pypdf
- langchain-openai
- pydantic
- python-dotenv
- SQLite

## Project structure

- `app.py` — Streamlit UI and orchestration
- `db.py` — SQLite schema and persistence layer
- `documents.py` — PDF text extraction
- `evaluation_agent.py` — LLM-based supplier scoring
- `validation.py` — structured validation and normalization
- `scoring.py` — weighted scoring and benchmarks
- `ranking.py` — deterministic ranking logic
- `seed_db.py` — initial database seeding
- `keys.py` — environment variable loading for API keys
- `data/` — sample supplier PDFs
- `sample_output/` — example output artifacts

## Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root and add your OpenAI API key:

   ```env
   OPENAI_API_KEY=your_api_key_here
   ```

4. Initialize the database seed data:

   ```bash
   python seed_db.py
   ```

## Run the app

```bash
streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal (typically http://localhost:8501).

## Notes

- The app uses a local SQLite database called `rfp.db`.
- The `.env` file is ignored by Git for security.
- The project is intentionally deterministic in arithmetic and ranking, while the LLM is only used to generate initial evidence-based scorecards.

## License

This project is for educational and internal evaluation use unless otherwise specified by the repository owner.
