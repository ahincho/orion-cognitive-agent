"""uvicorn entry point for ORION Cognitive Agent.

Invoked by ``make run-local`` / ``make run-bedrock`` or directly:

    uv run python -m orion_cognitive_agent.api.server
"""

from __future__ import annotations

import uvicorn

from orion_cognitive_agent.api.app import create_app
from orion_cognitive_agent.config import get_settings


def main() -> None:
    """Run the FastAPI app under uvicorn with settings-derived config.

    ``create_app(settings)`` requires an explicit ``Settings`` instance, so
    we instantiate the app here and pass the object directly to uvicorn
    rather than relying on the ``factory=True`` mode (which would call
    ``create_app()`` with no arguments and fail at ASGI startup with
    ``missing 1 required positional argument: 'settings'`` — observed in
    Bedrock AgentCore logs on 2026-07-21).
    """
    settings = get_settings()
    app = create_app(settings)
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
