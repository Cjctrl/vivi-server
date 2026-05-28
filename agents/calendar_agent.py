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

logger = structlog.get_logger(__name__).bind(component="calendar_agent")

_CREDENTIALS_PATH = Path("config/credentials.json")
# JSON (google-auth authorized-user format), not pickle: deserializing a pickle
# token executes arbitrary code if the file is tampered with. A stale .pickle
# from before this migration is simply ignored — the OAuth flow re-runs once
# and writes the JSON token.
_TOKEN_PATH = Path("config/classroom_token.json")

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.me.readonly",
    "https://www.googleapis.com/auth/classroom.student-submissions.me.readonly",
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
        else:
            return {
                "status": "error",
                "error": f"Unknown action '{action}'. Use: sync, query.",
                "confidence": 0.0,
            }

    # ------------------------------------------------------------------

    def _get_service(self):
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
        except ImportError:
            raise RuntimeError(
                "Google API libraries not installed. "
                "Run: pip install google-auth-oauthlib google-api-python-client"
            )

        creds: Optional[Credentials] = None
        if _TOKEN_PATH.exists():
            creds = Credentials.from_authorized_user_file(str(_TOKEN_PATH), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(_CREDENTIALS_PATH), SCOPES)
                creds = flow.run_local_server(port=0)
            _TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
            _TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

        return build("calendar", "v3", credentials=creds)

    def _sync(self) -> Dict[str, Any]:
        try:
            service = self._get_service()
        except Exception as exc:
            return {"status": "error", "error": str(exc), "confidence": 0.0}

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

        except Exception as exc:
            logger.exception("[calendar_agent] sync failed")
            return {"status": "error", "error": str(exc), "confidence": 0.0}

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
        except Exception as exc:
            return {"status": "error", "error": str(exc), "confidence": 0.0}
