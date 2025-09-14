# server1.py
from fastapi import FastAPI
from backend import ingest, config
from backend.rag import EmbeddingsClient, GeminiClient, RAGPipeline
from backend.vectorstore import FaissStore
import os

app = FastAPI(title="Server 1 - Ingestion + L1 Summary")

# Paths
RAW_DIR = os.path.join(config.PDFS_DIR, "raw")
L1_DIR = os.path.join(config.PDFS_DIR, "summaries", "L1")
os.makedirs(L1_DIR, exist_ok=True)

INDEX_PATH = "server1_index.faiss"
META_PATH = "server1_meta.json"

# Init clients
embedder = EmbeddingsClient(model_name="models/embedding-001", api_key=config.GOOGLE_API_KEY)
llm = GeminiClient(model_name="gemini-1.5-flash", api_key=config.GOOGLE_API_KEY)
store = FaissStore(INDEX_PATH, META_PATH)
rag = RAGPipeline(store, embedder, llm)


@app.post("/ingest")
def ingest_and_summarize():
    chunks = ingest.ingest_pdfs(RAW_DIR)
    rag.build_index(chunks)

    # Merge text and summarize to ~1/10th
    full_text = "\n".join(c["text"] for c in chunks)
    summary = ingest.summarize_text(full_text, target_ratio=0.1, api_key=config.GOOGLE_API_KEY)

    # Save summary as L1 document
    out_path = os.path.join(L1_DIR, "summary_L1.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(summary)
    return {"status": "ok", "chunks": len(chunks), "summary_file": out_path}


@app.post("/query")
def query_server1(question: str):
    return rag.answer(question, top_k=5, max_output_tokens=512)
