"""
Structured telemetry for agent execution steps.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__).bind(component="core")

_TRACES_DIR = Path("./traces")


@dataclass
class StepTrace:
    trace_id: str
    agent: str
    stage: str
    elapsed_ms: float
    confidence: float
    status: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExecutionTrace:
    """Collects StepTrace objects for one execution run and writes a JSON report."""

    def __init__(self, trace_id: str) -> None:
        self.trace_id = trace_id
        self.steps: List[StepTrace] = []
        self.started_at = datetime.now(timezone.utc).isoformat()

    def add(self, step: StepTrace) -> None:
        self.steps.append(step)

    def record(
        self,
        agent: str,
        stage: str,
        elapsed_ms: float,
        confidence: float,
        status: str,
        error: Optional[str] = None,
        **metadata: Any,
    ) -> None:
        self.add(
            StepTrace(
                trace_id=self.trace_id,
                agent=agent,
                stage=stage,
                elapsed_ms=elapsed_ms,
                confidence=confidence,
                status=status,
                error=error,
                metadata=metadata,
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "started_at": self.started_at,
            "steps": [
                {
                    "trace_id": s.trace_id,
                    "agent": s.agent,
                    "stage": s.stage,
                    "elapsed_ms": s.elapsed_ms,
                    "confidence": s.confidence,
                    "status": s.status,
                    "error": s.error,
                    "metadata": s.metadata,
                }
                for s in self.steps
            ],
        }

    def to_markdown_table(self) -> str:
        header = "| Agent | Stage | Status | Confidence | Elapsed (ms) | Error |"
        sep = "| --- | --- | --- | --- | --- | --- |"
        rows = [
            f"| {s.agent} | {s.stage} | {s.status} | {s.confidence:.2f} | {s.elapsed_ms:.1f} | {s.error or ''} |"
            for s in self.steps
        ]
        return "\n".join([header, sep] + rows)

    def flush(self) -> Optional[Path]:
        """Write trace to ./traces/<trace_id>.json. Returns path on success."""
        try:
            _TRACES_DIR.mkdir(parents=True, exist_ok=True)
            out = _TRACES_DIR / f"{self.trace_id}.json"
            out.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
            logger.debug("Trace written to %s", out)
            return out
        except Exception as exc:
            logger.warning("Failed to write trace: %s", exc)
            return None
