# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) demonstration project that showcases how to use OpenAI's Responses API with various MCP servers. The project includes both Streamlit UI applications and FastAPI server implementations for interacting with multiple database and service backends through MCP.

## Key Architecture Components

### Core Applications
- **openai_api_mcp_sample.py** - Main Streamlit application entry point (helper_mcp.py:MCPApplication)
- **mcp_api_server.py** - FastAPI-based REST server for MCP operations (FastAPI app instance)
- **mcp_api_client.py** - Client library for MCP API server interactions (MCPAPIClient class)

### Helper Modules
- **helper_mcp.py** - Core MCP functionality, database connections, and application logic
- **helper_api.py** - OpenAI API integration, YAML config management via ConfigManager singleton
- **helper_st.py** - Streamlit UI components and interface helpers
- **helper_mcp_pages.py** - Page management for multi-page Streamlit apps

### Database Support
The project supports multiple database backends:
- **PostgreSQL** - Primary relational database with schema:
  - `customers` (id, name, email, age, city, created_at)
  - `orders` (id, customer_id, product_name, price, quantity, order_date)
  - `products` (id, name, category, price, stock_quantity, description)
- **Redis** - Caching and session storage
- **Elasticsearch** - Document search and indexing
- **Qdrant** - Vector database for embeddings and similarity search

## Common Development Commands

### Environment Setup
```bash
# Initial setup with dependency installation (auto-detects uv/pip)
./setup_env.sh

# Manual dependency installation
pip install -r requirements.txt
# OR using uv (preferred if available)
uv sync
```

### Running Applications
```bash
# Start Streamlit application
streamlit run openai_api_mcp_sample.py --server.port=8501
# OR with uv
uv run streamlit run openai_api_mcp_sample.py --server.port=8501

# Start FastAPI server (recommended)
./start_api.sh
# OR manually
uvicorn mcp_api_server:app --host 0.0.0.0 --port 8000 --reload
```

### Database and Infrastructure
```bash
# Start MCP demo environment with Docker Compose
docker-compose -f docker-compose/docker-compose.mcp-demo.yml up -d

# Setup test data
python setup_test_data.py
python setup_sample_data.py

# Check Qdrant diagnostic
python qdrant_diagnostic.py

# Run quick tests
python quick_test.py
```

### Development Workflow
```bash
# Check database connections
./check_server/check_qdrant.sh

# Health checks are automatic on startup
# API server: /health endpoint
# Client: automatic health check on initialization
```

## Configuration

### Environment Variables
Required in `.env` file:
- `OPENAI_API_KEY` - OpenAI API key for Responses API
- `PG_CONN_STR` - PostgreSQL connection string (default: `postgresql://testuser:testpass@localhost:5432/testdb`)
- `REDIS_URL` - Redis connection URL (default: `redis://localhost:6379/0`)
- `ELASTIC_URL` - Elasticsearch URL (default: `http://localhost:9200`)
- `QDRANT_URL` - Qdrant URL (default: `http://localhost:6333`)
- `PINECONE_API_KEY` - Pinecone API key (optional)

### Model Configuration
The project uses `config.yml` for comprehensive OpenAI model configuration:
- **Model Categories**: 
  - frontier (GPT-5 series)
  - reasoning (o3/o4-mini, o1/o1-pro)
  - deep_research (o3/o4 deep research variants)
  - standard (GPT-4o/4.1 series)
  - vision, audio, realtime, image, search, embeddings
- **Default Model**: gpt-4.1 (configurable via ConfigManager singleton)
- **Audio Support**: Complete TTS/STT pipeline with Japanese support
- **Configuration Management**: helper_api.py:ConfigManager singleton handles YAML config loading and model categorization with pricing information

### Project Structure
- `doc/` - Documentation and guides including config, setup, and RAG documentation
- `README_doc/` - Setup instructions, API docs, and Claude Code guides
- `docker-compose/` - Docker Compose configurations for MCP demo environment
  - `init-data/` - Database initialization scripts
- `check_server/` - Server health check scripts
- `assets/` - Static assets including application screenshots
- `helper_*.py` - Core application logic modules
- `mcp_api_*.py` - MCP API server and client implementations
- `setup_*.py` - Environment and data setup scripts

## MCP Integration Pattern

The project demonstrates the MCP integration pattern where:
1. Multiple MCP servers are containerized and exposed via HTTP/SSE endpoints
2. OpenAI Responses API connects to these servers using `server_url` configuration
3. The `helper_mcp.py` orchestrates different database operations through MCP protocols
4. UI applications (Streamlit) provide interactive interfaces for MCP operations

### MCP Server Endpoints
When running the Docker Compose setup, MCP servers are exposed on these ports:
- Redis MCP: `http://localhost:8000/mcp`
- PostgreSQL MCP: `http://localhost:8001/mcp`
- Elasticsearch MCP: `http://localhost:8002/mcp`
- Qdrant MCP: `http://localhost:8003/mcp`

### API Endpoints (FastAPI Server)
The `mcp_api_server.py` provides these REST endpoints:
- **Health**: `/health` - Server health check
- **Customers**: `/api/customers` (GET, POST), `/api/customers/{id}` (GET)
- **Products**: `/api/products` (GET), `/api/products/{id}` (GET)
- **Orders**: `/api/orders` (GET, POST)
- **Analytics**: `/api/stats/sales`, `/api/stats/customers/{id}/orders`

## Testing and Development

### Testing Commands
```bash
# Run basic API functionality tests
python quick_test.py

# Generate test data for all databases
python setup_test_data.py

# Setup sample data with realistic examples
python setup_sample_data.py

# Run Qdrant diagnostics
python qdrant_diagnostic.py
```

### Development Tips
- Health checks are automatic in client classes
- Use `uv` for faster dependency management when available
- Database connections auto-retry with sensible defaults
- Configuration via `config.yml` supports hot-reloading in development

## Dependencies

Key dependencies from pyproject.toml:
- **streamlit>=1.48.0** - Web UI framework
- **openai>=1.99.9** - OpenAI API client with Responses API support
- **fastapi>=0.116.1** - REST API framework with automatic API docs
- **Database clients**: psycopg2-binary, redis, elasticsearch, qdrant-client
- **Data processing**: pandas, numpy
- **Server**: uvicorn (ASGI server)
- **Development**: python-dotenv, watchdog

### Python Version
Requires Python >=3.12.2
```