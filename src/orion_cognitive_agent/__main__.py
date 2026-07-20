"""Entry point for running ORION Cognitive Agent as a CLI.

Usage (via uv):

    uv run python -m orion_cognitive_agent

For the FastAPI server, see ``orion_cognitive_agent.api.server:main``.
"""

from orion_cognitive_agent import __version__, get_settings


def main() -> None:
    """Print resolved settings; useful as a sanity-check CLI."""
    settings = get_settings()
    print(f"ORION Cognitive Agent v{__version__}")
    print(f"  environment      : {settings.environment.value}")
    print(f"  log_level        : {settings.log_level}")
    print(f"  model_provider   : {settings.model_provider.value}")
    print(f"  model_id         : {settings.model_id}")
    print(f"  aws_region       : {settings.aws_region}")
    print(f"  api_host:port    : {settings.api_host}:{settings.api_port}")
    print(f"  max_turns        : {settings.max_turns}")


if __name__ == "__main__":
    main()
