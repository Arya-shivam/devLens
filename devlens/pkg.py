from typing import Dict, Any

def format_package_query(name: str, lang: str = "") -> str:
    """
    Convert a package lookup into an optimized SearXNG query.
    For MVP, we just construct a good search string.
    """
    query_parts = [name, "package"]
    if lang:
        query_parts.append(lang)
        
    # Example: "httpx package python"
    return " ".join(query_parts)
