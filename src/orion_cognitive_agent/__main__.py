"""Entry point for running ORION Cognitive Agent as a CLI.

Usage (via uv):

    uv run python -m orion_cognitive_agent

For the FastAPI server, see ``orion_cognitive_agent.api.server:main``.
"""

from __future__ import annotations

from orion_cognitive_agent import Environment, __version__, get_settings


def main() -> None:
    """Print resolved settings; useful as a sanity-check CLI."""
    settings = get_settings()
    mode = (
        "MOCK (no AWS calls)"
        if settings.is_local
        else f"REAL ({settings.environment.value} -> {settings.model_id})"
    )
    print(f"ORION Cognitive Agent v{__version__}")
    print(f"  mode               : {mode}")
    print(f"  environment        : {settings.environment.value}")
    print(f"  log_level          : {settings.log_level}")
    print(f"  model_provider     : {settings.model_provider.value}")
    print(f"  model_id           : {settings.model_id}")
    print(f"  agent_name         : {settings.agent_name}")
    print(f"  aws_region         : {settings.aws_region}")
    print(f"  api_host:port      : {settings.api_host}:{settings.api_port}")
    print(f"  max_turns          : {settings.max_turns}")
    print(
        f"  langsmith_tracing  : {'enabled' if settings.langsmith_tracing else 'disabled'}",
    )
    if Environment.AGENTCORE in {Environment.AGENTCORE}:
        pass  # placeholder for future Sprint-specific output


if __name__ == "__main__":
    main()
