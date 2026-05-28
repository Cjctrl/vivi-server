"""
Abstract base class for all agents with safe execution wrapper.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Dict

import structlog

logger = structlog.get_logger(__name__).bind(component="core")


class BaseAgent(ABC):
    """All agents must inherit from BaseAgent and implement execute()."""

    name: str

    @abstractmethod
    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent logic."""
        ...

    def safe_execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Wrap execute() with timing, logging, and error capture."""
        start = time.perf_counter()
        logger.debug("[%s] starting | args_keys=%s", self.name, list(arguments.keys()))
        try:
            result = self.execute(arguments)
            elapsed = time.perf_counter() - start
            result.setdefault("status", "success")
            result.setdefault("confidence", 0.5)
            result.setdefault("error", None)
            result["_agent"] = self.name
            result["_elapsed_ms"] = round(elapsed * 1000, 1)
            logger.info(
                "[%s] completed in %.1fms | confidence=%.2f",
                self.name,
                elapsed * 1000,
                result["confidence"],
            )
            return result
        except Exception as exc:
            elapsed = time.perf_counter() - start
            logger.exception("[%s] failed after %.1fms", self.name, elapsed * 1000)
            return {
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}",
                "confidence": 0.0,
                "_agent": self.name,
                "_elapsed_ms": round(elapsed * 1000, 1),
            }
