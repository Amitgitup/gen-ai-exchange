# Advanced Multi-Level Summarization System

A sophisticated hierarchical document summarization system that processes bulk PDF data through multiple levels of compression, each handled by dedicated servers with intelligent query routing.

## 🏗️ Architecture Overview

The system implements a **3-tier summarization architecture**:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Server 1      │    │   Server 2      │    │   Server 3      │
│   (L1 Summary)  │───▶│   (L2 Summary)  │───▶│   (L3 Summary)  │
│   Full Docs     │    │   10x Compress  │    │   10x Compress  │
│   + RAG Index   │    │   + RAG Index   │    │   + RAG Index   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Orchestrator   │
                    │ Intelligent     │
                    │ Query Router    │
                    └─────────────────┘
```

### Server Responsibilities

- **Server 1**: Ingests raw PDFs, creates full-text embeddings, generates L1 summary (10% compression)
- **Server 2**: Takes L1 summary, creates L2 summary (20% of L1), maintains its own RAG index
- **Server 3**: Takes L2 summary, creates L3 ultra-summary (10% of L2), maintains its own RAG index
- **Orchestrator**: Intelligent query routing based on query complexity and intent

## 🚀 Quick Start

### Prerequisites

```bash
# Install dependencies
pip install fastapi uvicorn httpx pydantic google-generativeai faiss-cpu pypdf numpy python-dotenv

# Set up environment
export GOOGLE_API_KEY="your_google_api_key_here"
```

### 1. Start the System

```bash
# Start all servers
python manage_system.py start

# Or start individual servers
python manage_system.py start --server server1
python manage_system.py start --server server2
python manage_system.py start --server server3
python manage_system.py start --server orchestrator
```

### 2. Ingest Documents

```bash
# Trigger full ingestion pipeline
curl -X POST "http://localhost:8000/ingest"

# Or trigger individual steps
curl -X POST "http://localhost:8001/ingest"  # Server 1: PDF ingestion
curl -X POST "http://localhost:8002/summarize_l1"  # Server 2: L1→L2
curl -X POST "http://localhost:8003/summarize_l2"  # Server 3: L2→L3
```

### 3. Query the System

```bash
# Intelligent query routing (recommended)
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the key points about Jharkhand policies?"}'

# Direct query to specific server
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Give me detailed information about MSME policy"}'
```

## 🧠 Intelligent Query Routing

The orchestrator automatically routes queries based on complexity:

### Query Types & Routing

| Query Type | Keywords | Routed To | Use Case |
|------------|----------|-----------|----------|
| **Simple** | "key points", "bullet", "concise", "short" | Server 3 | High-level overview |
| **Moderate** | "summary", "overview", "brief", "explain" | Server 2 | General summaries |
| **Detailed** | "detailed", "full", "section", "specific" | Server 1 | Factual details |
| **Comprehensive** | "comprehensive", "complete analysis" | Server 1 | Full document analysis |

### Example Queries

```bash
# Simple query → Server 3 (ultra-compressed)
"What are the key points?"

# Moderate query → Server 2 (moderate compression)  
"Give me a summary of the policies"

# Detailed query → Server 1 (full document)
"What are the specific requirements in section 4.2?"

# Comprehensive query → Server 1 (full document)
"Provide a comprehensive analysis of all policies"
```

## 📊 System Management

### Monitoring Commands

```bash
# Check system status
python manage_system.py status

# Monitor system health
python manage_system.py monitor

# Stop all servers
python manage_system.py stop

# Restart system
python manage_system.py restart
```

### Health Checks

Each server provides health endpoints:

```bash
# Check individual server health
curl http://localhost:8001/health
curl http://localhost:8002/health  
curl http://localhost:8003/health
curl http://localhost:8000/health

# Get server statistics
curl http://localhost:8001/stats
curl http://localhost:8002/stats
curl http://localhost:8003/stats
curl http://localhost:8000/stats
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# API Configuration
GOOGLE_API_KEY=your_api_key_here

# Model Configuration  
EMBEDDING_MODEL=models/text-embedding-004
GEMINI_MODEL=models/gemini-1.5-flash

# Chunking Configuration
CHUNK_SIZE=1200
CHUNK_OVERLAP=200

# Server Ports
SERVER1_PORT=8001
SERVER2_PORT=8002
SERVER3_PORT=8003
ORCHESTRATOR_PORT=8000

# Compression Ratios
SERVER1_COMPRESSION=0.1
SERVER2_COMPRESSION=0.2
SERVER3_COMPRESSION=0.1

# Performance
REQUEST_TIMEOUT=30.0
MAX_RETRIES=3
```

### Server-Specific Configuration

Each server can be configured independently:

- **Compression ratios**: How much to compress at each level
- **Token limits**: Maximum response length
- **Top-K**: Number of relevant chunks to retrieve
- **Ports**: Custom port assignments

## 🔧 API Reference

### Orchestrator Endpoints (Port 8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/query` | POST | Intelligent query routing |
| `/query/{server}` | POST | Direct query to specific server |
| `/health` | GET | System health check |
| `/stats` | GET | Aggregated statistics |

### Server Endpoints

#### Server 1 (Port 8001)
- `POST /ingest` - Ingest PDFs and create L1 summary
- `POST /query` - Query full document index
- `GET /health` - Health check
- `GET /stats` - Server statistics

#### Server 2 (Port 8002)  
- `POST /summarize_l1` - Create L2 summary from L1
- `POST /query` - Query L2 summary index
- `GET /health` - Health check
- `GET /stats` - Server statistics

#### Server 3 (Port 8003)
- `POST /summarize_l2` - Create L3 summary from L2
- `POST /query` - Query L3 summary index  
- `GET /health` - Health check
- `GET /stats` - Server statistics

## 📁 Project Structure

```
jharkhand-chatbot/
├── backend/
│   ├── servers/
│   │   ├── server1.py          # L1 Summary Server
│   │   ├── server2.py          # L2 Summary Server  
│   │   └── server3.py          # L3 Summary Server
│   ├── orchestrator.py         # Intelligent Query Router
│   ├── enhanced_config.py     # Configuration Management
│   ├── rag.py                 # RAG Pipeline Components
│   ├── vectorstore.py         # FAISS Vector Store
│   ├── ingest.py              # PDF Processing
│   └── schemas.py             # Pydantic Models
├── manage_system.py           # System Management Script
├── pdfs/
│   ├── raw/                   # Input PDF files
│   └── summaries/
│       ├── L1/               # Level 1 summaries
│       ├── L2/               # Level 2 summaries
│       └── L3/               # Level 3 summaries
└── experiment/               # Vector indices and metadata
```

## 🎯 Key Features

### ✅ Implemented Features

- **Multi-level summarization** with configurable compression ratios
- **Intelligent query routing** based on query complexity analysis
- **Automatic fallback** when primary servers fail
- **Comprehensive error handling** and logging
- **Health monitoring** and system status tracking
- **Lazy initialization** for efficient resource usage
- **Async/await support** for better performance
- **Graceful shutdown** handling
- **Configuration management** with environment variables

### 🔄 Workflow

1. **Ingestion**: Server 1 processes PDFs → creates L1 summary
2. **Compression**: Server 2 compresses L1 → creates L2 summary  
3. **Ultra-compression**: Server 3 compresses L2 → creates L3 summary
4. **Query Routing**: Orchestrator analyzes query → routes to appropriate server
5. **Response**: Selected server processes query → returns answer with citations

## 🚨 Error Handling

The system includes comprehensive error handling:

- **Server failures**: Automatic fallback to alternative servers
- **Network timeouts**: Configurable timeout and retry logic
- **Missing dependencies**: Clear error messages and validation
- **API failures**: Graceful degradation and error reporting
- **Resource limits**: Proper cleanup and resource management

## 📈 Performance Considerations

- **Lazy loading**: Servers initialize only when needed
- **Caching**: Vector indices are persisted and reused
- **Async operations**: Non-blocking I/O for better throughput
- **Resource management**: Proper cleanup and memory management
- **Configurable timeouts**: Prevent hanging requests

## 🔮 Future Enhancements

- **Dynamic server scaling** based on load
- **Advanced query analysis** using ML models
- **Multi-language support** for different document types
- **Real-time monitoring** dashboard
- **Automated testing** and CI/CD pipeline
- **Docker containerization** for easy deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the logs: `python manage_system.py monitor`
2. Verify configuration: `python manage_system.py status`
3. Check individual server health endpoints
4. Review the error messages and logs

---

**Built with ❤️ for efficient document processing and intelligent query routing**
