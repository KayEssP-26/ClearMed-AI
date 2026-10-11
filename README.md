# ClearMed AI

ClearMed AI is a medical report simplification application that turns complex clinical text into clearer, plain-English explanations. It combines a FastAPI backend and a React/Vite frontend with a retrieval-augmented generation (RAG) pipeline to provide context-aware simplifications for medical notes, discharge summaries, and uploaded reports.

## What it does

- Simplifies clinical text entered directly by the user.
- Processes uploaded medical reports (PDF/JPG/PNG) through OCR and simplification.
- Uses retrieval-augmented generation to ground explanations in relevant medical context.
- Provides readability metrics before and after simplification.
- Includes an evaluation dashboard and benchmark workflow for measuring quality.

## Project structure

```text
backend/
  app/
    config.py
    main.py
    models.py
    db/
    pipeline/
    prompts/
    rag/
frontend/
  react/
    index.html
    package.json
    src/
    vite.config.js
scripts/
  ingest_corpus.py
eval/
  evaluate.py
golden_set.json
  results.json
```

## Architecture overview

- Backend: FastAPI service exposing `/health`, `/simplify`, and `/simplify-report` endpoints.
- Frontend: React + Vite app in `frontend/react` for report upload, text simplification, and dashboard viewing.
- RAG layer: retrieves relevant chunks and passes them into the model prompt.
## Prerequisites

- Python 3.10+
- A Hugging Face token
- Optional: Pinecone and Supabase credentials if you want to use the full retrieval stack

## Environment setup

1. Copy [.env.example](.env.example) to `.env`.
2. Fill in the required values:
   - `HF_TOKEN`
   - `PINECONE_API_KEY`
   - `PINECONE_INDEX_NAME`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `BACKEND_URL` (default: `http://localhost:8000`)

## Local development

### 1) Install dependencies

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use .venv\Scripts\activate
pip install -r backend/requirements.txt
cd frontend/react
npm install
```

### 2) Start the backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3) Start the frontend

In a second terminal:

```bash
cd frontend/react
npm run dev -- --host 0.0.0.0
```

The app should open in your browser at `http://localhost:5173`.

## Optional data ingestion

If you want to ingest a corpus into the retrieval system, install the extra ingest dependencies and run:

```bash
pip install -r backend/requirements-ingest.txt
python scripts/ingest_corpus.py 500
```

## Evaluation

To run the evaluation suite:

```bash
pip install -r eval/requirements.txt
python eval/evaluate.py
```

Results are written to [eval/results.json](eval/results.json).

## Notes

This tool is intended for educational and informational purposes only. It should not be used as a substitute for professional medical advice, emergency guidance, or diagnosis.
