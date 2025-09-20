# server1.py
import logging
import os
import time
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend import ingest, config
from backend.rag import EmbeddingsClient, GeminiClient, RAGPipeline
from backend.vectorstore import FaissStore
from backend.schemas import StatsResponse, HealthResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Server 1 - Ingestion + L1 Summary", version="1.0.0")

# Paths
RAW_DIR = os.path.join(config.PDFS_DIR, "raw")
L1_DIR = os.path.join(config.PDFS_DIR, "summaries", "L1")
os.makedirs(L1_DIR, exist_ok=True)

INDEX_PATH = "server1_index.faiss"
META_PATH = "server1_meta.json"

# Global state
_initialized = False
_store = None
_rag = None

def get_rag_pipeline() -> RAGPipeline:
    """Lazy initialization of RAG pipeline"""
    global _rag, _store, _initialized
    
    if not _initialized:
        try:
            logger.info("Initializing Server 1 RAG pipeline...")
            embedder = EmbeddingsClient(model_name="models/embedding-001", api_key=config.GOOGLE_API_KEY)
            llm = GeminiClient(model_name="gemini-1.5-flash", api_key=config.GOOGLE_API_KEY)
            _store = FaissStore(INDEX_PATH, META_PATH)
            _store.load()
            _rag = RAGPipeline(_store, embedder, llm)
            _initialized = True
            logger.info("Server 1 RAG pipeline initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {e}")
            raise HTTPException(status_code=500, detail=f"RAG initialization failed: {str(e)}")
    
    return _rag

class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5
    max_output_tokens: Optional[int] = 1024


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    try:
        rag_pipeline = get_rag_pipeline()
        stats = rag_pipeline.store.stats()
        return HealthResponse(
            status="ok",
            stats=StatsResponse(**stats)
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="error",
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
    """Get server statistics"""
    try:
        rag_pipeline = get_rag_pipeline()
        return StatsResponse(**rag_pipeline.store.stats())
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest")
async def ingest_and_summarize():
    """Ingest PDFs and create L1 summary"""
    try:
        logger.info("Starting ingestion process...")
        start_time = time.time()
        
        # Ingest PDFs
        chunks = ingest.ingest_pdfs(RAW_DIR)
        logger.info(f"Extracted {len(chunks)} chunks from PDFs")
        
        # Build RAG index
        rag_pipeline = get_rag_pipeline()
        vectors_added = rag_pipeline.build_index(chunks)
        logger.info(f"Added {vectors_added} vectors to index")

        # Create L1 summary
        full_text = "\n".join(c["text"] for c in chunks)
        logger.info("Generating L1 summary...")
        summary = ingest.summarize_text(full_text, target_ratio=0.1, api_key=config.GOOGLE_API_KEY)

        # Save summary
        out_path = os.path.join(L1_DIR, "summary_L1.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(summary)
        
        processing_time = time.time() - start_time
        logger.info(f"Ingestion completed in {processing_time:.2f} seconds")
        
        return {
            "status": "ok", 
            "chunks": len(chunks),
            "vectors_added": vectors_added,
            "summary_file": out_path,
            "processing_time": processing_time,
            "summary_length": len(summary)
        }
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/query")
async def query_server1(request: QueryRequest):
    """Query the full document index"""
    try:
        rag_pipeline = get_rag_pipeline()
        result = rag_pipeline.answer(
            request.question, 
            top_k=request.top_k, 
            max_output_tokens=request.max_output_tokens
        )
        return result
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.post("/query/{question}")
async def query_server1_legacy(question: str):
    """Legacy query endpoint for backward compatibility"""
    request = QueryRequest(question=question)
    return await query_server1(request)
