"""Tools for ORION Cognitive Agent.

Convention (shared across the ORION monorepo):

- ``<tool>/handler.py`` - pure business logic, no ``@tool`` decorator.
- ``<tool>/tool.py``   - thin LangChain ``@tool`` wrapper.

The handlers are unit-testable without LLM dependencies; the wrappers
carry the ``@tool`` decorator, docstring, and type hints that the
LangGraph runtime needs.

Public API:

- :data:`ECHO_TOOL` - scaffold tool, lands in Sprint A. Will be
  deprecated once the first domain-specific tool is onboarded.
"""

from orion_cognitive_agent.tools.echo.tool import echo_tool

ECHO_TOOL = echo_tool

__all__ = ["ECHO_TOOL", "echo_tool"]
