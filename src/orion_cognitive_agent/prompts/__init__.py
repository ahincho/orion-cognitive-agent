"""System prompts for ORION Cognitive Agent.

Prompts are versioned as ``.md`` files in this directory and loaded via
:mod:`orion_cognitive_agent.prompts.loader`. This package re-exports
the canonical names used by the factory and downstream tooling.

- ``SYSTEM_PROMPT`` - coordinator's main system prompt.
- ``reload_prompts()`` - invalidate the loader cache (for tests / admin).
- ``list_prompts()`` - list all available prompts.
"""

from orion_cognitive_agent.prompts.loader import (
    list_prompts,
    load_prompt,
    reload_prompts,
)

SYSTEM_PROMPT = load_prompt("coordinator")

__all__ = [
    "SYSTEM_PROMPT",
    "list_prompts",
    "reload_prompts",
]
