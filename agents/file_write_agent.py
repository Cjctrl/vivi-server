"""
File Write Agent — safe atomic file creation, editing, and reading within the workspace.
"""

from __future__ import annotations

import structlog
import os
from pathlib import Path
from typing import Any, Dict

from config.settings import NEXUS_KB_PATH
from core.base_agent import BaseAgent

logger = structlog.get_logger(__name__).bind(component="file_write_agent")

_WORKSPACE_ROOT = Path(NEXUS_KB_PATH or "./").resolve()
_MAX_READ_BYTES = 1_048_576  # 1 MB


class FileWriteAgent(BaseAgent):
    """
    Write, append, find-replace, and read files safely within the workspace root.

    All paths are resolved and validated to prevent directory traversal.
    Actions: write, append, replace_section, read
    """

    name = "file_write_agent"

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        action: str = (arguments.get("action") or "write").lower()

        dispatch = {
            "write": self._write,
            "append": self._append,
            "replace_section": self._replace_section,
            "read": self._read,
        }
        handler = dispatch.get(action)
        if handler is None:
            return {
                "status": "error",
                "error": f"Unknown action '{action}'. Use: write, append, replace_section, read.",
                "confidence": 0.0,
            }
        return handler(arguments)

    # ------------------------------------------------------------------

    def _resolve(self, raw_path: str) -> Path | str:
        """Resolve path and verify it's inside the workspace root. Returns Path or error str."""
        if not raw_path:
            return "path is required"
        try:
            resolved = Path(raw_path).resolve()
        except Exception as exc:
            return f"Invalid path: {exc}"
        if ".." in Path(raw_path).parts:
            return f"Path '{raw_path}' contains '..' — refusing to write."
        if not resolved.is_relative_to(_WORKSPACE_ROOT):
            return f"Path '{raw_path}' is outside the workspace root. Refusing to write."
        return resolved

    def _write(self, args: Dict[str, Any]) -> Dict[str, Any]:
        raw = str(args.get("path", ""))
        content: str = str(args.get("content", ""))
        overwrite: bool = bool(args.get("overwrite", False))
        create_dirs: bool = bool(args.get("create_dirs", True))
        encoding: str = str(args.get("encoding", "utf-8"))

        result = self._resolve(raw)
        if isinstance(result, str):
            return {"status": "error", "error": result, "confidence": 0.0}
        path = result

        if path.exists() and not overwrite:
            return {
                "status": "error",
                "error": f"File already exists: {path}. Set overwrite=True to replace.",
                "confidence": 0.0,
            }

        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)

        tmp = Path(str(path) + ".tmp")
        try:
            tmp.write_text(content, encoding=encoding)
            os.replace(tmp, path)
        except Exception as exc:
            tmp.unlink(missing_ok=True)
            return {"status": "error", "error": f"Write failed: {exc}", "confidence": 0.0}

        return {
            "status": "success",
            "path": str(path),
            "bytes_written": len(content.encode(encoding)),
            "confidence": 1.0,
            "error": None,
        }

    def _append(self, args: Dict[str, Any]) -> Dict[str, Any]:
        raw = str(args.get("path", ""))
        content: str = str(args.get("content", ""))
        encoding: str = str(args.get("encoding", "utf-8"))

        result = self._resolve(raw)
        if isinstance(result, str):
            return {"status": "error", "error": result, "confidence": 0.0}
        path = result

        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("a", encoding=encoding) as f:
                f.write(content)
        except Exception as exc:
            return {"status": "error", "error": f"Append failed: {exc}", "confidence": 0.0}

        return {
            "status": "success",
            "path": str(path),
            "bytes_appended": len(content.encode(encoding)),
            "confidence": 1.0,
            "error": None,
        }

    def _replace_section(self, args: Dict[str, Any]) -> Dict[str, Any]:
        raw = str(args.get("path", ""))
        find: str = str(args.get("find", ""))
        replace: str = str(args.get("replace", ""))

        result = self._resolve(raw)
        if isinstance(result, str):
            return {"status": "error", "error": result, "confidence": 0.0}
        path = result

        if not path.exists():
            return {"status": "error", "error": f"File not found: {path}", "confidence": 0.0}

        try:
            original = path.read_text(encoding="utf-8")
        except Exception as exc:
            return {"status": "error", "error": f"Read failed: {exc}", "confidence": 0.0}

        count = original.count(find)
        if count == 0:
            return {"status": "error", "error": "Pattern not found in file.", "confidence": 0.0}
        if count > 1:
            return {
                "status": "error",
                "error": f"Pattern is ambiguous (appears {count} times). Use a more specific pattern.",
                "confidence": 0.0,
            }

        new_content = original.replace(find, replace, 1)
        tmp = Path(str(path) + ".tmp")
        try:
            tmp.write_text(new_content, encoding="utf-8")
            os.replace(tmp, path)
        except Exception as exc:
            tmp.unlink(missing_ok=True)
            return {"status": "error", "error": f"Write failed: {exc}", "confidence": 0.0}

        return {
            "status": "success",
            "path": str(path),
            "replacements": 1,
            "confidence": 1.0,
            "error": None,
        }

    def _read(self, args: Dict[str, Any]) -> Dict[str, Any]:
        raw = str(args.get("path", ""))

        result = self._resolve(raw)
        if isinstance(result, str):
            return {"status": "error", "error": result, "confidence": 0.0}
        path = result

        if not path.exists():
            return {"status": "error", "error": f"File not found: {path}", "confidence": 0.0}

        size = path.stat().st_size
        if size > _MAX_READ_BYTES:
            return {
                "status": "error",
                "error": f"File too large ({size} bytes > {_MAX_READ_BYTES} limit).",
                "confidence": 0.0,
            }

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            return {"status": "error", "error": f"Read failed: {exc}", "confidence": 0.0}

        return {
            "status": "success",
            "path": str(path),
            "content": content,
            "size_bytes": size,
            "confidence": 1.0,
            "error": None,
        }
