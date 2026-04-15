import sys
import json
import asyncio
import time
import typer
from rich.panel import Panel
from rich.text import Text
from typing import Optional
import importlib.metadata

from .search import SearchClient
from .ranker import rank_and_filter
from .error import is_piped, read_stdin, parse_error
from .ai import summarize_results, classify_query, generate_answer
from .pkg import format_package_query
from .config import get_default_limit
from .render import (
    console, render_results, render_prompt, render_spinner_status,
    render_error_unreachable, render_no_results, render_banner,
)
from .interactive import run_interactive
from .browser import open_url
from .theme import THEME

app = typer.Typer(
    help="devLens - Privacy-first search engine for developers",
    no_args_is_help=False,
    invoke_without_command=True,
)


def get_version():
    try:
        return importlib.metadata.version("devlens-cli")
    except Exception:
        return "0.1.0"


async def _do_search(query: str, web_mode: bool = False, source: str = "",
                     lang: str = "") -> tuple:
    """Run search + rank, return (results, elapsed, intent)."""
    client = SearchClient()
    start = time.monotonic()
    raw_results = await client.search(query=query)
    elapsed = time.monotonic() - start

    intent = "other"
    if not web_mode:
        try:
            intent = await classify_query(query)
        except Exception:
            pass

    dev_mode = not web_mode
    results = rank_and_filter(raw_results, dev_mode=dev_mode, lang=lang,
                              source_filter=source, intent=intent)
    return results, elapsed, intent


# ── Main search (default command) ─────────────────────────────────

@app.command(name="s")
def search_cmd(
    query: str = typer.Argument(..., help="Developer search query"),
    source: str = typer.Option(None, "--source", help="Filter by source"),
    lang: str = typer.Option(None, "--lang", help="Filter by language"),
    limit: int = typer.Option(None, help="Result limit"),
    json_out: bool = typer.Option(False, "--json", help="Output JSON"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color"),
    no_ai: bool = typer.Option(False, "--no-ai", help="Disable AI features"),
    open_idx: int = typer.Option(None, "--open", "-o", help="Open result N in browser"),
):
    """Dev search (interactive). Example: dlens s 'python asyncio'"""
    if limit is None:
        limit = get_default_limit()

    with render_spinner_status("searching docs..."):
        try:
            results, elapsed, intent = asyncio.run(
                _do_search(query, source=source or "", lang=lang or ""))
        except Exception as e:
            render_error_unreachable(e)
            raise typer.Exit(code=1)

    results = results[:limit]
    if not results:
        render_no_results(query)
        raise typer.Exit()

    if json_out:
        console.print(json.dumps(results, indent=2))
        return

    if open_idx is not None:
        if 1 <= open_idx <= len(results):
            open_url(results[open_idx - 1].get("url", ""))
        else:
            console.print(f"  [yellow]no result #{open_idx}[/]")
        return

    run_interactive(results, query, elapsed)


# ── Web search ────────────────────────────────────────────────────

@app.command()
def web(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(None, help="Number of results to show"),
    json_out: bool = typer.Option(False, "--json", help="Output JSON"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color"),
    open_idx: int = typer.Option(None, "--open", "-o", help="Open result N"),
):
    """General internet search with no dev-specific filtering."""
    if limit is None:
        limit = get_default_limit()

    with render_spinner_status("searching..."):
        try:
            results, elapsed, _ = asyncio.run(
                _do_search(query, web_mode=True))
        except Exception as e:
            render_error_unreachable(e)
            raise typer.Exit(code=1)

    results = results[:limit]
    if not results:
        render_no_results(query)
        raise typer.Exit()

    if json_out:
        console.print(json.dumps(results, indent=2))
        return

    if open_idx is not None:
        if 1 <= open_idx <= len(results):
            open_url(results[open_idx - 1].get("url", ""))
        else:
            console.print(f"  [yellow]no result #{open_idx}[/]")
        return

    run_interactive(results, query, elapsed)


# ── Error search ──────────────────────────────────────────────────

@app.command()
def error(
    message: str = typer.Argument(..., help="Error message to search"),
    source: str = typer.Option(None, "--source", help="Filter by source"),
    lang: str = typer.Option(None, "--lang", help="Filter by language"),
    limit: int = typer.Option(None, help="Result limit"),
    json_out: bool = typer.Option(False, "--json", help="Output JSON"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color"),
    open_idx: int = typer.Option(None, "--open", "-o", help="Open result N"),
):
    """Search for an error message, optimizing for StackOverflow and GitHub."""
    if limit is None:
        limit = get_default_limit()
    clean_query = parse_error(message)
    final_query = f"{clean_query} error {lang if lang else ''}".strip()

    with render_spinner_status("searching docs..."):
        try:
            results, elapsed, _ = asyncio.run(
                _do_search(final_query, source=source or "", lang=lang or ""))
        except Exception as e:
            render_error_unreachable(e)
            raise typer.Exit(code=1)

    results = results[:limit]
    if not results:
        render_no_results(final_query)
        raise typer.Exit()

    if json_out:
        console.print(json.dumps(results, indent=2))
        return

    if open_idx is not None:
        if 1 <= open_idx <= len(results):
            open_url(results[open_idx - 1].get("url", ""))
        else:
            console.print(f"  [yellow]no result #{open_idx}[/]")
        return

    run_interactive(results, final_query, elapsed)


# ── Package search ────────────────────────────────────────────────

@app.command()
def pkg(
    name: str = typer.Argument(..., help="Package name"),
    lang: str = typer.Option(None, "--lang", help="Language context"),
    limit: int = typer.Option(None, help="Result limit"),
    json_out: bool = typer.Option(False, "--json", help="Output JSON"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color"),
    open_idx: int = typer.Option(None, "--open", "-o", help="Open result N"),
):
    """Look up a package by name."""
    if limit is None:
        limit = get_default_limit()
    query = format_package_query(name, lang)

    with render_spinner_status("searching packages..."):
        try:
            results, elapsed, _ = asyncio.run(
                _do_search(query, lang=lang or ""))
        except Exception as e:
            render_error_unreachable(e)
            raise typer.Exit(code=1)

    results = results[:limit]
    if not results:
        render_no_results(query)
        raise typer.Exit()

    if json_out:
        console.print(json.dumps(results, indent=2))
        return

    if open_idx is not None:
        if 1 <= open_idx <= len(results):
            open_url(results[open_idx - 1].get("url", ""))
        else:
            console.print(f"  [yellow]no result #{open_idx}[/]")
        return

    run_interactive(results, query, elapsed)


# ── Shortcut commands ─────────────────────────────────────────────

@app.command()
def save(
    command: str = typer.Argument(..., help="The command to save"),
    tag: str = typer.Argument(..., help="Memorable label"),
    category: str = typer.Option("general", "--cat", "-c", help="Category"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing tag"),
):
    """Save a command shortcut. Usage: dlens save '<command>' '<tag>' [--cat <category>]"""
    from .shortcuts.store import save_shortcut

    from .render import render_success, render_warning
    try:
        s = save_shortcut(command, tag, category, force=force)
        console.print()
        render_success(f"saved! {s.tag}")
        console.print(f"  [dim]id: {s.id}[/]")
        console.print()
    except ValueError as e:
        console.print()
        render_warning(str(e))
        console.print()


@app.command()
def look(
    query: str = typer.Argument(..., help="Fuzzy search your shortcuts"),
    limit: int = typer.Option(5, "--limit", "-n"),
):
    """Fuzzy search saved shortcuts."""
    from .shortcuts.search import fuzzy_find
    from .shortcuts.interactive import run_interactive as shortcuts_interactive

    from .render import render_warning
    matches = fuzzy_find(query, limit=limit)
    if not matches:
        render_no_results(query)
        return

    shortcuts_interactive(matches)


@app.command(name="shortcuts")
def list_shortcuts(
    cat: str = typer.Option(None, "--cat", "-c", help="Filter by category"),
    recent: bool = typer.Option(False, "--recent", "-r", help="Sort by last used"),
    top: bool = typer.Option(False, "--top", "-t", help="Sort by use count"),
):
    """List all saved shortcuts."""
    from .shortcuts.render import render_all, render_match
    from .shortcuts.search import find_by_category

    if cat:
        items = find_by_category(cat)
        if not items:
            render_no_results(cat)
            return
        console.print()
        for i, s in enumerate(items, 1):
            render_match(s, 100, i)
        return

    sort = "recent" if recent else "top" if top else "category"
    render_all(sort=sort)


@app.command()
def rm(
    query: str = typer.Argument(None, help="Fuzzy tag to delete"),
    cat: str = typer.Option(None, "--cat", help="Delete entire category"),
    all_: bool = typer.Option(False, "--all", help="Delete all shortcuts"),
):
    """Delete a shortcut or group of shortcuts."""
    from .shortcuts.store import delete_shortcut, delete_by_category, delete_all

    if all_:
        confirm = console.input("  [bold red]delete ALL shortcuts?[/] (y/N) ")
        if confirm.strip().lower() == "y":
            delete_all()
            console.print("  [red]all shortcuts deleted[/]")
        return

    if cat:
        confirm = console.input(f"  delete all [bold]{cat}[/] shortcuts? (y/N) ")
        if confirm.strip().lower() == "y":
            count = delete_by_category(cat)
            console.print(f"  [red]deleted {count} {cat} shortcuts[/]")
        return

    if query:
        from .shortcuts.search import fuzzy_find
        matches = fuzzy_find(query, limit=3)
        if not matches:
            console.print(f"\n  [yellow]no match for '{query}'[/]\n")
            return
        shortcut, score = matches[0]
        confirm = console.input(f"  delete [bold]{shortcut.tag}[/]? (y/N) ")
        if confirm.strip().lower() == "y":
            delete_shortcut(shortcut.id)
            console.print("  [red]deleted[/]")
    else:
        console.print("  [yellow]provide a tag to delete, --cat, or --all[/]")


# ── Version + pipe handler ────────────────────────────────────────

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Print version"),
):
    """devLens - Privacy-first search engine for developers"""
    if version:
        render_banner()
        raise typer.Exit()

    if ctx.invoked_subcommand is not None:
        return

    # No subcommand → show banner + usage hints
    if not (is_piped() and not sys.stdin.closed):
        render_banner()
        console.print(
            f"  [bold]usage:[/]  dlens s '<query>'    [dim]dev search[/]\n"
            f"          dlens web '<query>'  [dim]general search[/]\n"
            f"          dlens look '<tag>'   [dim]find a shortcut[/]\n"
            f"          dlens --help         [dim]all commands[/]\n"
        )
        raise typer.Exit(0)

    # Handle piped input
    if is_piped() and not sys.stdin.closed:
        piped_data = read_stdin()
        if piped_data.strip():
            clean_query = parse_error(piped_data)
            pipeline_query = f"{clean_query} error".strip()
            with render_spinner_status("searching docs..."):
                try:
                    results, elapsed, intent = asyncio.run(
                        _do_search(pipeline_query))
                except Exception as e:
                    render_error_unreachable(e)
                    raise typer.Exit(code=1)

            if results:
                with render_spinner_status("generating answer..."):
                    answer = asyncio.run(generate_answer(pipeline_query, results, intent))
                answer_text = Text(answer, style="dim italic")
                console.print(Panel(
                    answer_text,
                    title="[bold bright_white]devLens Answer[/]",
                    border_style=THEME["accent"],
                    padding=(1, 2),
                    expand=False,
                ))
            return


if __name__ == "__main__":
    app()
