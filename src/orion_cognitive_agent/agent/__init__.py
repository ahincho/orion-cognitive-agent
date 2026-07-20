"""DeepAgent factory + middlewares for ORION Cognitive Agent.

Public API:

- :class:`ORIONAgent`       - immutable handle to a configured agent.
- :func:`create_orion_agent` - top-level factory (delegates per env).
- :func:`is_factory_available` - capability probe (no AWS calls).
- :class:`MaxTurnsMiddleware` - stop agent cleanly on turn cap.
"""

from orion_cognitive_agent.agent.factory import (
    ORIONAgent,
    create_orion_agent,
    is_factory_available,
)
from orion_cognitive_agent.agent.middleware import MaxTurnsMiddleware

__all__ = [
    "MaxTurnsMiddleware",
    "ORIONAgent",
    "create_orion_agent",
    "is_factory_available",
]
