# 🩺 ClearMed AI

> **Translate complex clinical language into plain English—instantly.**

ClearMed AI is an AI-powered medical report simplification application that converts complex clinical text into patient-friendly explanations. It combines a **FastAPI backend**, **Streamlit frontend**, and a **Retrieval-Augmented Generation (RAG)** pipeline to generate context-aware, easy-to-understand summaries of medical notes, discharge summaries, and uploaded reports. :contentReference[oaicite:0]{index=0}

---

## ✨ Features

- 📝 Simplifies complex medical text into plain English
- 📄 Supports PDF, JPG, and PNG medical report uploads
- 🔍 OCR extraction for scanned medical reports
- 🧠 Retrieval-Augmented Generation (RAG) using Pinecone
- 🏥 Biomedical Named Entity Recognition (NER)
- 📊 Readability analysis (before vs after simplification)
- 📈 Built-in evaluation dashboard
- 📚 Benchmarking using ROUGE-L, BERTScore, and readability metrics

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
     ┌────────────┼────────────┐
     ▼            ▼            ▼
 HuggingFace   Pinecone    Supabase
   (LLM +        (RAG)       Logging
 Embeddings +
    NER)
```

---

## 📂 Project Structure

```text
backend/
│
├── app/
│   ├── config.py
│   ├── main.py
│   ├── models.py
│   ├── db/
│   ├── pipeline/
│   ├── prompts/
│   └── rag/
│
├── requirements.txt
├── requirements-ingest.txt
└── Dockerfile

frontend/
│
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

### Backend
- FastAPI
- Python
- Hugging Face Inference API
- Pinecone
- Supabase

### Frontend
- Streamlit
- Altair
- Pandas

### AI Pipeline
- Llama 3.1 8B Instruct
- all-MiniLM-L6-v2 Embeddings
- Biomedical NER
- Retrieval-Augmented Generation (RAG)

### Evaluation
- ROUGE-L
- BERTScore
- Flesch Reading Ease

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Hugging Face API Token
- Pinecone API Key
- Supabase Project
- (Optional) Tesseract OCR

---

### Environment Variables

Copy

```
.env.example
```

to

```
.env
```

and configure:

```env
HF_TOKEN=
PINECONE_API_KEY=
PINECONE_INDEX_NAME=

SUPABASE_URL=
SUPABASE_KEY=

BACKEND_URL=http://localhost:8000
```

---

## 💻 Local Setup

### Create Virtual Environment

```bash
python -m venv .venv
```

Windows

```bash
.venv\Scripts\activate
```

Linux/Mac

```bash
source .venv/bin/activate
```

---

### Install Dependencies

Backend

```bash
pip install -r backend/requirements.txt
```

Frontend

```bash
pip install -r frontend/requirements.txt
```

---

### Start Backend

```bash
cd backend

uvicorn app.main:app --reload
```

---

### Start Frontend

```bash
streamlit run frontend/app.py
```

---

## 📄 OCR Support

Supported formats

- PDF
- JPG
- JPEG
- PNG

Scanned PDFs are automatically OCR processed before simplification.

---

## 📚 Corpus Ingestion (Optional)

Install the additional dependencies

```bash
pip install -r backend/requirements-ingest.txt
```

Run

```bash
python scripts/ingest_corpus.py 500
```

---

# 📈 Evaluation Results

ClearMed AI includes an evaluation dashboard that compares generated simplifications against a manually curated golden set using semantic similarity, lexical overlap, and readability metrics. :contentReference[oaicite:1]{index=1}

| Metric | Result |
|---------|--------|
| Cases Evaluated | **50** |
| Mean ROUGE-L | **0.106** |
| Mean BERTScore F1 | **0.690** |
| Mean Readability Gain | **+47.3** |

### Additional Insights

- **Median ROUGE-L:** 0.101
- **ROUGE-L Range:** 0.046 – 0.187
- **Median BERTScore:** 0.689
- **BERTScore Range:** 0.598 – 0.752
- **Median Readability Gain:** +39.5
- **Readability Gain Range:** +8.9 – +136.5

The evaluation dashboard also provides:

- 📈 Readability improvement scatter plots
- 📊 Readability gain distribution
- 🔍 Semantic vs lexical similarity visualization
- 📋 Per-case benchmark comparison
- 📖 Generated answer vs reference inspection for each benchmark case :contentReference[oaicite:2]{index=2}

---

## 🔮 Future Improvements

- Medical chatbot interface
- Multi-language simplification
- Clinical report summarization
- Improved RAG corpus
- Better OCR for handwritten reports
- Explainability using cited medical sources

---

## ⚠️ Disclaimer

> **ClearMed AI is intended for educational and informational purposes only. AI-generated explanations may be inaccurate, incomplete, or outdated. This application is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional before making medical decisions. Do not rely on this tool for emergencies or urgent medical situations.** :contentReference[oaicite:3]{index=3}

---

## 📜 License

This project is licensed under the MIT License.
