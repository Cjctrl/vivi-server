"""
Unified confidence scoring utilities for all agents.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConfidenceScore(BaseModel):
    value: float = Field(..., ge=0.0, le=1.0)
    level: ConfidenceLevel
    reason: str = ""

    @classmethod
    def from_value(cls, value: float, reason: str = "") -> "ConfidenceScore":
        value = max(0.0, min(1.0, value))
        if value >= 0.75:
            level = ConfidenceLevel.HIGH
        elif value >= 0.40:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW
        return cls(value=value, level=level, reason=reason)


def hits_confidence(hits: List[Any], top_score_weight: float = 0.7) -> float:
    """Estimate confidence for ranked search hits."""
    if not hits:
        return 0.0
    scores = []
    for hit in hits:
        if isinstance(hit, dict):
            scores.append(float(hit.get("score", 0.0)))
        else:
            scores.append(float(getattr(hit, "score", 0.0)))
    top_score = scores[0] if scores else 0.0
    avg_score = sum(scores) / len(scores) if scores else 0.0
    confidence = top_score_weight * top_score + (1.0 - top_score_weight) * avg_score
    return max(0.0, min(1.0, confidence))


def llm_output_confidence(text: str, has_context: bool) -> float:
    """Heuristic confidence for LLM-generated text."""
    lower = text.lower()
    uncertainty_phrases = [
        "i don't know",
        "not sure",
        "unable to",
        "cannot",
        "i'm not sure",
        "no information",
        "unknown",
    ]
    if any(phrase in lower for phrase in uncertainty_phrases):
        return 0.2
    if len(text) < 50:
        return 0.4
    length_bonus = min(0.2, len(text) / 2000.0)
    context_bonus = 0.1 if has_context else 0.0
    return max(0.0, min(0.95, 0.6 + length_bonus + context_bonus))


def error_confidence() -> float:
    """Confidence for error responses."""
    return 0.0
