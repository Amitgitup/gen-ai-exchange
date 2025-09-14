# server3.py
from fastapi import FastAPI
from backend import config
from backend.rag import EmbeddingsClient, GeminiClient, RAGPipeline
from backend.vectorstore import FaissStore
import os

app = FastAPI(title="Server 3 - L3 Summary (Ultra-condensed)")

RAW_DIR = os.path.join(config.PDFS_DIR, "raw")
L3_DIR = os.path.join(config.PDFS_DIR, "summaries", "L3")
os.makedirs(L3_DIR, exist_ok=True)

INDEX_PATH = "server3_index.faiss"
META_PATH = "server3_meta.json"

# Init RAG stack
embedder = EmbeddingsClient(model_name="models/embedding-001", api_key=config.GOOGLE_API_KEY)
llm = GeminiClient(model_name="gemini-1.5-flash", api_key=config.GOOGLE_API_KEY)
store = FaissStore(INDEX_PATH, META_PATH)
rag = RAGPipeline(store, embedder, llm)


@app.post("/summarize_l2")
def summarize_l2():
    """Consumes L2 summary → produces L3 ultra-summary (~1/10th of L2)."""
    l2_file = os.path.join(config.PDFS_DIR, "summaries", "L2", "summary_L2.txt")
    if not os.path.exists(l2_file):
        return {"error": "No L2 summary found. Run Server2 first."}

    with open(l2_file, "r", encoding="utf-8") as f:
        l2_text = f.read()

    # Summarize further (~10% of L2 length, super-condensed bullet points)
    summary = rag.llm.summarize(l2_text, target_ratio=0.1)

    out_path = os.path.join(L3_DIR, "summary_L3.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(summary)

    return {"status": "ok", "summary_file": out_path}


@app.post("/query")
def query_server3(question: str):
    """Query the ultra-condensed summary"""
    return rag.answer(question, top_k=3, max_output_tokens=256)
