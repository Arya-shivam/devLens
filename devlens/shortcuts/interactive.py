import subprocess
from .store import Shortcut, record_use, delete_shortcut, update_shortcut
from .render import render_results, console


def run_interactive(matches: list[tuple[Shortcut, int]]):
    """Interactive REPL after fuzzy search results."""
    if not matches:
        console.print("\n  [yellow]no matches found[/]\n")
        return

    render_results(matches)

    while True:
        try:
            raw = console.input("\n  [bold]>[/] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print()
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
                    console.print(f"  [green]copied![/] [dim]{cmd_preview}[/]")
                except ImportError:
                    console.print(f"  [cyan]{shortcut.command}[/]")
                    console.print("  [dim](copy manually — pyperclip not available)[/]")
                except Exception:
                    console.print(f"  [cyan]{shortcut.command}[/]")
                    console.print("  [dim](clipboard not available — copy manually)[/]")

        # Run: "r" or "r 2"
        elif cmd.startswith("r"):
            result = _pick(cmd, "r", matches)
            if result:
                shortcut, _ = result
                console.print(f"  [dim]running:[/] [cyan]{shortcut.command}[/]\n")
                record_use(shortcut.id)
                subprocess.run(shortcut.command, shell=True)

        # Edit: "e" or "e 2"
        elif cmd.startswith("e"):
            result = _pick(cmd, "e", matches)
            if result:
                shortcut, _ = result
                console.print(f"  current: [cyan]{shortcut.command}[/]")
                new_cmd = console.input("  new command (enter to keep): ").strip()
                new_tag = console.input("  new tag (enter to keep): ").strip()
                update_shortcut(
                    shortcut.id,
                    command=new_cmd or None,
                    tag=new_tag or None,
                )
                console.print("  [green]updated![/]")

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
                    console.print("  [red]deleted[/]")
                    break

        else:
            console.print(
                "  [yellow]commands: c copy · r run · e edit · d delete · q quit[/]"
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
    console.print("  [yellow]usage: <command> <number>[/]")
    return None
