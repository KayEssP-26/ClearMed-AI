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
- Node.js and npm
- A Google Gemini API key
- A Pinecone API key and index name; retrieval is used for every simplification request.
- Tesseract OCR installed and available on `PATH` for image uploads and scanned PDFs. On Windows, set the `TESSERACT_CMD` environment variable if Tesseract is installed outside the standard locations.
- Optional: Supabase URL and key for request logging. Logging failures do not prevent simplification.

## Environment setup

1. Copy [.env.example](.env.example) to `.env` in the repository root.
2. Set `GEMINI_API_KEY`, `PINECONE_API_KEY`, and `PINECONE_INDEX_NAME`.
3. Set `SUPABASE_URL` and `SUPABASE_KEY` only if request logging is desired.

The React app defaults to `http://localhost:8000` for its API. To use another backend URL, set `VITE_API_URL` in `frontend/react/.env.local`.

## Local development

### Install dependencies

Run these commands from the repository root. Activate the virtual environment in each new terminal before starting the backend.

```powershell
python -m venv .venv
\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
npm --prefix frontend/react install
```

On macOS or Linux, activate it with `source .venv/bin/activate` instead.

### Start the backend

```powershell
Set-Location backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start the frontend

In a second terminal, run from the repository root:

```powershell
npm --prefix frontend/react run dev -- --host 0.0.0.0
```

Open `http://localhost:5173`. The backend health endpoint is `http://localhost:8000/health`.

## Optional data ingestion

The one-time corpus loader downloads PubMedQA using the Hugging Face `datasets` package; model generation and embeddings use Gemini, not Hugging Face Inference APIs. Ingestion makes Gemini embedding requests and writes to the `gemini-embedding-001-v1` Pinecone namespace. To rebuild that corpus, install both dependency sets and run:

```bash
pip install -r backend/requirements.txt -r backend/requirements-ingest.txt
python scripts/ingest_corpus.py 500
```

The count argument is the number of abstracts to ingest. Gemini quota limits may require waiting between embedding batches.

## Evaluation

To run the evaluation suite:

```bash
pip install -r eval/requirements.txt
python eval/evaluate.py
```

Results are written to [eval/results.json](eval/results.json).

## Notes

This tool is intended for educational and informational purposes only. It should not be used as a substitute for professional medical advice, emergency guidance, or diagnosis.
