# # server2.py
# import logging
# import os
# import time
# from typing import Dict, Any, Optional

# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel

# from backend import config
# from backend.rag import EmbeddingsClient, GeminiClient, RAGPipeline
# from backend.vectorstore import FaissStore
# from backend.schemas import StatsResponse, HealthResponse

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI(title="Server 2 - L2 Summary", version="1.0.0")

# L2_DIR = os.path.join(config.PDFS_DIR, "summaries", "L2")
# os.makedirs(L2_DIR, exist_ok=True)

# INDEX_PATH = "server2_index.faiss"
# META_PATH = "server2_meta.json"

# # Global state
# _initialized = False
# _store = None
# _rag = None

# class QueryRequest(BaseModel):
#     question: str
#     top_k: Optional[int] = 5
#     max_output_tokens: Optional[int] = 512

# def get_rag_pipeline() -> RAGPipeline:
#     """Lazy initialization of RAG pipeline"""
#     global _rag, _store, _initialized
    
#     if not _initialized:
#         try:
#             logger.info("Initializing Server 2 RAG pipeline...")
#             embedder = EmbeddingsClient(model_name="models/embedding-001", api_key=config.GOOGLE_API_KEY)
#             llm = GeminiClient(model_name="gemini-1.5-flash", api_key=config.GOOGLE_API_KEY)
#             _store = FaissStore(INDEX_PATH, META_PATH)
#             _store.load()
#             _rag = RAGPipeline(_store, embedder, llm)
#             _initialized = True
#             logger.info("Server 2 RAG pipeline initialized successfully")
#         except Exception as e:
#             logger.error(f"Failed to initialize RAG pipeline: {e}")
#             raise HTTPException(status_code=500, detail=f"RAG initialization failed: {str(e)}")
    
#     return _rag


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

# @app.post("/summarize_l1")
# async def summarize_l1():
#     """Takes L1 summaries → produces L2 summary (~1/5th of L1)."""
#     try:
#         logger.info("Starting L1 to L2 summarization...")
#         start_time = time.time()
        
#         l1_file = os.path.join(config.PDFS_DIR, "summaries", "L1", "summary_L1.txt")
#         if not os.path.exists(l1_file):
#             raise HTTPException(status_code=404, detail="No L1 summary found. Run Server1 first.")

#         with open(l1_file, "r", encoding="utf-8") as f:
#             l1_text = f.read()
        
#         logger.info(f"L1 text length: {len(l1_text)} characters")

#         # Summarize further (e.g. ~20% length of L1)
#         rag_pipeline = get_rag_pipeline()
#         summary = rag_pipeline.llm.summarize(l1_text, target_ratio=0.2)
        
#         logger.info(f"L2 summary length: {len(summary)} characters")

#         out_path = os.path.join(L2_DIR, "summary_L2.txt")
#         with open(out_path, "w", encoding="utf-8") as f:
#             f.write(summary)
        
#         processing_time = time.time() - start_time
#         logger.info(f"L2 summarization completed in {processing_time:.2f} seconds")

#         return {
#             "status": "ok", 
#             "summary_file": out_path,
#             "processing_time": processing_time,
#             "l1_length": len(l1_text),
#             "l2_length": len(summary),
#             "compression_ratio": len(summary) / len(l1_text) if l1_text else 0
#         }
#     except Exception as e:
#         logger.error(f"L2 summarization failed: {e}")
#         raise HTTPException(status_code=500, detail=f"L2 summarization failed: {str(e)}")


# @app.post("/query")
# async def query_server2(request: QueryRequest):
#     """Query the L2 summary index"""
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
# async def query_server2_legacy(question: str):
#     """Legacy query endpoint for backward compatibility"""
#     request = QueryRequest(question=question)
#     return await query_server2(request)

# server2.py (Corrected)
import logging
import os
import time
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend import config
from backend.rag import EmbeddingsClient, GeminiClient, RAGPipeline
from backend.vectorstore import FaissStore
from backend.schemas import StatsResponse, HealthResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Server 2 - L2 Summary", version="1.0.0")

# DEFINE YOUR ALLOWED ORIGINS
origins = [
    "http://localhost:3000",
    # You might want to add your production frontend URL here as well
    # e.g., "https://your-app-name.vercel.app"
]

# ADD THE MIDDLEWARE TO YOUR APP
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

L2_DIR = os.path.join(config.PDFS_DIR, "summaries", "L2")
os.makedirs(L2_DIR, exist_ok=True)

INDEX_PATH = "server2_index.faiss"
META_PATH = "server2_meta.json"

# Global state
_initialized = False
_store = None
_rag = None

class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5
    max_output_tokens: Optional[int] = 512

def get_rag_pipeline() -> RAGPipeline:
    """Lazy initialization of RAG pipeline"""
    global _rag, _store, _initialized
    
    if not _initialized:
        try:
            logger.info("Initializing Server 2 RAG pipeline...")
            embedder = EmbeddingsClient(model_name="models/embedding-001", api_key=config.GOOGLE_API_KEY)
            llm = GeminiClient(model_name="gemini-1.5-flash", api_key=config.GOOGLE_API_KEY)
            _store = FaissStore(INDEX_PATH, META_PATH)
            _store.load()
            _rag = RAGPipeline(_store, embedder, llm)
            _initialized = True
            logger.info("Server 2 RAG pipeline initialized successfully")
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

@app.post("/summarize_l1")
async def summarize_l1():
    """Takes L1 summaries → produces L2 summary (~1/5th of L1) and indexes it."""
    try:
        logger.info("Starting L1 to L2 summarization...")
        start_time = time.time()
        
        l1_file = os.path.join(config.PDFS_DIR, "summaries", "L1", "summary_L1.txt")
        if not os.path.exists(l1_file):
            raise HTTPException(status_code=404, detail="No L1 summary found. Run Server1 first.")

        with open(l1_file, "r", encoding="utf-8") as f:
            l1_text = f.read()
        
        logger.info(f"L1 text length: {len(l1_text)} characters")

        rag_pipeline = get_rag_pipeline()
        
        # Summarize further (e.g. ~20% length of L1)
        summary = rag_pipeline.llm.summarize(l1_text, target_ratio=0.2)
        logger.info(f"L2 summary length: {len(summary)} characters")
        
        # Save summary text file
        out_path = os.path.join(L2_DIR, "summary_L2.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(summary)
            
        # --- FIX: Index the newly created summary ---
        logger.info("Indexing the L2 summary...")
        summary_chunks = [{
            "text": summary,
            "metadata": {"source": "summary_L2.txt"}
        }]
        vectors_added = rag_pipeline.build_index(summary_chunks)
        rag_pipeline.store.save()
        logger.info(f"Added {vectors_added} vectors to Server 2 index. Index saved.")
        # ---------------------------------------------
        
        processing_time = time.time() - start_time
        logger.info(f"L2 summarization completed in {processing_time:.2f} seconds")

        return {
            "status": "ok", 
            "summary_file": out_path,
            "vectors_added": vectors_added,
            "processing_time": processing_time,
            "l1_length": len(l1_text),
            "l2_length": len(summary),
            "compression_ratio": len(summary) / len(l1_text) if l1_text else 0
        }
    except Exception as e:
        logger.error(f"L2 summarization failed: {e}")
        raise HTTPException(status_code=500, detail=f"L2 summarization failed: {str(e)}")


@app.post("/query")
async def query_server2(request: QueryRequest):
    """Query the L2 summary index"""
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
async def query_server2_legacy(question: str):
    """Legacy query endpoint for backward compatibility"""
    request = QueryRequest(question=question)
    return await query_server2(request)