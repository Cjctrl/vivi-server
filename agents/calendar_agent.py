"""
Google Calendar Agent — reads upcoming events into local SQLite.
Shares the OAuth token with classroom_agent.
"""

from __future__ import annotations

import structlog
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.base_agent import BaseAgent

try:
    from config import settings as _settings
except Exception:  # settings should always import, but never hard-fail the agent
    _settings = None

logger = structlog.get_logger(__name__).bind(component="calendar_agent")


def _cfg(name: str, default: str) -> str:
    return (getattr(_settings, name, None) or default) if _settings else default


# Calendar uses the PERSONAL Google account and its OWN token (Classroom uses a
# separate token for the school account). Paths resolve from settings (anchored
# to PROJECT_ROOT) so they're stable regardless of the process's cwd.
# JSON (google-auth authorized-user format), not pickle.
_CREDENTIALS_PATH = Path(_cfg("GOOGLE_CREDENTIALS_PATH", "config/credentials.json"))
_TOKEN_PATH = Path(_cfg("GOOGLE_CALENDAR_TOKEN", "config/google_calendar_token.json"))
_LOGIN_HINT = _cfg("GOOGLE_CALENDAR_ACCOUNT", "") or None

# Full read/WRITE so the agent can also create events.
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
]

_CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "robotics": ["robotics", "ftc", "frc", "robot", "meeting"],
    "exam": ["test", "exam", "quiz", "midterm", "final"],
    "deadline": ["due", "deadline", "submit", "submission"],
    "appointment": ["appointment", "doctor", "dentist"],
}


def _categorize(title: str) -> str:
    lower = title.lower()
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return category
    return "other"


class CalendarAgent(BaseAgent):
    """Reads Google Calendar events and stores them in SQLite for offline querying."""

    name = "calendar_agent"

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        action: str = (arguments.get("action") or "query").lower()

        if not _CREDENTIALS_PATH.exists():
            return {
                "status": "error",
                "error": "Google credentials not found. Place credentials.json in config/.",
                "confidence": 0.0,
            }

        if action == "sync":
            return self._sync()
        elif action == "query":
            return self._query(str(arguments.get("filter", "upcoming")))
        elif action == "create":
            return self._create(arguments)
        else:
            return {
                "status": "error",
                "error": f"Unknown action '{action}'. Use: sync, query, create.",
                "confidence": 0.0,
            }

    # ------------------------------------------------------------------

    def _get_service(self):
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            import httplib2
            from google_auth_httplib2 import AuthorizedHttp
        except ImportError:
            raise RuntimeError(
                "Google API libraries not installed. "
                "Run: pip install google-auth-oauthlib google-api-python-client google-auth-httplib2"
            )

        creds: Optional[Credentials] = None
        if _TOKEN_PATH.exists():
            creds = Credentials.from_authorized_user_file(str(_TOKEN_PATH), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(_CREDENTIALS_PATH), SCOPES)
                kwargs = {"port": 0, "access_type": "offline", "prompt": "consent"}
                if _LOGIN_HINT:
                    kwargs["login_hint"] = _LOGIN_HINT
                creds = flow.run_local_server(**kwargs)
            _TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
            _TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

        # Wrap the credentials in an authorized http with a 15s socket timeout so
        # a hung Google call cannot block the agent forever. build() forbids
        # passing both http= and credentials=, so auth is carried by AuthorizedHttp.
        authed_http = AuthorizedHttp(creds, http=httplib2.Http(timeout=15))
        return build("calendar", "v3", http=authed_http)

    def _sync(self) -> Dict[str, Any]:
        try:
            service = self._get_service()
        except Exception:
            logger.exception("[calendar_agent] failed to build Google service")
            return {"status": "error", "error": "calendar authentication failed", "confidence": 0.0}

        now = datetime.now(timezone.utc)
        time_min = now.isoformat()
        time_max = (now + timedelta(days=14)).isoformat()

        try:
            from sqlalchemy.orm import Session
            from db.school_models import CalendarEvent, engine

            events_synced = 0

            calendars_resp = service.calendarList().list().execute()
            calendars = calendars_resp.get("items", [])

            with Session(engine) as session:
                for cal in calendars:
                    cal_id = cal["id"]
                    cal_name = cal.get("summary", "Unknown")

                    events_resp = (
                        service.events()
                        .list(
                            calendarId=cal_id,
                            timeMin=time_min,
                            timeMax=time_max,
                            singleEvents=True,
                            orderBy="startTime",
                        )
                        .execute()
                    )

                    for event in events_resp.get("items", []):
                        event_id = event["id"]
                        title = event.get("summary", "Untitled")
                        start = event.get("start", {})
                        end = event.get("end", {})

                        all_day = "date" in start
                        start_str = start.get("dateTime") or start.get("date", "")
                        end_str = end.get("dateTime") or end.get("date", "")

                        is_recurring = bool(event.get("recurringEventId"))
                        category = _categorize(title)

                        existing = session.query(CalendarEvent).filter_by(google_event_id=event_id).first()
                        if existing:
                            existing.title = title
                            existing.start_datetime = start_str
                            existing.end_datetime = end_str
                            existing.category = category
                        else:
                            session.add(
                                CalendarEvent(
                                    google_event_id=event_id,
                                    calendar_name=cal_name,
                                    title=title,
                                    start_datetime=start_str,
                                    end_datetime=end_str,
                                    all_day=all_day,
                                    location=event.get("location"),
                                    description=event.get("description"),
                                    is_recurring=is_recurring,
                                    category=category,
                                )
                            )
                            events_synced += 1

                session.commit()

            return {
                "status": "success",
                "events_synced": events_synced,
                "confidence": 1.0,
                "error": None,
            }

        except Exception:
            logger.exception("[calendar_agent] sync failed")
            return {"status": "error", "error": "calendar sync failed", "confidence": 0.0}

    def _create(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Google Calendar event on the primary calendar (WRITE)."""
        try:
            service = self._get_service()
        except Exception:
            logger.exception("[calendar_agent] failed to build Google service")
            return {"status": "error", "error": "calendar authentication failed", "confidence": 0.0}

        summary = str(arguments.get("summary") or arguments.get("title") or "").strip()
        if not summary:
            return {"status": "error", "error": "event needs a title", "confidence": 0.0}

        all_day = bool(arguments.get("all_day"))
        start = arguments.get("start")
        end = arguments.get("end")
        body: Dict[str, Any] = {"summary": summary}
        if arguments.get("description"):
            body["description"] = str(arguments["description"])
        if arguments.get("location"):
            body["location"] = str(arguments["location"])

        try:
            if all_day:
                # start/end are YYYY-MM-DD; Google treats end.date as exclusive.
                from datetime import date as _date, timedelta as _td
                if not start:
                    start = str(_date.today())
                if not end:
                    end = str(_date.fromisoformat(str(start)) + _td(days=1))
                body["start"] = {"date": str(start)}
                body["end"] = {"date": str(end)}
            else:
                if not start or not end:
                    return {"status": "error",
                            "error": "a timed event needs start and end (RFC3339 dateTime)",
                            "confidence": 0.0}
                tz = str(arguments.get("timezone") or "")
                body["start"] = {"dateTime": str(start)}
                body["end"] = {"dateTime": str(end)}
                if tz:
                    body["start"]["timeZone"] = tz
                    body["end"]["timeZone"] = tz
            created = service.events().insert(calendarId="primary", body=body).execute()
            return {
                "status": "success",
                "event_id": created.get("id"),
                "html_link": created.get("htmlLink"),
                "summary": summary,
                "confidence": 1.0,
                "error": None,
            }
        except Exception:
            logger.exception("[calendar_agent] create failed")
            return {"status": "error", "error": "could not create event", "confidence": 0.0}

    def _query(self, filter_: str) -> Dict[str, Any]:
        try:
            from sqlalchemy import or_
            from sqlalchemy.orm import Session
            from db.school_models import CalendarEvent, engine

            today = str(date.today())
            week_end = str(date.today() + timedelta(days=7))
            two_weeks = str(date.today() + timedelta(days=14))

            with Session(engine) as session:
                q = session.query(CalendarEvent)

                if filter_ == "today":
                    q = q.filter(CalendarEvent.start_datetime.like(f"{today}%"))
                elif filter_ == "week":
                    q = q.filter(
                        CalendarEvent.start_datetime >= today,
                        CalendarEvent.start_datetime <= week_end,
                    )
                elif filter_.startswith("keyword:"):
                    term = filter_.split(":", 1)[1].lower()
                    q = q.filter(CalendarEvent.title.ilike(f"%{term}%"))
                else:  # "upcoming" default
                    q = q.filter(
                        CalendarEvent.start_datetime >= today,
                        CalendarEvent.start_datetime <= two_weeks,
                    )

                rows = q.order_by(CalendarEvent.start_datetime).all()

            events = [
                {
                    "title": r.title,
                    "start": r.start_datetime,
                    "end": r.end_datetime,
                    "calendar": r.calendar_name,
                    "all_day": r.all_day,
                    "category": r.category,
                    "location": r.location,
                }
                for r in rows
            ]

            return {
                "status": "success",
                "events": events,
                "count": len(events),
                "filter": filter_,
                "confidence": 1.0,
                "error": None,
            }
        except Exception:
            logger.exception("[calendar_agent] query failed")
            return {"status": "error", "error": "calendar query failed", "confidence": 0.0}
