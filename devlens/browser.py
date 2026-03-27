import subprocess
import sys
import shutil
from .config import config


def get_browser_command() -> str | None:
    """Read optional browser command from config."""
    return config.get("browser", {}).get("command")


def open_url(url: str) -> None:
    """Open a URL in the system default browser."""
    custom = get_browser_command()
    if custom:
        subprocess.run(custom.split() + [url], check=False)
        return

    if sys.platform == "darwin":
        subprocess.run(["open", url], check=False)
    elif sys.platform == "win32":
        subprocess.run(["start", url], shell=True, check=False)
    else:
        if shutil.which("xdg-open"):
            subprocess.run(["xdg-open", url], check=False)
        else:
            for browser in ["firefox", "chromium", "chromium-browser", "google-chrome"]:
                if shutil.which(browser):
                    subprocess.run([browser, url], check=False)
                    return
            print(f"  could not detect a browser. open manually:\n  {url}")
