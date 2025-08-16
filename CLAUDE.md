# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) demonstration project that showcases how to use OpenAI's Responses API with various MCP servers. The project includes both Streamlit UI applications and FastAPI server implementations for interacting with multiple database and service backends through MCP.

## Key Architecture Components

### Core Applications
- **openai_api_mcp_sample.py** - Main Streamlit application entry point (line 11: `from helper_mcp import MCPApplication`)
- **mcp_api_server.py** - FastAPI-based REST server for MCP operations (line 19: `app = FastAPI`)
- **mcp_api_client.py** - Client library for MCP API server interactions (line 14: `class MCPAPIClient`)

### Helper Modules
- **helper_mcp.py** - Core MCP functionality, database connections, and application logic
- **helper_api.py** - OpenAI API integration, configuration management, and response processing  
- **helper_st.py** - Streamlit UI components and interface helpers
- **helper_mcp_pages.py** - Page management for multi-page Streamlit apps

### Database Support
The project supports multiple database backends:
- PostgreSQL (psycopg2-binary)
- Redis 
- Elasticsearch
- Qdrant (vector database)

## Common Development Commands

### Environment Setup
```bash
# Initial setup with dependency installation
./setup_env.sh

# Install dependencies manually
pip install -r requirements.txt
# OR using uv (if available)
uv add streamlit openai python-dotenv pandas numpy requests redis psycopg2-binary elasticsearch qdrant-client watchdog
```

### Running Applications
```bash
# Start Streamlit application
streamlit run openai_api_mcp_sample.py --server.port=8501

# Start FastAPI server
uvicorn mcp_api_server:app --host 0.0.0.0 --port 8000 --reload
# OR using the script
./start_api.sh
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

# API server health check (helper_api.py:33)
# Client includes health check on initialization (mcp_api_client.py:33)
```

## Configuration

### Environment Variables
Required in `.env` file:
- `OPENAI_API_KEY` - OpenAI API key for Responses API
- `PG_CONN_STR` - PostgreSQL connection string (default: `postgresql://testuser:testpass@localhost:5432/testdb`)
- `REDIS_URL` - Redis connection URL (default: `redis://localhost:6379/0`)
- `ELASTIC_URL` - Elasticsearch URL (default: `http://localhost:9200`)
- `QDRANT_URL` - Qdrant URL (default: `http://localhost:6333`)

### Project Structure
- `doc/` - Documentation and guides
- `docker-compose/` - Docker Compose configurations for MCP servers
- `check_server/` - Server health check scripts
- `assets/` - Static assets including images

## MCP Integration Pattern

The project demonstrates the MCP integration pattern where:
1. Multiple MCP servers are containerized and exposed via HTTP/SSE endpoints
2. OpenAI Responses API connects to these servers using `server_url` configuration
3. The `helper_mcp.py` orchestrates different database operations through MCP protocols
4. UI applications (Streamlit) provide interactive interfaces for MCP operations

## Testing

- `quick_test.py` - Basic functionality tests
- `setup_test_data.py` - Test data generation for databases
- Health checks are built into the client classes (mcp_api_client.py:33)

## Dependencies

Key dependencies from pyproject.toml:
- streamlit>=1.48.0 - Web UI framework
- openai>=1.99.9 - OpenAI API client with Responses API support
- fastapi>=0.116.1 - REST API framework
- Database clients: psycopg2-binary, redis, elasticsearch, qdrant-client
- Data processing: pandas, numpy
- Server: uvicorn