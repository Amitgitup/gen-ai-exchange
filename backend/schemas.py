from pydantic import BaseModel, Field
from typing import List, Optional, Any


class IngestRequest(BaseModel):
    force_rebuild: bool = Field(False, description="If true, re-create the index from scratch")


class IngestResponse(BaseModel):
    files_processed: int
    chunks_added: int
    vectors: int
    message: str


class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = None
    max_output_tokens: Optional[int] = 512


class Citation(BaseModel):
    source_file: str
    page_start: int
    page_end: int
    score: float
    snippet: str


class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]
    used_top_k: int
    prompt: str


class StatsResponse(BaseModel):
    vectors: int
    files_indexed: int
    index_path: str
    metadata_path: str
    index_exists: bool
    last_modified: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    stats: StatsResponse
