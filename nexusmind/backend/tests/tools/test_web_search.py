"""Tests for web search functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.tools.web_search.schemas import (
    SearchProvider,
    SearchRequest,
    SearchResponse,
    SearchResult,
    SearchConfig,
    SearchCacheEntry,
)
from app.tools.web_search.service import WebSearchService, SearchCache, RateLimiter


class TestSearchSchemas:
    """Test search schemas."""

    def test_search_request_defaults(self):
        """Test SearchRequest default values."""
        request = SearchRequest(query="test query")
        assert request.query == "test query"
        assert request.provider is None
        assert request.max_results == 10
        assert request.include_answer is False
        assert request.search_depth == "basic"

    def test_search_request_custom(self):
        """Test SearchRequest with custom values."""
        request = SearchRequest(
            query="python web framework",
            provider=SearchProvider.TAVILY,
            max_results=20,
            include_answer=True,
            topic="programming",
        )
        assert request.max_results == 20
        assert request.topic == "programming"

    def test_search_result(self):
        """Test SearchResult."""
        result = SearchResult(
            title="Python Tutorial",
            url="https://example.com/python",
            snippet="Learn Python programming",
            score=0.95,
            provider=SearchProvider.DUCKDUCKGO,
        )
        assert result.title == "Python Tutorial"
        assert result.provider == SearchProvider.DUCKDUCKGO

    def test_search_response(self):
        """Test SearchResponse."""
        results = [
            SearchResult(
                title="Result 1",
                url="https://example.com/1",
                snippet="Snippet 1",
                provider=SearchProvider.TAVILY,
            ),
        ]
        response = SearchResponse(
            query="test",
            results=results,
            total=1,
            provider=SearchProvider.TAVILY,
            execution_time=0.5,
        )
        assert response.total == 1
        assert response.cached is False

    def test_search_config_defaults(self):
        """Test SearchConfig defaults."""
        config = SearchConfig()
        assert config.default_provider == SearchProvider.DUCKDUCKGO
        assert config.rate_limit_requests == 10
        assert config.cache_ttl_seconds == 3600
        assert config.max_retries == 3


class TestRateLimiter:
    """Test rate limiter."""

    @pytest.mark.asyncio
    async def test_acquire_token(self):
        """Test acquiring a token."""
        limiter = RateLimiter(requests_per_minute=60)
        await limiter.acquire()  # Should not raise

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting behavior."""
        limiter = RateLimiter(requests_per_minute=2)

        # Should allow 2 requests
        await limiter.acquire()
        await limiter.acquire()

        # Third request should wait
        import asyncio
        start = asyncio.get_event_loop().time()
        await limiter.acquire()
        elapsed = asyncio.get_event_loop().time() - start

        # Should have waited a bit
        assert elapsed > 0


class TestSearchCache:
    """Test search cache."""

    @pytest.fixture
    def cache(self):
        """Create a cache for testing."""
        return SearchCache(ttl_seconds=60)

    @pytest.mark.asyncio
    async def test_cache_set_get(self, cache):
        """Test setting and getting cached results."""
        results = [
            SearchResult(
                title="Test",
                url="https://example.com",
                snippet="Test snippet",
                provider=SearchProvider.DUCKDUCKGO,
            )
        ]
        response = SearchResponse(
            query="test",
            results=results,
            total=1,
            provider=SearchProvider.DUCKDUCKGO,
            execution_time=0.1,
        )

        await cache.set(response)

        # Should be able to get it back
        cached = await cache.get("test", SearchProvider.DUCKDUCKGO)
        assert cached is not None
        assert cached.cached is True
        assert len(cached.results) == 1

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache):
        """Test cache miss."""
        result = await cache.get("nonexistent", SearchProvider.DUCKDUCKGO)
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_clear(self, cache):
        """Test clearing cache."""
        results = [
            SearchResult(
                title="Test",
                url="https://example.com",
                snippet="Test",
                provider=SearchProvider.DUCKDUCKGO,
            )
        ]
        response = SearchResponse(
            query="test",
            results=results,
            total=1,
            provider=SearchProvider.DUCKDUCKGO,
            execution_time=0.1,
        )

        await cache.set(response)
        await cache.clear()

        cached = await cache.get("test", SearchProvider.DUCKDUCKGO)
        assert cached is None


class TestWebSearchService:
    """Test web search service."""

    @pytest.fixture
    def config(self):
        """Create config for testing."""
        return SearchConfig(
            default_provider=SearchProvider.DUCKDUCKGO,
            rate_limit_requests=60,
            cache_ttl_seconds=60,
        )

    @pytest.fixture
    def service(self, config):
        """Create service for testing."""
        return WebSearchService(config)

    def test_service_init(self, config):
        """Test service initialization."""
        service = WebSearchService(config)
        assert service.config == config
        assert service._cache is not None

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Slow test - requires network")
    async def test_get_duckduckgo_provider(self, service):
        """Test getting DuckDuckGo provider."""
        provider = service._get_provider(SearchProvider.DUCKDUCKGO)
        assert provider is not None
        from app.tools.web_search.providers.duckduckgo import DuckDuckGoProvider
        assert isinstance(provider, DuckDuckGoProvider)

    def test_get_provider_requires_api_key(self):
        """Test that providers requiring API keys raise error without."""
        config = SearchConfig(
            tavily_api_key=None,
            brave_api_key=None,
        )
        service = WebSearchService(config)

        with pytest.raises(ValueError, match="Tavily API key"):
            service._get_provider(SearchProvider.TAVILY)

        with pytest.raises(ValueError, match="Brave API key"):
            service._get_provider(SearchProvider.BRAVE)

    @pytest.mark.asyncio
    async def test_summarize_results(self, service):
        """Test result summarization."""
        results = [
            SearchResult(
                title="Python Tutorial",
                url="https://example.com/python",
                snippet="Learn Python programming from scratch",
                provider=SearchProvider.DUCKDUCKGO,
            ),
            SearchResult(
                title="JavaScript Guide",
                url="https://example.com/js",
                snippet="JavaScript basics and advanced topics",
                provider=SearchProvider.DUCKDUCKGO,
            ),
        ]
        response = SearchResponse(
            query="programming languages",
            results=results,
            total=2,
            provider=SearchProvider.DUCKDUCKGO,
            execution_time=0.5,
        )

        summary = await service.summarize_results(response)
        assert "Found 2 results" in summary
        assert "Python Tutorial" in summary
        assert "JavaScript Guide" in summary

    @pytest.mark.asyncio
    async def test_summarize_empty_results(self, service):
        """Test summarizing empty results."""
        response = SearchResponse(
            query="nothing",
            results=[],
            total=0,
            provider=SearchProvider.DUCKDUCKGO,
            execution_time=0.1,
        )

        summary = await service.summarize_results(response)
        assert "No results found" in summary

    @pytest.mark.asyncio
    async def test_cache_stats(self, service):
        """Test getting cache statistics."""
        stats = service.get_cache_stats()
        assert "entries" in stats
        assert "ttl_seconds" in stats

    @pytest.mark.asyncio
    async def test_clear_cache(self, service):
        """Test clearing cache."""
        await service.clear_cache()
        stats = service.get_cache_stats()
        assert stats["entries"] == 0


class TestSearchProviders:
    """Test individual search providers."""

    def test_tavily_provider_import(self):
        """Test Tavily provider can be imported."""
        from app.tools.web_search.providers.tavily import TavilyProvider
        assert TavilyProvider is not None

    def test_brave_provider_import(self):
        """Test Brave provider can be imported."""
        from app.tools.web_search.providers.brave import BraveProvider
        assert BraveProvider is not None

    def test_duckduckgo_provider_import(self):
        """Test DuckDuckGo provider can be imported."""
        from app.tools.web_search.providers.duckduckgo import DuckDuckGoProvider
        assert DuckDuckGoProvider is not None


class TestSearchProviderEnum:
    """Test SearchProvider enum."""

    def test_provider_values(self):
        """Test provider enum values."""
        assert SearchProvider.TAVILY.value == "tavily"
        assert SearchProvider.BRAVE.value == "brave"
        assert SearchProvider.DUCKDUCKGO.value == "duckduckgo"

    def test_provider_from_string(self):
        """Test creating provider from string."""
        assert SearchProvider("tavily") == SearchProvider.TAVILY
        assert SearchProvider("brave") == SearchProvider.BRAVE
        assert SearchProvider("duckduckgo") == SearchProvider.DUCKDUCKGO
