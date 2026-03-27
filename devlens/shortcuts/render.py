from collections import defaultdict
from rich.console import Console
from .store import Shortcut, all_shortcuts

console = Console()

CAT_COLORS = {
    "git":     "bright_green",
    "docker":  "bright_cyan",
    "ffmpeg":  "bright_yellow",
    "curl":    "bright_magenta",
    "npm":     "red",
    "python":  "blue",
    "general": "white",
}


def cat_color(category: str) -> str:
    return CAT_COLORS.get(category.lower(), "bright_white")


def render_match(shortcut: Shortcut, score: int, index: int):
    color = cat_color(shortcut.category)
    last = shortcut.last_used[:10] if shortcut.last_used else "never"

    console.print(
        f"  [bold dim]{index}[/]  [bold]{shortcut.tag}[/]  "
        f"[{color}][{shortcut.category}][/]  "
        f"[dim](match: {score}%)[/]"
    )
    console.print(f"     [bold cyan]{shortcut.command}[/]")
    console.print(
        f"     [dim]used {shortcut.use_count}x · last used {last} · id {shortcut.id}[/]"
    )
    console.print()


def render_results(matches: list[tuple[Shortcut, int]]):
    console.print()
    for i, (shortcut, score) in enumerate(matches, start=1):
        render_match(shortcut, score, i)
    console.rule(style="dim")
    console.print(
        "  [dim]c[/] copy  "
        "[dim]r[/] run  "
        "[dim]e[/] edit  "
        "[dim]d[/] delete  "
        "[dim]q[/] quit",
        justify="center",
    )


def render_all(sort: str = "category"):
    shortcuts = all_shortcuts()
    if not shortcuts:
        console.print("\n  [dim]no shortcuts saved yet.[/]")
        console.print('  [dim]try: dlens save "<command>" --tag "label"[/]\n')
        return

    if sort == "recent":
        shortcuts.sort(key=lambda s: s.last_used or "", reverse=True)
    elif sort == "top":
        shortcuts.sort(key=lambda s: s.use_count, reverse=True)

    console.print()
    console.print(f"  [bold]devLens shortcuts[/]  [dim]· {len(shortcuts)} saved[/]")
    console.print()

    if sort == "category":
        by_cat: dict[str, list[Shortcut]] = defaultdict(list)
        for s in shortcuts:
            by_cat[s.category].append(s)

        for cat, items in sorted(by_cat.items()):
            color = cat_color(cat)
            console.print(f"  [{color}]{cat}[/]")
            for s in items:
                cmd_preview = s.command[:55] + "…" if len(s.command) > 55 else s.command
                console.print(
                    f"  [dim]──[/] [bold]{s.tag:<30}[/] [cyan]{cmd_preview}[/]"
                )
            console.print()
    else:
        for s in shortcuts:
            color = cat_color(s.category)
            cmd_preview = s.command[:50] + "…" if len(s.command) > 50 else s.command
            console.print(
                f"  [bold]{s.tag:<32}[/] [{color}][{s.category}][/]  "
                f"[dim]used {s.use_count}x[/]"
            )
            console.print(f"  [cyan]{cmd_preview}[/]")
            console.print()
