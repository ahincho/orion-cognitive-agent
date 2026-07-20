"""Pydantic Settings for ORION Cognitive Agent.

All environment variables use the ``ORION_AGENT_`` prefix and are loaded
from the process environment or from a local ``.env`` file (see
``.env.example``).
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Deployment environments for ORION Cognitive Agent.

    Only ``local`` is fully implemented today. ``bedrock`` and
    ``agentcore`` are routed to the future Sprint work tracked in
    ``docs/architectural-decisions/0002-aws-target-bedrock-agentcore.md``.
    """

    LOCAL = "local"
    BEDROCK = "bedrock"
    AGENTCORE = "agentcore"


class ModelProvider(StrEnum):
    """LLM provider for the agent.

    Only ``bedrock`` is supported today. The enum is kept extensible so
    adding ``openai`` / ``anthropic`` / ``ollama`` later is a one-line
    change in this file plus a corresponding factory branch.
    """

    BEDROCK = "bedrock"


class Settings(BaseSettings):
    """ORION Cognitive Agent — runtime configuration.

    Populated from environment variables prefixed with ``ORION_AGENT_``.
    Values declared in a local ``.env`` file override process environment
    defaults (dev-friendly).
    """

    model_config = SettingsConfigDict(
        env_prefix="ORION_AGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # -------------------------------------------------------------------------
    # Runtime
    # -------------------------------------------------------------------------
    environment: Environment = Field(
        default=Environment.LOCAL,
        description="Deployment environment: local | bedrock | agentcore.",
    )
    log_level: str = Field(
        default="INFO",
        description="Python logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )

    # -------------------------------------------------------------------------
    # Model
    # -------------------------------------------------------------------------
    model_provider: ModelProvider = Field(
        default=ModelProvider.BEDROCK,
        description="LLM provider for the agent.",
    )
    model_id: str = Field(
        default="us.anthropic.claude-sonnet-4-20250514",
        description=(
            "Bedrock model ID. Default is the cross-region inference "
            "profile for Anthropic Claude Sonnet 4."
        ),
    )
    aws_region: str = Field(
        default="us-east-1",
        description="AWS region for the Bedrock client.",
    )

    # -------------------------------------------------------------------------
    # API server
    # -------------------------------------------------------------------------
    api_host: str = Field(
        default="0.0.0.0",
        description="Bind host for the FastAPI server.",
    )
    api_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Bind port for the FastAPI server.",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:4200"],
        description='Origins allowed by CORS (JSON list, e.g. ["http://localhost:4200"])',
    )

    # -------------------------------------------------------------------------
    # Agent limits
    # -------------------------------------------------------------------------
    max_turns: int = Field(
        default=50,
        ge=1,
        description=(
            "Max LLM turns per session. Caps the LangGraph MessagesState "
            "length to avoid runaway loops (see ref: spark-match-08-deep-agent)."
        ),
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance.

    ``lru_cache`` ensures process-wide singleton — calling
    ``get_settings()`` repeatedly yields the same immutable view of the
    environment-derived configuration.
    """
    return Settings()
