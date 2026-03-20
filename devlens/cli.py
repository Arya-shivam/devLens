import sys
import json
import asyncio
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

app = typer.Typer(help="devLens - Privacy-first search engine for developers", no_args_is_help=True)
console = Console()

def get_version():
    try:
        return importlib.metadata.version("devlens")
    except Exception:
        return "0.1.0"

def _print_results(results: list, query: str, lang: str, limit: int, 
                   use_json: bool, no_color: bool, dev_mode: bool = True):
    if no_color:
        global console
        console = Console(color_system=None)
        
    display_results = results[:limit]
    
    if use_json:
        console.print(json.dumps(display_results, indent=2))
        return

    console.print()
    header_text = f" devLens  {len(display_results)} results"
    if lang:
        header_text += f" · {lang}"
    if not dev_mode:
        header_text += " · web"
    
    console.print(f"[bold cyan]{header_text}[/bold cyan]")
    console.print()
    
    for idx, r in enumerate(display_results):
        title = r.get("title", "No title")
        url = r.get("url", "No URL")
        content = r.get("content", "").replace("\n", " ")
        if len(content) > 150:
            content = content[:147] + "..."
            
        domain = url.split("://")[-1].split("/")[0] if "://" in url else url
        
        console.print(f"  [bold green]{idx + 1}[/bold green]  [bold]{title}[/bold]")
        console.print(f"     [blue]{domain}[/blue]  ·  {url}")
        console.print(f"     {content}")
        console.print()

async def async_search(query: str, web_mode: bool = False, source: str = "", 
                       lang: str = "", summarize: bool = False, limit: int = 8, 
                       json_output: bool = False, no_color: bool = False, no_ai: bool = False):
    
    client = SearchClient()
    if not json_output:
        with console.status("[bold green]Searching SearXNG..."):
            try:
                raw_results = await client.search(query=query)
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")
                raise typer.Exit(code=1)
    else:
        try:
            raw_results = await client.search(query=query)
        except Exception as e:
            console.print(json.dumps({"error": str(e)}))
            raise typer.Exit(code=1)
            

    intent = "other"
    if not web_mode and not no_ai:
        if not json_output:
            with console.status("[bold green]Analyzing query intent..."):
                intent = await classify_query(query)
        else:
            intent = await classify_query(query)
            
    dev_mode = not web_mode
    results = rank_and_filter(raw_results, dev_mode=dev_mode, lang=lang, source_filter=source, intent=intent)
    
    # ── Agentic mode
    if not no_ai and not web_mode and results:
        if not json_output:
            with console.status("[bold green]Reading sources & generating answer..."):
                answer = await generate_answer(query, results, intent)

            console.print()
            console.print(Panel(
                answer,
                title="🔍 devLens Answer",
                border_style="cyan",
                padding=(1, 2),
            ))

            # Show compact source references below the answer
            console.print()
            console.print("[bold dim]Sources:[/bold dim]")
            for idx, r in enumerate(results[:5]):
                title = r.get("title", "")
                url = r.get("url", "")
                console.print(f"  [dim]{idx+1}. {title}[/dim]")
                console.print(f"     [blue underline]{url}[/blue underline]")
            console.print()
            return
        else:
            answer = await generate_answer(query, results, intent)
            console.print(json.dumps({"answer": answer, "sources": [r.get("url") for r in results[:5]]}, indent=2))
            return
    
    # ── Fallback: no-ai / web mode → show raw results ─────────────────
    if summarize and not no_ai:
        if not json_output:
            with console.status("[bold green]Generating AI summary..."):
                summary_text = await summarize_results(query, results)
            console.print(Panel(summary_text, title="🤖 AI Summary", border_style="green", padding=(1, 2)))
            
    _print_results(results, query, lang, limit, json_output, no_color, dev_mode)

@app.command()
def web(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(None, help="Number of results to show"),
    json: bool = typer.Option(False, "--json", help="Output JSON"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output")
):
    """General internet search with no dev-specific filtering."""
    if limit is None: limit = get_default_limit()
    asyncio.run(async_search(query, web_mode=True, limit=limit, json_output=json, no_color=no_color))

@app.command()
def error(
    message: str = typer.Argument(..., help="Error message to search"),
    source: str = typer.Option(None, "--source", help="Filter by source (docs, github, stackoverflow)"),
    lang: str = typer.Option(None, "--lang", help="Filter by language"),
    summarize: bool = typer.Option(False, "--summarize", help="Show AI summary"),
    limit: int = typer.Option(None, help="Result limit"),
    json: bool = typer.Option(False, "--json", help="Output JSON"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
    no_ai: bool = typer.Option(False, "--no-ai", help="Disable AI features")
):
    """Search for an error message, optimizing for StackOverflow and GitHub Issues."""
    if limit is None: limit = get_default_limit()
    clean_query = parse_error(message)
    final_query = f"{clean_query} error {lang if lang else ''}".strip()
    asyncio.run(async_search(final_query, web_mode=False, source=source, lang=lang, 
                            summarize=summarize, limit=limit, json_output=json, 
                            no_color=no_color, no_ai=no_ai))

@app.command()
def pkg(
    name: str = typer.Argument(..., help="Package name"),
    lang: str = typer.Option(None, "--lang", help="Language context for package"),
    limit: int = typer.Option(None, help="Result limit"),
    json: bool = typer.Option(False, "--json", help="Output JSON"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output")
):
    """Look up a package by name."""
    if limit is None: limit = get_default_limit()
    query = format_package_query(name, lang)
    asyncio.run(async_search(query, web_mode=False, lang=lang, limit=limit, 
                             json_output=json, no_color=no_color))

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    query: Optional[str] = typer.Argument(None, help="Developer search query"),
    source: str = typer.Option(None, "--source", help="Filter by source (docs, github, stackoverflow)"),
    lang: str = typer.Option(None, "--lang", help="Filter by language"),
    summarize: bool = typer.Option(False, "--summarize", help="Show AI summary"),
    limit: int = typer.Option(None, help="Result limit"),
    json: bool = typer.Option(False, "--json", help="Output JSON"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
    no_ai: bool = typer.Option(False, "--no-ai", help="Disable AI features"),
    version: bool = typer.Option(False, "--version", help="Print version and exit")
):
    """devLens - Privacy-first search engine for developers"""
    if version:
        console.print(f"devLens {get_version()}")
        raise typer.Exit()
        
    if ctx.invoked_subcommand is not None:
        return
        
    if limit is None: limit = get_default_limit()
    
    if is_piped() and not sys.stdin.closed:
        piped_data = read_stdin()
        if piped_data.strip():
            clean_query = parse_error(piped_data)
            pipeline_query = f"{clean_query} error {lang if lang else ''}".strip()
            asyncio.run(async_search(pipeline_query, web_mode=False, source=source, lang=lang, 
                                    summarize=summarize, limit=limit, json_output=json, 
                                    no_color=no_color, no_ai=no_ai))
            return
            
    if query:
        asyncio.run(async_search(query, web_mode=False, source=source, lang=lang, 
                                summarize=summarize, limit=limit, json_output=json, 
                                no_color=no_color, no_ai=no_ai))
    elif not is_piped():
        console.print(ctx.get_help())

if __name__ == "__main__":
    app()
