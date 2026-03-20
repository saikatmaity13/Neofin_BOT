"""
Tool: web_search
Uses Tavily Search API for real-time web results.
Get a free key at: https://tavily.com (free tier: 1000 searches/month)
"""
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def web_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    import streamlit as st
    import urllib.request, json as _json, urllib.error

    api_key = ""
    try:
        api_key = st.secrets.get("TAVILY_API_KEY", "")
    except Exception:
        import os
        api_key = os.environ.get("TAVILY_API_KEY", "")

    if not api_key:
        return [{"title": "No Tavily Key", "url": "",
                 "content": "Add TAVILY_API_KEY to .streamlit/secrets.toml to enable web search."}]

    payload = _json.dumps({
        "api_key":      api_key,
        "query":        query,
        "search_depth": "basic",
        "max_results":  max_results,
        "include_answer": True,
    }).encode()

    try:
        req = urllib.request.Request(
            "https://api.tavily.com/search",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = _json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return [{"title": "Search Error", "url": "", "content": f"Tavily error: {e.code} {e.reason}"}]
    except Exception as e:
        return [{"title": "Search Error", "url": "", "content": str(e)}]

    results = []
    if data.get("answer"):
        results.append({"title": "Direct Answer", "url": "", "content": data["answer"]})
    for r in data.get("results", []):
        results.append({
            "title":   r.get("title", ""),
            "url":     r.get("url", ""),
            "content": r.get("content", "")[:600],
        })
    return results


def format_search_for_llm(results: List[Dict[str, Any]]) -> str:
    if not results:
        return "No results found."
    lines = []
    for i, r in enumerate(results, 1):
        src = f" ({r['url']})" if r["url"] else ""
        lines.append(f"[{i}] {r['title']}{src}\n    {r['content']}")
    return "\n\n".join(lines)