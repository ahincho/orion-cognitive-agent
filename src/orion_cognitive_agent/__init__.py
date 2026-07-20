"""ORION Cognitive Agent - top-level package.

Re-exports the public API for callers that prefer a flat import
surface, e.g. ``from orion_cognitive_agent import create_orion_agent,
get_settings``.

Internal layout:

    src/orion_cognitive_agent/
    ├── agent/         # DeepAgent factory + middlewares
    ├── api/           # FastAPI app + uvicorn runner
    ├── aws/           # Lazy boto3 clients (bedrock-runtime)
    ├── config/        # Pydantic settings (env-driven)
    ├── observability/ # LangSmith + future AgentCore spans
    ├── prompts/       # Versioned .md prompts loaded by metadata
    ├── tools/         # @tool-decorated functions exposed to the LLM
    └── utils/         # Logging + small helpers
"""

from orion_cognitive_agent import agent, api, aws, config, observability, prompts, tools, utils
from orion_cognitive_agent.agent import create_orion_agent
from orion_cognitive_agent.config import (
    Environment,
    ModelProvider,
    Settings,
    get_settings,
)

__version__ = "0.2.0"

__all__ = [
    "Environment",
    "ModelProvider",
    "Settings",
    "__version__",
    "agent",
    "api",
    "aws",
    "config",
    "create_orion_agent",
    "get_settings",
    "observability",
    "prompts",
    "tools",
    "utils",
]
