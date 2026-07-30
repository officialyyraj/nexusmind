# Web Search API Documentation

The web search module provides a unified interface for searching the web using multiple providers (Tavily, Brave Search, DuckDuckGo) with built-in caching, rate limiting, and automatic retries.

## Quick Start

```python
from app.tools.web_search import WebSearchService, SearchProvider, SearchRequest

# Create service
service = WebSearchService()

# Execute search
request = SearchRequest(query="python web framework", max_results=5)
response = await service.search(request)

print(f"Found {response.total} results")
for result in response.results:
    print(f"- {result.title}: {result.url}")
```

## Configuration

### SearchConfig

```python
from app.tools.web_search import SearchConfig

config = SearchConfig(
    default_provider=SearchProvider.DUCKDUCKGO,
    tavily_api_key="your-tavily-key",
    brave_api_key="your-brave-key",
    rate_limit_requests=10,  # requests per minute
    cache_ttl_seconds=3600,  # 1 hour
    max_retries=3,
    retry_delay_seconds=1.0,
)

service = WebSearchService(config)
```

## Providers

### DuckDuckGo (Free)

No API key required. Good for basic searches.

```python
from app.tools.web_search import SearchProvider

request = SearchRequest(
    query="python tutorial",
    provider=SearchProvider.DUCKDUCKGO,
)
```

### Tavily

Requires API key from [tavily.com](https://tavily.com).

```python
config = SearchConfig(
    tavily_api_key="tvly-xxxxx",
    default_provider=SearchProvider.TAVILY,
)
```

Features:
- AI-generated answers
- Topic filtering (general, news, science)
- Search depth (basic, advanced)

### Brave Search

Requires API key from [brave.com/search/api](https://brave.com/search/api/).

```python
config = SearchConfig(
    brave_api_key="BSA-xxxxx",
    default_provider=SearchProvider.BRAVE,
)
```

## Search Request

### SearchRequest Schema

```python
class SearchRequest:
    query: str                      # Search query
    provider: SearchProvider | None  # Provider (auto-select if None)
    max_results: int = 10           # 1-50 results
    include_answer: bool = False     # Include AI answer (Tavily)
    include_raw_content: bool = False # Include raw content (Tavily)
    search_depth: str = "basic"      # basic or advanced
    topic: str = "general"          # general, news, science
```

## Search Response

### SearchResponse Schema

```python
class SearchResponse:
    query: str                      # Original query
    results: list[SearchResult]     # Search results
    total: int                      # Total results count
    provider: SearchProvider         # Provider used
    execution_time: float           # Search duration
    cached: bool                    # Whether result was cached
```

### SearchResult Schema

```python
class SearchResult:
    title: str                      # Result title
    url: str                       # Result URL
    snippet: str                   # Result snippet/description
    score: float | None            # Relevance score
    published_date: str | None     # Publication date
    provider: SearchProvider       # Provider
```

## Examples

### Basic Search

```python
from app.tools.web_search import WebSearchService, SearchRequest

service = WebSearchService()
request = SearchRequest(query="machine learning tutorial")
response = await service.search(request)

for result in response.results:
    print(result.title, result.url)
```

### Multi-Query Search

```python
queries = [
    "python web frameworks",
    "javascript frontend libraries",
    "rust systems programming",
]

responses = await service.search_multi(queries)

for response in responses:
    print(f"\nQuery: {response.query}")
    for result in response.results[:3]:
        print(f"  - {result.title}")
```

### Summarization

```python
response = await service.search(
    SearchRequest(query="climate change research")
)

summary = await service.summarize_results(response)
print(summary)
```

### With Tavily (Advanced)

```python
request = SearchRequest(
    query="latest AI research",
    provider=SearchProvider.TAVILY,
    max_results=10,
    include_answer=True,
    search_depth="advanced",
    topic="science",
)

response = await service.search(request)
print(f"Answer: {response.results[0].snippet if response.results else 'No answer'}")
```

## Caching

Results are cached automatically. Cache settings:

```python
config = SearchConfig(cache_ttl_seconds=3600)  # 1 hour default
service = WebSearchService(config)

# Clear cache manually
await service.clear_cache()

# Get cache stats
stats = service.get_cache_stats()
print(f"Cached entries: {stats['entries']}")
```

## Rate Limiting

Rate limiting is applied per-provider:

```python
config = SearchConfig(rate_limit_requests=10)  # 10 requests/minute
```

If rate limited, requests will wait automatically.

## Automatic Retries

Failed requests are automatically retried with exponential backoff:

```python
config = SearchConfig(
    max_retries=3,
    retry_delay_seconds=1.0,  # 1s, 2s, 4s backoff
)
```

## Integration with Research Agent

```python
from app.agents.implementations import ResearcherAgent
from app.tools.web_search import get_search_service

# Create search service
search_service = get_search_service()

# Create researcher with web search
agent = ResearcherAgent(search_service=search_service)

# Use agent
state = await agent.execute({"task": "latest AI trends"})
findings = state["result"]["findings"]
```

## Error Handling

```python
try:
    response = await service.search(request)
except httpx.HTTPStatusError as e:
    print(f"HTTP error: {e.response.status_code}")
except Exception as e:
    print(f"Error: {e}")
```

## API Reference

### WebSearchService

| Method | Description |
|--------|-------------|
| `search(request)` | Execute single search |
| `search_multi(queries)` | Execute multiple searches concurrently |
| `summarize_results(response)` | Generate text summary |
| `clear_cache()` | Clear search cache |
| `get_cache_stats()` | Get cache statistics |

### SearchCache

| Method | Description |
|--------|-------------|
| `get(query, provider)` | Get cached result |
| `set(response)` | Cache a response |
| `clear()` | Clear all cache |
| `clear_expired()` | Remove expired entries |

### RateLimiter

| Method | Description |
|--------|-------------|
| `acquire()` | Acquire rate limit token |

## Environment Variables

For production, use environment variables for API keys:

```bash
export TAVILY_API_KEY="tvly-xxxxx"
export BRAVE_API_KEY="BSA-xxxxx"
```

```python
import os

config = SearchConfig(
    tavily_api_key=os.getenv("TAVILY_API_KEY"),
    brave_api_key=os.getenv("BRAVE_API_KEY"),
)
```
