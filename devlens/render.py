"""
devLens — terminal render layer.

All display functions used by the CLI live here.  Every component pulls
its colours and layout constraints from theme.THEME so the look can be
changed in a single file.

Run standalone for a preview:
    python -m devlens.render
"""

from __future__ import annotations

import importlib.metadata
import shutil
import time
from typing import Any, Dict, List, Optional

from rich.console import Console, Group
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.spinner import Spinner
from rich.text import Text

from .theme import THEME

# ── Shared console ────────────────────────────────────────────────

import os
import sys

# Ensure Python uses UTF-8 for stdout on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

console = Console(highlight=False, width=min(
    THEME["max_width"], shutil.get_terminal_size().columns
))

_INDENT = THEME["indent"]
_MAX_W  = THEME["max_width"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1.  STARTUP BANNER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _get_version() -> str:
    try:
        return importlib.metadata.version("devlens")
    except Exception:
        return "0.2.0"


def render_banner() -> None:
    """Print the devLens startup banner — fast, no animation."""
    logo_lines = THEME["logo"].rstrip("\n").split("\n")
    version = _get_version()

    # Logo in accent colour
    for line in logo_lines:
        if line.strip():
            console.print(
                Text(f"{_INDENT}{line}", style=THEME["accent"])
            )

    # Tagline (italic, dim)
    console.print(
        Text(f"{_INDENT}{THEME['tagline']}", style=THEME["tagline_style"])
    )

    # Version — right-aligned within max_width
    ver_text = Text(f"v{version}", style=THEME["secondary"])
    ver_text.pad_left(_MAX_W - len(f"v{version}"))
    console.print(ver_text)
    console.print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2.  SOURCE CLASSIFICATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _classify_source(url: str) -> str:
    """Quick source classification from URL."""
    u = url.lower()
    if any(x in u for x in ["docs.", "/docs/", "readthedocs", "devdocs",
                              "-lang.org", ".dev"]):
        return "docs"
    if "github.com" in u:
        return "github"
    if any(x in u for x in ["stackoverflow.com", "stackexchange.com",
                              "serverfault.com"]):
        return "stackoverflow"
    if any(x in u for x in ["pypi.org", "npmjs.com", "crates.io",
                              "pkg.go.dev", "packagist.org"]):
        return "package"
    if any(x in u for x in ["medium.com", "dev.to", "hashnode.com",
                              "towardsdatascience.com"]):
        return "blogs"
    return "web"


def _source_badge(source: str) -> Text:
    """Return a colour-coded pill badge for a source type."""
    colour = THEME["source"].get(source, THEME["source"]["web"])
    label  = THEME["source_labels"].get(source, source)
    badge  = Text()
    badge.append(" ", style=f"on {colour}")
    badge.append(f" {label} ", style=f"bold {colour}")
    return badge


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3.  SEARCH RESULTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_results(results: List[Dict[str, Any]], query: str,
                   elapsed: float = 0.0) -> None:
    """Render numbered search results with source badges."""
    console.print()

    # ── Header: result count left, elapsed time right ──
    header = Text()
    left_part = f"{_INDENT}{len(results)} results for "
    header.append(left_part, style=THEME["secondary"])
    header.append(query, style=THEME["title_style"])

    elapsed_str = f"{elapsed:.2f}s"
    padding_needed = _MAX_W - len(left_part) - len(query) - len(elapsed_str)
    if padding_needed > 0:
        header.append(" " * padding_needed)
    header.append(elapsed_str, style=THEME["secondary"])
    console.print(header)
    console.print()

    rule_width = int(_MAX_W * THEME["rule_width_pct"])

    for idx, r in enumerate(results, start=1):
        title   = r.get("title", "No title")
        url     = r.get("url", "")
        snippet = r.get("content", "").replace("\n", " ").strip()
        if len(snippet) > THEME["snippet_max"]:
            snippet = snippet[: THEME["snippet_max"] - 3] + "..."

        source = _classify_source(url)
        badge  = _source_badge(source)
        domain = url.split("://")[-1].split("/")[0] if "://" in url else url

        # Line 1: [n]  Title  badge
        line1 = Text()
        line1.append(f"{_INDENT}[", style=THEME["index_style"])
        line1.append(str(idx), style=THEME["index_style"])
        line1.append("]  ", style=THEME["index_style"])
        line1.append(title, style=THEME["title_style"])
        line1.append("  ")
        line1.append_text(badge)
        console.print(line1)

        # Line 2: domain (dimmed)
        console.print(
            Text(f"{_INDENT}     {domain}", style=THEME["url_style"])
        )

        # Line 3: snippet (muted)
        if snippet:
            console.print(
                Text(f"{_INDENT}     {snippet}", style=THEME["snippet_style"])
            )

        # Separator between results (not after last)
        if idx < len(results):
            console.print()
            console.print(
                Padding(
                    Rule(style="dim", characters="-"),
                    (0, _MAX_W - rule_width, 0, 5),
                )
            )
            console.print()

    console.print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4.  INTERACTIVE PROMPT / HINTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_prompt() -> None:
    """Render the command-hint footer below results."""
    hints = Text(style=THEME["hint_style"])
    hints.append(f"{_INDENT}")
    parts = [
        ("o", "<n> open"),
        ("s", " summarize"),
        ("/", " <query> search"),
        ("n", " next"),
        ("q", " quit"),
    ]
    for i, (key, desc) in enumerate(parts):
        if i > 0:
            hints.append("    ", style=THEME["hint_style"])
        hints.append(key, style=f"{THEME['accent']} bold")
        hints.append(desc, style=THEME["hint_style"])
    console.print(hints)


def prompt_input() -> str:
    """Render the interactive prompt glyph and read input."""
    glyph = THEME["prompt_glyph"]
    style = THEME["prompt_style"]
    return console.input(f"\n  [{style}]{glyph}[/] ")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5.  LOADING / SPINNER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_spinner_status(message: str = "searching..."):
    """Return a console.status context manager with themed spinner."""
    return console.status(
        f"[{THEME['secondary']}]{_INDENT}{message}[/]",
        spinner=THEME["spinner_style"],
        spinner_style=THEME["accent"],
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6.  SHORTCUT RESULTS  (dlens look)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _cat_color(category: str) -> str:
    return THEME["category"].get(category.lower(), "dim")


def render_shortcut(shortcut, score: int, index: int) -> None:
    """Render a single shortcut match — bordered box style."""
    color = _cat_color(shortcut.category)
    last  = shortcut.last_used[:10] if shortcut.last_used else "never"

    # Title line: index + category badge + tag
    line1 = Text()
    line1.append(f"{_INDENT}[", style=THEME["index_style"])
    line1.append(str(index), style=THEME["index_style"])
    line1.append("]  ", style=THEME["index_style"])
    # Category badge
    line1.append(f" {shortcut.category} ", style=f"bold {color}")
    line1.append("  ")
    line1.append(shortcut.tag, style=THEME["title_style"])

    # Command in a subtle bordered box
    cmd_text = Text(f"  {shortcut.command}", style=THEME["accent"])
    box = Panel(
        cmd_text,
        border_style="dim",
        expand=False,
        padding=(0, 1),
        width=min(len(shortcut.command) + 8, _MAX_W - 4),
    )

    # Metadata
    meta = Text(style=THEME["secondary"])
    meta.append(f"{_INDENT}     used {shortcut.use_count}x")
    meta.append(f"  ·  last {last}")
    if score < 100:
        meta.append(f"  ·  match {score}%")

    console.print(line1)
    console.print(Padding(box, (0, 0, 0, 5)))
    console.print(meta)
    console.print()


def render_shortcut_results(matches) -> None:
    """Render shortcut matches with the themed actions bar."""
    console.print()
    for i, (shortcut, score) in enumerate(matches, start=1):
        render_shortcut(shortcut, score, i)

    # Actions bar
    actions = Text(style=THEME["hint_style"])
    actions.append(f"{_INDENT}")
    for i, (key, label) in enumerate([
        ("c", " copy"), ("r", " run"), ("e", " edit"),
        ("d", " delete"), ("q", " quit"),
    ]):
        if i > 0:
            actions.append("    ", style=THEME["hint_style"])
        actions.append(key, style=f"{THEME['accent']} bold")
        actions.append(label, style=THEME["hint_style"])
    console.print(actions)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7.  NOTE CONFIRMATION  (dlens note)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_note_saved(filepath: str) -> None:
    """Slim green success bar for saved notes."""
    line = Text()
    line.append(f"{_INDENT}✓", style=f"bold {THEME['success']}")
    line.append(f"  saved to Logseq  →  ", style=THEME["primary"])
    line.append(filepath, style=THEME["secondary"])
    console.print()
    console.print(line)
    console.print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8.  ERROR STATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_error_unreachable(raw_error: str | Exception) -> None:
    """SearXNG-unreachable warning panel — not a raw traceback."""
    body = Text()
    body.append("Search engine unreachable\n\n", style=f"bold {THEME['warning']}")
    body.append("What failed: ", style=THEME["primary"])
    body.append("could not connect to SearXNG instance\n", style=THEME["secondary"])
    body.append("How to fix:  ", style=THEME["primary"])
    body.append("make sure Docker Desktop is running and the\n", style=THEME["secondary"])
    body.append("             SearXNG container is started ", style=THEME["secondary"])
    body.append("(docker compose up -d)\n\n", style=f"{THEME['accent']}")
    body.append(str(raw_error), style="dim")

    console.print()
    console.print(Padding(
        Panel(body, border_style=THEME["warning"], expand=False,
              width=min(_MAX_W - 2, 78), padding=(1, 2)),
        (0, 0, 0, 2),
    ))
    console.print()


def render_no_results(query: str) -> None:
    """No results — with a suggested reformulation."""
    console.print()
    line = Text()
    line.append(f"{_INDENT}no results for ", style=THEME["empty_style"])
    line.append(f'"{query}"', style=THEME["primary"])
    console.print(line)

    hint = Text()
    hint.append(f"{_INDENT}try: ", style=THEME["secondary"])
    # Simple reformulation: drop quotes, add "how to"
    suggestion = query.strip("'\"")
    if not suggestion.lower().startswith("how"):
        suggestion = f"how to {suggestion}"
    hint.append(suggestion, style=THEME["accent"])
    console.print(hint)
    console.print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9.  SHORTCUT LIST  (dlens shortcuts)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_shortcuts_header(count: int) -> None:
    header = Text()
    header.append(f"{_INDENT}devLens shortcuts", style=THEME["title_style"])
    header.append(f"  ·  {count} saved", style=THEME["secondary"])
    console.print()
    console.print(header)
    console.print()


def render_shortcuts_empty() -> None:
    console.print()
    console.print(
        Text(f"{_INDENT}no shortcuts saved yet.", style=THEME["empty_style"])
    )
    console.print(
        Text(f'{_INDENT}try: dlens save "<command>" "<tag>"',
             style=THEME["secondary"])
    )
    console.print()


def render_category_block(category: str, items) -> None:
    """Render a category header + its commands."""
    color = _cat_color(category)
    console.print(Text(f"{_INDENT}{category}", style=f"bold {color}"))
    for s in items:
        cmd_preview = s.command[:55] + "…" if len(s.command) > 55 else s.command
        line = Text()
        line.append(f"{_INDENT}  ── ", style="dim")
        line.append(f"{s.tag:<30}", style=THEME["title_style"])
        line.append(cmd_preview, style=THEME["accent"])
        console.print(line)
    console.print()


def render_shortcut_flat(shortcut, category_color: str) -> None:
    """Single shortcut in flat list mode (recent / top)."""
    cmd_preview = (shortcut.command[:50] + "…"
                   if len(shortcut.command) > 50 else shortcut.command)
    line1 = Text()
    line1.append(f"{_INDENT}")
    line1.append(f"{shortcut.tag:<32}", style=THEME["title_style"])
    line1.append(f" {shortcut.category} ", style=f"bold {category_color}")
    line1.append(f"  used {shortcut.use_count}x", style=THEME["secondary"])
    console.print(line1)
    console.print(Text(f"{_INDENT}{cmd_preview}", style=THEME["accent"]))
    console.print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 10. GENERIC MESSAGES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_success(message: str) -> None:
    console.print(
        Text(f"{_INDENT}✓  {message}", style=f"bold {THEME['success']}")
    )

def render_warning(message: str) -> None:
    console.print(
        Text(f"{_INDENT}⚠  {message}", style=THEME["warning"])
    )

def render_info(message: str) -> None:
    console.print(Text(f"{_INDENT}{message}", style=THEME["secondary"]))

def render_bye() -> None:
    console.print(Text(f"\n{_INDENT}bye", style=THEME["secondary"]))
    console.print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DEMO — preview the UI without a live backend
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_DEMO_RESULTS: List[Dict[str, Any]] = [
    {
        "title": "asyncio — Asynchronous I/O",
        "url": "https://docs.python.org/3/library/asyncio.html",
        "content": (
            "asyncio is a library to write concurrent code using the "
            "async/await syntax. It is used as a foundation for multiple "
            "Python asynchronous frameworks."
        ),
    },
    {
        "title": "Real Python: Async IO in Python",
        "url": "https://realpython.com/async-io-python/",
        "content": (
            "A walkthrough of writing concurrent code in Python using "
            "asyncio, covering coroutines, tasks, and the event loop."
        ),
    },
    {
        "title": "aio-libs/aiohttp: Async HTTP client/server",
        "url": "https://github.com/aio-libs/aiohttp",
        "content": (
            "aiohttp is an asynchronous HTTP Client/Server framework. "
            "Supports both client and server Web-Sockets out-of-the-box."
        ),
    },
    {
        "title": "How do I run two async tasks at the same time?",
        "url": "https://stackoverflow.com/questions/29269370",
        "content": (
            "Use asyncio.gather() to run multiple coroutines concurrently. "
            "Each coroutine will run in the same event loop on a single thread."
        ),
    },
    {
        "title": "httpx 0.27 — A next-generation HTTP client for Python",
        "url": "https://pypi.org/project/httpx/",
        "content": (
            "HTTPX is a fully featured HTTP client library for Python 3. "
            "It includes an integrated command-line client, HTTP/2 support, "
            "and async APIs."
        ),
    },
]


def demo() -> None:
    """Full UI preview with fake data — no live backend needed."""
    render_banner()

    # ── Search results ──
    render_results(_DEMO_RESULTS, "python asyncio", elapsed=0.42)
    render_prompt()
    console.print()

    # ── Loading state ──
    console.print(
        Text(f"\n{_INDENT}── loading state preview ──", style="dim italic")
    )
    for msg in THEME["spinner_messages"]:
        spinner = Spinner(THEME["spinner_style"], style=THEME["accent"])
        line = Text()
        line.append(f"{_INDENT}")
        console.print(
            Text(f"{_INDENT}  ◌ {msg}", style=THEME["secondary"])
        )
    console.print()

    # ── Shortcut result ──
    console.print(
        Text(f"{_INDENT}── shortcut result preview ──", style="dim italic")
    )
    console.print()

    class _FakeShortcut:
        tag = "restart-containers"
        command = "docker compose down && docker compose up -d"
        category = "docker"
        use_count = 14
        last_used = "2026-04-05T09:30:00"

    render_shortcut(_FakeShortcut(), score=92, index=1)

    # ── Note saved ──
    console.print(
        Text(f"{_INDENT}── note confirmation preview ──", style="dim italic")
    )
    render_note_saved("journals/2026_04_07.md")

    # ── Error states ──
    console.print(
        Text(f"{_INDENT}── error state previews ──", style="dim italic")
    )
    render_error_unreachable(
        "ConnectionError: Cannot connect to host localhost:8080"
    )
    render_no_results("fzf rust alternative 2026")


if __name__ == "__main__":
    demo()
