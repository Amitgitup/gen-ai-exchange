# Jharkhand Policies RAG Backend

FastAPI backend for RAG over Jharkhand government policy PDFs using Google Embeddings + Gemini and FAISS.

## Setup
1. Python 3.10+
2. Create and activate venv
```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r backend/requirements.txt
```
3. Copy environment template and set `GOOGLE_API_KEY`
```bash
copy backend\.env.example backend\.env
# edit backend\.env and add GOOGLE_API_KEY
```

## Run
```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

Open docs at `http://localhost:8000/docs`.

## Endpoints
- `GET /health` → service status and index stats
- `GET /stats` → index stats
- `POST /ingest` → build index from PDFs
  - body: `{ "force_rebuild": false }`
- `POST /query` → ask a question
  - body: `{ "question": "...", "top_k": 6, "max_output_tokens": 512 }`

## Index files
Defaults to `experiment/jharkhand_faiss.index` and `experiment/jharkhand_metadata.json`.

## Frontend usage
- Call `/ingest` once (or when PDFs change), then `/query` for questions.
- Show `QueryResponse.answer` and list `citations` with file and page range.
