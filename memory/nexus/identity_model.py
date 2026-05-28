"""
memory/nexus/identity_model.py
Layer 1 of Memory V2 — the Semantic Identity Model.

Where the rest of NEXUS stores *what the user said*, this layer stores *who the
user is*: a structured, evolving profile inferred from observed interactions
rather than from any static config. The conductor feeds every completed
interaction in (best-effort, fire-and-forget) and pulls a short context blurb
out before each task to prime agent prompts.

Design constraints (all enforced below):
  * Never block a task — update_from_interaction degrades to a silent no-op if
    Ollama is down, and is throttled to at most one LLM call per 5 minutes.
  * Persist to identity.json under MEMORY_DB_PATH so the profile survives
    restarts.
  * Merge new signal into the existing model with weighted confidence instead
    of clobbering it, so a single noisy interaction can't swing a trait wildly.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import CONDUCTOR_MODEL, MEMORY_DB_PATH
from core.llm_client import LLMClient

logger = logging.getLogger(__name__)


def _atomic_write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    """Write text atomically: write to a sibling temp file, then os.replace into place.

    Guarantees: either the old file persists unchanged, or the new content is fully
    written and visible. No half-written state is observable to readers.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding) as fh:
            fh.write(content)
        os.replace(tmp, path)
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise

# At most one LLM-backed update this often — guards against thrashing the model
# when many tasks complete in quick succession.
_MIN_UPDATE_INTERVAL = timedelta(minutes=5)

# Exponential-moving-average weight applied to a freshly observed trait
# confidence. Old value keeps (1 - this); new observation contributes this.
# Low enough that one interaction nudges rather than overwrites.
_TRAIT_EMA_WEIGHT = 0.4

_IDENTITY_FILE = "identity.json"

_EXTRACTION_SYSTEM = (
    "You maintain an evolving profile of a single user from one interaction at "
    "a time. Extract ONLY genuinely NEW signal about who the user is — never "
    "restate what is already known, and never include task content or transient "
    "state. Return ONLY a JSON object with these optional keys (omit a key "
    "entirely if there is no new signal for it):\n"
    '  "inferred_traits": {"<trait_name>": <confidence 0.0-1.0>},\n'
    '  "expertise_map": {"<domain>": "beginner|intermediate|expert"},\n'
    '  "communication_preferences": {"<pref_name>": <value>},\n'
    '  "recurring_goals": ["<goal>"],\n'
    '  "known_dislikes": ["<dislike>"]\n'
    "Trait names are snake_case predicates, e.g. prefers_concise_answers, "
    "likes_code_examples. Return {} if nothing new can be inferred."
)


class UserIdentityModel:
    """Structured, self-updating profile of the user.

    The model is small and entirely in-memory once loaded; persistence is a
    plain JSON file. All public methods are safe to call from worker threads —
    a single lock guards every read/modify/write of the underlying dict.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        base = Path(db_path) if db_path is not None else Path(MEMORY_DB_PATH)
        base.mkdir(parents=True, exist_ok=True)
        self._path = base / _IDENTITY_FILE

        self._lock = threading.Lock()
        self._llm = LLMClient()

        # Profile fields
        self.inferred_traits: Dict[str, float] = {}
        self.expertise_map: Dict[str, str] = {}
        self.communication_preferences: Dict[str, Any] = {}
        self.recurring_goals: List[str] = []
        self.known_dislikes: List[str] = []
        self.last_updated: Optional[datetime] = None

        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("[identity] load failed, starting fresh: %s", exc)
            return
        self.inferred_traits = {k: float(v) for k, v in (data.get("inferred_traits") or {}).items()}
        self.expertise_map = dict(data.get("expertise_map") or {})
        self.communication_preferences = dict(data.get("communication_preferences") or {})
        self.recurring_goals = list(data.get("recurring_goals") or [])
        self.known_dislikes = list(data.get("known_dislikes") or [])
        raw_ts = data.get("last_updated")
        if raw_ts:
            try:
                self.last_updated = datetime.fromisoformat(raw_ts)
            except ValueError:
                self.last_updated = None

    def _save(self) -> None:
        payload = {
            "inferred_traits": self.inferred_traits,
            "expertise_map": self.expertise_map,
            "communication_preferences": self.communication_preferences,
            "recurring_goals": self.recurring_goals,
            "known_dislikes": self.known_dislikes,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }
        try:
            _atomic_write_text(self._path, json.dumps(payload, indent=2))
        except Exception as exc:
            logger.warning("[identity] save failed: %s", exc)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_from_interaction(
        self, task: str, result: str, feedback: Optional[str] = None
    ) -> None:
        """Fold one interaction's new signal into the profile.

        Best-effort and self-throttling: returns silently if updated within the
        last 5 minutes or if the LLM is unavailable. Never raises.
        """
        now = datetime.now(timezone.utc)

        # Throttle — read last_updated under the lock so concurrent callers can't
        # both slip past the gate.
        with self._lock:
            if self.last_updated is not None:
                last = self.last_updated
                if last.tzinfo is None:
                    last = last.replace(tzinfo=timezone.utc)
                if now - last < _MIN_UPDATE_INTERVAL:
                    return
            # Reserve this slot immediately so a second concurrent call bails out.
            self.last_updated = now

        signal = self._extract_signal(task, result, feedback)
        if not isinstance(signal, dict) or not signal:
            # Nothing new — still persist the bumped last_updated so the throttle
            # window is honoured.
            with self._lock:
                self._save()
            return

        with self._lock:
            self._merge(signal)
            self._save()

    def _extract_signal(
        self, task: str, result: str, feedback: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Ask the small model for new identity signal. Returns {} / None on failure."""
        user_block = f"TASK:\n{task}\n\nRESULT:\n{result}"
        if feedback:
            user_block += f"\n\nUSER FEEDBACK:\n{feedback}"
        # Tell the model what we already know so it returns only *new* signal.
        known = json.dumps(
            {
                "inferred_traits": sorted(self.inferred_traits.keys()),
                "expertise_map": self.expertise_map,
                "recurring_goals": self.recurring_goals,
                "known_dislikes": self.known_dislikes,
            }
        )
        try:
            return self._llm.chat_json(
                model=CONDUCTOR_MODEL,
                messages=[
                    {"role": "system", "content": _EXTRACTION_SYSTEM},
                    {"role": "user", "content": f"ALREADY KNOWN:\n{known}\n\n{user_block}"},
                ],
                fallback={},
            )
        except Exception as exc:
            logger.debug("[identity] extraction failed (ignored): %s", exc)
            return {}

    def _merge(self, signal: Dict[str, Any]) -> None:
        """Merge extracted signal into the profile. Caller must hold the lock."""
        traits = signal.get("inferred_traits")
        if isinstance(traits, dict):
            for name, conf in traits.items():
                try:
                    conf_f = max(0.0, min(1.0, float(conf)))
                except (TypeError, ValueError):
                    continue
                if name in self.inferred_traits:
                    old = self.inferred_traits[name]
                    self.inferred_traits[name] = round(
                        old * (1 - _TRAIT_EMA_WEIGHT) + conf_f * _TRAIT_EMA_WEIGHT, 4
                    )
                else:
                    self.inferred_traits[name] = round(conf_f, 4)

        expertise = signal.get("expertise_map")
        if isinstance(expertise, dict):
            for domain, level in expertise.items():
                if isinstance(level, str) and level:
                    self.expertise_map[domain] = level

        prefs = signal.get("communication_preferences")
        if isinstance(prefs, dict):
            self.communication_preferences.update(prefs)

        for goal in signal.get("recurring_goals") or []:
            if isinstance(goal, str) and goal and goal not in self.recurring_goals:
                self.recurring_goals.append(goal)

        for dislike in signal.get("known_dislikes") or []:
            if isinstance(dislike, str) and dislike and dislike not in self.known_dislikes:
                self.known_dislikes.append(dislike)

    # ------------------------------------------------------------------
    # Read — context injection
    # ------------------------------------------------------------------

    def get_context_for_task(self, task: str) -> str:
        """Return a 2-3 sentence summary of identity context relevant to *task*.

        Deterministic and I/O-free — this runs inline before task execution, so
        it must never make a network call. It simply formats the stored profile,
        lightly biased toward expertise domains whose name appears in the task.
        """
        with self._lock:
            if not (
                self.inferred_traits
                or self.expertise_map
                or self.communication_preferences
                or self.recurring_goals
                or self.known_dislikes
            ):
                return ""

            sentences: List[str] = []

            # Strongest traits first.
            top_traits = sorted(
                self.inferred_traits.items(), key=lambda kv: kv[1], reverse=True
            )[:3]
            top_traits = [(n, c) for n, c in top_traits if c >= 0.5]
            if top_traits:
                rendered = ", ".join(n.replace("_", " ") for n, _ in top_traits)
                sentences.append(f"The user tends to: {rendered}.")

            # Expertise — surface task-relevant domains first, else the strongest.
            if self.expertise_map:
                task_lower = task.lower()
                relevant = [d for d in self.expertise_map if d.lower() in task_lower]
                domains = relevant or list(self.expertise_map.keys())[:2]
                rendered = ", ".join(f"{d} ({self.expertise_map[d]})" for d in domains[:3])
                if rendered:
                    sentences.append(f"Known expertise: {rendered}.")

            prefs_bits: List[str] = []
            if self.communication_preferences:
                prefs_bits.append(
                    ", ".join(
                        f"{k}={v}" for k, v in list(self.communication_preferences.items())[:3]
                    )
                )
            if self.known_dislikes:
                prefs_bits.append("dislikes " + "; ".join(self.known_dislikes[:2]))
            if prefs_bits:
                sentences.append("Preferences: " + "; ".join(prefs_bits) + ".")

            return " ".join(sentences[:3])

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain-dict snapshot of the profile (for diagnostics/tests)."""
        with self._lock:
            return {
                "inferred_traits": dict(self.inferred_traits),
                "expertise_map": dict(self.expertise_map),
                "communication_preferences": dict(self.communication_preferences),
                "recurring_goals": list(self.recurring_goals),
                "known_dislikes": list(self.known_dislikes),
                "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_identity_model: Optional[UserIdentityModel] = None
_singleton_lock = threading.Lock()


def get_identity_model() -> UserIdentityModel:
    """Return the process-wide UserIdentityModel singleton."""
    global _identity_model
    if _identity_model is None:
        with _singleton_lock:
            if _identity_model is None:
                _identity_model = UserIdentityModel()
    return _identity_model