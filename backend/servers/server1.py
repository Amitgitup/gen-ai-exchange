# # server1.py
# import logging
# import os
# import time
# from typing import Dict, Any, Optional

# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel

# from backend import ingest, config
# from backend.rag import EmbeddingsClient, GeminiClient, RAGPipeline
# from backend.vectorstore import FaissStore
# from backend.schemas import StatsResponse, HealthResponse

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI(title="Server 1 - Ingestion + L1 Summary", version="1.0.0")

# # Paths
# RAW_DIR = os.path.join(config.PDFS_DIR, "raw")
# L1_DIR = os.path.join(config.PDFS_DIR, "summaries", "L1")
# os.makedirs(L1_DIR, exist_ok=True)

# INDEX_PATH = "server1_index.faiss"
# META_PATH = "server1_meta.json"

# # Global state
# _initialized = False
# _store = None
# _rag = None

# def get_rag_pipeline() -> RAGPipeline:
#     """Lazy initialization of RAG pipeline"""
#     global _rag, _store, _initialized
    
#     if not _initialized:
#         try:
#             logger.info("Initializing Server 1 RAG pipeline...")
#             embedder = EmbeddingsClient(model_name="models/embedding-001", api_key=config.GOOGLE_API_KEY)
#             llm = GeminiClient(model_name="gemini-1.5-flash", api_key=config.GOOGLE_API_KEY)
#             _store = FaissStore(INDEX_PATH, META_PATH)
#             _store.load()
#             _rag = RAGPipeline(_store, embedder, llm)
#             _initialized = True
#             logger.info("Server 1 RAG pipeline initialized successfully")
#         except Exception as e:
#             logger.error(f"Failed to initialize RAG pipeline: {e}")
#             raise HTTPException(status_code=500, detail=f"RAG initialization failed: {str(e)}")
    
#     return _rag

# class QueryRequest(BaseModel):
#     question: str
#     top_k: Optional[int] = 5
#     max_output_tokens: Optional[int] = 1024


# @app.get("/health", response_model=HealthResponse)
# async def health():
#     """Health check endpoint"""
#     try:
#         rag_pipeline = get_rag_pipeline()
#         stats = rag_pipeline.store.stats()
#         return HealthResponse(
#             status="ok",
#             stats=StatsResponse(**stats)
#         )
#     except Exception as e:
#         logger.error(f"Health check failed: {e}")
#         return HealthResponse(
#             status="error",
#             stats=StatsResponse(
#                 vectors=0,
#                 files_indexed=0,
#                 index_path="",
#                 metadata_path="",
#                 index_exists=False
#             )
#         )

# @app.get("/stats", response_model=StatsResponse)
# async def stats():
#     """Get server statistics"""
#     try:
#         rag_pipeline = get_rag_pipeline()
#         return StatsResponse(**rag_pipeline.store.stats())
#     except Exception as e:
#         logger.error(f"Stats retrieval failed: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/ingest")
# async def ingest_and_summarize():
#     """Ingest PDFs and create L1 summary"""
#     try:
#         logger.info("Starting ingestion process...")
#         start_time = time.time()
        
#         # Ingest PDFs
#         chunks = ingest.ingest_pdfs(RAW_DIR)
#         logger.info(f"Extracted {len(chunks)} chunks from PDFs")
        
#         # Build RAG index
#         rag_pipeline = get_rag_pipeline()
#         vectors_added = rag_pipeline.build_index(chunks)
#         logger.info(f"Added {vectors_added} vectors to index")

#         # Create L1 summary
#         full_text = "\n".join(c["text"] for c in chunks)
#         logger.info("Generating L1 summary...")
#         summary = ingest.summarize_text(full_text, target_ratio=0.1, api_key=config.GOOGLE_API_KEY)

#         # Save summary
#         out_path = os.path.join(L1_DIR, "summary_L1.txt")
#         with open(out_path, "w", encoding="utf-8") as f:
#             f.write(summary)
        
#         processing_time = time.time() - start_time
#         logger.info(f"Ingestion completed in {processing_time:.2f} seconds")
        
#         return {
#             "status": "ok", 
#             "chunks": len(chunks),
#             "vectors_added": vectors_added,
#             "summary_file": out_path,
#             "processing_time": processing_time,
#             "summary_length": len(summary)
#         }
#     except Exception as e:
#         logger.error(f"Ingestion failed: {e}")
#         raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

# @app.post("/query")
# async def query_server1(request: QueryRequest):
#     """Query the full document index"""
#     try:
#         rag_pipeline = get_rag_pipeline()
#         result = rag_pipeline.answer(
#             request.question, 
#             top_k=request.top_k, 
#             max_output_tokens=request.max_output_tokens
#         )
#         return result
#     except Exception as e:
#         logger.error(f"Query failed: {e}")
#         raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

# @app.post("/query/{question}")
# async def query_server1_legacy(question: str):
#     """Legacy query endpoint for backward compatibility"""
#     request = QueryRequest(question=question)
#     return await query_server1(request)

# server1.py (Corrected)
# server1.py (fixed & hardened)

import logging
import os
import time
import asyncio
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import your existing backend modules (unchanged)
from backend import ingest, config
from backend.rag import EmbeddingsClient, GeminiClient, RAGPipeline
from backend.vectorstore import FaissStore
from backend.schemas import StatsResponse, HealthResponse

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server1")

# --- App setup ---
app = FastAPI(title="Server 1 - Ingestion + L1 Summary", version="1.0.0")

origins = [
    "http://localhost:3000",
    # Add other origins if required
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Paths & Config ---
RAW_DIR = os.path.join(config.PDFS_DIR, "raw")
L1_DIR = os.path.join(config.PDFS_DIR, "summaries", "L1")
os.makedirs(L1_DIR, exist_ok=True)

INDEX_PATH = "server1_index.faiss"
META_PATH = "server1_meta.json"

# --- Global lazy state (protected with lock) ---
_initialized = False
_store: Optional[FaissStore] = None
_rag: Optional[RAGPipeline] = None
_init_lock = asyncio.Lock()


# Pydantic model used for incoming queries
class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5
    max_output_tokens: Optional[int] = 1024


async def _create_store_if_missing(index_path: str, meta_path: str) -> FaissStore:
    """
    Create a FaissStore object. If index/meta files don't exist, create an empty store
    rather than failing.
    """
    store = FaissStore(index_path, meta_path)
    try:
        # The FaissStore.load() should check for file existence internally,
        # but guard here in case it raises.
        store.load()
        logger.info("FaissStore loaded from disk.")
    except FileNotFoundError:
        logger.info("Index or metadata not found on disk. Creating a fresh store.")
        # Ensure any internal initialization happens (depends on FaissStore impl)
        try:
            store.create_empty()
            store.save()
            logger.info("Created and saved empty FaissStore.")
        except AttributeError:
            # If your FaissStore doesn't have create_empty(), fallback to load() attempt and continue.
            logger.warning("FaissStore does not implement create_empty(); continuing with existing store instance.")
    except Exception as exc:
        logger.exception("Unexpected error loading FaissStore: %s", exc)
        # raise to let caller handle as 500
        raise

    return store


async def get_rag_pipeline() -> RAGPipeline:
    """
    Lazy, thread-safe initialization of the RAG pipeline components.
    Returns a ready-to-use RAGPipeline or raises HTTPException on hard failure.
    """
    global _initialized, _store, _rag

    # Fast path
    if _initialized and _rag is not None:
        return _rag

    async with _init_lock:
        # Double-check after acquiring lock
        if _initialized and _rag is not None:
            return _rag

        try:
            logger.info("Initializing Server 1 RAG pipeline...")
            # Initialize embedder & llm clients (these constructors may raise)
            embedder = EmbeddingsClient(model_name="models/embedding-001", api_key=config.GOOGLE_API_KEY)
            llm = GeminiClient(model_name="gemini-1.5-flash", api_key=config.GOOGLE_API_KEY)

            # Create/load vector store safely
            _store = await _create_store_if_missing(INDEX_PATH, META_PATH)

            # Build RAG pipeline (assumes RAGPipeline(store, embedder, llm))
            _rag = RAGPipeline(_store, embedder, llm)

            # Mark initialized only after all steps succeed
            _initialized = True
            logger.info("RAG pipeline initialized successfully.")
            return _rag

        except Exception as exc:
            logger.exception("RAG initialization failed: %s", exc)
            # Make sure partial state doesn't remain marked initialized
            _initialized = False
            _rag = None
            _store = None
            # Surface helpful error to client/orchestrator
            raise HTTPException(status_code=500, detail=f"RAG initialization failed: {str(exc)}")


# -----------------------
# Health & Stats endpoints
# -----------------------
@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check for Server 1.
    Returns 'ok' when store is accessible & returns stats; otherwise returns 'error' + best-effort stats.
    """
    try:
        rag = await get_rag_pipeline()
        # Ensure store.stats() returns a dict compatible with StatsResponse
        stats = {}
        try:
            stats = rag.store.stats()
        except Exception as e:
            logger.warning("Failed to read store stats: %s", e)
            # Provide a fallback empty stats structure
            stats = {
                "vectors": 0,
                "files_indexed": 0,
                "index_path": INDEX_PATH,
                "metadata_path": META_PATH,
                "index_exists": False,
            }

        return HealthResponse(status="ok", stats=StatsResponse(**stats))
    except HTTPException as http_exc:
        # Initialization failed; return structured HealthResponse with 'error' status
        logger.warning("Health initialization error: %s", http_exc.detail)
        empty_stats = StatsResponse(
            vectors=0,
            files_indexed=0,
            index_path="",
            metadata_path="",
            index_exists=False,
        )
        return HealthResponse(status="error", stats=empty_stats)
    except Exception as exc:
        logger.exception("Unexpected health endpoint failure: %s", exc)
        empty_stats = StatsResponse(
            vectors=0,
            files_indexed=0,
            index_path="",
            metadata_path="",
            index_exists=False,
        )
        return HealthResponse(status="error", stats=empty_stats)


@app.get("/stats", response_model=StatsResponse)
async def stats():
    """
    Returns index statistics. Raises 500 on failure.
    """
    try:
        rag = await get_rag_pipeline()
        st = rag.store.stats()
        return StatsResponse(**st)
    except HTTPException as exc:
        logger.warning("Stats endpoint: initialization error: %s", exc.detail)
        raise
    except Exception as exc:
        logger.exception("Stats retrieval failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# -----------------------
# Ingestion endpoint
# -----------------------
@app.post("/ingest")
async def ingest_and_summarize(request: Request):
    """
    Ingest PDFs from RAW_DIR, build index and create L1 summary.
    Accepts an optional JSON body with {"target_ratio": float} to control summary ratio.
    """
    start_time = time.time()
    try:
        logger.info("Starting ingestion process...")

        # Accept optional override params from body
        try:
            body = await request.json()
            if not isinstance(body, dict):
                body = {}
        except Exception:
            body = {}

        target_ratio = float(body.get("target_ratio", 0.1))

        # Extract chunks from PDFs (ingest.ingest_pdfs should return list of chunks with 'text')
        try:
            chunks = ingest.ingest_pdfs(RAW_DIR)
        except FileNotFoundError as e:
            logger.warning("Raw PDF directory not found or empty: %s", e)
            chunks = []
        except Exception as e:
            logger.exception("PDF ingestion raised an exception: %s", e)
            raise HTTPException(status_code=500, detail=f"Ingestion pipeline error: {e}")

        if not chunks:
            processing_time = time.time() - start_time
            logger.info("No documents found during ingestion.")
            return {
                "status": "ok",
                "chunks": 0,
                "vectors_added": 0,
                "summary_file": None,
                "processing_time": processing_time,
                "summary_length": 0,
                "note": "No documents found to ingest."
            }

        # Build RAG index
        rag_pipeline = await get_rag_pipeline()
        try:
            vectors_added = rag_pipeline.build_index(chunks)
            logger.info("Vectors added to index: %s", vectors_added)
        except Exception as e:
            logger.exception("Failed to build index: %s", e)
            raise HTTPException(status_code=500, detail=f"Index build failed: {e}")

        # Save index if anything changed (store.save may raise)
        try:
            if hasattr(rag_pipeline.store, "save"):
                rag_pipeline.store.save()
                logger.info("Index saved to disk.")
        except Exception as e:
            # Non-fatal: log and continue, but inform caller
            logger.warning("Failed to save index to disk: %s", e)

        # Create L1 summary (wrap the summarizer)
        full_text = "\n".join(c.get("text", "") for c in chunks if isinstance(c, dict))
        try:
            summary = ingest.summarize_text(full_text, target_ratio=target_ratio, api_key=config.GOOGLE_API_KEY)
            if not isinstance(summary, str):
                summary = str(summary)
        except Exception as e:
            logger.exception("Summarization failed: %s", e)
            # Fallback: produce a simple extractive short summary
            logger.info("Falling back to extractive summary (first 1000 chars).")
            summary = (full_text[:1000] + "...") if full_text else ""

        # Save summary to disk
        out_path = os.path.join(L1_DIR, "summary_L1.txt")
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(summary)
        except Exception as e:
            logger.exception("Failed to write summary file: %s", e)
            out_path = None  # indicate not saved

        processing_time = time.time() - start_time
        logger.info("Ingestion completed in %.2f seconds", processing_time)

        return {
            "status": "ok",
            "chunks": len(chunks),
            "vectors_added": vectors_added,
            "summary_file": out_path,
            "processing_time": processing_time,
            "summary_length": len(summary),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Ingestion endpoint error: %s", e)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")


# -----------------------
# Query endpoints
# -----------------------
@app.post("/query")
async def query_server1(request: QueryRequest):
    """
    Query the full document index.
    Returns whatever rag_pipeline.answer() returns (must be JSON-serializable).
    """
    try:
        rag_pipeline = await get_rag_pipeline()
        result = rag_pipeline.answer(
            request.question,
            top_k=request.top_k,
            max_output_tokens=request.max_output_tokens
        )
        # Ensure JSON serializable; if not, coerce
        if not isinstance(result, (dict, list, str, int, float, type(None))):
            result = {"result": str(result)}
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Query failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")


@app.get("/query/{question}")
@app.post("/query/{question}")
async def query_server1_legacy(question: str):
    """
    Backward-compatible endpoint that accepts question in path.
    """
    req = QueryRequest(question=question)
    return await query_server1(req)
