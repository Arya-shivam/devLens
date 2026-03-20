import httpx
from typing import Any, Dict, List, Optional
from .config import get_engine_url

class SearchClient:
    def __init__(self, base_url: Optional[str] = None):
        if base_url is None:
            base_url = get_engine_url()
        self.base_url = base_url.rstrip('/')
        self.endpoint = f"{self.base_url}/search"
        
    async def search(self, query: str, engines: Optional[List[str]] = None, categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Query the SearXNG instance and return JSON results.
        """
        params = {
            "q": query,
            "format": "json"
        }
        if engines:
            params["engines"] = ",".join(engines)
        if categories:
            params["categories"] = ",".join(categories)
            
        async with httpx.AsyncClient(http2=True) as client:
            try:
                response = await client.get(self.endpoint, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])
            except httpx.HTTPError as e:
                # Re-raise with user-friendly message
                raise RuntimeError(f"Connection error to API. Is SearXNG running at {self.base_url}? Error: {str(e)}")
