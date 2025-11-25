# Design Document

## Overview

This design document outlines the architecture for integrating specialized search and utility tools from the TypeScript codebase into the Python Deep Research Agent. The integration will add X/Twitter search, YouTube search, Reddit search, academic paper search, and various utility tools, significantly expanding the agent's research capabilities.

### Key Design Principles

1. **API Parity**: Maintain similar functionality to TypeScript implementations
2. **Python Idioms**: Use Python best practices (async/await, type hints, Pydantic)
3. **LangChain Integration**: Implement tools using LangChain's @tool decorator
4. **Modular Design**: Each tool is independent and can be enabled/disabled
5. **Consistent Interface**: All tools follow the same pattern for inputs/outputs

## Architecture

### High-Level Architecture

```
research_agent/
├── tools/
│   ├── __init__.py
│   ├── web_search.py          # Existing
│   ├── code_executor.py       # Existing
│   ├── memory_search.py       # Existing
│   ├── x_search.py            # NEW - X/Twitter search
│   ├── youtube_search.py      # NEW - YouTube search
│   ├── reddit_search.py       # NEW - Reddit search
│   ├── academic_search.py     # NEW - Academic papers
│   ├── currency_converter.py  # NEW - Currency conversion
│   ├── datetime_tool.py       # NEW - Date/time utilities
│   ├── weather_tool.py        # NEW - Weather data
│   ├── flight_tracker.py      # NEW - Flight tracking
│   ├── stock_chart.py         # NEW - Stock data
│   ├── crypto_tools.py        # NEW - Crypto data
│   └── map_tools.py           # NEW - Location services
│
├── clients/                    # NEW - API client wrappers
│   ├── __init__.py
│   ├── xai_client.py          # xAI Grok API
│   ├── youtube_client.py      # YouTube caption extraction
│   └── tool_registry.py       # Tool registration system
│
└── utils/
    └── models.py              # Extended with new data models
```


## Components and Interfaces

### 1. X/Twitter Search Tool

**Purpose**: Search X (Twitter) posts using xAI Grok API with live search capabilities.

**Implementation**:
```python
from langchain.tools import tool
from typing import List, Optional
from pydantic import BaseModel, Field

class XSearchParams(BaseModel):
    queries: List[str] = Field(min_items=1, max_items=5)
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None
    include_x_handles: Optional[List[str]] = Field(None, max_items=10)
    exclude_x_handles: Optional[List[str]] = Field(None, max_items=10)
    post_favorites_count: Optional[int] = Field(None, ge=0)
    post_view_count: Optional[int] = Field(None, ge=0)
    max_results: Optional[List[int]] = None

class XSearchResult(BaseModel):
    content: str
    citations: List[dict]
    sources: List[dict]
    query: str
    date_range: str
    handles: List[str]

@tool
async def x_search(
    queries: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    include_x_handles: Optional[List[str]] = None,
    exclude_x_handles: Optional[List[str]] = None,
    post_favorites_count: Optional[int] = None,
    post_view_count: Optional[int] = None,
    max_results: Optional[List[int]] = None
) -> dict:
    """
    Search X (Twitter) posts using xAI Grok API.
    
    Args:
        queries: List of search queries (1-5)
        start_date: Start date in YYYY-MM-DD format (default: 15 days ago)
        end_date: End date in YYYY-MM-DD format (default: today)
        include_x_handles: X handles to include (max 10)
        exclude_x_handles: X handles to exclude (max 10)
        post_favorites_count: Minimum favorites required
        post_view_count: Minimum views required
        max_results: Max results per query (default: 15)
    
    Returns:
        Dictionary with searches, date_range, and handles
    """
    client = get_xai_client()
    
    # Set default date range (15 days)
    if not start_date:
        start_date = (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Execute searches in parallel
    tasks = [
        _execute_x_search(
            client, query, start_date, end_date,
            include_x_handles, exclude_x_handles,
            post_favorites_count, post_view_count,
            max_results[i] if max_results else 15
        )
        for i, query in enumerate(queries)
    ]
    
    searches = await asyncio.gather(*tasks, return_exceptions=True)
    
    return {
        "searches": [s for s in searches if not isinstance(s, Exception)],
        "date_range": f"{start_date} to {end_date}",
        "handles": include_x_handles or exclude_x_handles or []
    }
```

**xAI Client**:
```python
class XAIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.x.ai/v1"
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60.0
        )
    
    async def search_with_grok(
        self,
        query: str,
        start_date: str,
        end_date: str,
        max_results: int = 15,
        **filters
    ) -> dict:
        """Execute X search using Grok API."""
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            json={
                "model": "grok-4-fast-non-reasoning",
                "messages": [{"role": "user", "content": query}],
                "search_parameters": {
                    "mode": "on",
                    "from_date": start_date,
                    "to_date": end_date,
                    "max_search_results": max_results,
                    "return_citations": True,
                    "sources": [{"type": "x", **filters}]
                }
            }
        )
        return response.json()
```


### 2. YouTube Search Tool

**Purpose**: Search YouTube videos and extract transcripts/captions.

**Implementation**:
```python
from youtube_transcript_api import YouTubeTranscriptApi
from exa_py import Exa

class YouTubeSearchParams(BaseModel):
    query: str
    time_range: Literal['day', 'week', 'month', 'year', 'anytime']

class VideoResult(BaseModel):
    video_id: str
    url: str
    title: Optional[str]
    thumbnail_url: Optional[str]
    captions: Optional[str]
    timestamps: Optional[List[str]]
    published_date: Optional[str]

@tool
async def youtube_search(
    query: str,
    time_range: Literal['day', 'week', 'month', 'year', 'anytime'] = 'week'
) -> dict:
    """
    Search YouTube videos and extract transcripts.
    
    Args:
        query: Search query
        time_range: Time range filter
    
    Returns:
        Dictionary with video results including transcripts
    """
    exa = Exa(api_key=get_config().exa_api_key)
    
    # Calculate date range
    start_date, end_date = _calculate_date_range(time_range)
    
    # Search YouTube using Exa
    search_options = {
        "type": "auto",
        "num_results": 5,
        "include_domains": ["youtube.com", "youtu.be", "m.youtube.com"]
    }
    
    if start_date:
        search_options["start_published_date"] = start_date
    if end_date:
        search_options["end_published_date"] = end_date
    
    results = await exa.search_and_contents(query, **search_options)
    
    # Process videos in batches
    videos = []
    for result in results.results:
        video_id = _extract_video_id(result.url)
        if not video_id:
            continue
        
        # Get transcript
        captions = await _get_video_transcript(video_id)
        
        # Generate timestamps
        timestamps = await _generate_timestamps(video_id, captions)
        
        videos.append(VideoResult(
            video_id=video_id,
            url=result.url,
            title=result.title,
            thumbnail_url=f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            captions=captions,
            timestamps=timestamps,
            published_date=result.published_date
        ))
    
    return {"results": videos}

async def _get_video_transcript(video_id: str) -> Optional[str]:
    """Extract video transcript using youtube-transcript-api."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return "\n".join([entry['text'] for entry in transcript])
    except Exception as e:
        logger.warning(f"Failed to get transcript for {video_id}: {e}")
        return None

async def _generate_timestamps(
    video_id: str,
    captions: Optional[str],
    target_count: int = 30
) -> Optional[List[str]]:
    """Generate chapter timestamps from captions."""
    if not captions:
        return None
    
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        total_duration = transcript[-1]['start'] + transcript[-1]['duration']
        interval = max(10, total_duration / target_count)
        
        timestamps = []
        for i in range(0, int(total_duration), int(interval)):
            # Find closest caption
            entry = min(transcript, key=lambda x: abs(x['start'] - i))
            time_str = _format_timestamp(entry['start'])
            timestamps.append(f"{time_str} - {entry['text'][:50]}")
        
        return timestamps[:target_count]
    except Exception as e:
        logger.warning(f"Failed to generate timestamps: {e}")
        return None
```


### 3. Reddit Search Tool

**Purpose**: Search Reddit content using Tavily API.

**Implementation**:
```python
from tavily import TavilyClient

class RedditSearchParams(BaseModel):
    queries: List[str] = Field(min_items=1, max_items=5)
    max_results: Optional[List[int]] = None
    time_range: Optional[List[Literal['day', 'week', 'month', 'year']]] = None

class RedditResult(BaseModel):
    url: str
    title: str
    content: str
    score: float
    published_date: Optional[str]
    subreddit: str
    is_reddit_post: bool

@tool
async def reddit_search(
    queries: List[str],
    max_results: Optional[List[int]] = None,
    time_range: Optional[List[str]] = None
) -> dict:
    """
    Search Reddit content using Tavily API.
    
    Args:
        queries: List of search queries (1-5)
        max_results: Max results per query (default: 20)
        time_range: Time range per query (default: 'week')
    
    Returns:
        Dictionary with search results per query
    """
    tavily = TavilyClient(api_key=get_config().tavily_api_key)
    
    tasks = [
        _execute_reddit_search(
            tavily,
            query,
            max_results[i] if max_results else 20,
            time_range[i] if time_range else 'week'
        )
        for i, query in enumerate(queries)
    ]
    
    searches = await asyncio.gather(*tasks, return_exceptions=True)
    
    return {
        "searches": [s for s in searches if not isinstance(s, Exception)]
    }

async def _execute_reddit_search(
    tavily: TavilyClient,
    query: str,
    max_results: int,
    time_range: str
) -> dict:
    """Execute single Reddit search."""
    try:
        results = await tavily.search(
            query,
            max_results=max(20, max_results),
            time_range=time_range,
            include_raw_content='markdown',
            search_depth='advanced',
            chunks_per_source=5,
            topic='general',
            include_domains=['reddit.com']
        )
        
        processed = []
        for result in results['results']:
            is_post = '/comments/' in result['url']
            subreddit = 'unknown'
            if is_post:
                match = re.search(r'reddit\.com\/r\/([^/]+)', result['url'])
                if match:
                    subreddit = match.group(1)
            
            processed.append(RedditResult(
                url=result['url'],
                title=result['title'],
                content=result.get('content', ''),
                score=result.get('score', 0.0),
                published_date=result.get('published_date'),
                subreddit=subreddit,
                is_reddit_post=is_post
            ))
        
        return {
            "query": query,
            "results": processed,
            "time_range": time_range
        }
    except Exception as e:
        logger.error(f"Reddit search failed for '{query}': {e}")
        return {"query": query, "results": [], "time_range": time_range}
```


### 4. Academic Search Tool

**Purpose**: Search academic papers using Exa API.

**Implementation**:
```python
class AcademicSearchParams(BaseModel):
    queries: List[str] = Field(min_items=1, max_items=5)
    max_results: Optional[List[int]] = None

class AcademicResult(BaseModel):
    title: str
    url: str
    summary: str
    published_date: Optional[str]
    author: Optional[str]

@tool
async def academic_search(
    queries: List[str],
    max_results: Optional[List[int]] = None
) -> dict:
    """
    Search academic papers and research.
    
    Args:
        queries: List of search queries (1-5)
        max_results: Max results per query (default: 20)
    
    Returns:
        Dictionary with academic paper results
    """
    exa = Exa(api_key=get_config().exa_api_key)
    
    tasks = [
        _execute_academic_search(
            exa,
            query,
            max_results[i] if max_results else 20
        )
        for i, query in enumerate(queries)
    ]
    
    searches = await asyncio.gather(*tasks, return_exceptions=True)
    
    return {
        "searches": [s for s in searches if not isinstance(s, Exception)]
    }

async def _execute_academic_search(
    exa: Exa,
    query: str,
    max_results: int
) -> dict:
    """Execute single academic search."""
    try:
        results = await exa.search_and_contents(
            query,
            type="auto",
            num_results=max_results,
            category="research paper",
            summary={"query": "Abstract of the Paper"}
        )
        
        # Deduplicate and clean
        seen_urls = set()
        processed = []
        
        for paper in results.results:
            if paper.url in seen_urls or not paper.summary:
                continue
            
            seen_urls.add(paper.url)
            
            # Clean summary and title
            clean_summary = re.sub(r'^Summary:\s*', '', paper.summary, flags=re.IGNORECASE)
            clean_title = re.sub(r'\s\[.*?\]$', '', paper.title or '')
            
            processed.append(AcademicResult(
                title=clean_title,
                url=paper.url,
                summary=clean_summary,
                published_date=paper.published_date,
                author=paper.author
            ))
        
        return {
            "query": query,
            "results": processed
        }
    except Exception as e:
        logger.error(f"Academic search failed for '{query}': {e}")
        return {"query": query, "results": []}
```


### 5. Utility Tools

**Currency Converter**:
```python
@tool
async def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str
) -> dict:
    """Convert currency using exchange rate API."""
    # Implementation using exchangerate-api or similar
    pass

**DateTime Tool**:
```python
@tool
async def datetime_operations(
    operation: Literal['convert_timezone', 'calculate_duration', 'format_date'],
    **params
) -> dict:
    """Perform datetime operations."""
    # Implementation using datetime and pytz
    pass
```

**Weather Tool**:
```python
@tool
async def get_weather(
    location: str,
    forecast_days: int = 1
) -> dict:
    """Get weather data for a location."""
    # Implementation using OpenWeatherMap or similar
    pass
```

**Flight Tracker**:
```python
@tool
async def track_flight(
    flight_number: str,
    date: Optional[str] = None
) -> dict:
    """Track flight status."""
    # Implementation using AviationStack or similar
    pass
```

**Stock Chart**:
```python
@tool
async def get_stock_data(
    symbol: str,
    period: str = '1d',
    interval: str = '1h'
) -> dict:
    """Get stock market data."""
    # Implementation using yfinance or Alpha Vantage
    pass
```

**Crypto Tools**:
```python
@tool
async def get_crypto_data(
    symbol: str,
    vs_currency: str = 'usd'
) -> dict:
    """Get cryptocurrency data."""
    # Implementation using CoinGecko API
    pass
```

**Map Tools**:
```python
@tool
async def geocode_location(
    address: str
) -> dict:
    """Geocode an address to coordinates."""
    # Implementation using Google Maps API or similar
    pass
```


## Tool Registry System

### Purpose
Centralized system for registering, discovering, and managing tools.

**Implementation**:
```python
class ToolRegistry:
    """Central registry for all research tools."""
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._enabled_tools: Set[str] = set()
    
    def register(self, name: str, tool: Callable, enabled: bool = True):
        """Register a tool."""
        self._tools[name] = tool
        if enabled:
            self._enabled_tools.add(name)
    
    def get_enabled_tools(self) -> List[Callable]:
        """Get list of enabled tools."""
        return [
            self._tools[name]
            for name in self._enabled_tools
            if name in self._tools
        ]
    
    def enable_tool(self, name: str):
        """Enable a tool."""
        if name in self._tools:
            self._enabled_tools.add(name)
    
    def disable_tool(self, name: str):
        """Disable a tool."""
        self._enabled_tools.discard(name)

# Global registry instance
_registry = ToolRegistry()

def register_tool(name: str, enabled: bool = True):
    """Decorator to register a tool."""
    def decorator(func: Callable):
        _registry.register(name, func, enabled)
        return func
    return decorator

def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return _registry
```

**Usage in Agent**:
```python
class DeepResearchAgent:
    def __init__(self, ...):
        # Get enabled tools from registry
        self.tools = get_tool_registry().get_enabled_tools()
    
    def _create_agent_executor(self, plan: ResearchPlan):
        return AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,  # Use registered tools
            max_iterations=15
        )
```


## Data Models

### Extended Models for New Tools

```python
# X/Twitter Models
class XPost(BaseModel):
    text: str
    link: str
    favorites: Optional[int]
    views: Optional[int]
    author: Optional[str]

class XSearchResult(BaseModel):
    content: str
    citations: List[dict]
    sources: List[XPost]
    query: str
    date_range: str
    handles: List[str]

# YouTube Models
class VideoTimestamp(BaseModel):
    time: str  # Format: "1:23" or "1:23:45"
    title: str

class VideoResult(BaseModel):
    video_id: str
    url: str
    title: Optional[str]
    thumbnail_url: Optional[str]
    captions: Optional[str]
    timestamps: Optional[List[str]]
    published_date: Optional[str]
    views: Optional[str]
    likes: Optional[str]

# Reddit Models
class RedditResult(BaseModel):
    url: str
    title: str
    content: str
    score: float
    published_date: Optional[str]
    subreddit: str
    is_reddit_post: bool
    comments: List[str] = []

# Academic Models
class AcademicResult(BaseModel):
    title: str
    url: str
    summary: str
    published_date: Optional[str]
    author: Optional[str]
    citations: Optional[int]
```

## Configuration Updates

### Environment Variables

```python
# Add to Config class
class Config(BaseSettings):
    # Existing...
    
    # New API keys
    xai_api_key: Optional[str] = Field(None, env="XAI_API_KEY")
    openweather_api_key: Optional[str] = Field(None, env="OPENWEATHER_API_KEY")
    aviationstack_api_key: Optional[str] = Field(None, env="AVIATIONSTACK_API_KEY")
    alphavantage_api_key: Optional[str] = Field(None, env="ALPHAVANTAGE_API_KEY")
    coingecko_api_key: Optional[str] = Field(None, env="COINGECKO_API_KEY")
    google_maps_api_key: Optional[str] = Field(None, env="GOOGLE_MAPS_API_KEY")
    
    # Tool enablement
    enabled_tools: List[str] = Field(
        default=[
            "web_search",
            "code_executor",
            "memory_search",
            "x_search",
            "youtube_search",
            "reddit_search",
            "academic_search"
        ],
        env="ENABLED_TOOLS"
    )
```


## Error Handling Strategy

### Tool-Level Error Handling

```python
@tool
async def x_search(...) -> dict:
    """X search with comprehensive error handling."""
    try:
        # Main logic
        ...
    except httpx.HTTPError as e:
        logger.error(f"X search HTTP error: {e}", exc_info=True)
        return {
            "searches": [],
            "error": f"API request failed: {str(e)}",
            "date_range": "",
            "handles": []
        }
    except Exception as e:
        logger.error(f"X search unexpected error: {e}", exc_info=True)
        return {
            "searches": [],
            "error": f"Unexpected error: {str(e)}",
            "date_range": "",
            "handles": []
        }
```

### API Client Error Handling

```python
class XAIClient:
    async def search_with_grok(self, ...) -> dict:
        """Execute search with retry logic."""
        for attempt in range(3):
            try:
                response = await self.client.post(...)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                raise
            except httpx.RequestError as e:
                if attempt == 2:  # Last attempt
                    raise
                await asyncio.sleep(1)
        
        raise Exception("Max retries exceeded")
```

## Testing Strategy

### Unit Tests

```python
@pytest.mark.asyncio
async def test_x_search_tool():
    """Test X search with mocked API."""
    with patch('research_agent.clients.xai_client.XAIClient') as mock_client:
        mock_client.return_value.search_with_grok.return_value = {
            "choices": [{"message": {"content": "test"}}],
            "citations": []
        }
        
        result = await x_search(
            queries=["test query"],
            start_date="2024-01-01",
            end_date="2024-01-15"
        )
        
        assert "searches" in result
        assert len(result["searches"]) == 1

@pytest.mark.asyncio
async def test_youtube_search_tool():
    """Test YouTube search with mocked Exa."""
    with patch('exa_py.Exa') as mock_exa:
        mock_exa.return_value.search_and_contents.return_value = Mock(
            results=[
                Mock(
                    url="https://youtube.com/watch?v=test123",
                    title="Test Video",
                    published_date="2024-01-01"
                )
            ]
        )
        
        result = await youtube_search(
            query="test query",
            time_range="week"
        )
        
        assert "results" in result
        assert len(result["results"]) > 0
```

### Integration Tests

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_research_with_new_tools():
    """Test research flow with new tools enabled."""
    agent = DeepResearchAgent(
        llm=get_test_llm(),
        search_provider="exa"
    )
    
    # Enable new tools
    registry = get_tool_registry()
    registry.enable_tool("x_search")
    registry.enable_tool("youtube_search")
    
    result = await agent.research(
        "What are the latest trends in AI?"
    )
    
    assert result.query == "What are the latest trends in AI?"
    assert len(result.sources) > 0
```


## Performance Considerations

### 1. Parallel Execution

```python
# Execute multiple queries concurrently
async def execute_multi_query_tool(queries: List[str], executor_func):
    """Generic multi-query executor with concurrency control."""
    semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
    
    async def bounded_executor(query):
        async with semaphore:
            return await executor_func(query)
    
    tasks = [bounded_executor(q) for q in queries]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

### 2. Caching

```python
from functools import lru_cache
from aiocache import cached

@cached(ttl=3600, key_builder=lambda f, *args, **kwargs: f"{args[0]}:{kwargs}")
async def get_video_transcript(video_id: str) -> Optional[str]:
    """Cache video transcripts for 1 hour."""
    ...
```

### 3. Connection Pooling

```python
class APIClientManager:
    """Manage API client instances with connection pooling."""
    
    def __init__(self):
        self._clients: Dict[str, httpx.AsyncClient] = {}
    
    def get_client(self, name: str, **kwargs) -> httpx.AsyncClient:
        """Get or create HTTP client with pooling."""
        if name not in self._clients:
            self._clients[name] = httpx.AsyncClient(
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20
                ),
                timeout=httpx.Timeout(30.0),
                **kwargs
            )
        return self._clients[name]
    
    async def close_all(self):
        """Close all clients."""
        for client in self._clients.values():
            await client.aclose()
```

## Deployment Considerations

### Updated Dependencies

```txt
# requirements.txt additions
xai-sdk>=0.1.0
youtube-transcript-api>=0.6.0
yfinance>=0.2.0
pytz>=2023.3
requests>=2.31.0
```

### Environment Variables

```bash
# .env.example additions
XAI_API_KEY=your_xai_key_here
OPENWEATHER_API_KEY=your_openweather_key_here
AVIATIONSTACK_API_KEY=your_aviationstack_key_here
ALPHAVANTAGE_API_KEY=your_alphavantage_key_here
COINGECKO_API_KEY=your_coingecko_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_key_here

# Tool configuration
ENABLED_TOOLS=web_search,code_executor,memory_search,x_search,youtube_search,reddit_search,academic_search
```

### Docker Updates

```dockerfile
# Add new dependencies
RUN pip install --no-cache-dir \
    xai-sdk \
    youtube-transcript-api \
    yfinance \
    pytz
```

## Migration Path

### Phase 1: Core Search Tools
1. Implement X search tool
2. Implement YouTube search tool
3. Implement Reddit search tool
4. Implement Academic search tool

### Phase 2: Utility Tools
1. Implement currency converter
2. Implement datetime tool
3. Implement weather tool
4. Implement flight tracker
5. Implement stock chart tool
6. Implement crypto tools
7. Implement map tools

### Phase 3: Integration
1. Update tool registry
2. Update agent configuration
3. Add comprehensive tests
4. Update documentation

## Security Considerations

1. **API Key Management**: Store all keys in environment variables
2. **Rate Limiting**: Implement per-tool rate limiting
3. **Input Validation**: Validate all inputs using Pydantic
4. **Output Sanitization**: Clean and sanitize all API responses
5. **Error Messages**: Don't expose sensitive information in errors
