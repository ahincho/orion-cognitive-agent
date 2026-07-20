"""Markdown prompt loader for ORION Cognitive Agent.

Prompts live as ``.md`` files in this directory so that prompt
engineering becomes version-controlled, diff-friendly, and reviewable
as Markdown. Each file starts with a YAML frontmatter block (audience,
loaded_by, versioned) followed by the prompt body.

Public API:

- :func:`load_prompt` - return the prompt body (without frontmatter).
- :func:`get_prompt_metadata` - return the parsed YAML frontmatter.
- :func:`reload_prompts` - invalidate the cache (for tests / runtime edits).
- :func:`list_prompts` - return the names of all available prompts.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, TypedDict, cast

import yaml

from orion_cognitive_agent.config import get_settings

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


class PromptMetadata(TypedDict):
    """Parsed YAML frontmatter for a prompt file."""

    audience: str
    loaded_by: str
    versioned: bool


def _parse_prompt_file(path: Path) -> tuple[PromptMetadata, str]:
    """Read a prompt file and split it into (metadata, body).

    Returns ``(frontmatter_dict, prompt_body)``. Raises
    ``FileNotFoundError`` if the file is missing and ``ValueError`` if
    the frontmatter is malformed. Falls back to empty metadata if no
    frontmatter is present.
    """
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return PromptMetadata(audience="", loaded_by="", versioned=False), text

    fm_text, body = match.group(1), match.group(2)
    try:
        raw_meta: Any = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path.name}: {exc}") from exc

    meta = cast(PromptMetadata, raw_meta)
    return meta, body.strip()


def _read_prompt_file(name: str) -> tuple[PromptMetadata, str]:
    """Read+parse a prompt file by stem (no ``.md`` suffix)."""
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt '{name}' not found at {path}")
    return _parse_prompt_file(path)


@lru_cache
def _get_cached_prompt(name: str) -> tuple[PromptMetadata, str]:
    """Cached read of a prompt file. Use :func:`reload_prompts` to flush."""
    return _read_prompt_file(name)


def load_prompt(name: str) -> str:
    """Return the body of the named prompt (without frontmatter)."""
    _, body = _get_cached_prompt(name)
    return body


def get_prompt_metadata(name: str) -> PromptMetadata:
    """Return the parsed YAML frontmatter for the named prompt."""
    meta, _ = _get_cached_prompt(name)
    return meta


def reload_prompts() -> None:
    """Invalidate the prompt cache.

    Useful in tests and in admin endpoints that allow runtime prompt
    edits. Also resets the ``get_settings`` cache so that
    ``prompt settings overrides`` (a future feature) take effect.
    """
    _get_cached_prompt.cache_clear()
    get_settings.cache_clear()


def list_prompts() -> list[str]:
    """Return the stems of all ``.md`` files in :data:`PROMPTS_DIR`."""
    return sorted(p.stem for p in PROMPTS_DIR.glob("*.md"))


__all__ = [
    "PROMPTS_DIR",
    "PromptMetadata",
    "get_prompt_metadata",
    "list_prompts",
    "load_prompt",
    "reload_prompts",
]
