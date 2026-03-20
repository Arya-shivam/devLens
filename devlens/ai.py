import json
import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from pydantic import BaseModel
from openrouter import OpenRouter
from .config import get_openrouter_api_key


class QueryClassification(BaseModel):
    intent: str


# ---------------------------------------------------------------------------
# Webpage scraping
# ---------------------------------------------------------------------------

async def _fetch_page(client: httpx.AsyncClient, url: str) -> str:
    """Fetch a single URL and return its cleaned text content (max ~4000 chars)."""
    try:
        resp = await client.get(url, timeout=8.0, follow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Remove noise elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
            tag.decompose()

        # Prefer <article> or <main> if present
        body = soup.find("article") or soup.find("main") or soup.find("body")
        text = body.get_text(separator="\n", strip=True) if body else ""

        # Trim to keep context window reasonable
        return text[:4000]
    except Exception:
        return ""


async def read_webpages(urls: List[str], max_pages: int = 3) -> List[Dict[str, str]]:
    """
    Concurrently fetch and extract text from the top *max_pages* URLs.
    Returns a list of {"url": ..., "text": ...} dicts.
    """
    targets = urls[:max_pages]
    async with httpx.AsyncClient(
        headers={"User-Agent": "devLens/0.1 (privacy-first dev search)"},
    ) as client:
        tasks = [_fetch_page(client, u) for u in targets]
        texts = await asyncio.gather(*tasks)

    pages = []
    for url, text in zip(targets, texts):
        if text.strip():
            pages.append({"url": url, "text": text})
    return pages


# ---------------------------------------------------------------------------
# Query classification
# ---------------------------------------------------------------------------

async def classify_query(query: str) -> str:
    """
    Classify the query intent into error, how-to, concept, package, or other.
    """
    key = get_openrouter_api_key()
    if not key:
        return "other"

    try:
        async with OpenRouter(api_key=key) as client:
            response = await client.chat.send_async(
                model="openrouter/auto",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a query classification engine for a developer search tool. "
                            "Classify the user's query into exactly one of these categories: "
                            "'error', 'how-to', 'concept', 'package', 'other'. "
                            "Respond only with a JSON object with an 'intent' key."
                        ),
                    },
                    {"role": "user", "content": f"Query: {query}"},
                ],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            try:
                data = json.loads(content)
                intent = data.get("intent", "other").lower()
                if intent in ("error", "how-to", "concept", "package", "other"):
                    return intent
            except json.JSONDecodeError:
                pass
    except Exception:
        pass
    return "other"


# ---------------------------------------------------------------------------
# Answer generation  (reads pages, synthesizes a final answer)
# ---------------------------------------------------------------------------

async def generate_answer(query: str, results: List[Dict[str, Any]], intent: str = "other") -> str:
    """
    1. Scrape the top search-result pages.
    2. Feed the full text + query to OpenRouter.
    3. Return a direct, synthesized technical answer.
    """
    key = get_openrouter_api_key()
    if not key:
        return "OpenRouter API key not configured. Set OPENROUTER_API_KEY environment variable or ~/.devlens/config.toml."

    # --- Step 1: read the actual webpages ---------------------------------
    urls = [r.get("url", "") for r in results if r.get("url")]
    pages = await read_webpages(urls, max_pages=3)

    if not pages:
        # Fallback to snippet-only mode
        snippets = "\n\n".join(
            f"Source: {r.get('title','')}\n{r.get('content','')}" for r in results[:5]
        )
        context_block = f"(Could not fetch full pages; using search snippets)\n\n{snippets}"
    else:
        parts = []
        for p in pages:
            parts.append(f"--- Source: {p['url']} ---\n{p['text']}")
        context_block = "\n\n".join(parts)

    # --- Step 2: build the prompt -----------------------------------------
    system_prompt = (
        "You are devLens, a developer-focused search assistant. "
        "You have been given the full text of several authoritative web pages that were retrieved for the user's query. "
        "Read and analyse the content carefully, then provide a clear, accurate, and concise technical answer. "
        "Include code examples when relevant. "
        "Cite the source URL inline when you reference specific information (e.g. [source](url)). "
        "Do NOT simply list the pages — give a definitive answer."
    )

    user_prompt = (
        f"Query: {query}\n"
        f"Detected intent: {intent}\n\n"
        f"--- Retrieved page contents ---\n\n{context_block}\n\n"
        "Based on the above sources, provide the best possible answer to the query."
    )

    # --- Step 3: call OpenRouter ------------------------------------------
    try:
        async with OpenRouter(api_key=key) as client:
            response = await client.chat.send_async(
                model="openrouter/auto",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content
    except Exception as e:
        return f"AI answer generation failed: {e}"


# ---------------------------------------------------------------------------
# Legacy summarize (kept for --summarize flag backward compat)
# ---------------------------------------------------------------------------

async def summarize_results(query: str, results: list) -> str:
    """Thin wrapper — delegates to generate_answer."""
    return await generate_answer(query, results)
