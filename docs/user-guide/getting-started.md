# Deep Research Agent

An autonomous AI-powered research agent that performs multi-step research using LangChain, LangGraph, and multiple search providers. The agent creates structured research plans, executes searches autonomously, and aggregates findings into comprehensive reports.

## Features

- 🤖 **Autonomous Research**: AI agent plans and executes research tasks independently
- 🔍 **Multi-Provider Search**: Supports Exa, Tavily, Firecrawl, and Parallel AI search
- 📊 **Code Execution**: Run Python code for data analysis and visualizations
- 💾 **Memory Integration**: Store and retrieve research context with Supermemory
- 🌊 **Real-time Streaming**: Server-Sent Events (SSE) for live progress updates
- 🎯 **Structured Planning**: LLM-generated research plans with 1-5 topics and up to 15 tasks
- 🔄 **Content Enrichment**: Automatic fallback for content retrieval
- 📝 **Comprehensive Logging**: Structured logging with context for debugging

### Specialized Search Tools

- 🐦 **X/Twitter Search**: Search X posts with date range, handle filtering, and engagement metrics via xAI Grok
- 📺 **YouTube Search**: Find videos with transcript extraction and chapter timestamps
- 🔴 **Reddit Search**: Search Reddit posts and comments with subreddit filtering
- 🎓 **Academic Search**: Search scholarly papers and research articles with abstracts

### Utility Tools

- 💱 **Currency Converter**: Convert between currencies with live exchange rates
- 🕐 **DateTime Operations**: Timezone conversion, duration calculations, and date formatting
- 🌤️ **Weather Data**: Current weather and forecasts for any location
- ✈️ **Flight Tracker**: Real-time flight status, delays, and gate information
- 📈 **Stock Data**: Historical stock prices and market indicators
- ₿ **Crypto Data**: Cryptocurrency prices, market cap, and trends
- 🗺️ **Map Tools**: Geocoding, reverse geocoding, and distance calculations

## Architecture

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

## Installation

### Prerequisites

- Python 3.11 or higher
- pip or uv package manager

### Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using uv (recommended)
uv pip install -r requirements.txt
```

### Additional Dependencies for Specialized Tools

The specialized search and utility tools require additional Python packages:

```bash
# For X/Twitter search
pip install xai-sdk

# For YouTube search (transcript extraction)
pip install youtube-transcript-api

# For stock data
pip install yfinance

# For datetime operations
pip install pytz

# All dependencies are included in requirements.txt
```

### Environment Variables

Create a `.env` file in the `research_agent/` directory or set environment variables:

```bash
# Required: LLM Provider (at least one)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Required: Search Provider (at least one)
EXA_API_KEY=...
TAVILY_API_KEY=...
FIRECRAWL_API_KEY=...
PARALLEL_API_KEY=...

# Optional: Memory Storage
SUPERMEMORY_API_KEY=...
SUPERMEMORY_BASE_URL=https://api.supermemory.ai

# Optional: Specialized Tool API Keys
XAI_API_KEY=...                    # For X/Twitter search via Grok
OPENWEATHER_API_KEY=...            # For weather data
AVIATIONSTACK_API_KEY=...          # For flight tracking
ALPHAVANTAGE_API_KEY=...           # For stock market data
COINGECKO_API_KEY=...              # For cryptocurrency data (optional, free tier available)
GOOGLE_MAPS_API_KEY=...            # For geocoding (optional, uses OpenStreetMap by default)

# Optional: Configuration
SEARCH_PROVIDER=exa  # exa, tavily, firecrawl, or parallel
LOG_LEVEL=INFO       # DEBUG, INFO, WARNING, ERROR
MAX_RESEARCH_TASKS=15
MAX_TOOL_CALLS=15
MAX_SEARCH_RESULTS=8
CONTENT_MAX_CHARS=3000

# Tool Configuration
ENABLED_TOOLS=web_search,code_executor,memory_search,x_search,youtube_search,reddit_search,academic_search
```

#### API Key Setup Guide

**Required Keys** (at least one LLM and one search provider):
- OpenAI or Anthropic for LLM
- Exa, Tavily, Firecrawl, or Parallel AI for search

**Optional Keys for Specialized Tools**:
- **X/Twitter Search**: Requires `XAI_API_KEY` from [x.ai](https://x.ai/)
- **YouTube Search**: Uses Exa API (already required for search)
- **Reddit Search**: Uses Tavily API (already required if using Tavily)
- **Academic Search**: Uses Exa API (already required for search)
- **Weather**: Requires `OPENWEATHER_API_KEY` from [OpenWeatherMap](https://openweathermap.org/api)
- **Flight Tracker**: Requires `AVIATIONSTACK_API_KEY` from [AviationStack](https://aviationstack.com/)
- **Stock Data**: Requires `ALPHAVANTAGE_API_KEY` from [Alpha Vantage](https://www.alphavantage.co/)
- **Crypto Data**: Optional `COINGECKO_API_KEY` from [CoinGecko](https://www.coingecko.com/en/api) (free tier works without key)
- **Map Tools**: Uses free OpenStreetMap Nominatim API (no key required)
- **Currency Converter**: Uses free exchangerate-api.com (no key required)
- **DateTime Operations**: No API key required

See `.env.example` for a complete template with all available configuration options.
```

## Usage

### CLI Usage

```bash
# Basic research
python main.py "What is quantum computing?"

# With specific search provider
python main.py "AI trends 2024" --provider tavily

# With user ID for memory
python main.py "Machine learning basics" --user-id user123

# JSON output format
python main.py "Climate change" --format json

# Save to file
python main.py "Python async" --output results.txt

# Debug mode
python main.py "Research topic" --log-level DEBUG
```

### API Usage

Start the FastAPI server:

```bash
# Development mode
python -m research_agent.api.main

# Or using uvicorn directly
uvicorn research_agent.api.main:app --reload --host 0.0.0.0 --port 8000
```

#### Endpoints

**Health Check**
```bash
curl http://localhost:8000/health
```

**Streaming Research**
```bash
curl -X POST http://localhost:8000/research/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "What is quantum computing?", "user_id": "user123"}' \
  --no-buffer
```

The streaming endpoint returns Server-Sent Events (SSE) with real-time progress:

```
data: {"type": "start", "query": "What is quantum computing?"}

data: {"type": "tool_start", "tool": "web_search", "input": "quantum computing basics"}

data: {"type": "tool_end", "output": "[SearchResult(...)]"}

data: {"type": "complete", "result": {...}}
```

### Python API Usage

```python
import asyncio
from langchain_openai import ChatOpenAI
from research_agent.agent.research_agent import DeepResearchAgent

async def main():
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    # Create agent
    agent = DeepResearchAgent(
        llm=llm,
        search_provider="exa"
    )
    
    # Execute research
    result = await agent.research(
        query="What is quantum computing?",
        user_id="user123"
    )
    
    # Access results
    print(f"Query: {result.query}")
    print(f"Findings: {result.text}")
    print(f"Sources: {len(result.sources)}")
    print(f"Execution time: {result.execution_time}s")
    
    for source in result.sources:
        print(f"- {source.title}: {source.url}")

asyncio.run(main())
```

## Configuration

### Search Providers

The agent supports multiple search providers, each with different strengths:

- **Exa**: Best for comprehensive web search with content retrieval
- **Tavily**: Optimized for news and real-time information
- **Firecrawl**: Good for web scraping and content extraction
- **Parallel AI**: Advanced AI-powered search with quality options

Configure via `SEARCH_PROVIDER` environment variable or CLI `--provider` flag.

### LLM Providers

Supports OpenAI and Anthropic models:

- **OpenAI**: Uses `gpt-4o-mini` by default
- **Anthropic**: Uses `claude-3-5-sonnet-20241022` by default

The agent automatically selects the provider based on available API keys.

### Memory Storage

Optional Supermemory integration for storing and retrieving research context:

- Stores each source as a separate memory
- Tags with user_id and session_id for isolation
- Enables building on past research
- Requires `SUPERMEMORY_API_KEY`

## Project Structure

```
research_agent/
├── agent/
│   ├── research_agent.py      # Main DeepResearchAgent class
│   ├── planner.py              # Research plan generation
│   └── callbacks.py            # Streaming callback handlers
├── tools/
│   ├── web_search.py           # Web search tool
│   ├── code_executor.py        # Python code execution
│   ├── memory_search.py        # Supermemory search
│   ├── x_search.py             # X/Twitter search
│   ├── youtube_search.py       # YouTube video search
│   ├── reddit_search.py        # Reddit content search
│   ├── academic_search.py      # Academic paper search
│   ├── currency_converter.py   # Currency conversion
│   ├── datetime_tool.py        # DateTime operations
│   ├── weather_tool.py         # Weather data
│   ├── flight_tracker.py       # Flight tracking
│   ├── stock_chart.py          # Stock market data
│   ├── crypto_tools.py         # Cryptocurrency data
│   └── map_tools.py            # Geocoding and maps
├── clients/
│   ├── xai_client.py           # xAI Grok API client
│   ├── youtube_client.py       # YouTube utilities
│   ├── tool_registry.py        # Tool registration system
│   └── client_manager.py       # API client management
├── strategies/
│   ├── base.py                 # SearchStrategy base class
│   ├── exa_strategy.py         # Exa implementation
│   ├── tavily_strategy.py      # Tavily implementation
│   ├── firecrawl_strategy.py   # Firecrawl implementation
│   ├── parallel_strategy.py    # Parallel AI implementation
│   ├── factory.py              # Strategy factory
│   └── content_enrichment.py   # Content retrieval with fallback
├── memory/
│   └── supermemory_client.py   # Supermemory integration
├── utils/
│   ├── config.py               # Configuration management
│   ├── models.py               # Pydantic data models
│   ├── logger.py               # Logging setup
│   ├── content_processor.py    # Content utilities
│   ├── performance.py          # Performance optimizations
│   ├── retry.py                # Retry logic
│   └── error_handling.py       # Error handling utilities
└── api/
    └── main.py                 # FastAPI application
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=research_agent

# Run specific test file
pytest tests/test_agent.py
```

### Code Quality

```bash
# Format code
black research_agent/

# Lint code
ruff check research_agent/

# Type checking
mypy research_agent/
```

## Troubleshooting

### Common Issues

**API Key Errors**
```
ValueError: Configuration validation failed: At least one LLM API key required
```
Solution: Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in your environment.

**Search Provider Errors**
```
ValueError: API key for search provider 'exa' is required
```
Solution: Set the appropriate API key (e.g., `EXA_API_KEY`) for your chosen provider.

**Import Errors**
```
ImportError: cannot import name 'AgentExecutor'
```
Solution: Ensure you have the latest versions of langchain and langgraph installed.

**Memory Warnings**
```
Supermemory API key not configured, memory features will be disabled
```
This is a warning, not an error. Memory features are optional. Set `SUPERMEMORY_API_KEY` to enable.

### Debug Mode

Enable detailed logging:

```bash
# CLI
python main.py "query" --log-level DEBUG

# Environment variable
export LOG_LEVEL=DEBUG
```

### Performance Tips

1. **Use Exa for best content quality**: Exa provides the most comprehensive content retrieval
2. **Limit max_tool_calls**: Reduce `MAX_TOOL_CALLS` for faster results (default: 15)
3. **Use caching**: Results are automatically deduplicated to avoid redundant searches
4. **Parallel execution**: The agent uses async operations for optimal performance

## API Reference

### DeepResearchAgent

Main class for autonomous research execution.

```python
class DeepResearchAgent:
    def __init__(
        self,
        llm: BaseChatModel,
        search_provider: Optional[str] = None,
        memory_client: Optional[SupermemoryClient] = None,
        stream_handler: Optional[AsyncCallbackHandler] = None
    )
    
    async def research(
        self,
        query: str,
        user_id: Optional[str] = None
    ) -> ResearchResult
```

### ResearchResult

Result object containing research findings.

```python
class ResearchResult(BaseModel):
    query: str
    plan: Optional[ResearchPlan]
    text: str
    sources: List[SearchResult]
    charts: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    execution_time: float
```

### SearchResult

Individual search result with content and metadata.

```python
class SearchResult(BaseModel):
    title: str
    url: str
    content: str
    published_date: Optional[str]
    author: Optional[str]
    favicon: Optional[str]
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Built with [LangChain](https://langchain.com/) and [LangGraph](https://langchain-ai.github.io/langgraph/)
- Search powered by [Exa](https://exa.ai/), [Tavily](https://tavily.com/), [Firecrawl](https://firecrawl.dev/), and [Parallel AI](https://parallel.ai/)
- Memory storage by [Supermemory](https://supermemory.ai/)

## Support

For issues, questions, or contributions, please open an issue on GitHub.
