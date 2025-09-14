import os
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import config
from backend.schemas import (
    IngestRequest, IngestResponse,
    QueryRequest, QueryResponse,
    StatsResponse, HealthResponse
)

app = FastAPI(title="Jharkhand Policies MCP Client", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# MCP Servers registry
# -------------------------------
SERVERS = {
    "server1": "http://localhost:8001",  # ingestion + 50-page L1 summary
    "server2": "http://localhost:8002",  # L2 summary (5 pages)
    "server3": "http://localhost:8003",  # L3 ultra-summary (concise notes)
}


# -------------------------------
# Health + Stats
# -------------------------------
@app.get("/health", response_model=HealthResponse)
async def health():
    """Basic healthcheck for MCP Client itself."""
    return HealthResponse(
        status="ok", 
        stats=StatsResponse(
            vectors=0, 
            files_indexed=0,
            index_path="",
            metadata_path="",
            index_exists=False
        )
    )


@app.get("/stats", response_model=StatsResponse)
async def stats():
    """Aggregates stats from all servers."""
    async with httpx.AsyncClient(timeout=180.0) as client:
        all_stats = []
        for name, url in SERVERS.items():
            try:
                resp = await client.get(f"{url}/stats")
                if resp.status_code == 200:
                    all_stats.append({name: resp.json()})
            except Exception:
                all_stats.append({name: {"error": "unreachable"}})

    return StatsResponse(vectors=0, dimension=0)  # placeholder
    # ⚡ If you want to merge stats properly:
    # return {"servers": all_stats}


# -------------------------------
# Ingestion Pipeline
# -------------------------------
@app.post("/ingest", response_model=IngestResponse)
async def ingest(req: IngestRequest):
    """
    Orchestrates ingestion pipeline:
    - Server1: raw PDFs → L1 summary
    - Server2: L1 → L2 summary
    - Server3: L2 → L3 ultra-summary
    """
    async with httpx.AsyncClient(timeout=180.0) as client:
        # Step 1: Ingest PDFs + build L1
        resp1 = await client.post(f"{SERVERS['server1']}/ingest", json={})
        data1 = resp1.json()

        # Step 2: Summarize into L2
        resp2 = await client.post(f"{SERVERS['server2']}/summarize_l1")
        data2 = resp2.json()

        # Step 3: Summarize into L3
        resp3 = await client.post(f"{SERVERS['server3']}/summarize_l2")
        data3 = resp3.json()

    return IngestResponse(
        files_processed=data1.get("files_processed", 0),
        chunks_added=data1.get("chunks_added", 0),
        vectors=data1.get("vectors", 0),
        message="Ingestion + L1, L2, L3 summaries complete"
    )


# -------------------------------
# Manual triggers for summaries
# -------------------------------
@app.post("/summarize_l1")
async def summarize_l1():
    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(f"{SERVERS['server2']}/summarize_l1")
        return resp.json()


@app.post("/summarize_l2")
async def summarize_l2():
    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(f"{SERVERS['server3']}/summarize_l2")
        return resp.json()


# -------------------------------
# Query Routing Logic
# -------------------------------
def pick_server(query: str) -> str:
    """
    Naive router: decides which server to call based on query intent.
    - server1 → factual/detailed queries
    - server2 → overview/summary queries
    - server3 → very high-level or 'key points' queries
    """
    q = query.lower()
    if any(word in q for word in ["detailed", "full", "section", "law", "policy"]):
        return "server1"
    elif any(word in q for word in ["summary", "overview", "brief"]):
        return "server2"
    elif any(word in q for word in ["key points", "bullet", "concise", "short"]):
        return "server3"
    else:
        return "server1"  # default fallback


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """Routes query to the most appropriate MCP server."""
    target_server = pick_server(req.question)
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{SERVERS[target_server]}/query",
            params={"question": req.question}
        )
        data = resp.json()

    return QueryResponse(
        answer=data.get("answer", str(data)),
        citations=data.get("citations", []),
        used_top_k=req.top_k or 5,
        prompt=data.get("prompt", "")
    )




# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX


# import os
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware

# from backend import config
# from backend.schemas import IngestRequest, IngestResponse, QueryRequest, QueryResponse, StatsResponse, HealthResponse
# from backend.vectorstore import FaissStore
# from backend.ingest import ingest_pdfs
# from backend.rag import RAGPipeline, EmbeddingsClient, GeminiClient

# app = FastAPI(title="Jharkhand Policies RAG Backend", version="1.0.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# store = FaissStore(config.INDEX_FILE, config.META_FILE)
# store.load()

# embedder = EmbeddingsClient(config.EMBEDDING_MODEL, config.GOOGLE_API_KEY)
# llm = GeminiClient(config.GEMINI_MODEL, config.GOOGLE_API_KEY)
# rag = RAGPipeline(store, embedder, llm)


# @app.get("/health", response_model=HealthResponse)
# async def health():
#     st = store.stats()
#     return HealthResponse(status="ok", stats=StatsResponse(**st))


# @app.get("/stats", response_model=StatsResponse)
# async def stats():
#     return StatsResponse(**store.stats())


# @app.post("/ingest", response_model=IngestResponse)
# async def ingest(req: IngestRequest):
#     if req.force_rebuild:
#         # Reset index and metadata
#         if os.path.exists(config.INDEX_FILE):
#             try:
#                 os.remove(config.INDEX_FILE)
#             except Exception:
#                 pass
#         if os.path.exists(config.META_FILE):
#             try:
#                 os.remove(config.META_FILE)
#             except Exception:
#                 pass
#         store.index = None
#         store.id_to_meta = {}
#         store._next_id = 0

#     chunks = ingest_pdfs(config.PDFS_DIR)
#     added = rag.build_index(chunks)
#     st = store.stats()
#     return IngestResponse(files_processed=len({c['source_file'] for c in chunks}), chunks_added=len(chunks), vectors=st["vectors"], message="Ingestion complete")


# @app.post("/query", response_model=QueryResponse)
# async def query(req: QueryRequest):
#     top_k = req.top_k or config.TOP_K_DEFAULT
#     result = rag.answer(req.question, top_k=top_k, max_output_tokens=req.max_output_tokens or 512)
#     return QueryResponse(answer=result["answer"], citations=result["citations"], used_top_k=top_k, prompt=result["prompt"])


# # For local dev from backend dir: uvicorn app:app --reload
