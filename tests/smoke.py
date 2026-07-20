"""Smoke tests for ORION Cognitive Agent."""

from __future__ import annotations

from fastapi.testclient import TestClient

from orion_cognitive_agent import __version__, create_orion_agent, get_settings
from orion_cognitive_agent.api import create_app
from orion_cognitive_agent.config import Environment


class TestPackageImport:
    """Verifica que el paquete importa sin errores y expone la API publica."""

    def test_version_is_string(self) -> None:
        assert isinstance(__version__, str)
        assert __version__  # non-empty


class TestSettings:
    """Verifica que Pydantic Settings resuelve los defaults esperados."""

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


class TestAgentFactory:
    """Verifica que la factory devuelve un handle inmutable."""

    def test_create_orion_agent_returns_handle(self) -> None:
        settings = get_settings()
        agent = create_orion_agent(settings)
        assert agent.environment == "local"
        assert agent.model_id == settings.model_id
        assert agent.max_turns == settings.max_turns

    def test_orion_agent_is_frozen(self) -> None:
        settings = get_settings()
        agent = create_orion_agent(settings)
        try:
            agent.environment = "bedrock"  # type: ignore[misc]
        except Exception as exc:  # FrozenInstanceError
            assert "frozen" in str(exc).lower() or "assign" in str(exc).lower()
        else:
            msg = "ORIONAgent should be frozen"
            raise AssertionError(msg)


class TestFastAPIApp:
    """Verifica que la app FastAPI responde a /health y /ag-ui."""

    def test_health_endpoint(self) -> None:
        settings = get_settings()
        app = create_app(settings)
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["environment"] == "local"

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
