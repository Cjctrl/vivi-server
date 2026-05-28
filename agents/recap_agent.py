"""
Recap Agent — writes dated session reports to the NEXUS knowledge base.

Each session becomes a node at 'session-recaps/{timestamp}' with type
'session-recap' and tags [vivi, session-recap, auto-generated].
All writes go through AgentMemoryClient; no direct file I/O.
"""

from __future__ import annotations

import concurrent.futures
import structlog
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config.settings import CONDUCTOR_MODEL, RECAP_PROSE_ENABLED
from core.base_agent import BaseAgent
from core.ollama_client import OllamaCallError, OllamaCircuitOpenError, get_client
from memory.nexus.nexus_memory_bridge import (
    AgentMemoryClient,
    NexusUnavailableError,
    get_memory_client,
)

logger = structlog.get_logger(__name__).bind(component="recap_agent")

_SUMMARY_MODEL = CONDUCTOR_MODEL
_LATENCY_THRESHOLD = 0.05
_PROSE_TIMEOUT = 30
_COLLECTION = "session-recaps"


class RecapAgent(BaseAgent):
    """Post-run recap agent — writes a NEXUS node for every session."""

    name = "recap_agent"

    def __init__(self, client: Optional[AgentMemoryClient] = None) -> None:
        self._client = client or get_memory_client()

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        task: str = arguments.get("task", "Unknown task")
        task_results: Dict[str, Any] = arguments.get("task_results", {})
        cognitive_analysis: Dict[str, Any] = arguments.get("cognitive_analysis", {})
        session_id: str = arguments.get("session_id", "")

        now_utc = datetime.now(timezone.utc)
        slug = now_utc.strftime("%Y-%m-%d-%H-%M-%S-utc")
        title = f"{_COLLECTION}/{slug}"

        body = self._build_body(
            task=task,
            task_results=task_results,
            cognitive_analysis=cognitive_analysis,
            session_id=session_id,
            now_utc=now_utc,
        )

        tags = ["vivi", "session-recap", "auto-generated"]
        if session_id:
            tags.append(f"session:{session_id}")

        try:
            # Check for duplicate session before writing
            if session_id:
                existing = self._client.get_by_tag(f"session:{session_id}")
                if existing:
                    title = f"{_COLLECTION}/{slug}-retry"

            node = self._client.create_node(
                title=title,
                body=body,
                tags=tags,
                node_type="session-recap",
            )
            logger.info("[recap_agent] wrote node: %s", title)
            return {
                "status": "success",
                "title": node.get("title", title),
                "confidence": 1.0,
                "error": None,
            }
        except NexusUnavailableError as exc:
            logger.error("[recap_agent] NEXUS unavailable: %s", exc)
            return {"status": "error", "title": title, "error": str(exc), "confidence": 0.0}
        except Exception as exc:
            logger.error("[recap_agent] write failed: %s", exc)
            return {"status": "error", "title": title, "error": str(exc), "confidence": 0.0}

    # ------------------------------------------------------------------

    def _build_body(
        self,
        task: str,
        task_results: Dict[str, Any],
        cognitive_analysis: Dict[str, Any],
        session_id: str,
        now_utc: datetime,
    ) -> str:
        display_title = now_utc.strftime("Session Recap %Y-%m-%d %H:%M:%S UTC")
        sections: List[str] = [
            f"# {display_title}\n",
            self._meta_block(now_utc, session_id),
            "## Task\n",
            f"> {task}\n",
        ]

        if cognitive_analysis:
            sections.append(self._routing_section(cognitive_analysis))

        sections.append(self._agent_results_section(task_results))
        sections.append(self._stats_section(task_results))

        if RECAP_PROSE_ENABLED:
            prose = self._generate_prose_review(task, task_results)
            if prose:
                sections += ["## Review\n", prose + "\n"]

        return "\n".join(sections)

    def _meta_block(self, now_utc: datetime, session_id: str) -> str:
        lines = [
            "| Field | Value |",
            "| --- | --- |",
            f"| **Date (UTC)** | {now_utc.strftime('%A, %B %d %Y')} |",
            f"| **Time (UTC)** | {now_utc.strftime('%H:%M:%S')} |",
        ]
        if session_id:
            lines.append(f"| **Session ID** | `{session_id}` |")
        return "\n".join(lines) + "\n"

    def _routing_section(self, cognitive_analysis: Dict[str, Any]) -> str:
        routing = cognitive_analysis.get("routing_recommendation", {})
        profile = cognitive_analysis.get("cognitive_profile", {})
        lines = [
            "## Routing Decision\n",
            f"- **Intent type:** {profile.get('intent_type', '—')}",
            f"- **Primary agent:** `{routing.get('primary_agent', '—')}`",
            f"- **Router confidence:** {cognitive_analysis.get('confidence', 0.0):.0%}\n",
        ]
        return "\n".join(lines)

    def _agent_results_section(self, task_results: Dict[str, Any]) -> str:
        if not task_results:
            return "## Agent Results\n\n_No agent results recorded._\n"

        lines = ["## Agent Results\n"]
        for task_id, result in task_results.items():
            agent_name = _get(result, "agent_name") or task_id
            status = _status_str(_get(result, "status", "unknown"))
            execution_time = float(_get(result, "execution_time", 0.0) or 0.0)
            error = _get(result, "error")
            raw_result = _get(result, "result") or _get(result, "result_preview")

            emoji = {"completed": "✅", "failed": "❌", "timeout": "⏱️", "cancelled": "🚫"}.get(
                status.lower(), "❓"
            )
            lines.append(f"### {emoji} `{agent_name}`\n")
            lines.append(f"- **Status:** {status}")
            if execution_time >= _LATENCY_THRESHOLD:
                lines.append(f"- **Duration:** {execution_time:.2f}s")
            if error:
                lines.append(f"- **Error:** {error}")
            if raw_result is not None:
                lines.append(f"- **Output preview:** `{_result_preview(raw_result)}`")
            lines.append("")
        return "\n".join(lines)

    def _stats_section(self, task_results: Dict[str, Any]) -> str:
        if not task_results:
            return ""
        total, completed, failed, timed_out, total_time = 0, 0, 0, 0, 0.0
        for result in task_results.values():
            total += 1
            status = _status_str(_get(result, "status", ""))
            if status == "completed":
                completed += 1
            elif status == "failed":
                failed += 1
            elif status == "timeout":
                timed_out += 1
            total_time += float(_get(result, "execution_time", 0.0) or 0.0)

        health = "🟢 All good" if not failed and not timed_out else (
            "🔴 Failures present" if failed else "🟡 Timeouts present"
        )
        rows = [
            "## Session Statistics\n",
            "| Metric | Value |",
            "| --- | --- |",
            f"| Total agents run | {total} |",
            f"| ✅ Completed | {completed} |",
            f"| ❌ Failed | {failed} |",
            f"| ⏱️ Timed out | {timed_out} |",
            f"| Total wall time | {total_time:.2f}s |",
            f"| Health | {health} |\n",
        ]
        return "\n".join(rows)

    def _generate_prose_review(self, task: str, task_results: Dict[str, Any]) -> str:
        if not task_results:
            return ""

        agent_lines = []
        for task_id, result in task_results.items():
            agent_name = _get(result, "agent_name") or task_id
            status = _status_str(_get(result, "status", "unknown"))
            error = _get(result, "error") or ""
            agent_lines.append(
                f"- {agent_name}: {status}" + (f" — {str(error)[:120]}" if error else "")
            )

        system = (
            "You are V.I.V.I writing an internal session debrief for the NEXUS knowledge base. "
            "Be concise (4–8 sentences). Write in third person. No markdown headings."
        )
        user = f"Task: {task}\n\nAgent outcomes:\n" + "\n".join(agent_lines) + "\n\nWrite the debrief:"

        result_holder: List[str] = []

        def _run() -> None:
            try:
                text = get_client().chat(
                    model=_SUMMARY_MODEL,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=0.4,
                )
                result_holder.append(text)
            except (OllamaCircuitOpenError, OllamaCallError):
                result_holder.append("Prose summary unavailable — LLM not responding.")
            except Exception as exc:
                logger.warning("[recap_agent] prose generation failed: %s", exc)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(_run)
            try:
                future.result(timeout=_PROSE_TIMEOUT)
            except concurrent.futures.TimeoutError:
                logger.warning("[recap_agent] prose summary timed out after %ds", _PROSE_TIMEOUT)
                return "Prose summary timed out."

        return result_holder[0] if result_holder else ""


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _status_str(status: Any) -> str:
    if hasattr(status, "value"):
        return str(status.value)
    return str(status)


def _result_preview(result: Any, max_chars: int = 200) -> str:
    if result is None:
        return "_None_"
    if isinstance(result, dict):
        for key in ("summary", "answer", "solution", "output", "result"):
            if key in result:
                text = str(result[key])
                break
        else:
            text = str(result)
    else:
        text = str(result)
    text = text.replace("\n", " ").strip()
    return text[:max_chars] + ("…" if len(text) > max_chars else "")
