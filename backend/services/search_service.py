"""
Search Service — Tavily web search integration.
Provides real-time web search augmentation for chat responses.
"""

import logging
from typing import Optional

from backend.config import Settings, get_settings

logger = logging.getLogger(__name__)


async def search_web(
    query: str,
    max_results: int = 3,
    settings: Optional[Settings] = None,
) -> list[dict]:
    """
    Search the web using Tavily API.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return.
        settings: Application settings. Uses cached singleton if None.

    Returns:
        List of search result dicts with 'url' and 'content' keys.
        Returns empty list if Tavily is not configured or search fails.
    """
    if settings is None:
        settings = get_settings()

    if not settings.tavily_api_key:
        logger.debug("Tavily API key not configured — skipping web search")
        return []

    try:
        from tavily import AsyncTavilyClient

        client = AsyncTavilyClient(api_key=settings.tavily_api_key)
        response = await client.search(
            query=query,
            max_results=max_results,
            search_depth="basic",
        )

        results = []
        for item in response.get("results", []):
            results.append({
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "title": item.get("title", ""),
            })

        logger.info("Tavily search returned %d results for: %s", len(results), query[:50])
        return results

    except Exception as e:
        logger.error("Tavily search failed: %s", e)
        return []


def is_search_available(settings: Optional[Settings] = None) -> bool:
    """Check if Tavily web search is configured and available."""
    if settings is None:
        settings = get_settings()
    return bool(settings.tavily_api_key)
