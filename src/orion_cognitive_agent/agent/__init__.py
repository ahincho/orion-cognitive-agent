"""DeepAgent factory + middlewares for ORION Cognitive Agent.

Public API:

- :class:`ORIONAgent`       - immutable handle to a configured agent.
- :func:`create_orion_agent` - top-level factory (delegates per env).
- :func:`is_factory_available` - capability probe (no AWS calls).

Middlewares are NOT re-exported here. Import them explicitly:

    from orion_cognitive_agent.agent.middleware import MaxTurnsMiddleware

This keeps ``from orion_cognitive_agent.agent import ORIONAgent``
working even when the ``bedrock`` dependency group is not installed
(middleware pulls in ``langchain.agents.middleware``).
"""

from orion_cognitive_agent.agent.factory import (
    ORIONAgent,
    create_orion_agent,
    is_factory_available,
)

__all__ = [
    "ORIONAgent",
    "create_orion_agent",
    "is_factory_available",
]
