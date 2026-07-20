"""Unified logging configuration for ORION Cognitive Agent.

Idempotent: calling :func:`setup_logging` more than once with the same
level does not duplicate handlers. The format mirrors the
``spark-match-08-deep-agent`` reference so log lines can be grep'd
uniformly across ORION services.

Usage:
    from orion_cognitive_agent.config import get_settings
    from orion_cognitive_agent.utils import setup_logging

    setup_logging(level=get_settings().log_level)
"""

from __future__ import annotations

import logging
import sys

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

_INSTALLED_HANDLERS: set[int] = set()


def _resolve_level(level: str | int | logging.Logger) -> int:
    """Resolve a level name/number/logger to a logging level integer."""
    if isinstance(level, logging.Logger):
        return level.level if level.level != logging.NOTSET else logging.INFO
    if isinstance(level, int):
        return level
    if isinstance(level, str):
        return logging.getLevelNamesMapping().get(level.upper(), logging.INFO)
    return logging.INFO


def setup_logging(
    level: str | int | logging.Logger = logging.INFO,
    *,
    stream: object | None = None,
) -> None:
    """Configure the root logger with the standard format.

    Idempotent: re-running with the same level does not stack handlers.
    First call wins; subsequent calls only adjust the level of existing
    handlers that this module owns.

    Args:
        level: Logging level as int, str name ("DEBUG"/"INFO"/...), or a
            ``logging.Logger`` instance.
        stream: Optional stream for the StreamHandler. Defaults to
            ``sys.stderr`` so agent output on stdout stays uncluttered.
    """
    resolved = _resolve_level(level)

    root = logging.getLogger()
    root.setLevel(resolved)

    existing = next(
        (h for h in root.handlers if id(h) in _INSTALLED_HANDLERS),
        None,
    )
    if existing is None:
        handler = logging.StreamHandler(stream if stream is not None else sys.stderr)  # type: ignore[arg-type]
        handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        root.addHandler(handler)
        _INSTALLED_HANDLERS.add(id(handler))
    else:
        existing.setLevel(resolved)
        if existing.formatter is None:
            existing.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

    if resolved > logging.DEBUG:
        for noisy in ("httpx", "httpcore", "urllib3"):
            logging.getLogger(noisy).setLevel(logging.WARNING)
    else:
        for noisy in ("httpx", "httpcore", "urllib3"):
            logging.getLogger(noisy).setLevel(logging.NOTSET)
