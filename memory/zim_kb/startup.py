"""
memory/zim_kb/startup.py
Spec startup sequence — idempotent boot / health check.

Runs the canonical startup steps from the Nexus spec:
  1. Ensure memory-disk directory layout exists / is accessible
  2. Open metadata DB; run PRAGMA integrity_check
  3. Verify registered ZIM files exist (by filename; no checksum)
  4. (deferred) load embedding model
  5. Init FTS5 indices (via init_db); sqlite-vec deferred
  6. Report catalog status

Missing ZIMs degrade the system but do not fail startup — per spec,
"report it as degraded but continue with available sources." Only a
metadata-DB integrity failure is a hard error.

Run:
    python -m memory.zim_kb.startup
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from pathlib import Path

from config.settings import (
    VIVI_MEMDSK_PATH,
    ZIM_KB_INDEX_DB,
)
from memory.zim_kb.catalog import all_archives, verify_presence
from memory.zim_kb.db import (
    REQUIRED_DIRS,
    ensure_directories,
    init_db,
    integrity_check,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StartupReport:
    memdsk_ok: bool
    dirs_present: tuple[str, ...]
    db_path: str
    db_integrity_ok: bool
    archives_registered: int
    archives_present: int
    archives_missing: int
    articles_cached: int
    chunks_cached: int
    last_article_ts: str | None
    degraded: bool

    def to_dict(self) -> dict:
        d = asdict(self)
        d["dirs_present"] = list(d["dirs_present"])
        return d


def run_startup(*, log: logging.Logger = logger) -> StartupReport:
    """Run the startup sequence end-to-end and return a structured report.

    Never raises for degraded conditions (missing ZIMs, empty cache).
    Raises on genuinely broken state that init_db / integrity_check can't
    recover from.
    """
    # Step 1 — memory-disk layout
    log.info("[1/6] ensuring memory-disk layout at %s", VIVI_MEMDSK_PATH)
    ensure_directories()
    memdsk_ok = Path(VIVI_MEMDSK_PATH).is_dir()
    dirs_present = tuple(d for d in REQUIRED_DIRS if Path(d).is_dir())
    log.info("       %d/%d required directories present", len(dirs_present), len(REQUIRED_DIRS))

    # Step 2 + Step 5a — open DB, apply schema, integrity check
    log.info("[2/6] opening metadata DB at %s", ZIM_KB_INDEX_DB)
    conn = init_db()
    db_integrity_ok = integrity_check(conn)
    log.info("       integrity=%s", "ok" if db_integrity_ok else "FAIL")

    # Step 3 — ZIM presence
    log.info("[3/6] verifying registered ZIM files")
    presence = verify_presence()
    registered = len(all_archives())
    present = len(presence.present)
    missing = len(presence.missing)
    log.info("       %d/%d ZIMs present on disk", present, registered)
    if missing:
        log.warning("       %d ZIM(s) missing - degraded mode", missing)
        for a in presence.missing[:5]:
            log.warning("         missing: %s", a.filename)
        if missing > 5:
            log.warning("         ...and %d more", missing - 5)

    # Step 4 — embedding model (deferred)
    log.info("[4/6] embedding model load - deferred (not yet implemented)")

    # Step 5b — sqlite-vec (deferred)
    log.info("[5/6] sqlite-vec index init - deferred (not yet implemented)")

    # Step 6 — catalog stats from the DB
    log.info("[6/6] gathering catalog stats")
    articles_cached = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    chunks_cached = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    last_ts_row = conn.execute("SELECT MAX(conversion_ts) FROM articles").fetchone()
    last_article_ts = last_ts_row[0] if last_ts_row else None
    conn.close()

    report = StartupReport(
        memdsk_ok=memdsk_ok,
        dirs_present=dirs_present,
        db_path=str(ZIM_KB_INDEX_DB),
        db_integrity_ok=db_integrity_ok,
        archives_registered=registered,
        archives_present=present,
        archives_missing=missing,
        articles_cached=articles_cached,
        chunks_cached=chunks_cached,
        last_article_ts=last_article_ts,
        degraded=bool(missing) or not db_integrity_ok,
    )

    log.info(
        "STARTUP %s - memdsk=%s integrity=%s archives=%d/%d cache=%d articles/%d chunks last=%s",
        "DEGRADED" if report.degraded else "READY",
        "ok" if report.memdsk_ok else "FAIL",
        "ok" if report.db_integrity_ok else "FAIL",
        report.archives_present,
        report.archives_registered,
        report.articles_cached,
        report.chunks_cached,
        report.last_article_ts or "never",
    )
    return report


def _main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        report = run_startup(log=logger)
    except Exception:
        logger.exception("startup FAILED with unexpected error")
        return 2
    # Degraded is acceptable; only integrity failure is a hard error.
    return 0 if report.db_integrity_ok else 1


if __name__ == "__main__":
    raise SystemExit(_main())
