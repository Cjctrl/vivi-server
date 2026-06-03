"""
Google Classroom Agent — syncs coursework/submissions to local SQLite.
Requires credentials.json in config/ and Google API libraries.
"""

from __future__ import annotations

import structlog
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.base_agent import BaseAgent

logger = structlog.get_logger(__name__).bind(component="classroom_agent")

_CREDENTIALS_PATH = Path("config/credentials.json")
# JSON (google-auth authorized-user format), not pickle: deserializing a pickle
# token executes arbitrary code if the file is tampered with. Shared with
# calendar_agent. A stale .pickle from before this migration is ignored — the
# OAuth flow re-runs once and writes the JSON token.
_TOKEN_PATH = Path("config/classroom_token.json")

SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.me.readonly",
    "https://www.googleapis.com/auth/classroom.student-submissions.me.readonly",
]

STATE_MAP: Dict[str, str] = {
    "TURNED_IN": "submitted",
    "RETURNED": "graded",
    "NEW": "missing",
    "CREATED": "upcoming",
}


class ClassroomAgent(BaseAgent):
    """Syncs Google Classroom assignments to SQLite and answers queries from the local DB."""

    name = "classroom_agent"

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        action: str = (arguments.get("action") or "query").lower()

        if not _CREDENTIALS_PATH.exists():
            return {
                "status": "error",
                "error": (
                    "Google Classroom credentials not configured. "
                    "Place credentials.json in config/."
                ),
                "confidence": 0.0,
            }

        if action == "sync":
            return self._sync()
        elif action == "query":
            return self._query(arguments.get("filter", "upcoming"))
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
                creds = flow.run_local_server(port=0)
            _TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
            _TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

        # Wrap the credentials in an authorized http with a 15s socket timeout so
        # a hung Google call cannot block the agent forever. build() forbids
        # passing both http= and credentials=, so auth is carried by AuthorizedHttp.
        authed_http = AuthorizedHttp(creds, http=httplib2.Http(timeout=15))
        return build("classroom", "v1", http=authed_http)

    def _sync(self) -> Dict[str, Any]:
        try:
            service = self._get_service()
        except Exception as exc:
            return {"status": "error", "error": str(exc), "confidence": 0.0}

        try:
            from sqlalchemy.orm import Session
            from db.school_models import Assignment, engine

            synced = 0
            courses_resp = service.courses().list(courseStates=["ACTIVE"]).execute()
            courses = courses_resp.get("courses", [])

            with Session(engine) as session:
                for course in courses:
                    course_id = course["id"]
                    class_name = course.get("name", "Unknown")

                    cw_resp = service.courses().courseWork().list(courseId=course_id).execute()
                    coursework = cw_resp.get("courseWork", [])

                    for work in coursework:
                        work_id = work["id"]
                        title = work.get("title", "Untitled")
                        due = _parse_due(work.get("dueDate"))

                        # Get student submission
                        subs_resp = (
                            service.courses()
                            .courseWork()
                            .studentSubmissions()
                            .list(courseId=course_id, courseWorkId=work_id)
                            .execute()
                        )
                        submissions = subs_resp.get("studentSubmissions", [])
                        state_raw = submissions[0].get("state", "CREATED") if submissions else "CREATED"
                        status = STATE_MAP.get(state_raw, "upcoming")

                        grade_raw = submissions[0].get("assignedGrade") if submissions else None
                        grade = str(grade_raw) if grade_raw is not None else None

                        existing = (
                            session.query(Assignment)
                            .filter_by(title=title, class_name=class_name, source="google_classroom")
                            .first()
                        )
                        if existing:
                            existing.status = status
                            if grade:
                                existing.grade = grade
                        else:
                            session.add(
                                Assignment(
                                    title=title,
                                    class_name=class_name,
                                    due_date=due,
                                    status=status,
                                    grade=grade,
                                    source="google_classroom",
                                    google_id=work_id,
                                )
                            )
                            synced += 1

                session.commit()

            return {"status": "success", "synced": synced, "confidence": 1.0, "error": None}

        except Exception as exc:
            logger.exception("[classroom_agent] sync failed")
            return {"status": "error", "error": str(exc), "confidence": 0.0}

    def _query(self, filter_: str) -> Dict[str, Any]:
        try:
            from sqlalchemy.orm import Session
            from db.school_models import Assignment, engine

            today_str = str(date.today())

            with Session(engine) as session:
                q = session.query(Assignment)

                if filter_ == "missing":
                    q = q.filter(Assignment.status == "missing")
                elif filter_ == "today":
                    q = q.filter(Assignment.due_date == today_str)
                elif filter_ == "upcoming":
                    q = q.filter(
                        Assignment.due_date >= today_str,
                        Assignment.status.in_(["upcoming", "submitted"]),
                    )
                elif filter_ == "graded":
                    q = q.filter(Assignment.status == "graded")
                # "all" → no filter

                rows = q.order_by(Assignment.due_date).all()
                assignments = [
                    {
                        "id": r.id,
                        "title": r.title,
                        "class_name": r.class_name,
                        "due_date": r.due_date,
                        "status": r.status,
                        "grade": r.grade,
                        "source": r.source,
                    }
                    for r in rows
                ]

            return {
                "status": "success",
                "assignments": assignments,
                "count": len(assignments),
                "filter": filter_,
                "confidence": 1.0,
                "error": None,
            }
        except Exception as exc:
            return {"status": "error", "error": str(exc), "confidence": 0.0}


def _parse_due(due_date: Optional[Dict[str, int]]) -> Optional[str]:
    if not due_date:
        return None
    try:
        return f"{due_date['year']}-{due_date['month']:02d}-{due_date['day']:02d}"
    except (KeyError, ValueError):
        return None