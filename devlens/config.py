import os
import pathlib
import tomllib
from typing import Any, Dict

CONFIG_DIR = pathlib.Path.home() / ".devlens"
CONFIG_FILE = CONFIG_DIR / "config.toml"

DEFAULT_CONFIG = {
    "search": {
        "engine_url": "http://localhost:8080",
        "default_limit": 8
    },
    "ai": {
        "openrouter_api_key": ""
    }
}

def load_config() -> Dict[str, Any]:
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, "rb") as f:
            return tomllib.load(f)
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config_data: Dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    lines: list[str] = []
    if "search" in config_data:
        lines.append("[search]")
        lines.append(f'engine_url = "{config_data["search"].get("engine_url", "http://localhost:8080")}"')
        lines.append(f'default_limit = {config_data["search"].get("default_limit", 8)}')
        lines.append("")
    
    if "ai" in config_data:
        lines.append("[ai]")
        lines.append(f'openrouter_api_key = "{config_data["ai"].get("openrouter_api_key", "")}"')
        lines.append("")
    
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

config = load_config()

def get_engine_url() -> str:
    return config.get("search", {}).get("engine_url", "http://localhost:8080")

def get_default_limit() -> int:
    return config.get("search", {}).get("default_limit", 8)

def get_openrouter_api_key() -> str:
    # Environment variable overrides config file
    env_key = os.environ.get("OPENROUTER_API_KEY")
    return env_key or config.get("ai", {}).get("openrouter_api_key", "")
