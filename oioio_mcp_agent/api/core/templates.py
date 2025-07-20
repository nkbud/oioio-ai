"""
Template handling for the API frontend.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

# Get template directory
template_directory = Path(__file__).parent.parent / "templates"

# Create templates
templates = Jinja2Templates(directory=str(template_directory))


def configure_templates(app: FastAPI) -> None:
    """Configure templates for FastAPI."""
    app.state.templates = templates


def include_templates(app: FastAPI) -> None:
    """Add template handlers to FastAPI app."""
    
    @app.get("/")
    async def index(request: Request) -> templates.TemplateResponse:
        """Render index page."""
        return templates.TemplateResponse(
            "pages/index.html",
            {"request": request, "title": "OIOIO MCP Agent"}
        )

    @app.get("/login")
    async def login(request: Request) -> templates.TemplateResponse:
        """Render login page."""
        return templates.TemplateResponse(
            "pages/login.html",
            {"request": request, "title": "Login - OIOIO MCP Agent"}
        )

    @app.get("/dashboard")
    async def dashboard(request: Request) -> templates.TemplateResponse:
        """Render dashboard page."""
        # In a real app, we would check authentication here
        return templates.TemplateResponse(
            "pages/dashboard.html",
            {"request": request, "title": "Dashboard - OIOIO MCP Agent"}
        )

    @app.get("/agents")
    async def agents(request: Request) -> templates.TemplateResponse:
        """Render agents page."""
        # In a real app, we would check authentication here
        return templates.TemplateResponse(
            "pages/agents.html",
            {"request": request, "title": "Agents - OIOIO MCP Agent"}
        )

    @app.get("/knowledge")
    async def knowledge(request: Request) -> templates.TemplateResponse:
        """Render knowledge page."""
        # In a real app, we would check authentication here
        return templates.TemplateResponse(
            "pages/knowledge.html",
            {"request": request, "title": "Knowledge - OIOIO MCP Agent"}
        )