"""Tavily web search: pulls live sources to ground fact-check verdicts in
current, real information instead of only the model's training data."""
import os
from typing import Dict, List
from urllib.parse import urlparse

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "").strip()

_client = None
if TAVILY_API_KEY:
    try:
        from tavily import TavilyClient
        _client = TavilyClient(api_key=TAVILY_API_KEY)
    except Exception as e:
        print(f"[tavily] init failed: {e}")
        _client = None


def search_web(claim: str, max_results: int = 5) -> List[Dict]:
    """Return live web results for a claim: [{title, url, domain, snippet}].
    Returns [] if no key is configured or the search fails, so callers can
    fall back to model-only reasoning without breaking the flow."""
    if _client is None:
        return []
    try:
        resp = _client.search(
            query=claim,
            search_depth="basic",
            max_results=max_results,
            include_answer=False,
        )
        results = []
        for r in resp.get("results", []):
            url = r.get("url", "")
            domain = urlparse(url).netloc.replace("www.", "")
            results.append({
                "title": r.get("title", domain or "Source"),
                "url": url,
                "domain": domain,
                "snippet": (r.get("content", "") or "")[:220],
            })
        return results
    except Exception as e:
        print(f"[tavily] search failed: {e}")
        return []


def format_for_prompt(results: List[Dict]) -> str:
    if not results:
        return "(no live web results available)"
    lines = []
    for r in results:
        lines.append(f"- [{r['domain']}] {r['title']}: {r['snippet']}")
    return "\n".join(lines)