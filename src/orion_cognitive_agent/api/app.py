"""FastAPI application factory for ORION Cognitive Agent.

The app exposes:

- ``GET  /health`` - liveness probe + agent metadata.
- ``POST /ag-ui``  - placeholder endpoint. The real AG-UI streaming
                     protocol (``ag-ui-langgraph``) lands in a future
                     Sprint; this echo is enough for frontend smoke
                     tests today.

The factory pattern keeps the FastAPI app testable: instantiate the
app with explicit settings in tests, while ``server.py`` wires the
uvicorn runner to ``get_settings()``.

A ``lifespan`` context handler initialises structured logging,
configures LangSmith tracing, and constructs the agent handle before
the first request lands.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from orion_cognitive_agent.agent import ORIONAgent, create_orion_agent
from orion_cognitive_agent.config import Settings
from orion_cognitive_agent.observability.langsmith import configure_langsmith
from orion_cognitive_agent.utils import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan - initialise logging + agent on startup."""
    settings: Settings = app.state.settings

    # Centralised logging (idempotent).
    setup_logging(level=settings.log_level)
    logger.info(
        "Starting ORION Cognitive Agent (environment=%s, model=%s)",
        settings.environment.value,
        settings.model_string,
    )

    # LangSmith tracing. Idempotent.
    configure_langsmith()

    # Construct the agent handle (lazy - builds the deepagent graph
    # only when environment != LOCAL).
    agent = create_orion_agent(settings)
    app.state.agent = agent
    logger.info(
        "Agent ready (graph=%s)",
        "compiled" if agent.graph is not None else "metadata-only",
    )

    yield

    logger.info("ORION Cognitive Agent stopped")


def create_app(settings: Settings) -> FastAPI:
    """Build and return the FastAPI app bound to the given settings."""
    app = FastAPI(
        title="ORION Cognitive Agent",
        version="0.2.0",
        description=("ORION cognitive agent: Deep Agent over AWS Bedrock, exposed via FastAPI."),
        lifespan=lifespan,
    )

    # CORS - allow Angular frontend dev server (matches
    # ``Settings.cors_origins`` default).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # `settings` and `agent` are populated in ``lifespan``; we attach
    # `settings` here too so test code that constructs the app without
    # lifespan can still read it.
    app.state.settings = settings
    app.state.agent = ORIONAgent(
        environment=settings.environment.value,
        model_id=settings.model_id,
        max_turns=settings.max_turns,
        agent_name=settings.agent_name,
    )

    @app.get("/health")
    def health() -> dict[str, object]:
        """Liveness probe + agent metadata."""
        agent = app.state.agent
        return {
            "status": "ok",
            "environment": agent.environment,
            "model_id": agent.model_id,
            "agent_name": agent.agent_name,
            "max_turns": agent.max_turns,
        }

    @app.post("/ag-ui")
    def ag_ui(payload: dict[str, object]) -> dict[str, object]:
        """Placeholder AG-UI endpoint.

        Future Sprints will replace this with the real SSE stream from
        the DeepAgent (via ``ag-ui-langgraph``). For now, it echoes
        the payload so the frontend integration can be smoke-tested.
        """
        agent = app.state.agent
        return {
            "echo": payload,
            "agent_environment": agent.environment,
            "stub": True,
        }

    return app
