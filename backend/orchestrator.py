"""
Advanced Multi-Level Summarization Orchestrator

This module provides intelligent query routing and server management
for the hierarchical summarization system.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend import config
from backend.schemas import QueryRequest, QueryResponse, Citation


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryComplexity(Enum):
    """Query complexity levels for routing decisions"""
    SIMPLE = "simple"          # High-level overview, key points
    MODERATE = "moderate"      # Summary, overview questions
    DETAILED = "detailed"      # Specific facts, detailed information
    COMPREHENSIVE = "comprehensive"  # Full document analysis


@dataclass
class ServerConfig:
    """Configuration for each summarization server"""
    name: str
    url: str
    level: int
    compression_ratio: float
    description: str
    max_tokens: int = 512
    top_k: int = 5


class QueryAnalyzer:
    """Analyzes queries to determine complexity and routing strategy"""
    
    SIMPLE_KEYWORDS = {
        "key points", "bullet", "concise", "short", "brief", "overview",
        "main points", "highlights", "summary", "gist", "essence"
    }
    
    MODERATE_KEYWORDS = {
        "summary", "overview", "brief", "describe", "explain", "what is",
        "tell me about", "give me", "provide", "outline"
    }
    
    DETAILED_KEYWORDS = {
        "detailed", "full", "section", "law", "policy", "regulation",
        "specific", "exact", "precise", "complete", "entire", "all",
        "how does", "what are the", "explain in detail", "step by step"
    }
    
    COMPREHENSIVE_KEYWORDS = {
        "comprehensive", "complete analysis", "full document", "everything",
        "entire policy", "all aspects", "thorough", "exhaustive"
    }
    
    @classmethod
    def analyze_query(cls, query: str) -> Tuple[QueryComplexity, float]:
        """
        Analyze query to determine complexity level and confidence score
        
        Returns:
            Tuple of (complexity_level, confidence_score)
        """
        query_lower = query.lower()
        
        # Check for comprehensive queries
        comprehensive_matches = sum(1 for kw in cls.COMPREHENSIVE_KEYWORDS if kw in query_lower)
        if comprehensive_matches > 0:
            return QueryComplexity.COMPREHENSIVE, min(0.9, 0.6 + comprehensive_matches * 0.1)
        
        # Check for detailed queries
        detailed_matches = sum(1 for kw in cls.DETAILED_KEYWORDS if kw in query_lower)
        if detailed_matches > 0:
            return QueryComplexity.DETAILED, min(0.9, 0.5 + detailed_matches * 0.1)
        
        # Check for moderate queries
        moderate_matches = sum(1 for kw in cls.MODERATE_KEYWORDS if kw in query_lower)
        if moderate_matches > 0:
            return QueryComplexity.MODERATE, min(0.8, 0.4 + moderate_matches * 0.1)
        
        # Check for simple queries
        simple_matches = sum(1 for kw in cls.SIMPLE_KEYWORDS if kw in query_lower)
        if simple_matches > 0:
            return QueryComplexity.SIMPLE, min(0.8, 0.3 + simple_matches * 0.1)
        
        # Default to moderate for ambiguous queries
        return QueryComplexity.MODERATE, 0.3


class ServerManager:
    """Manages communication with summarization servers"""
    
    def __init__(self):
        self.servers = {
            "server1": ServerConfig(
                name="server1",
                url="http://localhost:8001",
                level=1,
                compression_ratio=0.1,
                description="Full document ingestion and L1 summary",
                max_tokens=1024,
                top_k=8
            ),
            "server2": ServerConfig(
                name="server2", 
                url="http://localhost:8002",
                level=2,
                compression_ratio=0.2,
                description="L2 summary (moderate compression)",
                max_tokens=512,
                top_k=5
            ),
            "server3": ServerConfig(
                name="server3",
                url="http://localhost:8003", 
                level=3,
                compression_ratio=0.1,
                description="L3 ultra-summary (high compression)",
                max_tokens=256,
                top_k=3
            )
        }
        self.timeout = httpx.Timeout(30.0)
    
    async def check_server_health(self, server_name: str) -> bool:
        """Check if a server is healthy and responsive"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.servers[server_name].url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Server {server_name} health check failed: {e}")
            return False
    
    async def query_server(self, server_name: str, question: str, 
                          top_k: Optional[int] = None, 
                          max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Query a specific server with the question"""
        server = self.servers[server_name]
        
        params = {
            "question": question,
            "top_k": top_k or server.top_k,
            "max_output_tokens": max_tokens or server.max_tokens
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{server.url}/query",
                    params=params
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error querying {server_name}: {e}")
            raise HTTPException(status_code=e.response.status_code, 
                              detail=f"Server {server_name} returned error: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error querying {server_name}: {e}")
            raise HTTPException(status_code=503, 
                              detail=f"Server {server_name} is unavailable: {str(e)}")
    
    async def get_server_stats(self, server_name: str) -> Dict[str, Any]:
        """Get statistics from a specific server"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.servers[server_name].url}/stats")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to get stats from {server_name}: {e}")
            return {"error": str(e)}


class IntelligentRouter:
    """Intelligent query routing with fallback strategies"""
    
    def __init__(self, server_manager: ServerManager):
        self.server_manager = server_manager
        self.query_analyzer = QueryAnalyzer()
    
    def select_primary_server(self, complexity: QueryComplexity) -> str:
        """Select the primary server based on query complexity"""
        if complexity == QueryComplexity.SIMPLE:
            return "server3"  # Ultra-compressed summary
        elif complexity == QueryComplexity.MODERATE:
            return "server2"  # Moderate summary
        elif complexity == QueryComplexity.DETAILED:
            return "server1"  # Full document
        else:  # COMPREHENSIVE
            return "server1"  # Full document for comprehensive analysis
    
    def get_fallback_servers(self, primary_server: str) -> List[str]:
        """Get fallback servers in order of preference"""
        fallback_map = {
            "server1": ["server2", "server3"],
            "server2": ["server1", "server3"], 
            "server3": ["server2", "server1"]
        }
        return fallback_map.get(primary_server, ["server1"])
    
    async def route_query(self, question: str, 
                         top_k: Optional[int] = None,
                         max_tokens: Optional[int] = None,
                         use_fallback: bool = True) -> Dict[str, Any]:
        """
        Route query to the most appropriate server with fallback support
        
        Args:
            question: The user's question
            top_k: Number of top results to retrieve
            max_tokens: Maximum tokens for response
            use_fallback: Whether to try fallback servers if primary fails
            
        Returns:
            Response from the selected server
        """
        # Analyze query complexity
        complexity, confidence = self.query_analyzer.analyze_query(question)
        primary_server = self.select_primary_server(complexity)
        
        logger.info(f"Query analysis: {complexity.value} (confidence: {confidence:.2f}) -> {primary_server}")
        
        # Try primary server first
        try:
            result = await self.server_manager.query_server(
                primary_server, question, top_k, max_tokens
            )
            result["routing_info"] = {
                "primary_server": primary_server,
                "complexity": complexity.value,
                "confidence": confidence,
                "fallback_used": False
            }
            return result
        except Exception as e:
            logger.warning(f"Primary server {primary_server} failed: {e}")
            
            if not use_fallback:
                raise e
            
            # Try fallback servers
            fallback_servers = self.get_fallback_servers(primary_server)
            last_error = e
            
            for fallback_server in fallback_servers:
                try:
                    logger.info(f"Trying fallback server: {fallback_server}")
                    result = await self.server_manager.query_server(
                        fallback_server, question, top_k, max_tokens
                    )
                    result["routing_info"] = {
                        "primary_server": primary_server,
                        "fallback_server": fallback_server,
                        "complexity": complexity.value,
                        "confidence": confidence,
                        "fallback_used": True,
                        "fallback_reason": str(last_error)
                    }
                    return result
                except Exception as fallback_error:
                    logger.warning(f"Fallback server {fallback_server} also failed: {fallback_error}")
                    last_error = fallback_error
            
            # All servers failed
            raise HTTPException(
                status_code=503,
                detail=f"All servers failed. Last error: {str(last_error)}"
            )


# Global instances
server_manager = ServerManager()
router = IntelligentRouter(server_manager)


# FastAPI app for the orchestrator
app = FastAPI(
    title="Multi-Level Summarization Orchestrator",
    description="Intelligent query routing for hierarchical document summarization",
    version="2.0.0"
)


@app.get("/health")
async def health_check():
    """Health check for the orchestrator"""
    server_status = {}
    for server_name in server_manager.servers:
        server_status[server_name] = await server_manager.check_server_health(server_name)
    
    healthy_servers = sum(server_status.values())
    total_servers = len(server_status)
    
    return {
        "status": "healthy" if healthy_servers > 0 else "degraded",
        "orchestrator": "ok",
        "servers": server_status,
        "healthy_count": healthy_servers,
        "total_count": total_servers
    }


@app.get("/stats")
async def get_aggregated_stats():
    """Get aggregated statistics from all servers"""
    stats = {}
    for server_name in server_manager.servers:
        stats[server_name] = await server_manager.get_server_stats(server_name)
    
    return {
        "servers": stats,
        "timestamp": time.time(),
        "orchestrator_version": "2.0.0"
    }


@app.post("/query", response_model=QueryResponse)
async def intelligent_query(request: QueryRequest):
    """
    Intelligent query routing with automatic server selection
    """
    try:
        result = await router.route_query(
            question=request.question,
            top_k=request.top_k,
            max_tokens=request.max_output_tokens,
            use_fallback=True
        )
        
        # Convert citations to proper format
        citations = []
        for citation_data in result.get("citations", []):
            citations.append(Citation(**citation_data))
        
        return QueryResponse(
            answer=result.get("answer", ""),
            citations=citations,
            used_top_k=result.get("routing_info", {}).get("top_k", request.top_k or 5),
            prompt=result.get("prompt", "")
        )
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/{server_name}")
async def direct_query(server_name: str, request: QueryRequest):
    """
    Direct query to a specific server (bypasses intelligent routing)
    """
    if server_name not in server_manager.servers:
        raise HTTPException(status_code=404, detail=f"Server {server_name} not found")
    
    try:
        result = await server_manager.query_server(
            server_name, 
            request.question,
            request.top_k,
            request.max_output_tokens
        )
        
        citations = []
        for citation_data in result.get("citations", []):
            citations.append(Citation(**citation_data))
        
        return QueryResponse(
            answer=result.get("answer", ""),
            citations=citations,
            used_top_k=request.top_k or server_manager.servers[server_name].top_k,
            prompt=result.get("prompt", "")
        )
    except Exception as e:
        logger.error(f"Direct query to {server_name} failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
