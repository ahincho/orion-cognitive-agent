"""Echo tool - thin LangChain @tool wrapper around echo_handler.

The wrapper delegates to the handler and unwraps the structured
envelope so the LLM receives the data dict directly. Errors are
surfaced as a plain ``{"error": True, "errors": [...]}`` so the LLM
can recover gracefully and ask the user for clarification.

This tool is the Sprint A minimum viable surface for the deepagent
(in addition to whatever SubAgents land in later Sprints). It exists
primarily so we can validate that ``create_deep_agent`` is wired
correctly end-to-end before bringing in domain-specific tools.
"""

from __future__ import annotations

from typing import Any, cast

from langchain_core.tools import tool

from orion_cognitive_agent.tools.echo.handler import echo_handler


@tool
def echo_tool(text: str) -> dict[str, Any]:
    """Echo back the input text verbatim.

    Useful as a smoke-test tool for verifying that the deepagent is
    wired correctly. Will be deprecated once the first domain-specific
    tool lands.

    Args:
        text: Free-form text supplied by the user/LLM.

    Returns:
        ``{"echo": <text>}`` on success, or
        ``{"error": True, "errors": [<msg>]}`` if validation failed.
    """
    result = echo_handler(text=text)
    if result["status"] == "error":
        return {"error": True, "errors": result["errors"]}
    return cast(dict[str, Any], result["data"])


__all__ = ["echo_tool"]
