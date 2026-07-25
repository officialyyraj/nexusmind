"""DuckDuckGo search provider."""

import time
import asyncio

import httpx

from app.tools.web_search.schemas import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    SearchProvider,
)


class DuckDuckGoProvider:
    """DuckDuckGo HTML API provider (no API key required)."""

    BASE_URL = "https://duckduckgo.com/html/"

    async def search(self, request: SearchRequest) -> SearchResponse:
        """Execute a search using DuckDuckGo.
        
        Args:
            request: Search request
            
        Returns:
            Search response
        """
        start_time = time.time()

        params = {
            "q": request.query,
            "kl": "wt-wt",  # Region/language
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            html = response.text

        # Parse HTML results
        results = self._parse_html(html, request.max_results)

        execution_time = time.time() - start_time

        return SearchResponse(
            query=request.query,
            results=results,
            total=len(results),
            provider=SearchProvider.DUCKDUCKGO,
            execution_time=execution_time,
        )

    def _parse_html(self, html: str, max_results: int) -> list[SearchResult]:
        """Parse DuckDuckGo HTML response.
        
        Args:
            html: HTML response
            max_results: Maximum results to parse
            
        Returns:
            List of search results
        """
        results = []

        # Simple HTML parsing
        import re

        # Find result blocks
        result_pattern = r'<a class="result__a" href="([^"]+)">([^<]+)</a>'
        snippet_pattern = r'<a class="result__snippet" href="[^"]+">([^<]+)</a>'

        # Find URLs and titles
        url_title_matches = re.findall(result_pattern, html)
        snippet_matches = re.findall(snippet_pattern, html)

        for i, (url, title) in enumerate(url_title_matches[:max_results]):
            snippet = snippet_matches[i] if i < len(snippet_matches) else ""

            results.append(SearchResult(
                title=title.strip(),
                url=url,
                snippet=snippet.strip() if snippet else "",
                score=None,
                published_date=None,
                provider=SearchProvider.DUCKDUCKGO,
            ))

        return results
