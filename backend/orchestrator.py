"""
Advanced Multi-Level Summarization Orchestrator V2 (fixed)
"""
import asyncio
import logging
import time
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# --- API Models ---
class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5
    max_output_tokens: Optional[int] = 1024
    target_server: Optional[str] = None


# --- Enums and Data Classes ---
class QueryComplexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


@dataclass
class ServerConfig:
    name: str
    url: str
    level: int
    description: str


# --- Core Logic Components ---
class QueryAnalyzer:
    KEYWORD_MAP = {
        QueryComplexity.COMPREHENSIVE: {"comprehensive", "full document", "entire policy"},
        QueryComplexity.DETAILED: {"detailed", "section", "specific", "what are the"},
        QueryComplexity.MODERATE: {"summary", "overview", "describe", "explain"},
        QueryComplexity.SIMPLE: {"key points", "bullet points", "concise", "short"},
    }

    @classmethod
    def analyze_query(cls, query: str) -> Tuple[QueryComplexity, float]:
        query_lower = (query or "").lower()
        # Prefer more specific matches first (comprehensive/detailed)
        order = [
            QueryComplexity.COMPREHENSIVE,
            QueryComplexity.DETAILED,
            QueryComplexity.MODERATE,
            QueryComplexity.SIMPLE,
        ]
        for complexity in order:
            keywords = cls.KEYWORD_MAP.get(complexity, set())
            if any(kw in query_lower for kw in keywords):
                return complexity, 0.85
        return QueryComplexity.MODERATE, 0.4


class ServerManager:
    def __init__(self):
        self.servers: Dict[str, ServerConfig] = {
            "server1": ServerConfig(name="Server 1", url="http://localhost:8001", level=1, description="Full document index"),
            "server2": ServerConfig(name="Server 2", url="http://localhost:8002", level=2, description="Detailed summary index"),
            "server3": ServerConfig(name="Server 3", url="http://localhost:8003", level=3, description="Key points index"),
        }
        # default timeout for query_server
        self.timeout = httpx.Timeout(60.0)

    async def get_server_health(self, server_name: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        cfg = self.servers.get(server_name)
        if cfg is None:
            logger.warning("Health requested for unknown server: %s", server_name)
            return False, None

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{cfg.url.rstrip('/')}/health")
                # Safe parse
                try:
                    body = res.json() if res.content else None
                except Exception:
                    body = {"raw_text": res.text}
                return res.status_code == 200, body
        except Exception as exc:
            logger.debug("Health check error for %s: %s", server_name, exc)
            return False, None

    async def query_server(self, server_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        cfg = self.servers.get(server_name)
        if cfg is None:
            raise HTTPException(status_code=400, detail=f"Unknown server '{server_name}'")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{cfg.url.rstrip('/')}/query", json=payload)
                response.raise_for_status()
                # response.json() can raise; guard it
                try:
                    return response.json()
                except Exception:
                    return {"raw_text": response.text}
        except httpx.HTTPStatusError as e:
            # Attempt to extract meaningful detail if possible
            detail = None
            try:
                detail = e.response.json()
            except Exception:
                detail = {"status_text": e.response.text}
            # wrap as HTTPException so FastAPI can handle it smoothly
            raise HTTPException(status_code=e.response.status_code, detail=detail)
        except httpx.RequestError as e:
            logger.error("RequestError when contacting %s: %s", server_name, e)
            raise HTTPException(status_code=503, detail=f"{server_name} is unavailable: {str(e)}")


class IntelligentRouter:
    def __init__(self, server_manager: ServerManager):
        self.server_manager = server_manager
        self.query_analyzer = QueryAnalyzer()

    def select_primary_server(self, complexity: QueryComplexity) -> str:
        mapping = {
            QueryComplexity.SIMPLE.value: "server3",
            QueryComplexity.MODERATE.value: "server2",
            # default for detailed/comprehensive -> server1
        }
        return mapping.get(complexity.value, "server1")

    async def route_query(self, request: QueryRequest) -> Dict[str, Any]:
        # If the client specified a target server, use it (but validate)
        target = request.target_server
        complexity, confidence = self.query_analyzer.analyze_query(request.question)

        if not target or target not in self.server_manager.servers:
            target = self.select_primary_server(complexity)
            logger.info("Analyzed as %s, routing to %s", complexity.value, target)
        else:
            logger.info("Manual override to %s", target)

        # Build payload robustly (support pydantic v1 & v2)
        if hasattr(request, "model_dump"):
            payload = request.model_dump()
        else:
            # fallback to pydantic v1 .dict()
            payload = request.dict()

        # Try primary, then fallback mapping
        try:
            result = await self.server_manager.query_server(target, payload)
            # ensure it's a dict
            if not isinstance(result, dict):
                result = {"result": result}
            result["routing_info"] = {"primary_server": target, "complexity": complexity.value, "confidence": confidence}
            return result
        except HTTPException as outer_exc:
            # If primary server fails, attempt sensible fallback
            logger.warning("Primary server %s failed with: %s. Attempting fallback.", target, outer_exc.detail)
            fallback_map = {"server1": "server2", "server2": "server1", "server3": "server2"}
            fallback = fallback_map.get(target, "server1")
            try:
                result = await self.server_manager.query_server(fallback, payload)
                if not isinstance(result, dict):
                    result = {"result": result}
                result["routing_info"] = {"primary_server": target, "fallback_server": fallback, "complexity": complexity.value, "confidence": confidence}
                return result
            except HTTPException as exc2:
                # Both primary and fallback failed -> surface error
                logger.error("Fallback server %s also failed: %s", fallback, exc2.detail)
                raise HTTPException(status_code=503, detail={"error": "Both primary and fallback servers failed", "primary_error": outer_exc.detail, "fallback_error": exc2.detail})


# --- FastAPI App Setup ---
app = FastAPI(title="Advanced Summarization Orchestrator", version="2.0.0")
server_manager = ServerManager()
router = IntelligentRouter(server_manager)

# allow development origin; adapt in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- API Endpoints ---
@app.get("/health")
async def health_check():
    """Simple health check for the orchestrator itself."""
    return {"status": "ok", "service": "Orchestrator"}


@app.get("/system/health")
async def get_system_health():
    """Provides a consolidated health status of all downstream servers."""
    # prepare coroutines in insertion order
    tasks = [server_manager.get_server_health(n) for n in server_manager.servers.keys()]
    results = await asyncio.gather(*tasks)

    statuses = {}
    healthy_count = 0
    for (name, cfg), (running, data) in zip(server_manager.servers.items(), results):
        if running:
            healthy_count += 1
        # extract port safely (may not exist)
        port = None
        try:
            # naive attempt to get final part after last ':'
            port = cfg.url.rsplit(":", 1)[-1]
        except Exception:
            port = cfg.url
        statuses[name] = {"name": cfg.name, "port": port, "description": cfg.description, "running": running, "health": data}

    overall = "degraded"
    if healthy_count == len(statuses):
        overall = "healthy"
    elif healthy_count == 0:
        overall = "unhealthy"

    return {"timestamp": time.time(), "servers": statuses, "overall_health": overall, "healthy_count": healthy_count, "total_count": len(statuses)}


@app.post("/ingest")
async def ingest_documents(request: Request):
    """Forwards ingestion requests to Server 1."""
    cfg = server_manager.servers.get("server1")
    if cfg is None:
        raise HTTPException(status_code=500, detail="Ingestion server not configured.")

    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON body: {e}")

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            res = await client.post(f"{cfg.url.rstrip('/')}/ingest", json=body)
            # try to forward body and status code transparently
            try:
                content = res.json() if res.content else None
            except Exception:
                content = {"raw_text": res.text}
            return JSONResponse(status_code=res.status_code, content=content)
    except httpx.RequestError as e:
        logger.error("Ingestion request to server1 failed: %s", e)
        raise HTTPException(status_code=503, detail=f"Ingestion failed: {e}")


@app.post("/query")
async def intelligent_query(request: QueryRequest):
    """Handles intelligent query routing and returns the result."""
    result = await router.route_query(request)
    # Return as JSONResponse to avoid FastAPI double-encoding possible HTTPException content
    return JSONResponse(content=result)
