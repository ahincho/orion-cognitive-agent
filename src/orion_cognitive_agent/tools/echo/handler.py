"""Echo tool handler - pure business logic, no @tool decorator.

Separating handler from the LangChain-decorated wrapper
(``tool.py``) keeps the logic unit-testable without instantiating an
LLM. Tools are organised this way across the ORION monorepo; this file
establishes the convention for ``orion-cognitive-agent``.
"""

from __future__ import annotations

from typing import Any, Literal

EchoStatus = Literal["success", "error"]


def echo_handler(text: str) -> dict[str, Any]:
    """Return a structured envelope echoing the input text.

    Pure function - no I/O, no LLM dependency. Tests can invoke this
    directly without any LangGraph, langchain-aws, or DeepAgents setup.

    Args:
        text: The user-supplied text to echo back.

    Returns:
        ``{"status": "success", "data": {"echo": <text>}, "errors": None}``
        on success, ``{"status": "error", "data": None, "errors": [...]}``
        on invalid input.
    """
    if not isinstance(text, str):
        return {
            "status": "error",
            "data": None,
            "errors": ["text must be a string"],
        }
    if not text.strip():
        return {
            "status": "error",
            "data": None,
            "errors": ["text must be a non-empty string"],
        }
    return {
        "status": "success",
        "data": {"echo": text},
        "errors": None,
    }


__all__ = ["echo_handler"]
