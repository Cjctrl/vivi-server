"""
PowerSchool Agent — scrapes grades using Playwright.
Credentials read from environment variables only (never hardcoded).

IMPORTANT: Selectors below are district-specific.
Run with headless=False first to verify they match your district's login page.
"""

from __future__ import annotations

import structlog
import os
from datetime import date
from typing import Any, Dict, List

from core.base_agent import BaseAgent

logger = structlog.get_logger(__name__).bind(component="powerschool_agent")

# ---------------------------------------------------------------------------
# Selector constants — update these to match your district's PowerSchool UI
# ---------------------------------------------------------------------------
PS_USERNAME_SELECTOR = "#fieldAccount"
PS_PASSWORD_SELECTOR = "#fieldPassword"
PS_LOGIN_BUTTON      = "#btn-enter"
PS_GRADES_LINK       = "a[href*='grades']"
PS_GRADE_ROWS        = "tr.row"


class PowerSchoolAgent(BaseAgent):
    """Scrapes PowerSchool grade data and stores it in local SQLite."""

    name = "powerschool_agent"

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        ps_url = os.getenv("POWERSCHOOL_URL", "")
        ps_username = os.getenv("POWERSCHOOL_USERNAME", "")
        ps_password = os.getenv("POWERSCHOOL_PASSWORD", "")

        if not ps_url or not ps_username or not ps_password:
            return {
                "status": "error",
                "error": (
                    "PowerSchool credentials not configured. "
                    "Set POWERSCHOOL_URL, POWERSCHOOL_USERNAME, POWERSCHOOL_PASSWORD in environment."
                ),
                "confidence": 0.0,
            }

        action: str = (arguments.get("action") or "query").lower()

        if action == "sync":
            return self._sync(ps_url, ps_username, ps_password)
        elif action == "query":
            return self._query(arguments.get("filter", "all"))
        else:
            return {
                "status": "error",
                "error": f"Unknown action '{action}'. Use: sync, query.",
                "confidence": 0.0,
            }

    # ------------------------------------------------------------------

    def _sync(self, url: str, username: str, password: str) -> Dict[str, Any]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return {
                "status": "error",
                "error": "Playwright not installed. Run: pip install playwright && playwright install chromium",
                "confidence": 0.0,
            }

        grades_scraped: List[Dict[str, Any]] = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                page.goto(url, timeout=30000)
                page.fill(PS_USERNAME_SELECTOR, username)
                page.fill(PS_PASSWORD_SELECTOR, password)
                page.click(PS_LOGIN_BUTTON)
                page.wait_for_load_state("networkidle", timeout=15000)

                # Detect login/auth failure before scraping. On bad credentials
                # PowerSchool re-renders the login form (the password field
                # persists) rather than redirecting, so a rejected login used to
                # fall through and return status:"success" with 0 grades —
                # indistinguishable from an empty gradebook. If we're still on the
                # login page, fail honestly instead.
                if page.query_selector(PS_PASSWORD_SELECTOR) is not None:
                    browser.close()
                    return {
                        "status": "error",
                        "error": (
                            "PowerSchool login failed — credentials rejected (still on "
                            "the login page). Verify POWERSCHOOL_USERNAME / "
                            "POWERSCHOOL_PASSWORD and that the district login selectors "
                            "still match."
                        ),
                        "confidence": 0.0,
                    }

                # Navigate to grades (some districts show them on the landing page,
                # so the grades link is optional)
                grades_link = page.query_selector(PS_GRADES_LINK)
                if grades_link:
                    grades_link.click()
                    page.wait_for_load_state("networkidle", timeout=10000)

                rows = page.query_selector_all(PS_GRADE_ROWS)
                for row in rows:
                    cells = row.query_selector_all("td")
                    text = [c.inner_text().strip() for c in cells]
                    if len(text) >= 2:
                        grades_scraped.append({
                            "class_name": text[0] if len(text) > 0 else "",
                            "score_raw": text[1] if len(text) > 1 else "",
                            "letter_grade": text[2] if len(text) > 2 else "",
                        })

                browser.close()

        except Exception:
            logger.exception("[powerschool_agent] scrape failed")
            return {"status": "error", "error": "powerschool sync failed", "confidence": 0.0}

        # Persist to SQLite
        try:
            from sqlalchemy.orm import Session
            from db.school_models import Grade, engine

            with Session(engine) as session:
                for g in grades_scraped:
                    try:
                        score = float(g["score_raw"].replace("%", "").strip()) if g["score_raw"] else None
                        percentage = score
                    except ValueError:
                        score = None
                        percentage = None

                    existing = (
                        session.query(Grade)
                        .filter_by(class_name=g["class_name"], source="powerschool")
                        .first()
                    )
                    if existing:
                        existing.score = score
                        existing.percentage = percentage
                        existing.letter_grade = g["letter_grade"] or existing.letter_grade
                    else:
                        session.add(
                            Grade(
                                class_name=g["class_name"],
                                score=score,
                                percentage=percentage,
                                letter_grade=g["letter_grade"] or None,
                                source="powerschool",
                            )
                        )
                session.commit()
        except Exception as exc:
            logger.exception("[powerschool_agent] DB write failed")
            return {"status": "error", "error": f"DB write failed: {exc}", "confidence": 0.0}

        return {
            "status": "success",
            "grades_synced": len(grades_scraped),
            "source": "powerschool",
            "confidence": 0.9 if grades_scraped else 0.3,
            "error": None,
        }

    def _query(self, filter_: str) -> Dict[str, Any]:
        try:
            from sqlalchemy.orm import Session
            from db.school_models import Grade, engine

            with Session(engine) as session:
                q = session.query(Grade).filter(Grade.source == "powerschool")
                rows = q.all()

            grades = [
                {
                    "class_name": r.class_name,
                    "score": r.score,
                    "percentage": r.percentage,
                    "letter_grade": r.letter_grade,
                    "assignment_title": r.assignment_title,
                }
                for r in rows
            ]

            return {
                "status": "success",
                "grades": grades,
                "count": len(grades),
                "source": "powerschool",
                "confidence": 1.0,
                "error": None,
            }
        except Exception as exc:
            return {"status": "error", "error": str(exc), "confidence": 0.0}
