"""Web search service with caching, rate limiting, and retries."""

import asyncio
import hashlib
import time
from datetime import datetime, timedelta
from typing import Any

import httpx

from app.tools.web_search.providers.tavily import TavilyProvider
from app.tools.web_search.providers.brave import BraveProvider
from app.tools.web_search.providers.duckduckgo import DuckDuckGoProvider
from app.tools.web_search.schemas import (
    SearchCacheEntry,
    SearchConfig,
    SearchProvider,
    SearchRequest,
    SearchResponse,
    SearchResult,
)


class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""

    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.tokens = requests_per_minute
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary."""
        async with self._lock:
            while self.tokens < 1:
                self._refill()
                await asyncio.sleep(0.1)
            self.tokens -= 1

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        refill_amount = elapsed * (self.requests_per_minute / 60.0)
        self.tokens = min(self.requests_per_minute, self.tokens + refill_amount)
        self.last_refill = now


class SearchCache:
    """Cache for search results."""

    def __init__(self, ttl_seconds: int = 3600):
        self._cache: dict[str, SearchCacheEntry] = {}
        self._ttl_seconds = ttl_seconds
        self._lock = asyncio.Lock()

    def _make_key(self, query: str, provider: SearchProvider) -> str:
        """Generate cache key."""
        key_string = f"{provider.value}:{query.lower().strip()}"
        return hashlib.md5(key_string.encode()).hexdigest()

    async def get(
        self,
        query: str,
        provider: SearchProvider,
    ) -> SearchResponse | None:
        """Get cached result."""
        key = self._make_key(query, provider)

        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                return None

            # Check if expired
            if datetime.utcnow() > entry.timestamp + timedelta(seconds=entry.ttl_seconds):
                del self._cache[key]
                return None

            return SearchResponse(
                query=entry.query,
                results=entry.results,
                total=len(entry.results),
                provider=entry.provider,
                execution_time=0.0,
                cached=True,
            )

    async def set(
        self,
        response: SearchResponse,
        ttl_seconds: int | None = None,
    ) -> None:
        """Cache a response."""
        key = self._make_key(response.query, response.provider)
        ttl = ttl_seconds or self._ttl_seconds

        async with self._lock:
            self._cache[key] = SearchCacheEntry(
                query=response.query,
                provider=response.provider,
                results=response.results,
                timestamp=datetime.utcnow(),
                ttl_seconds=ttl,
            )

    async def clear(self) -> None:
        """Clear all cached results."""
        async with self._lock:
            self._cache.clear()

    async def clear_expired(self) -> int:
        """Remove expired entries and return count."""
        now = datetime.utcnow()
        expired_keys = []

        async with self._lock:
            for key, entry in self._cache.items():
                if now > entry.timestamp + timedelta(seconds=entry.ttl_seconds):
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]

        return len(expired_keys)


class WebSearchService:
    """Unified web search service with multiple providers."""

    def __init__(self, config: SearchConfig | None = None):
        self.config = config or SearchConfig()

        # Initialize providers
        self._providers: dict[SearchProvider, Any] = {}
        self._rate_limiter = RateLimiter(self.config.rate_limit_requests)
        self._cache = SearchCache(self.config.cache_ttl_seconds)

    def _get_provider(self, provider: SearchProvider | None):
        """Get or create provider instance."""
        if provider is None:
            provider = self.config.default_provider

        if provider not in self._providers:
            if provider == SearchProvider.TAVILY:
                if not self.config.tavily_api_key:
                    raise ValueError("Tavily API key not configured")
                self._providers[provider] = TavilyProvider(self.config.tavily_api_key)
            elif provider == SearchProvider.BRAVE:
                if not self.config.brave_api_key:
                    raise ValueError("Brave API key not configured")
                self._providers[provider] = BraveProvider(self.config.brave_api_key)
            elif provider == SearchProvider.DUCKDUCKGO:
                self._providers[provider] = DuckDuckGoProvider()

        return self._providers[provider]

    async def _execute_with_retries(
        self,
        provider: Any,
        request: SearchRequest,
    ) -> SearchResponse:
        """Execute search with automatic retries.
        
        Args:
            provider: Search provider instance
            request: Search request
            
        Returns:
            Search response
        """
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                return await provider.search(request)
            except httpx.HTTPStatusError as e:
                last_error = e
                # Don't retry on client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    raise
            except Exception as e:
                last_error = e

            # Wait before retry (exponential backoff)
            if attempt < self.config.max_retries - 1:
                delay = self.config.retry_delay_seconds * (2 ** attempt)
                await asyncio.sleep(delay)

        raise last_error

    async def search(self, request: SearchRequest) -> SearchResponse:
        """Execute a web search.
        
        Args:
            request: Search request
            
        Returns:
            Search response with results
        """
        provider = self._get_provider(request.provider)

        # Check cache first
        cached = await self._cache.get(request.query, request.provider or self.config.default_provider)
        if cached:
            return cached

        # Apply rate limiting
        await self._rate_limiter.acquire()

        # Execute search with retries
        response = await self._execute_with_retries(provider, request)

        # Cache the result
        await self._cache.set(response)

        return response

    async def search_multi(
        self,
        queries: list[str],
        provider: SearchProvider | None = None,
    ) -> list[SearchResponse]:
        """Execute multiple searches concurrently.
        
        Args:
            queries: List of search queries
            provider: Provider to use
            
        Returns:
            List of search responses
        """
        tasks = []
        for query in queries:
            request = SearchRequest(
                query=query,
                provider=provider,
            )
            tasks.append(self.search(request))

        return await asyncio.gather(*tasks, return_exceptions=True)

    async def summarize_results(
        self,
        response: SearchResponse,
        max_length: int = 500,
    ) -> str:
        """Generate a summary of search results.
        
        Args:
            response: Search response
            max_length: Maximum summary length
            
        Returns:
            Summary string
        """
        if not response.results:
            return "No results found."

        lines = [f"Found {response.total} results from {response.provider.value}:\n"]

        for i, result in enumerate(response.results[:5], 1):
            title = result.title[:80] + "..." if len(result.title) > 80 else result.title
            lines.append(f"{i}. {title}")
            lines.append(f"   {result.url}")
            snippet = result.snippet[:150] + "..." if len(result.snippet) > 150 else result.snippet
            lines.append(f"   {snippet}\n")

        summary = "\n".join(lines)

        if len(summary) > max_length:
            summary = summary[:max_length] + "..."

        return summary

    async def clear_cache(self) -> None:
        """Clear the search cache."""
        await self._cache.clear()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "entries": len(self._cache._cache),
            "ttl_seconds": self._cache._ttl_seconds,
        }


# Global service instance
_search_service: WebSearchService | None = None


def get_search_service(config: SearchConfig | None = None) -> WebSearchService:
    """Get or create the global search service.
    
    Args:
        config: Search configuration
        
    Returns:
        WebSearchService instance
    """
    global _search_service
    if _search_service is None or config is not None:
        _search_service = WebSearchService(config)
    return _search_service
