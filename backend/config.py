import os
from dotenv import load_dotenv

# Resolve paths relative to this file's directory
_BACKEND_DIR = os.path.dirname(__file__)
_ROOT_DIR = os.path.dirname(_BACKEND_DIR)

# Load .env from backend directory (works regardless of CWD)
load_dotenv(os.path.join(_BACKEND_DIR, ".env"))

# Directories
INDEX_DIR = os.getenv(
    "INDEX_DIR",
    os.path.normpath(os.path.join(_ROOT_DIR, "experiment"))
)

# Base PDFs directory (servers will build subpaths from this)
PDFS_DIR = os.getenv(
    "PDFS_DIR",
    os.path.normpath(os.path.join(_BACKEND_DIR, "pdfs"))
)

# Models
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-1.5-flash")

# Chunking
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1200"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

# Retrieval
TOP_K_DEFAULT = int(os.getenv("TOP_K", "6"))

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Filenames for persistence
INDEX_FILE = os.path.join(INDEX_DIR, "jharkhand_faiss.index")
META_FILE = os.path.join(INDEX_DIR, "jharkhand_metadata.json")

# Ensure base directories exist
os.makedirs(INDEX_DIR, exist_ok=True)
os.makedirs(PDFS_DIR, exist_ok=True)
