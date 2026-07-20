"""ORION Cognitive Agent - observability package.

Currently houses the LangSmith wiring. When AgentCore Observability
becomes available, it will be added here as a sibling sub-module.
"""

from orion_cognitive_agent.observability.langsmith import (
    configure_langsmith,
    is_langsmith_enabled,
)

__all__ = ["configure_langsmith", "is_langsmith_enabled"]
