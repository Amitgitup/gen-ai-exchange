"""
Enhanced Configuration for Multi-Level Summarization System

This module provides comprehensive configuration management for the
hierarchical document summarization system.
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class ServerConfig:
    """Configuration for individual summarization servers"""
    name: str
    port: int
    compression_ratio: float
    max_tokens: int
    top_k: int
    description: str


@dataclass
class SystemConfig:
    """Overall system configuration"""
    # API Configuration
    google_api_key: str
    
    # Model Configuration
    embedding_model: str
    gemini_model: str
    
    # Chunking Configuration
    chunk_size: int
    chunk_overlap: int
    
    # Server Configuration
    servers: Dict[str, ServerConfig]
    
    # Paths
    pdfs_dir: str
    summaries_dir: str
    index_dir: str
    
    # Performance
    timeout: float
    max_retries: int


class ConfigManager:
    """Manages configuration for the multi-server system"""
    
    def __init__(self, env_file: Optional[str] = None):
        # Load environment variables
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to load from backend directory
            backend_dir = os.path.dirname(__file__)
            env_path = os.path.join(backend_dir, ".env")
            if os.path.exists(env_path):
                load_dotenv(env_path)
        
        self._config = self._load_config()
    
    def _load_config(self) -> SystemConfig:
        """Load configuration from environment variables"""
        
        # Resolve paths relative to this file's directory
        _backend_dir = os.path.dirname(__file__)
        _root_dir = os.path.dirname(_backend_dir)
        
        # Base directories
        pdfs_dir = os.getenv(
            "PDFS_DIR",
            os.path.normpath(os.path.join(_backend_dir, "pdfs"))
        )
        
        summaries_dir = os.path.join(pdfs_dir, "summaries")
        index_dir = os.getenv(
            "INDEX_DIR",
            os.path.normpath(os.path.join(_root_dir, "experiment"))
        )
        
        # Ensure directories exist
        os.makedirs(pdfs_dir, exist_ok=True)
        os.makedirs(summaries_dir, exist_ok=True)
        os.makedirs(index_dir, exist_ok=True)
        
        # Server configurations
        servers = {
            "server1": ServerConfig(
                name="server1",
                port=int(os.getenv("SERVER1_PORT", "8001")),
                compression_ratio=float(os.getenv("SERVER1_COMPRESSION", "0.1")),
                max_tokens=int(os.getenv("SERVER1_MAX_TOKENS", "1024")),
                top_k=int(os.getenv("SERVER1_TOP_K", "8")),
                description="Full document ingestion and L1 summary"
            ),
            "server2": ServerConfig(
                name="server2",
                port=int(os.getenv("SERVER2_PORT", "8002")),
                compression_ratio=float(os.getenv("SERVER2_COMPRESSION", "0.2")),
                max_tokens=int(os.getenv("SERVER2_MAX_TOKENS", "512")),
                top_k=int(os.getenv("SERVER2_TOP_K", "5")),
                description="L2 summary (moderate compression)"
            ),
            "server3": ServerConfig(
                name="server3",
                port=int(os.getenv("SERVER3_PORT", "8003")),
                compression_ratio=float(os.getenv("SERVER3_COMPRESSION", "0.1")),
                max_tokens=int(os.getenv("SERVER3_MAX_TOKENS", "256")),
                top_k=int(os.getenv("SERVER3_TOP_K", "3")),
                description="L3 ultra-summary (high compression)"
            ),
            "orchestrator": ServerConfig(
                name="orchestrator",
                port=int(os.getenv("ORCHESTRATOR_PORT", "8000")),
                compression_ratio=0.0,  # Not applicable
                max_tokens=int(os.getenv("ORCHESTRATOR_MAX_TOKENS", "512")),
                top_k=int(os.getenv("ORCHESTRATOR_TOP_K", "5")),
                description="Intelligent query router"
            )
        }
        
        return SystemConfig(
            google_api_key=os.getenv("GOOGLE_API_KEY", ""),
            embedding_model=os.getenv("EMBEDDING_MODEL", "models/text-embedding-004"),
            gemini_model=os.getenv("GEMINI_MODEL", "models/gemini-1.5-flash"),
            chunk_size=int(os.getenv("CHUNK_SIZE", "1200")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
            servers=servers,
            pdfs_dir=pdfs_dir,
            summaries_dir=summaries_dir,
            index_dir=index_dir,
            timeout=float(os.getenv("REQUEST_TIMEOUT", "30.0")),
            max_retries=int(os.getenv("MAX_RETRIES", "3"))
        )
    
    @property
    def config(self) -> SystemConfig:
        """Get the current configuration"""
        return self._config
    
    def get_server_config(self, server_name: str) -> Optional[ServerConfig]:
        """Get configuration for a specific server"""
        return self._config.servers.get(server_name)
    
    def get_server_url(self, server_name: str) -> str:
        """Get URL for a specific server"""
        server_config = self.get_server_config(server_name)
        if not server_config:
            raise ValueError(f"Unknown server: {server_name}")
        return f"http://localhost:{server_config.port}"
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return any errors"""
        errors = []
        
        # Check API key
        if not self._config.google_api_key:
            errors.append("GOOGLE_API_KEY is required")
        
        # Check port conflicts
        ports = [server.port for server in self._config.servers.values()]
        if len(ports) != len(set(ports)):
            errors.append("Server ports must be unique")
        
        # Check compression ratios
        for name, server in self._config.servers.items():
            if name != "orchestrator" and not (0 < server.compression_ratio <= 1):
                errors.append(f"Server {name} compression ratio must be between 0 and 1")
        
        # Check directories
        for dir_name, dir_path in [
            ("PDFs", self._config.pdfs_dir),
            ("Summaries", self._config.summaries_dir),
            ("Index", self._config.index_dir)
        ]:
            if not os.path.exists(dir_path):
                errors.append(f"{dir_name} directory does not exist: {dir_path}")
        
        return errors
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary"""
        return {
            "google_api_key": "***" if self._config.google_api_key else "",
            "embedding_model": self._config.embedding_model,
            "gemini_model": self._config.gemini_model,
            "chunk_size": self._config.chunk_size,
            "chunk_overlap": self._config.chunk_overlap,
            "servers": {
                name: {
                    "name": server.name,
                    "port": server.port,
                    "compression_ratio": server.compression_ratio,
                    "max_tokens": server.max_tokens,
                    "top_k": server.top_k,
                    "description": server.description
                }
                for name, server in self._config.servers.items()
            },
            "paths": {
                "pdfs_dir": self._config.pdfs_dir,
                "summaries_dir": self._config.summaries_dir,
                "index_dir": self._config.index_dir
            },
            "performance": {
                "timeout": self._config.timeout,
                "max_retries": self._config.max_retries
            }
        }


# Global configuration instance
config_manager = ConfigManager()

# Backward compatibility - expose the config object
config = config_manager.config

# Export commonly used values for backward compatibility
GOOGLE_API_KEY = config.google_api_key
EMBEDDING_MODEL = config.embedding_model
GEMINI_MODEL = config.gemini_model
CHUNK_SIZE = config.chunk_size
CHUNK_OVERLAP = config.chunk_overlap
PDFS_DIR = config.pdfs_dir
INDEX_DIR = config.index_dir
TOP_K_DEFAULT = 5  # Default for backward compatibility

# Filenames for persistence
INDEX_FILE = os.path.join(INDEX_DIR, "jharkhand_faiss.index")
META_FILE = os.path.join(INDEX_DIR, "jharkhand_metadata.json")
