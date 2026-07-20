"""FastAPI + uvicorn entry points for ORION Cognitive Agent."""

from orion_cognitive_agent.api.app import create_app
from orion_cognitive_agent.api.server import main

__all__ = ["create_app", "main"]
