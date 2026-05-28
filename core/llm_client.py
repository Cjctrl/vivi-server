import json
from typing import Any, Dict, List, Optional

import structlog

from core.ollama_client import OllamaClientError, get_client

logger = structlog.get_logger(__name__).bind(component="core")


class LLMClient:
    """Thin facade over OllamaClient that adds JSON parsing and a fallback return value.

    All actual HTTP calls — including retry and circuit breaker — are handled
    by the shared OllamaClient singleton returned by get_client().
    """

    def __init__(self, default_temperature: float = 0.1):
        self.default_temperature = default_temperature
        self._client = get_client()

    def chat_json(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        fallback: Any = None,
    ) -> Any:
        """Send a chat request and parse the result as JSON."""
        try:
            content = self._client.chat(
                model,
                messages,
                temperature=temperature if temperature is not None else self.default_temperature,
            )
            return self._parse_json(content, fallback)
        except OllamaClientError as exc:
            logger.error("LLM chat_json failed: %s", exc)
            return fallback

    def embeddings(self, model: str, prompt: str) -> List[float]:
        """Request embeddings from Ollama."""
        try:
            return self._client.embed(model, prompt)
        except OllamaClientError as exc:
            logger.error("LLM embeddings failed: %s", exc)
            return []

    def _parse_json(self, content: str, fallback: Any = None) -> Any:
        """Try to parse a JSON string, stripping markdown wrappers and stray text."""
        if not isinstance(content, str):
            return fallback

        text = content.strip()
        # Remove markdown code fences if present
        if text.startswith("```") and text.endswith("```"):
            text = text[3:-3].strip()

        if "{" not in text and "[" not in text:
            logger.warning("LLM JSON parse failed: no JSON delimiters found")
            return fallback

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning("LLM JSON parse error: %s; raw output: %s", exc, text[:500])
            # Try to locate the first JSON object or array in the text
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                snippet = text[start : end + 1]
                try:
                    return json.loads(snippet)
                except json.JSONDecodeError:
                    pass

            start = text.find("[")
            end = text.rfind("]")
            if start != -1 and end != -1 and end > start:
                snippet = text[start : end + 1]
                try:
                    return json.loads(snippet)
                except json.JSONDecodeError:
                    pass

            return fallback
