import asyncio
import time
from typing import List, Dict, Any

from .browser import open_url
from .render import console, render_results, render_prompt
from .search import SearchClient
from .ranker import rank_and_filter
from .ai import summarize_results
from rich.panel import Panel


def run_interactive(results: List[Dict[str, Any]], query: str, elapsed: float):
    """Interactive REPL loop for search results."""
    render_results(results, query, elapsed)
    render_prompt()

    while True:
        try:
            raw = console.input("\n  [bold]>[/] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n  [dim]bye[/]\n")
            break

        cmd = raw.lower()

        if not cmd or cmd == "q":
            break

        # Open a result: "o 2", "o2", or just "2"
        elif cmd.startswith("o ") or cmd.startswith("o") and cmd[1:].isdigit() or cmd.isdigit():
            token = cmd.removeprefix("o").strip()
            if token.isdigit():
                idx = int(token)
                match = next((r for r in results if results.index(r) + 1 == idx), None)
                if match:
                    url = match.get("url", "")
                    open_url(url)
                    console.print(f"  [dim]→ opening {url}[/]")
                else:
                    console.print(f"  [yellow]no result #{idx}[/]")
            else:
                console.print("  [yellow]usage: o <number> or just type a number[/]")

        # Summarize
        elif cmd == "s":
            console.print()
            with console.status("[dim]summarizing…[/]", spinner="dots"):
                summary = asyncio.run(summarize_results(query, results))
            console.print(Panel(
                summary,
                title="🤖 AI Summary",
                border_style="green",
                padding=(1, 2),
            ))
            render_prompt()

        # New search
        elif cmd.startswith("/"):
            new_query = raw[1:].strip()
            if new_query:
                client = SearchClient()
                with console.status("[dim]searching…[/]", spinner="dots"):
                    start = time.monotonic()
                    try:
                        raw_results = asyncio.run(client.search(query=new_query))
                    except Exception as e:
                        console.print(f"  [bold red]Error:[/bold red] {e}")
                        continue
                    new_elapsed = time.monotonic() - start

                new_results = rank_and_filter(raw_results, dev_mode=True)
                if new_results:
                    results = new_results
                    query = new_query
                    render_results(results, query, new_elapsed)
                    render_prompt()
                else:
                    console.print("  [yellow]no results found[/]")
            else:
                console.print("  [yellow]usage: / <new query>[/]")

        # Next page (placeholder)
        elif cmd == "n":
            console.print("  [dim]next page — coming soon[/]")

        # Previous page (placeholder)
        elif cmd == "p":
            console.print("  [dim]prev page — coming soon[/]")

        else:
            console.print("  [yellow]unknown command. try: o <n> · s · / <query> · q[/]")
