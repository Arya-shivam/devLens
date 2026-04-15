"""
devLens — shortcut interactive REPL (themed).
"""

import subprocess
from .store import Shortcut, record_use, delete_shortcut, update_shortcut
from .render import render_results
from ..render import (
    console, prompt_input, render_success, render_warning,
    render_info, render_bye,
)


def run_interactive(matches: list[tuple[Shortcut, int]]):
    """Interactive REPL after fuzzy search results."""
    if not matches:
        render_warning("no matches found")
        return

    render_results(matches)

    while True:
        try:
            raw = prompt_input().strip()
        except (KeyboardInterrupt, EOFError):
            render_bye()
            break

        cmd = raw.lower()

        if not cmd or cmd == "q":
            break

        # Copy: "c" or "c 2"
        elif cmd.startswith("c"):
            result = _pick(cmd, "c", matches)
            if result:
                shortcut, _ = result
                try:
                    import pyperclip
                    pyperclip.copy(shortcut.command)
                    record_use(shortcut.id)
                    cmd_preview = shortcut.command[:60]
                    render_success(f"copied!  {cmd_preview}")
                except ImportError:
                    render_info(shortcut.command)
                    render_info("(copy manually — pyperclip not available)")
                except Exception:
                    render_info(shortcut.command)
                    render_info("(clipboard not available — copy manually)")

        # Run: "r" or "r 2"
        elif cmd.startswith("r"):
            result = _pick(cmd, "r", matches)
            if result:
                shortcut, _ = result
                render_info(f"running: {shortcut.command}")
                console.print()
                record_use(shortcut.id)
                subprocess.run(shortcut.command, shell=True)

        # Edit: "e" or "e 2"
        elif cmd.startswith("e"):
            result = _pick(cmd, "e", matches)
            if result:
                shortcut, _ = result
                render_info(f"current: {shortcut.command}")
                new_cmd = console.input("  new command (enter to keep): ").strip()
                new_tag = console.input("  new tag (enter to keep): ").strip()
                update_shortcut(
                    shortcut.id,
                    command=new_cmd or None,
                    tag=new_tag or None,
                )
                render_success("updated!")

        # Delete: "d" or "d 2"
        elif cmd.startswith("d"):
            result = _pick(cmd, "d", matches)
            if result:
                shortcut, _ = result
                confirm = console.input(
                    f"  delete [bold]{shortcut.tag}[/]? [dim](y/N)[/] "
                )
                if confirm.strip().lower() == "y":
                    delete_shortcut(shortcut.id)
                    render_warning("deleted")
                    break

        else:
            render_warning(
                "commands: c copy · r run · e edit · d delete · q quit"
            )


def _pick(raw: str, prefix: str,
          matches: list[tuple[Shortcut, int]]) -> tuple[Shortcut, int] | None:
    """Parse 'c 2' -> pick match at index 2. 'c' alone -> pick first."""
    parts = raw.removeprefix(prefix).strip()
    if not parts:
        return matches[0] if matches else None
    if parts.isdigit():
        idx = int(parts) - 1
        if 0 <= idx < len(matches):
            return matches[idx]
    render_warning("usage: <command> <number>")
    return None
