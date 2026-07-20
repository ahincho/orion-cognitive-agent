"""FastAPI application factory for ORION Cognitive Agent.

The app exposes:

- ``GET /health`` — liveness probe with agent metadata.
- ``POST /ag-ui``  — placeholder endpoint that will be wired to the real
  DeepAgent stream via ``ag-ui-langgraph`` in a future Sprint.

The factory pattern keeps the FastAPI app testable: instantiate the app
with explicit settings in tests, while ``server.py`` wires the uvicorn
runner to ``get_settings()``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI

from orion_cognitive_agent.agent import create_orion_agent

if TYPE_CHECKING:
    from orion_cognitive_agent.config import Settings


def create_app(settings: Settings) -> FastAPI:
    """Build and return the FastAPI app bound to the given settings."""
    app = FastAPI(
        title="ORION Cognitive Agent",
        version="0.1.0",
        description="ORION cognitive agent: Deep Agent over AWS Bedrock, exposed via FastAPI.",
    )
    agent = create_orion_agent(settings)

    @app.get("/health")
    def health() -> dict[str, object]:
        """Liveness probe."""
        return {
            "status": "ok",
            "environment": agent.environment,
            "model_id": agent.model_id,
        }

    @app.post("/ag-ui")
    def ag_ui(payload: dict[str, object]) -> dict[str, object]:
        """Placeholder AG-UI endpoint.

        Future Sprints will replace this with the real SSE stream from
        the DeepAgent (using ``ag-ui-langgraph``). For now, it echoes the
        payload so that frontend integration can be smoke-tested.
        """
        return {
            "echo": payload,
            "agent_environment": agent.environment,
            "stub": True,
        }

    return app
