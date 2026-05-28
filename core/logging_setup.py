"""
core/logging_setup.py
Single structlog configuration for the whole V.I.V.I process.

Historically core/, agents/, and overlay/ used the stdlib `logging` module
while orchestration/ used structlog, so log output was inconsistent and carried
no correlation context. This module gives everyone one structlog pipeline.

Two correlation fields flow through every record:

  * component — bound per logger at creation, e.g. ``get_logger("overlay")`` or
    ``structlog.get_logger(__name__).bind(component="coding_agent")``. Says
    *which subsystem* emitted the line.
  * task_id — bound into structlog's contextvars by the conductor for the
    duration of a task (and re-bound inside agent worker threads, see
    orchestration/conductor.py AsyncAgentWrapper). Says *which task* the line
    belongs to. ``merge_contextvars`` below pulls it into every record emitted
    while the contextvar is set — including from agent threads.

Call configure_logging() once at process start (entrypoints + conftest). It is
idempotent, so calling it again is harmless.
"""

from __future__ import annotations

import logging
import os

import structlog

_configured = False


def configure_logging(level: str | None = None) -> None:
    """Configure structlog process-wide. Idempotent.

    Existing printf-style call sites (``logger.info("x %s", y)``) keep working:
    structlog's FilteringBoundLogger applies %-formatting to positional args
    before the processor chain runs, so no call site needs rewriting.
    """
    global _configured
    if _configured:
        return

    log_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    structlog.configure(
        processors=[
            # Pull contextvars (task_id, agent, …) into every event first.
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    _configured = True


def get_logger(component: str, **initial_values):
    """Return a structlog logger pre-bound with a ``component`` field.

    Convenience wrapper so callers can write::

        from core.logging_setup import get_logger
        logger = get_logger("overlay")

    Equivalent to ``structlog.get_logger().bind(component=component, ...)``.
    """
    return structlog.get_logger().bind(component=component, **initial_values)
