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

The LangChain ``@tool`` wrapper is lazy-imported so this package
stays usable even when the ``bedrock`` dependency group is not
installed (handlers remain importable; only the tool wrapper
requires ``langchain_core``).
"""

from orion_cognitive_agent.tools.echo.handler import echo_handler

__all__ = ["ECHO_TOOL", "echo_handler", "echo_tool"]


def __getattr__(name: str) -> object:
    """Lazy-load the LangChain ``@tool`` wrapper on first access.

    Avoids importing ``langchain_core`` at module load time so
    smoke tests and ``Settings`` resolution work even without the
    ``bedrock`` group installed.
    """
    if name == "ECHO_TOOL":
        from orion_cognitive_agent.tools.echo.tool import echo_tool

        return echo_tool
    if name == "echo_tool":
        from orion_cognitive_agent.tools.echo.tool import echo_tool

        return echo_tool
    msg = f"module 'orion_cognitive_agent.tools' has no attribute {name!r}"
    raise AttributeError(msg)
