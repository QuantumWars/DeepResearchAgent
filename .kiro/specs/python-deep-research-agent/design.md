# Design Document

## Overview

The Python Deep Research Agent is an autonomous AI-powered research system that uses LangChain for orchestration, multiple search providers for information gathering, and Supermemory for context management. The system is designed to be simple, debuggable, and performant, with clear separation of concerns and extensive logging.

### Key Design Principles

1. **Simplicity First**: Use LangChain's abstractions to minimize boilerplate
2. **Async by Default**: All I/O operations use async/await for performance
3. **Fail Gracefully**: Comprehensive error handling with fallbacks
4. **Observable**: Extensive logging and streaming for debugging
5. **Modular**: Clear separation between agent, tools, strategies, and utilities

## Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Application                       │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/WebSocket
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Research Agent API                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         FastAPI Endpoint (Streaming SSE)             │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                      │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │           DeepResearchAgent (LangChain)              │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │  1. Research Planner (LLM + Structured Output)│   │  │
│  │  └──────────────────┬───────────────────────────┘   │  │
│  │                     │                                 │  │
│  │  ┌──────────────────▼───────────────────────────┐   │  │
│  │  │  2. Agent Executor (LangChain AgentExecutor) │   │  │
│  │  │     - Tool Selection                          │   │  │
│  │  │     - Autonomous Execution                    │   │  │
│  │  │     - Step Limit Enforcement                  │   │  │
│  │  └──────────────────┬───────────────────────────┘   │  │
│  │                     │                                 │  │
│  │  ┌──────────────────▼───────────────────────────┐   │  │
│  │  │  3. Streaming Callback Handler               │   │  │
│  │  │     - Real-time Progress Updates              │   │  │
│  │  │     - Event Emission (SSE)                    │   │  │
│  │  └───────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Tool Layer  │  │   Memory     │  │   Search     │
│              │  │   Layer      │  │  Strategies  │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Component Architecture

```
research_agent/
├── agent/
│   ├── __init__.py
│   ├── research_agent.py       # Main DeepResearchAgent class
│   ├── planner.py              # Research plan generation
│   └── callbacks.py            # Streaming callback handlers
│
├── tools/
│   ├── __init__.py
│   ├── web_search.py           # Web search tool (LangChain tool)
│   ├── code_executor.py        # Python code execution tool
│   ├── memory_search.py        # Supermemory search tool
│   └── x_search.py             # X/Twitter search tool
│
├── strategies/
│   ├── __init__.py
│   ├── base.py                 # SearchStrategy base class
│   ├── exa_strategy.py         # Exa search implementation
│   ├── tavily_strategy.py      # Tavily search implementation
│   ├── firecrawl_strategy.py   # Firecrawl search implementation
│   └── parallel_strategy.py    # Parallel AI search implementation
│
├── memory/
│   ├── __init__.py
│   ├── supermemory_client.py   # Supermemory integration
│   └── context_manager.py      # Context storage and retrieval
│
├── utils/
│   ├── __init__.py
│   ├── config.py               # Configuration management
│   ├── content_processor.py    # Content cleaning and deduplication
│   ├── logger.py               # Logging setup
│   └── models.py               # Pydantic models for data structures
│
├── api/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   └── routes.py               # API endpoints
│
└── main.py                     # CLI entry point
```

## Components and Interfaces

### 1. DeepResearchAgent

**Purpose**: Main orchestrator that coordinates research planning and execution.

**Key Methods**:
```python
class DeepResearchAgent:
    def __init__(
        self,
        llm: BaseChatModel,
        search_provider: str = "exa",
        memory_client: Optional[SupermemoryClient] = None,
        stream_handler: Optional[StreamingCallbackHandler] = None
    ):
        """Initialize the research agent with LLM and tools."""
        
    async def research(
        self,
        query: str,
        user_id: Optional[str] = None
    ) -> ResearchResult:
        """
        Execute autonomous research on a query.
        
        Steps:
        1. Generate research plan using LLM
        2. Create agent executor with tools
        3. Execute research autonomously
        4. Aggregate and deduplicate results
        5. Store in Supermemory
        """
        
    async def _create_research_plan(
        self,
        query: str
    ) -> ResearchPlan:
        """Generate structured research plan using LLM."""
        
    def _create_agent_executor(
        self,
        plan: ResearchPlan
    ) -> AgentExecutor:
        """Create LangChain agent executor with tools."""
```

**Dependencies**:
- LangChain's `AgentExecutor` for autonomous execution
- LLM for planning and tool selection
- Tools (web search, code execution, memory search)
- Streaming callback handler for progress updates

### 2. Research Planner

**Purpose**: Generate structured research plans using LLM with structured output.

**Implementation**:
```python
class ResearchPlanner:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm.with_structured_output(ResearchPlan)
        
    async def create_plan(
        self,
        query: str,
        context: Optional[str] = None
    ) -> ResearchPlan:
        """
        Generate research plan with 1-5 topics, each with 3-5 tasks.
        Total tasks limited to 15.
        """
        prompt = self._build_planning_prompt(query, context)
        plan = await self.llm.ainvoke(prompt)
        return self._validate_and_limit_plan(plan)
```

**Data Model**:
```python
class ResearchTask(BaseModel):
    title: str = Field(min_length=10, max_length=70)
    tasks: List[str] = Field(min_items=3, max_items=5)

class ResearchPlan(BaseModel):
    topics: List[ResearchTask] = Field(min_items=1, max_items=5)
    total_tasks: int
    
    @validator('total_tasks')
    def validate_task_limit(cls, v):
        if v > 15:
            raise ValueError("Total tasks cannot exceed 15")
        return v
```

### 3. Tool Layer

#### 3.1 Web Search Tool

**Purpose**: Search the web using pluggable search strategies.

**Implementation**:
```python
@tool
async def web_search(
    query: str,
    category: Optional[SearchCategory] = None,
    include_domains: Optional[List[str]] = None,
    max_results: int = 8
) -> List[SearchResult]:
    """
    Search the web for information.
    
    Args:
        query: Search query (5-15 words recommended)
        category: Optional category (news, company, research_paper, github, financial_report)
        include_domains: Optional list of domains to filter results
        max_results: Maximum number of results (default 8)
        
    Returns:
        List of search results with title, url, content, metadata
    """
    strategy = get_search_strategy()  # From config
    results = await strategy.search(query, category, include_domains, max_results)
    
    # Get full content with fallback
    enriched_results = await _enrich_with_content(results)
    
    # Deduplicate by domain and URL
    deduplicated = deduplicate_results(enriched_results)
    
    return deduplicated
```

**Search Strategy Interface**:
```python
class SearchStrategy(ABC):
    @abstractmethod
    async def search(
        self,
        query: str,
        category: Optional[SearchCategory],
        include_domains: Optional[List[str]],
        max_results: int
    ) -> List[SearchResult]:
        """Execute search and return results."""
        
    @abstractmethod
    async def get_content(
        self,
        urls: List[str]
    ) -> List[SearchResult]:
        """Retrieve full content for URLs."""
```

#### 3.2 Code Execution Tool

**Purpose**: Execute Python code in a sandboxed environment.

**Implementation**:
```python
@tool
async def execute_python_code(
    title: str,
    code: str
) -> CodeExecutionResult:
    """
    Execute Python code in a sandbox.
    
    Args:
        title: Description of what the code does
        code: Python code to execute
        
    Returns:
        Execution result with output, charts, and any errors
    """
    # Detect required libraries
    required_libs = detect_imports(code)
    missing_libs = [lib for lib in required_libs if lib not in AVAILABLE_LIBS]
    
    # Create sandbox (using Daytona or similar)
    sandbox = await create_sandbox()
    
    # Install missing libraries
    if missing_libs:
        await sandbox.install_packages(missing_libs)
    
    # Execute code
    result = await sandbox.execute(code)
    
    # Extract charts if any
    charts = extract_charts(result)
    
    # Cleanup
    await sandbox.cleanup()
    
    return CodeExecutionResult(
        output=result.stdout,
        error=result.stderr,
        charts=charts
    )
```

#### 3.3 Memory Search Tool

**Purpose**: Search past research stored in Supermemory.

**Implementation**:
```python
@tool
async def search_memories(
    query: str,
    user_id: str,
    limit: int = 10
) -> List[Memory]:
    """
    Search past research in Supermemory.
    
    Args:
        query: Search query
        user_id: User identifier for memory isolation
        limit: Maximum number of memories to return
        
    Returns:
        List of relevant memories from past research
    """
    client = get_supermemory_client()
    
    memories = await client.search(
        query=query,
        container_tags=[user_id],
        limit=limit
    )
    
    return memories
```

### 4. Search Strategies

#### 4.1 Exa Strategy

```python
class ExaSearchStrategy(SearchStrategy):
    def __init__(self, api_key: str):
        self.client = Exa(api_key)
        
    async def search(
        self,
        query: str,
        category: Optional[SearchCategory],
        include_domains: Optional[List[str]],
        max_results: int
    ) -> List[SearchResult]:
        """Execute Exa search."""
        response = await self.client.search_and_contents(
            query,
            num_results=max_results,
            type="auto",
            category=category.value if category else None,
            include_domains=include_domains,
            text=True,
            livecrawl="preferred"
        )
        
        return [
            SearchResult(
                title=clean_title(r.title),
                url=r.url,
                content=r.text[:1000],
                published_date=r.published_date,
                favicon=r.favicon
            )
            for r in response.results
        ]
        
    async def get_content(
        self,
        urls: List[str]
    ) -> List[SearchResult]:
        """Retrieve full content from URLs."""
        response = await self.client.get_contents(
            urls,
            text={"max_characters": 3000},
            livecrawl="preferred"
        )
        
        return [
            SearchResult(
                title=r.title or extract_title_from_url(r.url),
                url=r.url,
                content=r.text,
                published_date=r.published_date,
                favicon=r.favicon or generate_favicon_url(r.url)
            )
            for r in response.results
            if r.text and r.text.strip()
        ]
```

#### 4.2 Content Retrieval with Fallback

```python
async def enrich_with_content(
    results: List[SearchResult],
    primary_strategy: SearchStrategy,
    fallback_strategy: SearchStrategy
) -> List[SearchResult]:
    """
    Enrich search results with full content using fallback.
    
    1. Try primary strategy (e.g., Exa)
    2. For failed URLs, try fallback (e.g., Firecrawl)
    3. Return enriched results
    """
    urls = [r.url for r in results]
    
    # Try primary strategy
    try:
        enriched = await primary_strategy.get_content(urls)
        enriched_urls = {r.url for r in enriched}
        failed_urls = [url for url in urls if url not in enriched_urls]
    except Exception as e:
        logger.error(f"Primary content retrieval failed: {e}")
        failed_urls = urls
        enriched = []
    
    # Try fallback for failed URLs
    if failed_urls:
        logger.info(f"Using fallback for {len(failed_urls)} URLs")
        try:
            fallback_results = await fallback_strategy.get_content(failed_urls)
            enriched.extend(fallback_results)
        except Exception as e:
            logger.error(f"Fallback content retrieval failed: {e}")
    
    # Merge with original results
    enriched_map = {r.url: r for r in enriched}
    return [
        enriched_map.get(r.url, r) for r in results
    ]
```

### 5. Memory Layer

#### 5.1 Supermemory Client

```python
class SupermemoryClient:
    def __init__(self, api_key: str, base_url: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
    async def store_research(
        self,
        user_id: str,
        session_id: str,
        research_result: ResearchResult
    ) -> None:
        """Store research results in Supermemory."""
        memories = [
            {
                "content": source.content,
                "metadata": {
                    "title": source.title,
                    "url": source.url,
                    "published_date": source.published_date,
                    "session_id": session_id
                },
                "container_tags": [user_id, f"session:{session_id}"]
            }
            for source in research_result.sources
        ]
        
        await self.client.post("/memories/batch", json={"memories": memories})
        
    async def search(
        self,
        query: str,
        container_tags: List[str],
        limit: int = 10
    ) -> List[Memory]:
        """Search memories."""
        response = await self.client.post(
            "/search/memories",
            json={
                "q": query,
                "container_tags": container_tags,
                "limit": limit
            }
        )
        return [Memory(**m) for m in response.json()["results"]]
```

### 6. Streaming and Callbacks

#### 6.1 Streaming Callback Handler

```python
class ResearchStreamingCallback(AsyncCallbackHandler):
    """LangChain callback handler for streaming research progress."""
    
    def __init__(self, event_queue: asyncio.Queue):
        self.event_queue = event_queue
        
    async def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs
    ) -> None:
        """Called when a tool starts executing."""
        await self.event_queue.put({
            "type": "tool_start",
            "tool": serialized["name"],
            "input": input_str,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    async def on_tool_end(
        self,
        output: str,
        **kwargs
    ) -> None:
        """Called when a tool finishes executing."""
        await self.event_queue.put({
            "type": "tool_end",
            "output": output[:500],  # Truncate for streaming
            "timestamp": datetime.utcnow().isoformat()
        })
        
    async def on_agent_action(
        self,
        action: AgentAction,
        **kwargs
    ) -> None:
        """Called when agent takes an action."""
        await self.event_queue.put({
            "type": "agent_action",
            "tool": action.tool,
            "tool_input": action.tool_input,
            "log": action.log[:200],
            "timestamp": datetime.utcnow().isoformat()
        })
```

#### 6.2 SSE Streaming Endpoint

```python
@app.post("/research/stream")
async def research_stream(request: ResearchRequest):
    """Stream research progress via Server-Sent Events."""
    
    async def event_generator():
        event_queue = asyncio.Queue()
        callback = ResearchStreamingCallback(event_queue)
        
        # Start research in background
        research_task = asyncio.create_task(
            agent.research(
                query=request.query,
                user_id=request.user_id,
                stream_handler=callback
            )
        )
        
        # Stream events
        while not research_task.done():
            try:
                event = await asyncio.wait_for(
                    event_queue.get(),
                    timeout=0.1
                )
                yield f"data: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                continue
        
        # Get final result
        result = await research_task
        yield f"data: {json.dumps({'type': 'complete', 'result': result.dict()})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

## Data Models

### Core Data Structures

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class SearchCategory(str, Enum):
    NEWS = "news"
    COMPANY = "company"
    RESEARCH_PAPER = "research paper"
    GITHUB = "github"
    FINANCIAL_REPORT = "financial report"

class SearchResult(BaseModel):
    title: str
    url: str
    content: str
    published_date: Optional[str] = None
    author: Optional[str] = None
    favicon: Optional[str] = None

class ResearchTask(BaseModel):
    title: str = Field(min_length=10, max_length=70)
    tasks: List[str] = Field(min_items=3, max_items=5)

class ResearchPlan(BaseModel):
    topics: List[ResearchTask] = Field(min_items=1, max_items=5)
    
    @property
    def total_tasks(self) -> int:
        return sum(len(topic.tasks) for topic in self.topics)

class CodeExecutionResult(BaseModel):
    output: str
    error: Optional[str] = None
    charts: List[Dict[str, Any]] = []

class ResearchResult(BaseModel):
    query: str
    plan: ResearchPlan
    text: str  # Final synthesis
    sources: List[SearchResult]
    charts: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    execution_time: float

class Memory(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float
```

## Error Handling

### Error Handling Strategy

```python
class ResearchError(Exception):
    """Base exception for research errors."""
    pass

class SearchProviderError(ResearchError):
    """Error from search provider."""
    pass

class ContentRetrievalError(ResearchError):
    """Error retrieving content."""
    pass

class CodeExecutionError(ResearchError):
    """Error executing code."""
    pass

# Error handling in tools
@tool
async def web_search(query: str, **kwargs) -> List[SearchResult]:
    try:
        strategy = get_search_strategy()
        results = await strategy.search(query, **kwargs)
        return results
    except Exception as e:
        logger.error(f"Search failed for query '{query}': {e}", exc_info=True)
        # Return empty results instead of raising
        return []

# Error handling in agent
async def research(self, query: str, user_id: Optional[str] = None) -> ResearchResult:
    try:
        # Research execution
        ...
    except Exception as e:
        logger.error(f"Research failed: {e}", exc_info=True)
        # Return partial results if available
        return ResearchResult(
            query=query,
            plan=plan if 'plan' in locals() else None,
            text=f"Research failed: {str(e)}",
            sources=[],
            charts=[],
            tool_results=[],
            execution_time=0.0
        )
```

## Testing Strategy

### Unit Tests

```python
# Test search strategies
@pytest.mark.asyncio
async def test_exa_search_strategy():
    strategy = ExaSearchStrategy(api_key="test_key")
    results = await strategy.search("test query", None, None, 5)
    assert len(results) <= 5
    assert all(isinstance(r, SearchResult) for r in results)

# Test content deduplication
def test_deduplicate_by_domain():
    results = [
        SearchResult(url="https://example.com/1", ...),
        SearchResult(url="https://example.com/2", ...),
        SearchResult(url="https://other.com/1", ...)
    ]
    deduplicated = deduplicate_results(results)
    assert len(deduplicated) == 2  # One per domain

# Test research planner
@pytest.mark.asyncio
async def test_research_planner():
    planner = ResearchPlanner(llm=MockLLM())
    plan = await planner.create_plan("test query")
    assert 1 <= len(plan.topics) <= 5
    assert plan.total_tasks <= 15
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_full_research_flow():
    agent = DeepResearchAgent(
        llm=get_test_llm(),
        search_provider="exa"
    )
    
    result = await agent.research("What is quantum computing?")
    
    assert result.query == "What is quantum computing?"
    assert result.plan is not None
    assert len(result.sources) > 0
    assert result.text != ""
```

## Performance Optimizations

### 1. Async Operations

```python
# Parallel search execution
async def execute_searches(queries: List[str]) -> List[List[SearchResult]]:
    tasks = [web_search(query) for query in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r if not isinstance(r, Exception) else [] for r in results]
```

### 2. Connection Pooling

```python
# Reuse HTTP clients
class SearchStrategy:
    def __init__(self, api_key: str):
        self.client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            timeout=httpx.Timeout(30.0)
        )
```

### 3. Caching

```python
from functools import lru_cache
from aiocache import cached

@cached(ttl=3600)  # Cache for 1 hour
async def get_content(url: str) -> str:
    """Cache content retrieval."""
    ...
```

## Security Considerations

1. **API Key Management**: Store in environment variables, never in code
2. **Input Validation**: Validate all user inputs using Pydantic
3. **Sandbox Isolation**: Execute code in isolated containers
4. **Rate Limiting**: Implement rate limiting on API endpoints
5. **User Isolation**: Tag all memories with user IDs for data isolation

## Deployment

### Docker Configuration

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY research_agent/ ./research_agent/

# Run application
CMD ["uvicorn", "research_agent.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

```bash
# LLM Configuration
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Search Providers
EXA_API_KEY=...
TAVILY_API_KEY=...
FIRECRAWL_API_KEY=...
PARALLEL_API_KEY=...

# Memory
SUPERMEMORY_API_KEY=...
SUPERMEMORY_BASE_URL=https://api.supermemory.ai

# Code Execution
DAYTONA_API_KEY=...

# Configuration
SEARCH_PROVIDER=exa
LOG_LEVEL=INFO
MAX_RESEARCH_TASKS=15
```

## Monitoring and Observability

### Logging

```python
import structlog

logger = structlog.get_logger()

# Structured logging
logger.info(
    "research_started",
    query=query,
    user_id=user_id,
    plan_tasks=plan.total_tasks
)

logger.error(
    "search_failed",
    query=query,
    provider=provider,
    error=str(e),
    exc_info=True
)
```

### Metrics

```python
from prometheus_client import Counter, Histogram

research_requests = Counter('research_requests_total', 'Total research requests')
research_duration = Histogram('research_duration_seconds', 'Research execution time')
tool_calls = Counter('tool_calls_total', 'Tool calls', ['tool_name'])

@research_duration.time()
async def research(self, query: str) -> ResearchResult:
    research_requests.inc()
    ...
```
