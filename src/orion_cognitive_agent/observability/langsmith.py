"""LangSmith tracing wiring for ORION Cognitive Agent.

LangChain reads ``LANGSMITH_*`` environment variables and auto-instruments
every model call, tool call, and chain run. The convention is well
documented at https://docs.smith.langchain.com/

Activation matrix (evaluated at first model/tool call):

============================== =================== ==============================
``LANGSMITH_TRACING=true``     ``LANGSMITH_API_KEY``  Result
============================== =================== ==============================
false                         (any)                Tracing OFF, no overhead.
true                          unset                Tracing OFF (with WARNING).
true                          set                  Tracing ON to project.
============================== =================== ==============================

We do not manually construct a ``LangChainTracer`` because langchain-aws /
deepagents already pick up the env vars. This module only:

1. Pushes ORION settings into ``LANGSMITH_*`` env vars (so users only
   need to fill in ``ORION_AGENT_*`` in ``.env``).
2. Logs a one-line confirmation on startup so it is obvious whether
   tracing is on or off.
3. Exposes :func:`is_langsmith_enabled` for tests and runtime guards.
"""

from __future__ import annotations

import logging
import os

from orion_cognitive_agent.config import get_settings

logger = logging.getLogger(__name__)

ENV_TRACING = "LANGSMITH_TRACING"
ENV_API_KEY = "LANGSMITH_API_KEY"
ENV_PROJECT = "LANGSMITH_PROJECT"
ENV_ENDPOINT = "LANGSMITH_ENDPOINT"


def configure_langsmith() -> bool:
    """Push ORION settings into LangSmith's env vars.

    Returns True if tracing will be active, False otherwise. Idempotent
    - safe to call multiple times.

    Does NOT verify the API key against LangSmith. Connection validation
    happens on the first trace. Set ``ORION_AGENT_LANGSMITH_TRACING=true``
    and ``ORION_AGENT_LANGSMITH_API_KEY`` to enable.
    """
    settings = get_settings()

    if not settings.langsmith_tracing:
        logger.info("LangSmith tracing disabled (ORION_AGENT_LANGSMITH_TRACING=false)")
        return False

    if settings.langsmith_api_key is None:
        logger.warning(
            "LangSmith tracing requested (ORION_AGENT_LANGSMITH_TRACING=true) "
            "but ORION_AGENT_LANGSMITH_API_KEY is not set. Traces will NOT "
            "be sent. Get a free key at https://smith.langchain.com",
        )
        return False

    os.environ[ENV_TRACING] = "true"
    os.environ[ENV_API_KEY] = settings.langsmith_api_key.get_secret_value()
    os.environ[ENV_PROJECT] = settings.langsmith_project

    logger.info(
        "LangSmith tracing ENABLED (project=%s)",
        settings.langsmith_project,
    )
    return True


def is_langsmith_enabled() -> bool:
    """Return True if tracing is currently active in this process."""
    return os.environ.get(ENV_TRACING, "").lower() == "true" and bool(os.environ.get(ENV_API_KEY))


__all__ = [
    "ENV_API_KEY",
    "ENV_ENDPOINT",
    "ENV_PROJECT",
    "ENV_TRACING",
    "configure_langsmith",
    "is_langsmith_enabled",
]
