# 🩺 ClearMed AI

> **Translate complex clinical language into plain English — instantly.**

ClearMed AI is an AI-powered medical report simplification application that converts complex clinical text into patient-friendly explanations. It combines a **FastAPI backend**, a **Streamlit frontend**, and a **Retrieval-Augmented Generation (RAG)** pipeline to generate context-aware, easy-to-understand summaries of medical notes, discharge summaries, and uploaded reports.

---

## ✨ Features

- 📝 Simplifies complex medical text into plain English
- 📄 Supports PDF, JPG, and PNG medical report uploads
- 🔍 OCR extraction for scanned medical reports
- 🧠 Retrieval-Augmented Generation (RAG) using Pinecone
- 🏥 Biomedical Named Entity Recognition (NER)
- 📊 Readability analysis (before vs. after simplification)
- 📈 Built-in evaluation dashboard
- 📚 Benchmarking using ROUGE-L, BERTScore, and readability metrics, against a **physician-reviewed golden set**

---

## 🏗️ Architecture

```
                    User
                     │
                     ▼
             Streamlit Frontend
                     │
                     ▼
              FastAPI Backend
                     │
      ┌──────────────┼──────────────┐
      ▼              ▼              ▼
 Hugging Face     Pinecone       Supabase
(LLM + Embeddings   (RAG          (Logging)
    + NER)         retrieval)
```

---

## 📂 Project Structure

```text
backend/
├── app/
│   ├── config.py
│   ├── main.py
│   ├── models.py
│   ├── db/
│   ├── pipeline/
│   ├── prompts/
│   └── rag/
├── requirements.txt
├── requirements-ingest.txt
└── Dockerfile

frontend/
├── app.py
└── requirements.txt

scripts/
└── ingest_corpus.py

eval/
├── evaluate.py
├── golden_set.json
└── results.json

.github/
.env.example
.gitignore
README.md
```

---

## ⚙️ Tech Stack

**Backend**
- FastAPI
- Python
- Hugging Face Inference API
- Pinecone
- Supabase

**Frontend**
- Streamlit
- Altair
- Pandas

**AI Pipeline**
- Llama 3.1 8B Instruct
- all-MiniLM-L6-v2 embeddings
- Retrieval-Augmented Generation (RAG)

**Evaluation**
- ROUGE-L
- BERTScore
- Flesch Reading Ease

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Hugging Face API token
- Pinecone API key
- Supabase project
- Tesseract OCR (for scanned report support)

### Environment Variables

Copy `.env.example` to `.env` and fill in your own values:

```bash
cp .env.example .env
```

```env
HF_TOKEN=
PINECONE_API_KEY=
PINECONE_INDEX_NAME=
SUPABASE_URL=
SUPABASE_KEY=
BACKEND_URL=http://localhost:8000
```

Never commit `.env` — it's excluded via `.gitignore`. `.env.example` is the template that ships with the repo.

---

## 💻 Local Setup

**Create a virtual environment**

```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

Linux/Mac:
```bash
source .venv/bin/activate
```

**Install dependencies**

```bash
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

**Start the backend**

```bash
cd backend
uvicorn app.main:app --reload
```

**Start the frontend** (in a separate terminal)

```bash
streamlit run frontend/app.py
```

---

## 📄 OCR Support

Supported upload formats:
- PDF
- JPG / JPEG
- PNG

Scanned reports are automatically run through OCR before simplification.

---

## 📚 Corpus Ingestion (Optional)

To rebuild or expand the RAG retrieval corpus:

```bash
pip install -r backend/requirements-ingest.txt
python scripts/ingest_corpus.py 500
```

---

## 📈 Evaluation

ClearMed AI includes an evaluation dashboard that compares generated simplifications against a **golden set of clinician-reviewed reference simplifications**, scored on semantic similarity, lexical overlap, and readability.

### Golden Set Verification

The golden set (`eval/golden_set.json`) pairs complex clinical text with a plain-English reference simplification. To keep this a meaningful benchmark rather than a purely automated one:

- Reference simplifications are **reviewed by a licensed medical practitioner** before being added to the set, checking each one for clinical accuracy, no omitted safety-relevant information (e.g. dosages, urgency, follow-up instructions), and no added information not supported by the source text.
- Entries are revised or rejected if the reviewer flags an inaccuracy, ambiguity, or unsafe simplification.
- The golden set is treated as a living benchmark — new cases are added as edge cases are discovered (e.g. negations, multiple concurrent findings, ambiguous abbreviations), and re-reviewed when the reference wording changes.

This review step exists specifically to prevent the evaluation from validating the model against its own kind of writing. ROUGE-L and BERTScore measure similarity to the reference; the clinician review is what gives that reference — and therefore the resulting scores — clinical meaning.

**Note:** Automatic metrics (ROUGE-L, BERTScore) measure textual and semantic similarity to the reference, not clinical correctness on arbitrary input. They're a regression check for the fixed benchmark, not a guarantee of accuracy on real-world reports outside the golden set.

### Running the Evaluation

```bash
python eval/evaluate.py
```

Options:
```bash
python eval/evaluate.py --resume            # reuse prior successful runs, retry the rest
python eval/evaluate.py --recompute-bert     # recompute BERTScore without rerunning /simplify
```

### Current Results

| Metric | Mean | Median | Range |
|---|---|---|---|
| Cases evaluated | 50 | — | — |
| ROUGE-L | 0.106 | 0.101 | 0.046 – 0.187 |
| BERTScore F1 | 0.690 | 0.689 | 0.598 – 0.752 |
| Readability gain (Flesch reading ease) | +47.3 | +39.5 | +8.9 – +136.5 |

Low ROUGE-L is expected for good simplifications — plain-English paraphrases naturally use different words than the clinical original, so lexical overlap is not the primary quality signal. BERTScore (semantic similarity) and the per-case inspection view in the dashboard are more informative for judging output quality.

The dashboard also provides:
- 📈 Readability improvement scatter plot (original vs. simplified reading ease)
- 📊 Readability gain distribution across cases
- 🔍 Semantic vs. lexical similarity comparison
- 📋 Sortable per-case benchmark results
- 📖 Generated answer vs. reference inspection for individual cases

---

## 🔮 Future Improvements

- Entity-level fact-preservation checks (diffing NER output between source and simplified text, to catch hallucinated or dropped clinical details)
- Medical chatbot interface
- Multi-language simplification
- Clinical report summarization
- Expanded, more diverse RAG corpus
- Better OCR for handwritten reports
- Explainability via cited medical sources

---

## ⚠️ Disclaimer

> **ClearMed AI is intended for educational and informational purposes only. AI-generated explanations may be inaccurate, incomplete, or outdated. This application is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional before making medical decisions. Do not rely on this tool for emergencies or urgent medical situations.**

---

## 📜 License

This project is licensed under the Apache 2.0 License.
