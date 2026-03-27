from thefuzz import process, fuzz
from .store import Shortcut, all_shortcuts


def fuzzy_find(query: str, limit: int = 5) -> list[tuple[Shortcut, int]]:
    """
    Returns list of (Shortcut, score) tuples, sorted by score descending.
    Score is 0-100. Anything above 40 is a reasonable match.
    """
    shortcuts = all_shortcuts()
    if not shortcuts:
        return []

    # Build a map of tag -> shortcut for lookup
    tag_map = {s.tag: s for s in shortcuts}
    tags = list(tag_map.keys())

    # Fuzzy match against tags (token_set_ratio handles word order)
    matches = process.extract(
        query,
        tags,
        scorer=fuzz.token_set_ratio,
        limit=limit,
    )

    return [
        (tag_map[tag], score)
        for tag, score, *_ in matches
        if score >= 40
    ]


def exact_find(tag: str) -> Shortcut | None:
    for s in all_shortcuts():
        if s.tag.lower() == tag.lower():
            return s
    return None


def find_by_category(category: str) -> list[Shortcut]:
    return [s for s in all_shortcuts() if s.category.lower() == category.lower()]
