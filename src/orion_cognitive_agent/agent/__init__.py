"""DeepAgent factory and (futuro) subagentes del ORION Cognitive Agent."""

from orion_cognitive_agent.agent.factory import (
    ORIONAgent,
    create_orion_agent,
    is_factory_available,
)

__all__ = ["ORIONAgent", "create_orion_agent", "is_factory_available"]
