"""Smoke tests for ORION Cognitive Agent.

These tests verify the bootstrap contract: the package imports, settings
load from environment, the agent factory returns a usable handle, and
the FastAPI app responds to ``GET /health``.

They run without AWS credentials (covered by the ``environment=local``
default in ``Settings``) and without the ``bedrock`` optional dependency
group installed.
"""
