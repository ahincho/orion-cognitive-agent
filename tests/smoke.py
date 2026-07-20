"""Smoke + factory tests for ORION Cognitive Agent.

These tests verify the bootstrap contract:

1. The package imports cleanly and exposes the public API.
2. Pydantic Settings resolves the declared defaults.
3. The agent factory returns an immutable handle with the right
   fields for ``environment=local``.
4. The FastAPI app responds to ``GET /health`` and ``POST /ag-ui``.
5. With the ``bedrock`` dependency group installed, building the
   factory for ``environment=bedrock`` produces a compiled LangGraph
   state graph (no AWS calls are made in this test - we only check
   the handle structure).

They run without AWS credentials (covered by the ``environment=local``
default in ``Settings``) and without the ``bedrock`` optional
dependency group for cases 1-4; case 5 auto-skips when the group is
not installed.
"""

from __future__ import annotations

import dataclasses
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from orion_cognitive_agent import (
    Environment,
    Settings,
    __version__,
    create_orion_agent,
    get_settings,
)
from orion_cognitive_agent.agent import ORIONAgent, is_factory_available
from orion_cognitive_agent.api import create_app

# Re-imports needed for tests that depend on the lazy-loaded factory.
from orion_cognitive_agent.tools.echo.handler import echo_handler


class TestPackageImport:
    """Verify the package imports without errors and exposes the public API."""

    def test_version_is_string(self) -> None:
        assert isinstance(__version__, str)
        assert __version__

    def test_public_api_exports(self) -> None:
        # Smoke check: all advertised symbols are importable from the package.
        from orion_cognitive_agent import (  # noqa: F401
            Environment,
            Settings,
            create_orion_agent,
            get_settings,
        )


class TestSettings:
    """Verify Pydantic Settings resolves the declared defaults."""

    def test_settings_defaults_to_local(self) -> None:
        settings = get_settings()
        assert settings.environment == Environment.LOCAL

    def test_settings_model_id_default(self) -> None:
        settings = get_settings()
        assert settings.model_id == "us.anthropic.claude-sonnet-4-20250514"

    def test_settings_aws_region_default(self) -> None:
        settings = get_settings()
        assert settings.aws_region == "us-east-1"

    def test_settings_max_turns_positive(self) -> None:
        settings = get_settings()
        assert settings.max_turns >= 1

    def test_settings_model_string_format(self) -> None:
        settings = get_settings()
        assert settings.model_string == f"bedrock:{settings.model_id}"

    def test_settings_is_local_default(self) -> None:
        settings = get_settings()
        assert settings.is_local is True

    def test_settings_langsmith_disabled_by_default(self) -> None:
        settings = get_settings()
        assert settings.langsmith_tracing is False
        assert settings.langsmith_api_key is None


class TestAgentFactoryLocal:
    """The local factory produces a metadata-only handle."""

    def test_create_orion_agent_returns_handle(self) -> None:
        settings = get_settings()
        agent = create_orion_agent(settings)
        assert agent.environment == "local"
        assert agent.model_id == settings.model_id
        assert agent.max_turns == settings.max_turns
        assert agent.agent_name == settings.agent_name
        assert agent.graph is None

    def test_orion_agent_is_frozen(self) -> None:
        settings = get_settings()
        agent = create_orion_agent(settings)
        with pytest.raises(dataclasses.FrozenInstanceError):
            agent.environment = "bedrock"  # type: ignore[misc, attr-defined]

    def test_factory_local_does_not_require_bedrock(self) -> None:
        # is_factory_available must NOT crash even if bedrock group is
        # not installed - it returns False instead.
        result = is_factory_available()
        assert isinstance(result, bool)


def _has_aws_credentials() -> bool:
    """Return True if AWS credentials / region look usable in this env.

    Used to skip ``create_deep_agent(bedrock)`` integration tests in
    environments where no AWS is configured. We accept any of:

    - ``AWS_REGION`` / ``AWS_DEFAULT_REGION`` set in the env
      (sufficient for ``init_chat_model`` to construct ``ChatBedrock``
      even if no real credentials exist).
    - ``~/.aws/credentials`` present (used by local dev / CI secrets).
    - ``AWS_ACCESS_KEY_ID`` + ``AWS_SECRET_ACCESS_KEY`` set.

    The test still does NOT make a real Bedrock call - it only
    validates graph compilation, which forces ``ChatBedrock`` to
    resolve its auth chain.
    """
    if os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION"):
        return True
    if os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"):
        return True
    creds_file = Path.home() / ".aws" / "credentials"
    return creds_file.exists()


class TestAgentFactoryBedrock:
    """With the ``bedrock`` group installed, environment=bedrock compiles the graph."""

    @pytest.fixture
    def bedrock_settings(self) -> Settings:
        return Settings(
            environment=Environment.BEDROCK,
            model_id="us.anthropic.claude-sonnet-4-20250514",
            aws_region="us-east-1",
            max_turns=10,
            agent_name="orion-cognitive-agent-test",
        )

    @pytest.mark.skipif(
        not is_factory_available(),
        reason="bedrock group not installed (`uv sync --all-groups`)",
    )
    @pytest.mark.skipif(
        not _has_aws_credentials(),
        reason=(
            "no AWS region / credentials in this environment; ChatBedrock construction would fail"
        ),
    )
    def test_create_bedrock_agent_returns_compiled_graph(
        self,
        bedrock_settings: Settings,
    ) -> None:
        agent = create_orion_agent(bedrock_settings)
        assert agent.environment == "bedrock"
        assert agent.graph is not None
        # No actual Bedrock call here - this only validates that the
        # deepagent compiled without hitting AWS.

    def test_create_bedrock_agent_raises_when_group_missing(
        self,
        bedrock_settings: Settings,
    ) -> None:
        if is_factory_available():
            pytest.skip("bedrock group is installed; cannot exercise the missing-dep path")
        with pytest.raises(RuntimeError, match="bedrock"):
            create_orion_agent(bedrock_settings)


class TestAgentFactoryAgentCore:
    """environment=agentcore follows the same code path as bedrock today."""

    @pytest.mark.skipif(
        not is_factory_available(),
        reason="bedrock group not installed",
    )
    @pytest.mark.skipif(
        not _has_aws_credentials(),
        reason="no AWS region / credentials in this environment",
    )
    def test_create_agentcore_returns_compiled_graph(self) -> None:
        # environment=agentcore routes through the bedrock branch and
        # compiles the deepagent graph (the AgentCore Runtime protocol
        # is the responsibility of the container layer in Sprint C).
        settings = Settings(environment=Environment.AGENTCORE, aws_region="us-east-1")
        agent = create_orion_agent(settings)
        assert agent.environment == "agentcore"
        assert agent.graph is not None

    def test_create_agentcore_raises_when_group_missing(self) -> None:
        if is_factory_available():
            pytest.skip("bedrock group is installed; cannot exercise missing-dep path")
        settings = Settings(environment=Environment.AGENTCORE)
        with pytest.raises(RuntimeError, match="bedrock"):
            create_orion_agent(settings)


class TestEchoHandler:
    """The echo handler is unit-testable without an LLM."""

    def test_echo_handler_success(self) -> None:
        result = echo_handler(text="hola")
        assert result["status"] == "success"
        assert result["data"] == {"echo": "hola"}
        assert result["errors"] is None

    def test_echo_handler_empty_string(self) -> None:
        result = echo_handler(text="   ")
        assert result["status"] == "error"
        assert result["data"] is None
        assert result["errors"] is not None
        assert any("non-empty" in msg for msg in result["errors"])

    def test_echo_handler_non_string(self) -> None:
        result = echo_handler(text=123)  # type: ignore[arg-type, call-arg]
        assert result["status"] == "error"


class TestEchoTool:
    """The LangChain @tool wrapper around echo_handler."""

    @pytest.mark.skipif(
        not is_factory_available(),
        reason="bedrock group not installed (`uv sync --all-groups`)",
    )
    def test_echo_tool_is_structured_tool(self) -> None:
        # Lazy import - the tool module pulls in langchain_core, which
        # only exists when the bedrock group is installed.
        from orion_cognitive_agent.tools.echo.tool import echo_tool

        # ``langchain_core.tools.tool`` returns a ``StructuredTool``
        # instance, not a plain function. Sanity-check the contract:
        # a ``.name`` and a ``.invoke(input)`` method that round-trips
        # through the handler.
        assert hasattr(echo_tool, "name")
        assert echo_tool.name == "echo_tool"
        assert hasattr(echo_tool, "invoke")

        # End-to-end through the tool runtime (no real model calls):
        result = echo_tool.invoke({"text": "hola"})
        assert result == {"echo": "hola"}


class TestFastAPIApp:
    """Verify the app responds to /health and /ag-ui without AWS."""

    def test_health_endpoint(self) -> None:
        settings = get_settings()
        app = create_app(settings)
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["environment"] == "local"
        assert body["agent_name"] == settings.agent_name
        assert body["model_id"] == settings.model_id

    def test_ag_ui_endpoint_echoes_payload(self) -> None:
        settings = get_settings()
        app = create_app(settings)
        client = TestClient(app)
        response = client.post(
            "/ag-ui",
            json={"hello": "world"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["echo"] == {"hello": "world"}
        assert body["agent_environment"] == "local"
        assert body["stub"] is True


class TestORIONAgentHandle:
    """Structural checks on the ORIONAgent dataclass handle."""

    def test_handle_dataclass_fields(self) -> None:
        # Use ``dataclasses.fields`` to assert the public surface is
        # stable. Adding a non-optional field is a breaking change for
        # any caller that builds ORIONAgent by hand.
        fields = {f.name for f in dataclasses.fields(ORIONAgent)}
        assert "environment" in fields
        assert "model_id" in fields
        assert "max_turns" in fields
        assert "agent_name" in fields
        assert "graph" in fields
