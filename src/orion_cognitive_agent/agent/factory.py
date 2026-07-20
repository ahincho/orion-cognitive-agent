"""Agent factory for ORION Cognitive Agent.

Assembles the deepagent (LangGraph state graph) with the right
backend for the configured environment:

- ``Environment.LOCAL``     - metadata-only handle (no AWS calls).
- ``Environment.BEDROCK``   - real ``create_deep_agent`` over
                              ``ChatBedrockConverse`` from langchain-aws.
- ``Environment.AGENTCORE`` - same as ``BEDROCK``; the AgentCore
                              Runtime protocol is wired in the
                              ``api.app`` lifespan / entry-point in
                              a future Sprint (see ADR-0002).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from orion_cognitive_agent.config import Environment, Settings

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


@dataclass(frozen=True)
class ORIONAgent:
    """Immutable handle to the agent.

    Fields:

    - ``environment`` / ``model_id`` / ``max_turns`` / ``agent_name``:
      reflected from ``Settings`` for introspection (used by
      ``/health`` and ``__main__``).
    - ``graph``: the compiled LangGraph state graph. ``None`` for
      ``Environment.LOCAL`` (no AWS calls).
    """

    environment: str
    model_id: str
    max_turns: int
    agent_name: str
    graph: CompiledStateGraph[Any, Any, Any, Any] | None = field(default=None)


def is_factory_available() -> bool:
    """Return True if DeepAgents + langchain-aws can be imported.

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

    For ``environment=local`` this returns a metadata-only handle -
    no AWS calls, no need for the ``bedrock`` dependency group.

    For ``environment=bedrock`` and ``environment=agentcore`` this
    imports ``deepagents.create_deep_agent``, wires the
    ``ChatBedrockConverse`` model via the ``bedrock:<model_id>``
    string convention, attaches the ``echo_tool`` and the
    ``MaxTurnsMiddleware`` guard, and wraps the compiled graph in an
    :class:`ORIONAgent` handle.

    Raises:
        RuntimeError: if the ``bedrock`` dependency group is not
            installed and a non-local environment is requested.
        ImportError: as raised by the deepagents stack.
    """
    common = ORIONAgent(
        environment=settings.environment.value,
        model_id=settings.model_id,
        max_turns=settings.max_turns,
        agent_name=settings.agent_name,
    )

    if settings.environment == Environment.LOCAL:
        return common

    return ORIONAgent(
        environment=common.environment,
        model_id=common.model_id,
        max_turns=common.max_turns,
        agent_name=common.agent_name,
        graph=_build_bedrock_graph(settings),
    )


def _build_bedrock_graph(
    settings: Settings,
) -> CompiledStateGraph[Any, Any, Any, Any]:
    """Build the compiled LangGraph state graph over AWS Bedrock.

    Lazy-imports the heavy dependencies so that ``environment=local``
    users can still import the package without the ``bedrock`` group
    installed.

    The provider prefix in ``settings.model_string`` is consumed by
    DeepAgents - ``"bedrock:..."`` resolves to ``ChatBedrockConverse``
    from ``langchain-aws`` (see langchain-aws docs).
    """
    try:
        from deepagents import create_deep_agent
        from langchain.agents.middleware import AgentState
    except ImportError as exc:
        raise RuntimeError(
            "environment="
            f"{settings.environment.value}"
            " requires the `bedrock` dependency group. Install via "
            "`uv sync --group bedrock`.",
        ) from exc

    # Local imports keep cycle-order stable and the cold-start footprint
    # of `from orion_cognitive_agent import get_settings` small.
    from orion_cognitive_agent.agent.middleware import MaxTurnsMiddleware
    from orion_cognitive_agent.prompts import SYSTEM_PROMPT
    from orion_cognitive_agent.tools import ECHO_TOOL

    if not isinstance(AgentState, type):  # pragma: no cover - sanity check
        pass

    return create_deep_agent(
        model=settings.model_string,
        tools=[ECHO_TOOL],
        system_prompt=SYSTEM_PROMPT,
        name=settings.agent_name,
        middleware=[MaxTurnsMiddleware()],
    )
