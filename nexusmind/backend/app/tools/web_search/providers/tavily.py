"""Tavily search provider."""

import time
from typing import Any

import httpx

from app.tools.web_search.schemas import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    SearchProvider,
)


class TavilyProvider:
    """Tavily search API provider."""

    BASE_URL = "https://api.tavily.com"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search(self, request: SearchRequest) -> SearchResponse:
        """Execute a search using Tavily.
        
        Args:
            request: Search request
            
        Returns:
            Search response
        """
        start_time = time.time()
        
        url = f"{self.BASE_URL}/search"
        
        params = {
            "api_key": self.api_key,
            "query": request.query,
            "search_depth": request.search_depth,
            "max_results": request.max_results,
            "include_answer": request.include_answer,
            "include_raw_content": request.include_raw_content,
        }
        
        if request.topic != "general":
            params["topic"] = request.topic
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=params)
            response.raise_for_status()
            data = response.json()
        
        results = []
        for item in data.get("results", []):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
                score=item.get("score"),
                published_date=item.get("published_date"),
                provider=SearchProvider.TAVILY,
            ))
        
        execution_time = time.time() - start_time
        
        return SearchResponse(
            query=request.query,
            results=results,
            total=len(results),
            provider=SearchProvider.TAVILY,
            execution_time=execution_time,
        )
