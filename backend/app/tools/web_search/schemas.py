"""Web search schemas."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SearchProvider(str, Enum):
    """Supported search providers."""

    TAVILY = "tavily"
    BRAVE = "brave"
    DUCKDUCKGO = "duckduckgo"


class SearchResult(BaseModel):
    """Individual search result."""

    title: str
    url: str
    snippet: str
    score: float | None = None
    published_date: str | None = None
    provider: SearchProvider


class SearchResponse(BaseModel):
    """Response from a search operation."""

    query: str
    results: list[SearchResult]
    total: int
    provider: SearchProvider
    execution_time: float
    cached: bool = False


class SearchRequest(BaseModel):
    """Search request."""

    query: str = Field(..., description="Search query")
    provider: SearchProvider | None = Field(None, description="Provider to use (auto-select if None)")
    max_results: int = Field(10, ge=1, le=50, description="Maximum results")
    include_answer: bool = Field(False, description="Include AI answer")
    include_raw_content: bool = Field(False, description="Include raw content")
    search_depth: str = Field("basic", description="Search depth: basic, advanced")
    topic: str = Field("general", description="Topic: general, news, science")


class SearchConfig(BaseModel):
    """Search configuration."""

    default_provider: SearchProvider = SearchProvider.DUCKDUCKGO
    tavily_api_key: str | None = None
    brave_api_key: str | None = None
    rate_limit_requests: int = 10  # requests per minute
    cache_ttl_seconds: int = 3600  # 1 hour
    max_retries: int = 3
    retry_delay_seconds: float = 1.0


class SearchCacheEntry(BaseModel):
    """Cached search result."""

    query: str
    provider: SearchProvider
    results: list[SearchResult]
    timestamp: datetime
    ttl_seconds: int
