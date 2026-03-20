import urllib.parse
from typing import Any, Dict, List, Optional

SOURCE_CATEGORIES = {
    "docs": ["docs.", "developer.", "-lang.org", ".dev", "readthedocs.io"],
    "github": ["github.com"],
    "stackoverflow": ["stackoverflow.com", "serverfault.com"],
    "blogs": ["medium.com", "dev.to", "hashnode.com", "towardsdatascience.com"]
}

def analyze_source(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.lower()
    
    for category, domains in SOURCE_CATEGORIES.items():
        for d in domains:
            if d in domain:
                return category
                
    if "doc" in domain or "manual" in domain:
        return "docs"
        
    return "other"

def score_result(result: Dict[str, Any], dev_mode: bool = True, intent: str = "other") -> float:
    base_score = float(result.get("score", 1.0))
    if not dev_mode:
        return base_score
        
    source = analyze_source(result.get("url", ""))
    
    weights = {
        "docs": 10.0,
        "github": 8.0,
        "stackoverflow": 7.0,
        "blogs": 2.0,
        "other": 1.0
    }
    
    if intent == "error":
        weights["stackoverflow"] = 12.0
        weights["github"] = 10.0
        weights["docs"] = 5.0
    elif intent == "how-to":
        weights["blogs"] = 6.0
        weights["stackoverflow"] = 8.0
        weights["docs"] = 9.0
    elif intent == "package":
        weights["github"] = 10.0
        weights["docs"] = 10.0
    elif intent == "concept":
        weights["docs"] = 12.0
        weights["blogs"] = 8.0
    
    bonus = weights.get(source, 1.0)
    return base_score * bonus

def deduplicate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen_urls = set()
    cleaned = []
    
    for r in results:
        url = r.get("url", "")
        # Remove trailing slash or fragment
        base_url = url.split("#")[0].rstrip("/")
        if base_url not in seen_urls:
            seen_urls.add(base_url)
            cleaned.append(r)
            
    return cleaned

def filter_by_language(results: List[Dict[str, Any]], lang: str) -> List[Dict[str, Any]]:
    if not lang:
        return results
        
    lang = lang.lower()
    filtered = []
    
    for r in results:
        content = str(r.get("content", "")).lower()
        title = str(r.get("title", "")).lower()
        url = str(r.get("url", "")).lower()
        
        if lang in title or lang in url or lang in content:
            filtered.append(r)
            
    return filtered

def rank_and_filter(results: List[Dict[str, Any]], 
                    dev_mode: bool = True,
                    lang: Optional[str] = None, 
                    source_filter: Optional[str] = None,
                    intent: str = "other") -> List[Dict[str, Any]]:
    
    processed = deduplicate_results(results)
    
    if lang:
        processed = filter_by_language(processed, lang)
        
    if source_filter:
        processed = [r for r in processed if analyze_source(r.get("url", "")) == source_filter.lower()]
        
    if dev_mode:
        for r in processed:
            r["_devlens_score"] = score_result(r, dev_mode, intent)
        processed.sort(key=lambda x: x.get("_devlens_score", 0.0), reverse=True)
        
    return processed
