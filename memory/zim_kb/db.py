"""
memory/zim_kb/db.py
Metadata database for the ZIM knowledge base.

Schema is loaded from schema.sql. The database lives at ZIM_KB_INDEX_DB
(default: <VIVI_MEMDSK_PATH>/metadata/nexus_index.sqlite).

Run as a script to initialise the database and check integrity:
    python -m memory.zim_kb.db
"""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Iterable

from config.settings import (
    VIVI_MEMDSK_PATH,
    ZIM_KB_EMBEDDINGS_DIR,
    ZIM_KB_INDEX_DB,
    ZIM_KB_MARKDOWN_DIR,
    ZIM_KB_METADATA_DIR,
    ZIM_KB_ZIM_DIR,
)

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

REQUIRED_DIRS: tuple[str, ...] = (
    VIVI_MEMDSK_PATH,
    ZIM_KB_ZIM_DIR,
    ZIM_KB_MARKDOWN_DIR,
    ZIM_KB_EMBEDDINGS_DIR,
    ZIM_KB_METADATA_DIR,
)


def ensure_directories(dirs: Iterable[str] = REQUIRED_DIRS) -> None:
    """Create the memory-disk directory layout if missing."""
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)


def get_connection(db_path: str | Path = ZIM_KB_INDEX_DB) -> sqlite3.Connection:
    """Open a sqlite connection with WAL mode and foreign keys enabled."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


def init_db(conn: sqlite3.Connection | None = None) -> sqlite3.Connection:
    """Apply schema.sql to the database. Safe to call repeatedly."""
    ensure_directories()
    if conn is None:
        conn = get_connection()
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema)
    conn.commit()
    return conn


def integrity_check(conn: sqlite3.Connection) -> bool:
    """Return True if PRAGMA integrity_check reports 'ok'."""
    row = conn.execute("PRAGMA integrity_check;").fetchone()
    result = row[0] if row else None
    if result != "ok":
        logger.error("zim_kb integrity check failed: %r", result)
        return False
    return True


def _main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logger.info("initialising zim_kb metadata DB at %s", ZIM_KB_INDEX_DB)
    conn = init_db()
    ok = integrity_check(conn)
    counts = {
        t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for t in ("articles", "chunks", "retrieval_log")
    }
    logger.info("integrity=%s counts=%s", "ok" if ok else "FAIL", counts)
    conn.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(_main())
