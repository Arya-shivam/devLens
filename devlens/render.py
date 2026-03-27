from rich.console import Console
from rich.text import Text
from typing import List, Dict, Any

console = Console()

SOURCE_COLORS = {
    "docs":          "bright_cyan",
    "github":        "bright_white",
    "stackoverflow": "yellow",
    "blogs":         "magenta",
    "other":         "dim white",
}

SOURCE_LABELS = {
    "docs":          "Docs",
    "github":        "GitHub",
    "stackoverflow": "Stack Overflow",
    "blogs":         "Blog",
    "other":         "Web",
}


def _classify_source(url: str) -> str:
    """Quick source classification from URL."""
    url_lower = url.lower()
    if any(x in url_lower for x in ["docs.", "/docs/", "readthedocs", "devdocs", "-lang.org", ".dev"]):
        return "docs"
    if "github.com" in url_lower:
        return "github"
    if "stackoverflow.com" in url_lower or "stackexchange.com" in url_lower or "serverfault.com" in url_lower:
        return "stackoverflow"
    if any(x in url_lower for x in ["medium.com", "dev.to", "hashnode.com", "towardsdatascience.com"]):
        return "blogs"
    return "other"


def render_results(results: List[Dict[str, Any]], query: str, elapsed: float = 0.0):
    """Render numbered search results with source badges."""
    console.print()
    console.print(
        f"  [bold blue]🔍 devLens[/]  [dim]·[/]  "
        f"[white]{len(results)} results[/]  [dim]·[/]  "
        f"[dim]{elapsed:.1f}s[/]"
    )
    console.print()

    for idx, r in enumerate(results, start=1):
        title = r.get("title", "No title")
        url = r.get("url", "")
        snippet = r.get("content", "").replace("\n", " ")
        if len(snippet) > 160:
            snippet = snippet[:157] + "..."

        source = _classify_source(url)
        color = SOURCE_COLORS.get(source, "dim white")
        label = SOURCE_LABELS.get(source, "Web")

        domain = url.split("://")[-1].split("/")[0] if "://" in url else url

        console.print(f"  [bold dim]{idx}[/]  [bold]{title}[/]")
        console.print(f"     [dim]{domain}[/]  [{color}]· {label}[/]")
        if snippet:
            console.print(f"     [dim]{snippet}[/]")
        console.print()


def render_prompt():
    """Render the interactive command bar."""
    console.rule(style="dim")
    console.print(
        "  [dim]o <n>[/] open  "
        "[dim]n[/] next  "
        "[dim]s[/] summarize  "
        "[dim]/ <query>[/] search  "
        "[dim]q[/] quit",
        justify="center",
    )
