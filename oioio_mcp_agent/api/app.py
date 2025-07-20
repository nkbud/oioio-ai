"""
Main FastAPI application for OIOIO MCP Agent API.
"""
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from oioio_mcp_agent.api.auth import get_session_middleware
from oioio_mcp_agent.api.db import Base, db_config
from oioio_mcp_agent.api.routers import (agents_router, auth_router,
                                   knowledge_router, tenants_router,
                                   users_router)
from oioio_mcp_agent.config import Config

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("api")

# Get the templates directory
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Create FastAPI app
app = FastAPI(
    title="OIOIO MCP Agent API",
    description="API for OIOIO MCP Agent - Autonomous MCP Server Knowledge Accumulation",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Add session middleware for OAuth
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "insecure_session_key"))

# Mount routes
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/users", tags=["users"])
app.include_router(tenants_router, prefix="/api/tenants", tags=["tenants"])
app.include_router(agents_router, prefix="/api/agents", tags=["agents"])
app.include_router(knowledge_router, prefix="/api/knowledge", tags=["knowledge"])


@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


# UI Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render index page."""
    return templates.TemplateResponse(
        "pages/index.html", 
        {"request": request, "title": "OIOIO MCP Agent"}
    )


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    """Render login page."""
    return templates.TemplateResponse(
        "pages/login.html", 
        {"request": request, "title": "Login - OIOIO MCP Agent"}
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render dashboard page."""
    # In a real app, this would check authentication
    return templates.TemplateResponse(
        "pages/dashboard.html", 
        {"request": request, "title": "Dashboard - OIOIO MCP Agent"}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred"},
    )


@app.on_event("startup")
async def startup_event() -> None:
    """Startup event handler."""
    logger.info("Starting API server")
    
    # Load configuration
    config = Config.load()
    
    # Setup database
    db_url = config.get("api", {}).get("database_url", "sqlite:///./oioio_mcp_agent.db")
    db_config.setup(db_url)
    
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=db_config.engine)
    
    logger.info(f"Connected to database: {db_url}")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Shutdown event handler."""
    logger.info("Shutting down API server")


def start() -> None:
    """Start the API server."""
    import uvicorn
    
    # Load configuration
    config = Config.load()
    api_config = config.get("api", {})
    
    host = api_config.get("host", "0.0.0.0")
    port = int(api_config.get("port", 8000))
    
    uvicorn.run(
        "oioio_mcp_agent.api.app:app",
        host=host,
        port=port,
        reload=api_config.get("reload", False),
    )


if __name__ == "__main__":
    start()