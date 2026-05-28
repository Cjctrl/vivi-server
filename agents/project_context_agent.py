"""
Project Context Agent — detects active projects from vault notes, git repos, and code files.
"""

from __future__ import annotations

import structlog
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import NEXUS_KB_PATH
from core.base_agent import BaseAgent

logger = structlog.get_logger(__name__).bind(component="project_context_agent")

_WORKSPACE_ROOT = Path(NEXUS_KB_PATH or "./").resolve()
_KB_LOOKBACK_DAYS = 30
_CODE_EXTENSIONS = frozenset({".py", ".js", ".ts", ".rs", ".go", ".cpp", ".java"})
_EXCLUDE_DIRS = frozenset({
    "node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build",
})
_MAX_RECENT_CODE = 15
_GIT_DEPTH = 3


class ProjectContextAgent(BaseAgent):
    """Scans vault, git repos, and code files to understand active projects."""

    name = "project_context_agent"

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        action: str = (arguments.get("action") or "scan").lower()

        if action == "scan":
            return self._full_scan()
        elif action == "query":
            return self._query_db()
        elif action == "recent_files":
            return self._recent_files()
        else:
            return {
                "status": "error",
                "error": f"Unknown action '{action}'. Use: scan, query, recent_files.",
                "confidence": 0.0,
            }

    # ------------------------------------------------------------------

    def _full_scan(self) -> Dict[str, Any]:
        vault_projects = self._detect_vault_projects()
        git_repos = self._get_git_context()
        recent_code = self._get_recent_code_files()

        active = [p for p in vault_projects if p["status"] == "active"]
        stalled = [p for p in vault_projects if p["status"] == "stalled"]
        current_focus = active[0]["name"] if active else (stalled[0]["name"] if stalled else "None")

        result = {
            "status": "success",
            "vault_projects": vault_projects,
            "git_repos": git_repos,
            "recent_code_files": recent_code,
            "active_project_count": len(active),
            "stalled_project_count": len(stalled),
            "current_focus": current_focus,
            "confidence": 0.9,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "error": None,
        }

        # Persist to DB
        try:
            self._persist(vault_projects, git_repos)
        except Exception as exc:
            logger.warning("[project_context_agent] DB persist failed: %s", exc)

        return result

    def _query_db(self) -> Dict[str, Any]:
        try:
            from sqlalchemy.orm import Session
            from db.school_models import ProjectRecord, engine

            with Session(engine) as session:
                rows = session.query(ProjectRecord).all()

            projects = [
                {
                    "name": r.name,
                    "source": r.source,
                    "file_or_path": r.file_or_path,
                    "status": r.status,
                    "last_modified": r.last_modified,
                    "has_tasks": r.has_tasks,
                }
                for r in rows
            ]
            return {
                "status": "success",
                "projects": projects,
                "count": len(projects),
                "confidence": 1.0,
                "error": None,
            }
        except Exception as exc:
            return {"status": "error", "error": str(exc), "confidence": 0.0}

    def _recent_files(self) -> Dict[str, Any]:
        files: List[Dict[str, Any]] = []
        if not _WORKSPACE_ROOT.exists():
            return {"status": "success", "files": [], "confidence": 0.5, "error": None}

        for path in _WORKSPACE_ROOT.rglob("*.md"):
            if _should_exclude(path):
                continue
            try:
                stat = path.stat()
                files.append({
                    "path": str(path),
                    "mtime": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    "size_bytes": stat.st_size,
                    "preview": path.read_text(encoding="utf-8", errors="ignore")[:200],
                })
            except Exception:
                continue

        files.sort(key=lambda x: x["mtime"], reverse=True)
        return {"status": "success", "files": files[:10], "confidence": 0.9, "error": None}

    # ------------------------------------------------------------------
    # Detection helpers
    # ------------------------------------------------------------------

    def _detect_vault_projects(self) -> List[Dict[str, Any]]:
        projects: List[Dict[str, Any]] = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=_KB_LOOKBACK_DAYS)

        if not _WORKSPACE_ROOT.exists():
            return projects

        for path in _WORKSPACE_ROOT.rglob("*.md"):
            if _should_exclude(path):
                continue
            try:
                stat = path.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                if mtime < cutoff:
                    continue

                content = path.read_text(encoding="utf-8", errors="ignore")
                if not _is_project_note(content):
                    continue

                name = _extract_project_name(content, path)
                days_old = (datetime.now(timezone.utc) - mtime).days
                status = "active" if days_old < 7 else ("stalled" if days_old < 30 else "archived")
                if "status: archived" in content.lower():
                    status = "archived"

                has_tasks = "- [ ]" in content

                projects.append({
                    "name": name,
                    "file": str(path),
                    "status": status,
                    "last_modified": mtime.isoformat(),
                    "has_tasks": has_tasks,
                })
            except Exception:
                continue

        projects.sort(key=lambda x: x["last_modified"], reverse=True)
        return projects

    def _get_git_context(self) -> List[Dict[str, Any]]:
        repos: List[Dict[str, Any]] = []

        def _walk(path: Path, depth: int) -> None:
            if depth > _GIT_DEPTH:
                return
            if (path / ".git").exists():
                repos.append(_read_git_repo(path))
                return
            try:
                for child in path.iterdir():
                    if child.is_dir() and child.name not in _EXCLUDE_DIRS:
                        _walk(child, depth + 1)
            except PermissionError:
                pass

        if _WORKSPACE_ROOT.exists():
            _walk(_WORKSPACE_ROOT, 0)
        return repos

    def _get_recent_code_files(self) -> List[Dict[str, Any]]:
        code_files: List[Dict[str, Any]] = []

        if not _WORKSPACE_ROOT.exists():
            return code_files

        for path in _WORKSPACE_ROOT.rglob("*"):
            if _should_exclude(path):
                continue
            if path.suffix.lower() not in _CODE_EXTENSIONS:
                continue
            try:
                stat = path.stat()
                code_files.append({
                    "path": str(path),
                    "mtime": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    "size_bytes": stat.st_size,
                    "extension": path.suffix,
                })
            except Exception:
                continue

        code_files.sort(key=lambda x: x["mtime"], reverse=True)
        return code_files[:_MAX_RECENT_CODE]

    def _persist(self, vault_projects: List[Dict[str, Any]], git_repos: List[Dict[str, Any]]) -> None:
        from sqlalchemy.orm import Session
        from db.school_models import ProjectRecord, engine

        with Session(engine) as session:
            for p in vault_projects:
                existing = (
                    session.query(ProjectRecord)
                    .filter_by(name=p["name"], source="vault")
                    .first()
                )
                if existing:
                    existing.status = p["status"]
                    existing.last_modified = p["last_modified"]
                    existing.has_tasks = p["has_tasks"]
                else:
                    session.add(
                        ProjectRecord(
                            name=p["name"],
                            source="vault",
                            file_or_path=p["file"],
                            status=p["status"],
                            last_modified=p["last_modified"],
                            has_tasks=p["has_tasks"],
                        )
                    )

            for r in git_repos:
                existing = (
                    session.query(ProjectRecord)
                    .filter_by(name=r["repo"], source="git")
                    .first()
                )
                if existing:
                    existing.current_branch = r.get("branch")
                    existing.readme_preview = r.get("readme_preview")
                else:
                    session.add(
                        ProjectRecord(
                            name=r["repo"],
                            source="git",
                            file_or_path=r["repo"],
                            status="active",
                            current_branch=r.get("branch"),
                            readme_preview=r.get("readme_preview"),
                        )
                    )

            session.commit()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _should_exclude(path: Path) -> bool:
    return any(part in _EXCLUDE_DIRS for part in path.parts)


def _is_project_note(content: str) -> bool:
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            frontmatter = content[:end]
            if "project:" in frontmatter or "status:" in frontmatter:
                return True
    lower = content.lower()
    if "# project" in lower or "## status" in lower or "## goals" in lower:
        return True
    if "- [ ]" in content:
        return True
    return False


def _extract_project_name(content: str, path: Path) -> str:
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            for line in content[:end].splitlines():
                if line.startswith("project:"):
                    return line.split(":", 1)[1].strip().strip('"').strip("'")
    stem = path.stem.replace("-", " ").replace("_", " ").title()
    return stem


def _read_git_repo(repo_path: Path) -> Dict[str, Any]:
    def _run(cmd: List[str]) -> str:
        try:
            r = subprocess.run(
                cmd, cwd=str(repo_path),
                capture_output=True, text=True, timeout=10,
            )
            return r.stdout.strip()
        except Exception:
            return ""

    branch = _run(["git", "branch", "--show-current"])
    log = _run(["git", "log", "--oneline", "-5"])
    diff_stat = _run(["git", "diff", "--stat", "HEAD"])
    stashes = _run(["git", "stash", "list"])

    readme_preview = ""
    for readme_name in ("README.md", "readme.md", "README.txt"):
        readme = repo_path / readme_name
        if readme.exists():
            try:
                readme_preview = readme.read_text(encoding="utf-8", errors="ignore")[:500]
            except Exception:
                pass
            break

    return {
        "repo": str(repo_path),
        "branch": branch,
        "recent_commits": [l for l in log.splitlines() if l],
        "changed_files": diff_stat,
        "stashes": stashes,
        "readme_preview": readme_preview,
    }
