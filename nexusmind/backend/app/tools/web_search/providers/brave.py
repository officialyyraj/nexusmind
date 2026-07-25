"""Brave Search provider."""

import time
from urllib.parse import urlencode

import httpx

from app.tools.web_search.schemas import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    SearchProvider,
)


class BraveProvider:
    """Brave Search API provider."""

    BASE_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search(self, request: SearchRequest) -> SearchResponse:
        """Execute a search using Brave Search.
        
        Args:
            request: Search request
            
        Returns:
            Search response
        """
        start_time = time.time()
        
        headers = {
            "X-Subscription-Token": self.api_key,
            "Accept": "application/json",
        }
        
        params = {
            "q": request.query,
            "count": min(request.max_results, 20),  # Brave max is 20
        }
        
        url = f"{self.BASE_URL}?{urlencode(params)}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
        
        results = []
        web_results = data.get("web", {}).get("results", [])
        
        for item in web_results[:request.max_results]:
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("description", ""),
                score=item.get("score"),
                published_date=item.get("age"),
                provider=SearchProvider.BRAVE,
            ))
        
        execution_time = time.time() - start_time
        
        return SearchResponse(
            query=request.query,
            results=results,
            total=len(results),
            provider=SearchProvider.BRAVE,
            execution_time=execution_time,
        )
