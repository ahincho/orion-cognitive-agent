"""ORION Cognitive Agent — top-level package.

Re-exports the public API for callers that prefer a flat import surface,
e.g. ``from orion_cognitive_agent import create_orion_agent, get_settings``.

Internal layout (planned):

    src/orion_cognitive_agent/
    ├── config/        # Pydantic settings (env-driven)
    ├── agent/         # DeepAgent factory + (futuros) subagentes
    ├── api/           # FastAPI app + uvicorn runner
    └── tools/         # @tool-decorated functions
"""

from orion_cognitive_agent import agent, api, config
from orion_cognitive_agent.agent import create_orion_agent
from orion_cognitive_agent.config import Settings, get_settings

__version__ = "0.1.0"

__all__ = [
    "Settings",
    "__version__",
    "agent",
    "api",
    "config",
    "create_orion_agent",
    "get_settings",
]
