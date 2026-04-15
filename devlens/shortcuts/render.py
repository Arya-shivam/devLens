"""
devLens — shortcut rendering (themed).

Delegates all visual work to the central render layer so the look stays
consistent across search results and shortcuts.
"""

from collections import defaultdict
from rich.console import Console

from ..render import (
    console,
    render_shortcut,
    render_shortcut_results,
    render_shortcuts_header,
    render_shortcuts_empty,
    render_category_block,
    render_shortcut_flat,
    _cat_color,
)
from ..theme import THEME
from .store import Shortcut, all_shortcuts


def render_match(shortcut: Shortcut, score: int, index: int):
    """Render a single shortcut match — delegates to central render."""
    render_shortcut(shortcut, score, index)


def render_results(matches: list[tuple[Shortcut, int]]):
    """Render shortcut matches with the themed actions bar."""
    render_shortcut_results(matches)


def render_all(sort: str = "category"):
    """List all saved shortcuts."""
    shortcuts = all_shortcuts()
    if not shortcuts:
        render_shortcuts_empty()
        return

    if sort == "recent":
        shortcuts.sort(key=lambda s: s.last_used or "", reverse=True)
    elif sort == "top":
        shortcuts.sort(key=lambda s: s.use_count, reverse=True)

    render_shortcuts_header(len(shortcuts))

    if sort == "category":
        by_cat: dict[str, list[Shortcut]] = defaultdict(list)
        for s in shortcuts:
            by_cat[s.category].append(s)

        for cat, items in sorted(by_cat.items()):
            render_category_block(cat, items)
    else:
        for s in shortcuts:
            color = _cat_color(s.category)
            render_shortcut_flat(s, color)
