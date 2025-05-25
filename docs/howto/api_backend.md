# How to Use the API Backend

This guide provides instructions for setting up and using the OIOIO MCP Agent API backend.

## Getting Started

The API backend is a multi-tenant FastAPI application that provides a REST API for interacting with the OIOIO MCP Agent system. It includes authentication, authorization, and a comprehensive set of endpoints for managing agents, knowledge, and system configuration.

## Prerequisites

- Python 3.9+
- PostgreSQL (for production) or SQLite (for development)
- Docker and Docker Compose (optional, for running the MCP server)

## Installation

1. Install the package:

```bash
pip install oioio-mcp-agent[api]
```

2. Set up environment variables in a `.env` file:

```
# Database
DATABASE_URL=sqlite:///./oioio_mcp_agent.db  # or ******localhost/dbname

# Authentication
JWT_SECRET=your_secure_jwt_secret
SESSION_SECRET=your_secure_session_secret

# OAuth (optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# API keys
OPENROUTER_API_KEY=your_openrouter_api_key
```

3. Initialize the database:

```bash
python -m oioio_mcp_agent db init
```

## Running the API Server

```bash
python -m oioio_mcp_agent serve --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000/` with documentation at `http://localhost:8000/api/docs`.