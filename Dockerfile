# syntax=docker/dockerfile:1.7
# ============================================================================
# ORION Cognitive Agent - Multi-stage container image
# ============================================================================
# Target runtime: AWS Bedrock AgentCore Runtime (ORION_AGENT_ENVIRONMENT=agentcore).
#
# Stage 1 (builder): installs uv + syncs the project + bedrock dep-group.
# Stage 2 (runtime): python:3.12-slim + non-root user + uvicorn entrypoint.
#
# Image size is intentionally minimal: only the project + bedrock group are
# installed (no dev tools, no test deps, no docs).
# ============================================================================

# ----------------------------------------------------------------------------
# Stage 1: builder - resolve dependencies via uv from the project lockfile
# ----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Install uv pinned via pipx-less static installer (multi-arch).
RUN pip install --no-cache-dir --disable-pip-version-check "uv==0.7.2"

WORKDIR /app

# Copy only the metadata first so the uv sync layer caches independently of
# source code changes.
COPY pyproject.toml uv.lock .python-version ./
COPY src ./src
COPY README.md ./

# Install runtime + bedrock group; dev tools excluded. --frozen refuses
# to mutate the lockfile. The bedrock group is required when
# ORION_AGENT_ENVIRONMENT=agentcore so the agent graph can be built.
RUN uv sync --frozen --no-dev --group bedrock

# ----------------------------------------------------------------------------
# Stage 2: runtime - slim image with the venv + source
# ----------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# OCI labels (per https://github.com/opencontainers/image-spec/blob/main/annotations.md).
LABEL org.opencontainers.image.title="orion-cognitive-agent" \
      org.opencontainers.image.description="ORION cognitive agent over AWS Bedrock AgentCore Runtime." \
      org.opencontainers.image.source="https://github.com/ahincho/orion-cognitive-agent" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.vendor="orion"

# Non-root user. UID/GID 10001 to leave room for system accounts.
RUN groupadd --system --gid 10001 orion \
 && useradd  --system --uid 10001 --gid orion --no-create-home --shell /usr/sbin/nologin orion

WORKDIR /app

# Copy the resolved venv (includes the bedrock runtime group) + source.
COPY --from=builder --chown=orion:orion /app/.venv /app/.venv
COPY --from=builder --chown=orion:orion /app/src          /app/src
COPY --from=builder --chown=orion:orion /app/pyproject.toml /app/uv.lock /app/.python-version ./

# Make venv first on PATH so ``python`` resolves to the pinned venv interpreter.
ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    # Bedrock AgentCore Runtime contract: container announces the agentcore
    # environment so the lifespan builds the deepagent graph on startup.
    ORION_AGENT_ENVIRONMENT=agentcore \
    ORION_AGENT_AWS_REGION=us-east-1 \
    ORION_AGENT_API_HOST=0.0.0.0 \
    # Port 8080 is the AgentCore HTTP protocol contract default
    # (per AWS docs: runtime-service-contract.html; tab "Compare supported
    # protocols" -> "HTTP Port 8080, Mount Path /invocations"). Local dev
    # loops with `make run-local` should override this with
    # `ORION_AGENT_API_PORT=8000` if needed.
    ORION_AGENT_API_PORT=8080

EXPOSE 8080

USER orion:orion

# Liveness probe via the Bedrock AgentCore contract endpoint.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request,sys; \
r=urllib.request.urlopen('http://127.0.0.1:8080/ping', timeout=3); \
sys.exit(0 if r.status == 200 else 1)" || exit 1

# Entrypoint: uvicorn factory wired to settings-derived config.
ENTRYPOINT ["python", "-m", "orion_cognitive_agent.api.server"]
