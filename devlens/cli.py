import sys
import json
import asyncio
import time
import typer
from rich.console import Console
from rich.panel import Panel
from typing import Optional
import importlib.metadata

from .search import SearchClient
from .ranker import rank_and_filter
from .error import is_piped, read_stdin, parse_error
from .ai import summarize_results, classify_query, generate_answer
from .pkg import format_package_query
from .config import get_default_limit
from .render import render_results, render_prompt
from .interactive import run_interactive
from .browser import open_url

app = typer.Typer(help="devLens - Privacy-first search engine for developers", no_args_is_help=True)
console = Console()

def get_version():
    try:
        return importlib.metadata.version("devlens-cli")
    except Exception:
        return "0.1.0"


async def _do_search(query: str, web_mode: bool = False, source: str = "",
                     lang: str = "") -> tuple:
    """Run search + rank, return (results, elapsed)."""
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


@app.command()
def web(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(None, help="Number of results to show"),
    json_out: bool = typer.Option(False, "--json", help="Output JSON"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
    open_idx: int = typer.Option(None, "--open", "-o", help="Open result N in browser"),
):
    """General internet search with no dev-specific filtering."""
    if limit is None:
        limit = get_default_limit()

    with console.status("[dim]searching…[/]", spinner="dots"):
        try:
            results, elapsed, _ = asyncio.run(
                _do_search(query, web_mode=True))
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(code=1)

    results = results[:limit]

    if not results:
        console.print("\n  [yellow]no results found[/]\n")
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


@app.command()
def error(
    message: str = typer.Argument(..., help="Error message to search"),
    source: str = typer.Option(None, "--source", help="Filter by source"),
    lang: str = typer.Option(None, "--lang", help="Filter by language"),
    limit: int = typer.Option(None, help="Result limit"),
    json_out: bool = typer.Option(False, "--json", help="Output JSON"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
    open_idx: int = typer.Option(None, "--open", "-o", help="Open result N in browser"),
):
    """Search for an error message, optimizing for StackOverflow and GitHub Issues."""
    if limit is None:
        limit = get_default_limit()
    clean_query = parse_error(message)
    final_query = f"{clean_query} error {lang if lang else ''}".strip()

    with console.status("[dim]searching…[/]", spinner="dots"):
        try:
            results, elapsed, _ = asyncio.run(
                _do_search(final_query, source=source or "", lang=lang or ""))
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(code=1)

    results = results[:limit]

    if not results:
        console.print("\n  [yellow]no results found[/]\n")
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


@app.command()
def pkg(
    name: str = typer.Argument(..., help="Package name"),
    lang: str = typer.Option(None, "--lang", help="Language context for package"),
    limit: int = typer.Option(None, help="Result limit"),
    json_out: bool = typer.Option(False, "--json", help="Output JSON"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
    open_idx: int = typer.Option(None, "--open", "-o", help="Open result N in browser"),
):
    """Look up a package by name."""
    if limit is None:
        limit = get_default_limit()
    query = format_package_query(name, lang)

    with console.status("[dim]searching…[/]", spinner="dots"):
        try:
            results, elapsed, _ = asyncio.run(
                _do_search(query, lang=lang or ""))
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(code=1)

    results = results[:limit]

    if not results:
        console.print("\n  [yellow]no results found[/]\n")
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


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    query: Optional[str] = typer.Argument(None, help="Developer search query"),
    source: str = typer.Option(None, "--source", help="Filter by source (docs, github, stackoverflow)"),
    lang: str = typer.Option(None, "--lang", help="Filter by language"),
    limit: int = typer.Option(None, help="Result limit"),
    json_out: bool = typer.Option(False, "--json", help="Output JSON"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
    no_ai: bool = typer.Option(False, "--no-ai", help="Disable AI features"),
    open_idx: int = typer.Option(None, "--open", "-o", help="Open result N in browser directly"),
    version: bool = typer.Option(False, "--version", help="Print version and exit"),
):
    """devLens - Privacy-first search engine for developers"""
    if version:
        console.print(f"devLens {get_version()}")
        raise typer.Exit()

    if ctx.invoked_subcommand is not None:
        return

    if limit is None:
        limit = get_default_limit()

    # ── Piped input → error mode, non-interactive
    if is_piped() and not sys.stdin.closed:
        piped_data = read_stdin()
        if piped_data.strip():
            clean_query = parse_error(piped_data)
            pipeline_query = f"{clean_query} error {lang if lang else ''}".strip()
            with console.status("[dim]searching…[/]", spinner="dots"):
                try:
                    results, elapsed, intent = asyncio.run(
                        _do_search(pipeline_query, source=source or "", lang=lang or ""))
                except Exception as e:
                    console.print(f"[bold red]Error:[/bold red] {e}")
                    raise typer.Exit(code=1)

            results = results[:limit]
            if not no_ai and results:
                with console.status("[dim]generating answer…[/]", spinner="dots"):
                    answer = asyncio.run(generate_answer(pipeline_query, results, intent))
                console.print(Panel(answer, title="🔍 devLens Answer",
                                    border_style="cyan", padding=(1, 2)))
            else:
                render_results(results, pipeline_query, elapsed)
            return

    if not query:
        if not is_piped():
            console.print(ctx.get_help())
        return

    # ── Main search
    with console.status("[dim]searching…[/]", spinner="dots"):
        try:
            results, elapsed, intent = asyncio.run(
                _do_search(query, source=source or "", lang=lang or ""))
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(code=1)

    results = results[:limit]

    if not results:
        console.print("\n  [yellow]no results found[/]\n")
        raise typer.Exit()

    # JSON output
    if json_out:
        console.print(json.dumps(results, indent=2))
        return

    # Direct open
    if open_idx is not None:
        if 1 <= open_idx <= len(results):
            open_url(results[open_idx - 1].get("url", ""))
        else:
            console.print(f"  [yellow]no result #{open_idx}[/]")
        return

    # Interactive mode (default)
    run_interactive(results, query, elapsed)


if __name__ == "__main__":
    app()
