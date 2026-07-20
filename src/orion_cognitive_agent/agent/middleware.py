"""Runtime middlewares for ORION Cognitive Agent.

Provides enforcement hooks that prevent the agent from running away.

:class:`MaxTurnsMiddleware` - stops the agent cleanly when the number
of model turns exceeds ``settings.max_turns``. Without this, LangGraph's
``recursion_limit=9999`` produces a cryptic error when hit.

Both are added to the agent via the ``middleware=[...]`` argument to
``create_deep_agent`` in :mod:`orion_cognitive_agent.agent.factory`.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain.agents.middleware import AgentMiddleware, AgentState
from langchain_core.messages import AIMessage
from langgraph.graph import END

from orion_cognitive_agent.config import get_settings

logger = logging.getLogger(__name__)


class MaxTurnsMiddleware(AgentMiddleware):
    """Stop the agent cleanly when turn count exceeds ``settings.max_turns``.

    Counts each model invocation. When the cap is reached, the
    middleware returns a state update with a final ``AIMessage``
    explaining the cutoff and routes the graph to ``END`` via
    ``goto``.

    The turn count is approximate (counts every model call, including
    subagent delegations). For an exact cap use LangGraph's
    ``recursion_limit`` (we set a high value to let our guard fire
    first).
    """

    def after_model(
        self,
        state: AgentState,
        runtime: object,
    ) -> dict[str, Any] | None:
        """Inspect messages after each model call; cap if too many."""
        settings = get_settings()
        cap = settings.max_turns

        messages = state.get("messages", [])
        ai_count = sum(1 for m in messages if isinstance(m, AIMessage))

        if ai_count >= cap:
            logger.warning(
                "Max turns reached (%d/%d) - stopping agent",
                ai_count,
                cap,
            )
            return {
                "messages": [
                    AIMessage(
                        content=(
                            f"He alcanzado el límite de {cap} turnos de "
                            "razonamiento en esta sesión. Si necesitas "
                            "más ayuda, abre una nueva conversación."
                        ),
                    ),
                ],
                "goto": END,
            }
        return None


__all__ = ["MaxTurnsMiddleware"]
