# server3.py
import logging
import os
import time
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend import config
from backend.rag import EmbeddingsClient, GeminiClient, RAGPipeline
from backend.vectorstore import FaissStore
from backend.schemas import StatsResponse, HealthResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Server 3 - L3 Summary (Ultra-condensed)", version="1.0.0")

L3_DIR = os.path.join(config.PDFS_DIR, "summaries", "L3")
os.makedirs(L3_DIR, exist_ok=True)

INDEX_PATH = "server3_index.faiss"
META_PATH = "server3_meta.json"

# Global state
_initialized = False
_store = None
_rag = None

class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 3
    max_output_tokens: Optional[int] = 256

def get_rag_pipeline() -> RAGPipeline:
    """Lazy initialization of RAG pipeline"""
    global _rag, _store, _initialized
    
    if not _initialized:
        try:
            logger.info("Initializing Server 3 RAG pipeline...")
            embedder = EmbeddingsClient(model_name="models/embedding-001", api_key=config.GOOGLE_API_KEY)
            llm = GeminiClient(model_name="gemini-1.5-flash", api_key=config.GOOGLE_API_KEY)
            _store = FaissStore(INDEX_PATH, META_PATH)
            _store.load()
            _rag = RAGPipeline(_store, embedder, llm)
            _initialized = True
            logger.info("Server 3 RAG pipeline initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {e}")
            raise HTTPException(status_code=500, detail=f"RAG initialization failed: {str(e)}")
    
    return _rag


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

@app.post("/summarize_l2")
async def summarize_l2():
    """Consumes L2 summary → produces L3 ultra-summary (~1/10th of L2)."""
    try:
        logger.info("Starting L2 to L3 summarization...")
        start_time = time.time()
        
        l2_file = os.path.join(config.PDFS_DIR, "summaries", "L2", "summary_L2.txt")
        if not os.path.exists(l2_file):
            raise HTTPException(status_code=404, detail="No L2 summary found. Run Server2 first.")

        with open(l2_file, "r", encoding="utf-8") as f:
            l2_text = f.read()
        
        logger.info(f"L2 text length: {len(l2_text)} characters")

        # Summarize further (~10% of L2 length, super-condensed bullet points)
        rag_pipeline = get_rag_pipeline()
        summary = rag_pipeline.llm.summarize(l2_text, target_ratio=0.1)
        
        logger.info(f"L3 summary length: {len(summary)} characters")

        out_path = os.path.join(L3_DIR, "summary_L3.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(summary)
        
        processing_time = time.time() - start_time
        logger.info(f"L3 summarization completed in {processing_time:.2f} seconds")

        return {
            "status": "ok", 
            "summary_file": out_path,
            "processing_time": processing_time,
            "l2_length": len(l2_text),
            "l3_length": len(summary),
            "compression_ratio": len(summary) / len(l2_text) if l2_text else 0
        }
    except Exception as e:
        logger.error(f"L3 summarization failed: {e}")
        raise HTTPException(status_code=500, detail=f"L3 summarization failed: {str(e)}")


@app.post("/query")
async def query_server3(request: QueryRequest):
    """Query the ultra-condensed summary"""
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
async def query_server3_legacy(question: str):
    """Legacy query endpoint for backward compatibility"""
    request = QueryRequest(question=question)
    return await query_server3(request)
