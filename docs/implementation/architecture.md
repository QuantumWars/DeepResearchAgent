# System Architecture

This document describes the architecture and design of the Deep Research Agent.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Applications                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │    CLI      │  │  REST API   │  │  Web UI     │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/WebSocket/SSE
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Research Agent API                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         FastAPI Endpoint (Streaming SSE)             │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                      │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │           DeepResearchAgent (LangGraph)              │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │  1. Research Planner (LLM + Structured Output)│   │  │
│  │  └──────────────────┬───────────────────────────┘   │  │
│  │                     │                                 │  │
│  │  ┌──────────────────▼───────────────────────────┐   │  │
│  │  │  2. LangGraph ReAct Agent                    │   │  │
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

## Core Components

### 1. Deep Research Agent (`research_agent/agent/research_agent.py`)

The main agent class that orchestrates the research process.

**Key Responsibilities:**
- Research planning using LLM
- Autonomous execution via LangGraph
- Tool selection and coordination
- Result aggregation and synthesis

**Architecture Pattern:** ReAct (Reasoning and Acting)

```python
class DeepResearchAgent:
    def __init__(self, llm, search_provider=None, memory_client=None):
        # Initialize tool registry
        # Configure search strategies
        # Setup memory integration

    async def research(self, query: str, user_id: str = None) -> ResearchResult:
        # 1. Generate research plan
        # 2. Execute LangGraph agent
        # 3. Aggregate results
        # 4. Return structured findings
```

### 2. Tool Registry (`research_agent/clients/tool_registry.py`)

Centralized tool management system.

**Features:**
- Dynamic tool registration
- Runtime enable/disable
- Configuration-based filtering
- Tool dependency management

```python
class ToolRegistry:
    def register(self, name: str, tool: Callable, enabled: bool = True)
    def enable_tool(self, name: str)
    def disable_tool(self, name: str)
    def get_enabled_tools(self) -> List[Callable]
```

### 3. Search Strategies (`research_agent/strategies/`)

Pluggable search provider architecture.

**Strategy Pattern Implementation:**
- `SearchStrategy` base class
- Provider-specific implementations
- Content enrichment with fallback
- Automatic failover

```python
class SearchStrategy(ABC):
    @abstractmethod
    async def search(self, query: str, max_results: int) -> List[SearchResult]

    @abstractmethod
    async def get_content(self, url: str) -> str
```

**Supported Providers:**
- Exa (recommended)
- Tavily
- Firecrawl
- Parallel AI

### 4. Tool Layer (`research_agent/tools/`)

Modular tool system with specialized capabilities.

**Tool Categories:**
- **Core Tools**: Web search, code execution, memory search
- **Specialized Search**: X, YouTube, Reddit, Academic
- **Utility Tools**: Currency, weather, flights, stocks, maps

**Architecture:**
- LangChain tool decorators
- Async/await patterns
- Comprehensive error handling
- Rate limiting and caching

### 5. Memory Layer (`research_agent/memory/`)

Integration with Supermemory for persistent storage.

**Features:**
- Research result storage
- Context retrieval
- User isolation
- Semantic search

### 6. Utilities (`research_agent/utils/`)

Shared infrastructure components.

**Components:**
- Configuration management
- Logging and monitoring
- Performance optimization
- Error handling and retry logic
- Content processing

## Data Flow

### Research Process Flow

1. **Query Reception**
   ```
   Client → API → DeepResearchAgent.research()
   ```

2. **Planning Phase**
   ```
   LLM → ResearchPlan → Topics and Tasks
   ```

3. **Execution Phase**
   ```
   LangGraph Agent → Tool Selection → API Calls → Results
   ```

4. **Aggregation Phase**
   ```
   Results → Content Processing → Synthesis → ResearchResult
   ```

5. **Response**
   ```
   ResearchResult → API → Client
   ```

### Tool Execution Flow

1. **Tool Selection**
   - Query analysis
   - Capability matching
   - Registry filtering

2. **API Interaction**
   - Rate limiting
   - Retry logic
   - Error handling

3. **Content Processing**
   - Deduplication
   - Content enrichment
   - Metadata extraction

## Design Patterns

### 1. Strategy Pattern
- **Location**: Search strategies
- **Purpose**: Pluggable search providers
- **Benefits**: Easy provider switching, testing, extension

### 2. Registry Pattern
- **Location**: Tool registry
- **Purpose**: Dynamic tool management
- **Benefits**: Runtime configuration, selective enabling

### 3. Factory Pattern
- **Location**: Search strategy factory
- **Purpose**: Provider instantiation
- **Benefits**: Configuration-based selection

### 4. Observer Pattern
- **Location**: Streaming callbacks
- **Purpose**: Real-time progress updates
- **Benefits**: Client progress tracking

### 5. Circuit Breaker Pattern
- **Location**: Retry logic
- **Purpose**: API failure handling
- **Benefits**: System resilience, graceful degradation

## Performance Considerations

### 1. Concurrency
- Async/await throughout
- Parallel tool execution
- Configurable concurrency limits

### 2. Caching
- Content caching with TTL
- Query deduplication
- Rate limit avoidance

### 3. Resource Management
- Connection pooling
- Memory optimization
- Timeout handling

### 4. Scalability
- Stateless design
- Horizontal scaling support
- Load balancer friendly

## Security Architecture

### 1. API Key Management
- Environment variable storage
- No hard-coded credentials
- Secure key rotation

### 2. Input Validation
- Pydantic model validation
- SQL injection prevention
- XSS protection

### 3. Rate Limiting
- Per-tool rate limiting
- Global request limits
- Exponential backoff

### 4. Error Handling
- No sensitive data exposure
- Consistent error responses
- Comprehensive logging

## Monitoring and Observability

### 1. Structured Logging
- Context-aware logging
- Request tracing
- Performance metrics

### 2. Error Tracking
- Comprehensive error handling
- Stack trace capture
- Error categorization

### 3. Performance Metrics
- Tool execution time
- API response times
- Success/failure rates

### 4. Health Checks
- API key validation
- Service availability
- Configuration verification

## Extension Points

### 1. New Search Providers
Implement `SearchStrategy` interface:
```python
class CustomSearchStrategy(SearchStrategy):
    async def search(self, query: str, max_results: int):
        # Implementation
```

### 2. New Tools
Create tool with LangChain decorator:
```python
@tool
async def custom_tool(input: str) -> dict:
    # Implementation
```

### 3. Custom Memory Providers
Implement memory interface:
```python
class CustomMemoryClient:
    async def store(self, data: dict):
        # Implementation
```

## Technology Stack

### Core Framework
- **LangChain**: LLM orchestration
- **LangGraph**: Agent framework
- **FastAPI**: REST API
- **Pydantic**: Data validation

### Infrastructure
- **AsyncIO**: Async programming
- **HTTPX**: HTTP client
- **Python 3.11+**: Runtime environment

### External APIs
- **OpenAI/Anthropic**: LLM providers
- **Exa/Tavily/Firecrawl**: Search providers
- **Various**: Specialized tools

## Deployment Architecture

### Development
```
Local Machine → Python Environment → Research Agent
```

### Production
```
Load Balancer → Multiple API Instances → Shared Memory/Cache
```

### Containerization
- Docker support
- Environment-based configuration
- Health check endpoints

## Future Enhancements

### 1. Multi-Modal Support
- Image processing
- Document parsing
- Audio/video content

### 2. Advanced Memory
- Knowledge graphs
- Contextual relationships
- Long-term memory

### 3. Collaboration Features
- Multi-user support
- Shared research sessions
- Real-time collaboration

### 4. Enhanced Search
- Semantic search
- Personalization
- Learning from user behavior