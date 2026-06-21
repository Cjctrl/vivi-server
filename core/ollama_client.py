"""
Ollama client with retries, timeouts, and circuit breaker.
All LLM calls must go through this client.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

import ollama
import structlog
from config.settings import (
    OLLAMA_MAX_RETRIES,
    OLLAMA_TIMEOUT_SECONDS,
    OLLAMA_CIRCUIT_THRESHOLD,
    OLLAMA_CIRCUIT_RESET_SECONDS,
)

logger = structlog.get_logger(__name__).bind(component="core")


class OllamaClientError(Exception):
    """Base exception for Ollama client errors."""


class OllamaCircuitOpenError(OllamaClientError):
    """Raised when the Ollama circuit breaker is open."""


class OllamaCallError(OllamaClientError):
    """Raised after all retry attempts fail."""


class EmbeddingDimensionError(OllamaClientError):
    """Raised when the returned embedding vector has the wrong size."""


class OllamaClient:
    """Resilient Ollama wrapper with retry and circuit breaker support."""

    def __init__(
        self,
        max_retries: int = OLLAMA_MAX_RETRIES,
        base_backoff: float = 1.5,
        timeout: int = OLLAMA_TIMEOUT_SECONDS,
        circuit_threshold: int = OLLAMA_CIRCUIT_THRESHOLD,
        circuit_reset_seconds: int = OLLAMA_CIRCUIT_RESET_SECONDS,
    ) -> None:
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self.timeout = timeout
        self.circuit_threshold = circuit_threshold
        self.circuit_reset_seconds = circuit_reset_seconds

        # The module-level ollama.chat/embeddings helpers use a default client
        # with no timeout, so a hung Ollama request would block forever. Route
        # all calls through a Client whose underlying httpx client carries our
        # timeout, so self.timeout is applied to the actual HTTP requests.
        self._ollama = ollama.Client(timeout=self.timeout)

        self._failures = 0
        self._last_failure_time = 0.0
        self._lock = threading.Lock()

    def _is_circuit_open(self) -> bool:
        with self._lock:
            if self._failures >= self.circuit_threshold:
                if time.monotonic() - self._last_failure_time >= self.circuit_reset_seconds:
                    self._failures = 0
                    return False
                return True
            return False

    def _record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            self._last_failure_time = time.monotonic()

    def _record_success(self) -> None:
        with self._lock:
            self._failures = 0

    def _call_with_retry(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        if self._is_circuit_open():
            raise OllamaCircuitOpenError("Circuit breaker open, refusing call")

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                start = time.monotonic()
                result = func(*args, **kwargs)
                elapsed = time.monotonic() - start
                logger.debug(
                    "Ollama call succeeded | attempt=%d | elapsed=%.2fs",
                    attempt,
                    elapsed,
                )
                self._record_success()
                return result
            except (ollama.ResponseError, TimeoutError, ConnectionError) as exc:
                # Only transient failures are retried. A 4xx ResponseError
                # (bad request, auth, not found) will never succeed on retry,
                # so fail fast instead of burning the retry budget.
                status = getattr(exc, "status_code", None)
                if status is not None and status < 500:
                    self._record_failure()
                    raise
                last_error = exc
                logger.warning(
                    "Ollama call failure | attempt=%d | error=%s",
                    attempt,
                    str(exc),
                )
                if attempt < self.max_retries:
                    delay = self.base_backoff ** attempt
                    time.sleep(delay)
                    continue
                self._record_failure()
                break

        raise OllamaCallError(
            f"Ollama call failed after {self.max_retries} retries: {last_error}"
        ) from last_error

    def chat(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        **options: Any,
    ) -> str:
        """Send a chat request and return the assistant message content."""

        def _chat() -> str:
            response = self._ollama.chat(
                model=model,
                messages=messages,
                options={"temperature": options.pop("temperature", 0.3), **options},
            )
            # ollama>=0.4 returns a ChatResponse object; older releases returned a
            # plain dict. Handle both: pull message.content off whichever shape.
            message = (
                response.get("message")
                if isinstance(response, dict)
                else getattr(response, "message", None)
            )
            if message is not None:
                content = (
                    message.get("content")
                    if isinstance(message, dict)
                    else getattr(message, "content", None)
                )
                if content is not None:
                    return str(content).strip()
            return str(response).strip()

        return self._call_with_retry(_chat)

    def embed(self, model: str, text: str) -> List[float]:
        """Return an embedding vector for text."""

        def _embed() -> List[float]:
            response = self._ollama.embeddings(model=model, prompt=text)
            # ollama>=0.4 returns an EmbeddingsResponse object; older returned a dict.
            if isinstance(response, dict):
                embedding = response.get("embedding", [])
            else:
                embedding = getattr(response, "embedding", None) or []
            if not embedding:
                raise OllamaCallError("Ollama embeddings returned no vector")
            return list(embedding)

        vector = self._call_with_retry(_embed)
        if model == "nomic-embed-text" and len(vector) != 768:
            raise EmbeddingDimensionError(
                f"Expected dimension 768 for nomic-embed-text, got {len(vector)}"
            )
        return vector

    def is_model_available(self, model: str) -> bool:
        """Return True if the model is available locally in Ollama."""
        try:
            models = self._ollama.list()
            if isinstance(models, dict):
                results = models.get("models", [])
            else:
                results = models
            return any(getattr(item, "name", None) == model or item.get("name") == model for item in results)
        except Exception:
            return False


_default_client: Optional[OllamaClient] = None
_default_client_lock = threading.Lock()


def get_client() -> OllamaClient:
    """Return a shared OllamaClient singleton.

    Double-checked locking so concurrent agents racing on first use don't each
    build a client (and tear down the shared circuit-breaker state). Mirrors the
    guard in vivi-brain's core/ollama_client.py.
    """
    global _default_client
    if _default_client is None:
        with _default_client_lock:
            if _default_client is None:
                _default_client = OllamaClient()
    return _default_client
