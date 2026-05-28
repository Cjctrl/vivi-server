"""
memory/zim_kb/catalog.py
Static registry of ZIM archives + domain-routing rules.

Single source of truth for which ZIM files the system knows about, where
they live on the memory disk, and which archive(s) to consult for a query
in a given domain. To register a new ZIM, append an Archive() to ARCHIVES.

Layout on disk (under ZIM_KB_ZIM_DIR):
    zim/
      wikipedia/
      devdocs/
      language_docs/
      stackexchange/
      system/
      other/

Run as a script to print the routing table and a presence report:
    python -m memory.zim_kb.catalog
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable

from config.settings import ZIM_KB_ZIM_DIR


# ---------------------------------------------------------------------------
# Variants and domains
# ---------------------------------------------------------------------------

class Variant(str, Enum):
    """ZIM image variant. Wikipedia archives come in three sizes; other
    archives don't carry an image variant and use NONE."""
    NOPIC = "nopic"   # text-only, smallest
    MINI  = "mini"    # condensed
    MAXI  = "maxi"    # full images
    NONE  = "none"    # archive does not have variants


class Domain(str, Enum):
    """Coarse query-routing domains. Each Archive declares a primary_domain,
    and _DOMAIN_FALLBACKS chains domains together for cache-miss escalation."""
    # Python ecosystem
    PYTHON_STDLIB    = "python_stdlib"
    PYTHON_PEPS      = "python_peps"
    FASTAPI          = "fastapi"
    PYTORCH          = "pytorch"
    TENSORFLOW       = "tensorflow"
    TENSORFLOW_CPP   = "tensorflow_cpp"
    PYGAME           = "pygame"
    # JavaScript / web
    JAVASCRIPT       = "javascript"
    TYPESCRIPT       = "typescript"
    NODE             = "node"
    DOM              = "dom"
    HTML             = "html"
    CSS              = "css"
    JSDOC            = "jsdoc"
    QUNIT            = "qunit"
    HTMX             = "htmx"
    SOCKETIO         = "socketio"
    ELECTRON         = "electron"
    HTTP             = "http"
    JS_ALGORITHMS    = "js_algorithms"
    # Systems languages
    C                = "c"
    CPP              = "cpp"
    RUST             = "rust"
    VULKAN           = "vulkan"
    # Tooling
    GIT              = "git"
    DOCKER           = "docker"
    BASH             = "bash"
    ZSH              = "zsh"
    # Game dev
    GODOT            = "godot"
    # Curriculum / education
    HTDP             = "htdp"
    # Wikipedia
    MATH             = "math"
    PHYSICS          = "physics"
    COMPUTER_SCIENCE = "computer_science"
    WIKIPEDIA_GENERAL = "wikipedia_general"
    # System / OS
    ARCH_LINUX       = "arch_linux"
    OPENWRT          = "openwrt"
    TERMUX           = "termux"
    # Stack Exchange
    SERVERFAULT      = "serverfault"
    CODE_REVIEW      = "code_review"
    ROBOTICS         = "robotics"
    ENGINEERING      = "engineering"
    SALESFORCE       = "salesforce"
    # Other
    COOKING          = "cooking"


# ---------------------------------------------------------------------------
# Archive dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Archive:
    """One ZIM archive registered with the system."""
    filename: str
    subdir: str               # immediate subdir under ZIM_KB_ZIM_DIR
    primary_domain: Domain
    variant: Variant
    notes: str = ""

    @property
    def path(self) -> Path:
        return Path(ZIM_KB_ZIM_DIR) / self.subdir / self.filename

    def exists(self) -> bool:
        return self.path.is_file()


# ---------------------------------------------------------------------------
# REGISTRY — append an Archive here to register a new ZIM.
# ---------------------------------------------------------------------------

ARCHIVES: tuple[Archive, ...] = (
    # --- Wikipedia ---------------------------------------------------------
    Archive("wikipedia_en_mathematics_nopic_2026-03.zim", "wikipedia",
            Domain.MATH, Variant.NOPIC, "Prefer for text-only math queries"),
    Archive("wikipedia_en_mathematics_mini_2026-03.zim", "wikipedia",
            Domain.MATH, Variant.MINI, "Compact fallback"),
    Archive("wikipedia_en_mathematics_maxi_2026-03.zim", "wikipedia",
            Domain.MATH, Variant.MAXI, "Full images; only when diagrams requested"),

    Archive("wikipedia_en_physics_nopic_2026-04.zim", "wikipedia",
            Domain.PHYSICS, Variant.NOPIC, "Prefer for text-only physics queries"),
    Archive("wikipedia_en_physics_mini_2026-04.zim", "wikipedia",
            Domain.PHYSICS, Variant.MINI),
    Archive("wikipedia_en_physics_maxi_2026-04.zim", "wikipedia",
            Domain.PHYSICS, Variant.MAXI, "Full images; only when diagrams requested"),

    Archive("wikipedia_en_computer_nopic_2026-03.zim", "wikipedia",
            Domain.COMPUTER_SCIENCE, Variant.NOPIC, "Prefer for text-only CS queries"),
    Archive("wikipedia_en_computer_maxi_2026-03.zim", "wikipedia",
            Domain.COMPUTER_SCIENCE, Variant.MAXI, "Full images"),

    Archive("wikipedia_en_all_mini_2026-03.zim", "wikipedia",
            Domain.WIKIPEDIA_GENERAL, Variant.MINI,
            "Broad fallback only; prefer domain-specific first"),

    # --- DevDocs (no image variant) ----------------------------------------
    Archive("devdocs_en_javascript_2026-04.zim",      "devdocs", Domain.JAVASCRIPT,     Variant.NONE),
    Archive("devdocs_en_typescript_2026-04.zim",      "devdocs", Domain.TYPESCRIPT,     Variant.NONE),
    Archive("devdocs_en_css_2026-04.zim",             "devdocs", Domain.CSS,            Variant.NONE),
    Archive("devdocs_en_html_2026-04.zim",            "devdocs", Domain.HTML,           Variant.NONE),
    Archive("devdocs_en_dom_2026-05.zim",             "devdocs", Domain.DOM,            Variant.NONE),
    Archive("devdocs_en_node_2026-05.zim",            "devdocs", Domain.NODE,           Variant.NONE),
    Archive("devdocs_en_bash_2026-04.zim",            "devdocs", Domain.BASH,           Variant.NONE),
    Archive("devdocs_en_zsh_2026-04.zim",             "devdocs", Domain.ZSH,            Variant.NONE),
    Archive("devdocs_en_c_2026-04.zim",               "devdocs", Domain.C,              Variant.NONE),
    Archive("devdocs_en_cpp_2026-04.zim",             "devdocs", Domain.CPP,            Variant.NONE),
    Archive("devdocs_en_rust_2026-04.zim",            "devdocs", Domain.RUST,           Variant.NONE),
    Archive("devdocs_en_git_2026-04.zim",             "devdocs", Domain.GIT,            Variant.NONE),
    Archive("devdocs_en_docker_2026-04.zim",          "devdocs", Domain.DOCKER,         Variant.NONE),
    Archive("devdocs_en_http_2026-04.zim",            "devdocs", Domain.HTTP,           Variant.NONE),
    Archive("devdocs_en_fastapi_2026-04.zim",         "devdocs", Domain.FASTAPI,        Variant.NONE),
    Archive("devdocs_en_pytorch_2026-04.zim",         "devdocs", Domain.PYTORCH,        Variant.NONE),
    Archive("devdocs_en_tensorflow_2026-05.zim",      "devdocs", Domain.TENSORFLOW,     Variant.NONE),
    Archive("devdocs_en_tensorflow-cpp_2026-05.zim",  "devdocs", Domain.TENSORFLOW_CPP, Variant.NONE),
    Archive("devdocs_en_pygame_2026-04.zim",          "devdocs", Domain.PYGAME,         Variant.NONE),
    Archive("devdocs_en_godot_2026-04.zim",           "devdocs", Domain.GODOT,          Variant.NONE),
    Archive("devdocs_en_vulkan_2026-04.zim",          "devdocs", Domain.VULKAN,         Variant.NONE),
    Archive("devdocs_en_electron_2026-04.zim",        "devdocs", Domain.ELECTRON,       Variant.NONE),
    Archive("devdocs_en_htmx_2026-04.zim",            "devdocs", Domain.HTMX,           Variant.NONE),
    Archive("devdocs_en_socketio_2026-04.zim",        "devdocs", Domain.SOCKETIO,       Variant.NONE),
    Archive("devdocs_en_jsdoc_2026-04.zim",           "devdocs", Domain.JSDOC,          Variant.NONE),
    Archive("devdocs_en_qunit_2026-04.zim",           "devdocs", Domain.QUNIT,          Variant.NONE),

    # --- Language & framework docs -----------------------------------------
    Archive("docs.python.org_en_all_2026-05.zim", "language_docs",
            Domain.PYTHON_STDLIB, Variant.NONE, "Python official documentation"),
    Archive("peps.python_en_all_2026-05.zim", "language_docs",
            Domain.PYTHON_PEPS, Variant.NONE, "Python PEPs"),
    Archive("freecodecamp_en_javascript-algorithms-and-data-structures_2026-05.zim",
            "language_docs", Domain.JS_ALGORITHMS, Variant.NONE,
            "freeCodeCamp JS algorithms & data structures"),
    Archive("htdp.org_en_all_2026-05.zim", "language_docs",
            Domain.HTDP, Variant.NONE, "How to Design Programs"),

    # --- Stack Exchange ----------------------------------------------------
    Archive("serverfault.com_en_all_2026-02.zim",             "stackexchange", Domain.SERVERFAULT, Variant.NONE),
    Archive("codereview.stackexchange.com_en_all_2026-02.zim", "stackexchange", Domain.CODE_REVIEW, Variant.NONE),
    Archive("robotics.stackexchange.com_en_all_2026-02.zim",   "stackexchange", Domain.ROBOTICS,    Variant.NONE),
    Archive("engineering.stackexchange.com_en_all_2026-02.zim", "stackexchange", Domain.ENGINEERING, Variant.NONE),
    Archive("salesforce.stackexchange.com_en_all_2026-02.zim",  "stackexchange", Domain.SALESFORCE,  Variant.NONE),

    # --- System / OS -------------------------------------------------------
    Archive("archlinux_en_all_maxi_2026-04.zim", "system", Domain.ARCH_LINUX, Variant.MAXI),
    Archive("openwrt.org_en_all_2026-03.zim",    "system", Domain.OPENWRT,    Variant.NONE),
    Archive("termux_en_all_maxi_2022-12.zim",    "system", Domain.TERMUX,     Variant.MAXI,
            "Vintage 2022-12 — note when answering Termux questions"),

    # --- Other -------------------------------------------------------------
    Archive("foss.cooking_en_all_2026-05.zim", "other", Domain.COOKING, Variant.NONE),
)


_BY_FILENAME: dict[str, Archive] = {a.filename: a for a in ARCHIVES}


def get_archive(filename: str) -> Archive | None:
    """Look up a registered archive by filename. None if unknown."""
    return _BY_FILENAME.get(filename)


def all_archives() -> tuple[Archive, ...]:
    """All registered archives, in registration order."""
    return ARCHIVES


def archives_for_domain(domain: Domain) -> tuple[Archive, ...]:
    """Archives whose primary_domain matches, in registration order."""
    return tuple(a for a in ARCHIVES if a.primary_domain == domain)


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

# Per-domain fallback chain — tried after the primary domain's archives.
# Empty if the domain has no useful fallback.
_DOMAIN_FALLBACKS: dict[Domain, tuple[Domain, ...]] = {
    # Python
    Domain.PYTHON_STDLIB:   (Domain.PYTHON_PEPS,),
    Domain.PYTHON_PEPS:     (Domain.PYTHON_STDLIB,),
    Domain.FASTAPI:         (Domain.PYTHON_STDLIB,),
    Domain.PYTORCH:         (Domain.TENSORFLOW, Domain.PYTHON_STDLIB),
    Domain.TENSORFLOW:      (Domain.PYTORCH, Domain.PYTHON_STDLIB),
    Domain.PYGAME:          (Domain.PYTHON_STDLIB,),
    # JS / web
    Domain.JAVASCRIPT:      (Domain.TYPESCRIPT, Domain.NODE, Domain.JSDOC),
    Domain.TYPESCRIPT:      (Domain.JAVASCRIPT,),
    Domain.NODE:            (Domain.JAVASCRIPT,),
    Domain.DOM:             (Domain.HTML, Domain.JAVASCRIPT),
    Domain.HTML:            (Domain.DOM, Domain.CSS),
    Domain.JS_ALGORITHMS:   (Domain.JAVASCRIPT, Domain.COMPUTER_SCIENCE),
    # Systems
    Domain.CPP:             (Domain.C,),
    Domain.C:               (Domain.CPP,),
    # Game dev
    Domain.GODOT:           (Domain.VULKAN,),
    # Curriculum
    Domain.HTDP:            (Domain.COMPUTER_SCIENCE,),
    # Wikipedia
    Domain.MATH:            (Domain.WIKIPEDIA_GENERAL,),
    Domain.PHYSICS:         (Domain.WIKIPEDIA_GENERAL, Domain.MATH),
    Domain.COMPUTER_SCIENCE: (Domain.WIKIPEDIA_GENERAL,),
    # System / OS
    Domain.ARCH_LINUX:      (Domain.SERVERFAULT,),
    Domain.OPENWRT:         (Domain.ARCH_LINUX,),
    Domain.TERMUX:          (Domain.BASH, Domain.ARCH_LINUX),
    # Stack Exchange
    Domain.SERVERFAULT:     (Domain.ARCH_LINUX,),
    Domain.ROBOTICS:        (Domain.ENGINEERING,),
}


def _ordered_by_variant(archives: Iterable[Archive], *, prefer_images: bool) -> list[Archive]:
    """Apply Wikipedia image-variant preference: nopic→mini→maxi by default,
    reversed if prefer_images=True. NONE-variant archives rank last."""
    order = ((Variant.MAXI, Variant.MINI, Variant.NOPIC)
             if prefer_images
             else (Variant.NOPIC, Variant.MINI, Variant.MAXI))
    rank = {v: i for i, v in enumerate(order)}
    return sorted(archives, key=lambda a: rank.get(a.variant, len(order)))


def route_query(domain: Domain, *, prefer_images: bool = False) -> tuple[Archive, ...]:
    """Return the ordered list of archives to consult for a query in `domain`.

    Order:
      1. Primary domain archives, sorted by variant preference.
      2. Each fallback domain (in declared order), expanded the same way.
    No archive appears twice in the result.
    """
    seen: set[str] = set()
    out: list[Archive] = []

    def _add(d: Domain) -> None:
        for a in _ordered_by_variant(archives_for_domain(d), prefer_images=prefer_images):
            if a.filename not in seen:
                seen.add(a.filename)
                out.append(a)

    _add(domain)
    for fb in _DOMAIN_FALLBACKS.get(domain, ()):
        _add(fb)
    return tuple(out)


# ---------------------------------------------------------------------------
# Presence check — used by the spec's startup sequence.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PresenceReport:
    present: tuple[Archive, ...]
    missing: tuple[Archive, ...]

    @property
    def degraded(self) -> bool:
        return bool(self.missing)


def verify_presence() -> PresenceReport:
    """Check every registered ZIM for on-disk presence. No checksum."""
    present = tuple(a for a in ARCHIVES if a.exists())
    missing = tuple(a for a in ARCHIVES if not a.exists())
    return PresenceReport(present=present, missing=missing)


def _main() -> int:
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    log = logging.getLogger(__name__)

    log.info("ZIM root: %s", ZIM_KB_ZIM_DIR)
    log.info("Registered archives: %d", len(ARCHIVES))

    # Spec sanity: every domain referenced in fallbacks must have at least one archive.
    domains_with_archives = {a.primary_domain for a in ARCHIVES}
    bad = [d for chain in _DOMAIN_FALLBACKS.values() for d in chain if d not in domains_with_archives]
    if bad:
        log.error("fallback references domain(s) with no archives: %s", sorted(set(b.value for b in bad)))
        return 1

    # Routing demos
    for dom in (Domain.MATH, Domain.PYTORCH, Domain.JAVASCRIPT, Domain.TERMUX):
        primary = route_query(dom)
        log.info("route(%-12s) -> %s", dom.value, [a.filename for a in primary])
    log.info("route(MATH, prefer_images=True) -> %s",
             [a.filename for a in route_query(Domain.MATH, prefer_images=True)])

    # Presence
    report = verify_presence()
    log.info("Present on disk: %d", len(report.present))
    log.info("Missing:         %d", len(report.missing))
    if report.missing:
        log.info("Example missing path: %s", report.missing[0].path)

    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
