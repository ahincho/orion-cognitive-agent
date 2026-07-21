"""FastAPI application factory for ORION Cognitive Agent.

The app exposes:

- ``GET  /ping``         - liveness probe for Bedrock AgentCore
                            Runtime (per AWS contract). Always returns
                            ``200 OK`` with agent metadata.
- ``POST /invocations``   - Bedrock AgentCore invocation endpoint. In
                            ``local`` mode it echoes the payload (smoke
                            contract); in ``bedrock``/``agentcore`` mode
                            it dispatches the request to the compiled
                            deepagent graph and returns the assistant
                            message.
- ``GET  /health``       - convenience probe used by the test suite and
                            by hand-driven smoke tests.
- ``POST /ag-ui``        - placeholder endpoint. The real AG-UI
                            streaming protocol (``ag-ui-langgraph``)
                            lands in a future Sprint; this echo is
                            enough for frontend smoke tests today.

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
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from orion_cognitive_agent.agent import ORIONAgent, create_orion_agent
from orion_cognitive_agent.config import Environment, Settings
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


def _agent_metadata(agent: ORIONAgent) -> dict[str, object]:
    """Serialize agent metadata used by ``/ping`` and ``/health``."""
    return {
        "status": "ok",
        "environment": agent.environment,
        "model_id": agent.model_id,
        "agent_name": agent.agent_name,
        "max_turns": agent.max_turns,
    }


def _extract_user_text(payload: dict[str, object]) -> str:
    """Normalise the request body coming into ``/invocations``.

    Accepts both shapes:

    - ``{"input": {"text": "..."}}`` — Bedrock AgentCore native shape.
    - ``{"text": "..."}`` — shorthand.
    - ``{"input": "..."}`` — stringified input.

    Returns the user message text or ``""`` if not found (callers
    decide whether the empty input is a 400 or an echo).
    """
    candidate = payload.get("input", payload)
    if isinstance(candidate, str):
        return candidate
    if isinstance(candidate, dict):
        raw = candidate.get("text")
        if isinstance(raw, str):
            return raw
    return ""


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
        """Liveness probe + agent metadata (test-suite convention)."""
        return _agent_metadata(app.state.agent)

    @app.get("/ping")
    async def ping() -> dict[str, object]:
        """Bedrock AgentCore Runtime liveness probe.

        Contract: ``GET /ping`` returns ``200 OK`` as long as the
        Python process is alive and the FastAPI app is wired. Body
        matches the ``/health`` payload for parity.
        """
        return _agent_metadata(app.state.agent)

    @app.post("/invocations")
    async def invocations(payload: dict[str, object]) -> dict[str, object]:
        # DEBUG (smoke-test 2026-07-21): log the raw payload to trace
        # whether Bedrock AgentCore forwards our JSON as-is. Cheap when
        # logs are off, keep it explicit at DEBUG level.
        logger.debug("invocations payload keys=%s", sorted(payload.keys()))
        """Bedrock AgentCore Runtime invocation endpoint.

        Contract: ``POST /invocations`` accepts an arbitrary JSON
        document and returns a JSON response. In ``local`` mode the
        endpoint echoes the payload (smoke contract). In
        ``bedrock``/``agentcore`` mode it dispatches the request to
        the compiled deepagent graph and returns the last assistant
        message.
        """
        env = app.state.settings.environment
        agent = app.state.agent

        # LOCAL mode: echo (used in tests and in the no-AWS dev loop).
        if env == Environment.LOCAL:
            return {
                "echo": payload,
                "agent_environment": agent.environment,
                "stub": True,
            }

        text = _extract_user_text(payload)
        if not text:
            raise HTTPException(
                status_code=400,
                detail=(
                    "missing user text: expected JSON shape "
                    '{"input": {"text": "..."}} or {"text": "..."}'
                ),
            )

        if agent.graph is None:
            # Defensive: if ``environment != LOCAL`` but the graph is
            # missing, the factory must have been called with
            # ``local`` somewhere. Surface the misconfig loudly.
            raise HTTPException(
                status_code=503,
                detail=(
                    f"agent graph not available in environment={env.value}; "
                    "check that the bedrock dependency group is installed "
                    "(`uv sync --group bedrock`).",
                ),
            )

        # Build the deepagent input. ``langchain_core.messages`` is part
        # of the optional bedrock group, so keep the import lazy here.
        from langchain_core.messages import HumanMessage

        result: Any = await agent.graph.ainvoke({"messages": [HumanMessage(content=text)]})
        messages = result.get("messages", []) if isinstance(result, dict) else []
        last_content: Any = ""
        if messages:
            tail = messages[-1]
            last_content = getattr(tail, "content", "")

        return {
            "output": {
                "text": last_content if isinstance(last_content, str) else str(last_content),
                "messages_count": len(messages),
            }
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
