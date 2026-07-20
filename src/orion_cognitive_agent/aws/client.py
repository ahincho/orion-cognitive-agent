"""Lazy AWS client factory for ORION Cognitive Agent.

We use a thin wrapper around ``boto3.client("bedrock-runtime")`` to:

1. Cache the client for the duration of the process (boto3 clients are
   designed to be reused, not re-instantiated per call).
2. Pick up AWS credentials from the standard chain (env vars, profile,
   IMDS - the latter being how AgentCore containers authenticate).
3. Keep type annotations loose (``Any``) because ``mypy`` cannot verify
   the boto3 surface and adding ``boto3-stubs`` everywhere is overkill
   for one client call.

The factory itself is a thin pass-through; everything else in the
codebase goes through ``langchain-aws`` (``ChatBedrockConverse``) which
is typed and lazy-imported inside the agent factory.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from orion_cognitive_agent.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_bedrock_runtime_client() -> Any:
    """Return a cached ``boto3.client("bedrock-runtime")`` instance.

    The region is taken from ``Settings.aws_region``. Credentials are
    resolved by boto3's default chain (env vars, profile, IMDS for
    AgentCore containers).

    Returns:
        A ``botocore.client.BedrockRuntime`` client. Typed as ``Any``
        because we don't pull boto3 type stubs into the project.

    Raises:
        ImportError: if boto3 is not installed (only ``bedrock`` group
            pulls it in).
    """
    try:
        import boto3
    except ImportError as exc:
        raise ImportError(
            "boto3 is required for environment=bedrock/agentcore. "
            "Install via `uv sync --group bedrock`.",
        ) from exc

    settings = get_settings()
    logger.debug(
        "Instantiating bedrock-runtime client (region=%s)",
        settings.aws_region,
    )
    return boto3.client(
        service_name="bedrock-runtime",
        region_name=settings.aws_region,
    )


def reset_bedrock_runtime_client_cache() -> None:
    """Invalidate the cached client (useful in tests after changing env)."""
    get_bedrock_runtime_client.cache_clear()


__all__ = ["get_bedrock_runtime_client", "reset_bedrock_runtime_client_cache"]
