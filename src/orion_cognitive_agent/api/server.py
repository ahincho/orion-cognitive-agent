"""uvicorn entry point for ORION Cognitive Agent.

Invoked by ``make run-local`` / ``make run-bedrock`` or directly:

    uv run python -m orion_cognitive_agent.api.server
"""

from __future__ import annotations

import uvicorn

from orion_cognitive_agent.config import get_settings


def main() -> None:
    """Run the FastAPI app under uvicorn with settings-derived config."""
    settings = get_settings()
    uvicorn.run(
        "orion_cognitive_agent.api.app:create_app",
        host=settings.api_host,
        port=settings.api_port,
        factory=True,
        reload=False,
    )


if __name__ == "__main__":
    main()
