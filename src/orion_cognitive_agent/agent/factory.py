"""Factory for the ORION Cognitive Agent.

The factory is intentionally thin during bootstrap: it returns a
metadata-only handle for ``environment="local"`` (no AWS calls, no
heavy deps required), and defers real DeepAgent instantiation for
``"bedrock"`` and ``"agentcore"`` until the corresponding runtime lands
(track in ``docs/architectural-decisions/0002-aws-target-bedrock-agentcore.md``).
"""

from __future__ import annotations

from dataclasses import dataclass

from orion_cognitive_agent.config import Settings


@dataclass(frozen=True)
class ORIONAgent:
    """Immutable handle to the agent.

    During bootstrap this is metadata-only. In future Sprints the same
    dataclass will wrap the real DeepAgent / LangGraph compiled graph
    so that ``app.py`` can call into it without changing the public API.
    """

    environment: str
    model_id: str
    max_turns: int


def is_factory_available() -> bool:
    """Return ``True`` if DeepAgents + langchain-aws can be imported.

    Used by the ``dev`` environment to decide whether to install the
    ``bedrock`` dependency group (see ``pyproject.toml``).
    """
    try:
        import deepagents  # noqa: F401
        import langchain_aws  # noqa: F401
    except ImportError:
        return False
    return True


def create_orion_agent(settings: Settings) -> ORIONAgent:
    """Create the ORION Cognitive Agent handle for the given settings.

    Only the ``local`` mode is fully implemented today. ``bedrock`` and
    ``agentcore`` modes will be fleshed out in their respective Sprints
    and will instantiate the real LangGraph graph here.
    """
    return ORIONAgent(
        environment=settings.environment.value,
        model_id=settings.model_id,
        max_turns=settings.max_turns,
    )
