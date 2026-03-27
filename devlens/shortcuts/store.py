import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

SHORTCUTS_PATH = Path.home() / ".devlens" / "shortcuts.json"


@dataclass
class Shortcut:
    id: str
    command: str
    tag: str
    category: str
    created: str
    last_used: str | None
    use_count: int


def _load() -> dict:
    if not SHORTCUTS_PATH.exists():
        return {"version": 1, "shortcuts": []}
    try:
        with open(SHORTCUTS_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception):
        return {"version": 1, "shortcuts": []}


def _save(data: dict) -> None:
    SHORTCUTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SHORTCUTS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def all_shortcuts() -> list[Shortcut]:
    data = _load()
    return [Shortcut(**s) for s in data["shortcuts"]]


def save_shortcut(command: str, tag: str, category: str = "general",
                  force: bool = False) -> Shortcut:
    data = _load()

    # Check for duplicate tag
    existing = next(
        (s for s in data["shortcuts"] if s["tag"].lower() == tag.lower()), None
    )
    if existing and not force:
        raise ValueError(
            f"tag '{tag}' already exists (id: {existing['id']}). "
            "Use --force to overwrite."
        )
    if existing and force:
        data["shortcuts"] = [s for s in data["shortcuts"] if s["id"] != existing["id"]]

    shortcut = Shortcut(
        id=uuid.uuid4().hex[:8],
        command=command,
        tag=tag,
        category=category.lower(),
        created=datetime.now(timezone.utc).isoformat(),
        last_used=None,
        use_count=0,
    )
    data["shortcuts"].append(asdict(shortcut))
    _save(data)
    return shortcut


def record_use(shortcut_id: str) -> None:
    data = _load()
    for s in data["shortcuts"]:
        if s["id"] == shortcut_id:
            s["use_count"] += 1
            s["last_used"] = datetime.now(timezone.utc).isoformat()
            break
    _save(data)


def delete_shortcut(shortcut_id: str) -> bool:
    data = _load()
    before = len(data["shortcuts"])
    data["shortcuts"] = [s for s in data["shortcuts"] if s["id"] != shortcut_id]
    _save(data)
    return len(data["shortcuts"]) < before


def delete_by_category(category: str) -> int:
    data = _load()
    before = len(data["shortcuts"])
    data["shortcuts"] = [
        s for s in data["shortcuts"] if s["category"].lower() != category.lower()
    ]
    _save(data)
    return before - len(data["shortcuts"])


def delete_all() -> None:
    _save({"version": 1, "shortcuts": []})


def update_shortcut(shortcut_id: str, command: str | None = None,
                    tag: str | None = None, category: str | None = None) -> bool:
    data = _load()
    for s in data["shortcuts"]:
        if s["id"] == shortcut_id:
            if command:
                s["command"] = command
            if tag:
                s["tag"] = tag
            if category:
                s["category"] = category
            _save(data)
            return True
    return False
