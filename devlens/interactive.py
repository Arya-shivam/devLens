"""
devLens — interactive REPL for search results.
"""

import asyncio
import time
from typing import List, Dict, Any

from .browser import open_url
from .render import (
    console, render_results, render_prompt, prompt_input,
    render_spinner_status, render_bye, render_info, render_warning,
)
from .search import SearchClient
from .ranker import rank_and_filter
from .ai import summarize_results
from .theme import THEME
from rich.panel import Panel
from rich.text import Text


def run_interactive(results: List[Dict[str, Any]], query: str, elapsed: float):
    """Interactive REPL loop for search results."""
    render_results(results, query, elapsed)
    render_prompt()

    while True:
        try:
            raw = prompt_input().strip()
        except (KeyboardInterrupt, EOFError):
            render_bye()
            break

        cmd = raw.lower()

        if not cmd or cmd == "q":
            break

        # Open a result: "o 2", "o2", or just "2"
        elif (cmd.startswith("o ") or
              (cmd.startswith("o") and cmd[1:].isdigit()) or
              cmd.isdigit()):
            token = cmd.removeprefix("o").strip()
            if token.isdigit():
                idx = int(token)
                match = next(
                    (r for r in results if results.index(r) + 1 == idx),
                    None,
                )
                if match:
                    url = match.get("url", "")
                    open_url(url)
                    render_info(f"→ opening {url}")
                else:
                    render_warning(f"no result #{idx}")
            else:
                render_warning("usage: o <number> or just type a number")

        # Summarize
        elif cmd == "s":
            console.print()
            with render_spinner_status("summarizing..."):
                summary = asyncio.run(summarize_results(query, results))

            summary_text = Text(summary, style="dim italic")
            console.print(Panel(
                summary_text,
                title="[bold bright_white]AI Summary[/]",
                border_style=THEME["accent"],
                padding=(1, 2),
                expand=False,
                width=min(THEME["max_width"] - 2, 78),
            ))
            render_prompt()

        # New search
        elif cmd.startswith("/"):
            new_query = raw[1:].strip()
            if new_query:
                client = SearchClient()
                with render_spinner_status("searching..."):
                    start = time.monotonic()
                    try:
                        raw_results = asyncio.run(
                            client.search(query=new_query)
                        )
                    except Exception as e:
                        render_warning(f"Error: {e}")
                        continue
                    new_elapsed = time.monotonic() - start

                new_results = rank_and_filter(raw_results, dev_mode=True)
                if new_results:
                    results = new_results
                    query = new_query
                    render_results(results, query, new_elapsed)
                    render_prompt()
                else:
                    render_warning("no results found")
            else:
                render_warning("usage: / <new query>")

        # Next page (placeholder)
        elif cmd == "n":
            render_info("next page — coming soon")

        # Previous page (placeholder)
        elif cmd == "p":
            render_info("prev page — coming soon")

        else:
            render_warning("unknown command. try: o <n> · s · / <query> · q")
