# =============================================================================
# ORION Cognitive Agent — Makefile
# =============================================================================
# Centralized command center. Each target is a thin wrapper around a
# `uv run ...` invocation. When `make` is unavailable, run the underlying
# command directly (see AGENTS.md notes).
#
# Conventions:
#   - QA targets: format-fix, lint-fix, format-check, lint-check, typecheck
#   - Test targets: test, test-cov
#   - Run targets: run-local, run-bedrock, run-agentcore
#   - Setup targets: install, install-bedrock, clean
# =============================================================================

# Default goal
.DEFAULT_GOAL := help

# uv places its virtualenv at .venv by default
export UV_PROJECT_ENVIRONMENT=.venv
export PYTHONPATH = ./src

# QA folders (single source of truth for format/lint)
QA_FOLDERS := src/ tests/

# =============================================================================
# Help
# =============================================================================

.PHONY: help
help: # Show this help message.
	@echo "ORION Cognitive Agent — Make targets"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?# .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?# "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# =============================================================================
# QA — Formatting & Linting
# =============================================================================

.PHONY: format-fix
format-fix: # Auto-format Python code with ruff.
	uv run ruff format $(QA_FOLDERS)

.PHONY: lint-fix
lint-fix: # Auto-fix linting issues with ruff.
	uv run ruff check --fix $(QA_FOLDERS)

.PHONY: format-check
format-check: # Check formatting without modifying files.
	uv run ruff format --check $(QA_FOLDERS)

.PHONY: lint-check
lint-check: # Check linting without fixing.
	uv run ruff check $(QA_FOLDERS)

.PHONY: typecheck
typecheck: # Run mypy strict type checker.
	uv run mypy src/

.PHONY: qa
qa: format-check lint-check typecheck # Run all QA checks (no fix).

.PHONY: qa-fix
qa-fix: format-fix lint-fix # Auto-fix format + lint, then verify with qa.

# =============================================================================
# Tests
# =============================================================================

.PHONY: test
test: # Run pytest (unit tests).
	uv run pytest

.PHONY: test-cov
test-cov: # Run pytest with coverage report.
	uv run pytest --cov=orion_cognitive_agent --cov-report=term-missing

.PHONY: test-verbose
test-verbose: # Run pytest with verbose output.
	uv run pytest -v

# =============================================================================
# Run
# =============================================================================

.PHONY: run-local
run-local: # Run the FastAPI server in local mode (default).
	uv run uvicorn orion_cognitive_agent.api.app:create_app --factory \
	  --host $$ORION_AGENT_API_HOST --port $${ORION_AGENT_API_PORT:-8000}

.PHONY: run-bedrock
run-bedrock: # Run the FastAPI server pointing at AWS Bedrock (requires AWS creds).
	ORION_AGENT_ENVIRONMENT=bedrock uv run uvicorn orion_cognitive_agent.api.app:create_app --factory \
	  --host $${ORION_AGENT_API_HOST:-0.0.0.0} --port $${ORION_AGENT_API_PORT:-8000}

.PHONY: run-agentcore
run-agentcore: # Run the FastAPI server pointing at Bedrock AgentCore (Sprint futuro).
	ORION_AGENT_ENVIRONMENT=agentcore uv run uvicorn orion_cognitive_agent.api.app:create_app --factory \
	  --host $${ORION_AGENT_API_HOST:-0.0.0.0} --port $${ORION_AGENT_API_PORT:-8000}

.PHONY: run-debug
run-debug: # Run with DEBUG-level logging.
	ORION_AGENT_LOG_LEVEL=DEBUG make run-local

.PHONY: cli-info
cli-info: # Print resolved settings (sanity-check).
	uv run python -m orion_cognitive_agent

# =============================================================================
# Setup
# =============================================================================

.PHONY: install
install: # Install all dev dependencies (no bedrock deps).
	uv sync --all-groups

.PHONY: install-bedrock
install-bedrock: # Install dev + bedrock runtime deps (deepagents, langchain-aws).
	uv sync --all-groups

.PHONY: lock
lock: # Update uv.lock without installing.
	uv lock

.PHONY: clean
clean: # Remove caches (.pytest_cache, .ruff_cache, .mypy_cache, __pycache__).
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache .mypy_cache
