# server2.py
from fastapi import FastAPI
from backend import config
from backend.rag import EmbeddingsClient, GeminiClient, RAGPipeline
from backend.vectorstore import FaissStore
import os

app = FastAPI(title="Server 2 - L2 Summary")

RAW_DIR = os.path.join(config.PDFS_DIR, "raw")
L2_DIR = os.path.join(config.PDFS_DIR, "summaries", "L2")
os.makedirs(L2_DIR, exist_ok=True)

INDEX_PATH = "server2_index.faiss"
META_PATH = "server2_meta.json"

# Init clients
embedder = EmbeddingsClient(model_name="models/embedding-001", api_key=config.GOOGLE_API_KEY)
llm = GeminiClient(model_name="gemini-1.5-flash", api_key=config.GOOGLE_API_KEY)
store = FaissStore(INDEX_PATH, META_PATH)
rag = RAGPipeline(store, embedder, llm)


@app.post("/summarize_l1")
def summarize_l1():
    """Takes L1 summaries → produces L2 summary (~1/5th of L1)."""
    l1_file = os.path.join(config.PDFS_DIR, "summaries", "L1", "summary_L1.txt")
    if not os.path.exists(l1_file):
        return {"error": "No L1 summary found. Run Server1 first."}

    with open(l1_file, "r", encoding="utf-8") as f:
        l1_text = f.read()

    # Summarize further (e.g. ~20% length of L1)
    summary = rag.llm.summarize(l1_text, target_ratio=0.2)

    out_path = os.path.join(L2_DIR, "summary_L2.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(summary)

    return {"status": "ok", "summary_file": out_path}


@app.post("/query")
def query_server2(question: str):
    return rag.answer(question, top_k=5, max_output_tokens=512)
