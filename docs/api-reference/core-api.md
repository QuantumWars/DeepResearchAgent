# API Documentation

This document provides comprehensive API documentation for the Deep Research Agent, including the tool registry system, configuration options, and examples of enabling/disabling tools.

## Table of Contents

- [Tool Registry API](#tool-registry-api)
- [Configuration API](#configuration-api)
- [Tool Management](#tool-management)
- [Agent API](#agent-api)
- [Examples](#examples)

---

## Tool Registry API

The tool registry system provides centralized management for all research tools.

### ToolRegistry Class

Located in `research_agent/clients/tool_registry.py`

#### Methods

##### `register(name: str, tool: Callable, enabled: bool = True)`

Register a new tool in the registry.

**Parameters**:
- `name` (str): Unique identifier for the tool
- `tool` (Callable): The tool function (decorated with `@tool`)
- `enabled` (bool): Whether the tool is enabled by default (default: True)

**Example**:
```python
from research_agent.clients.tool_registry import get_tool_registry

registry = get_tool_registry()
registry.register("my_custom_tool", my_tool_function, enabled=True)
```

##### `get_enabled_tools() -> List[Callable]`

Get a list of all enabled tools.

**Returns**: List of tool functions that are currently enabled

**Example**:
```python
registry = get_tool_registry()
enabled_tools = registry.get_enabled_tools()
print(f"Number of enabled tools: {len(enabled_tools)}")
```

##### `enable_tool(name: str)`

Enable a specific tool.

**Parameters**:
- `name` (str): Name of the tool to enable

**Example**:
```python
registry = get_tool_registry()
registry.enable_tool("x_search")
```

##### `disable_tool(name: str)`

Disable a specific tool.

**Parameters**:
- `name` (str): Name of the tool to disable

**Example**:
```python
registry = get_tool_registry()
registry.disable_tool("flight_tracker")
```

##### `list_all_tools() -> Dict[str, bool]`

Get a dictionary of all registered tools and their enabled status.

**Returns**: Dictionary mapping tool names to their enabled status

**Example**:
```python
registry = get_tool_registry()
all_tools = registry.list_all_tools()
for name, enabled in all_tools.items():
    print(f"{name}: {'enabled' if enabled else 'disabled'}")
```

### Tool Registration Decorator

Use the `@register_tool` decorator to automatically register tools.

**Example**:
```python
from research_agent.clients.tool_registry import register_tool
from langchain_core.tools import tool

@register_tool(name="my_tool", enabled=True)
@tool
async def my_custom_tool(query: str) -> dict:
    """My custom tool description."""
    return {"result": "success"}
```

### Getting the Global Registry

```python
from research_agent.clients.tool_registry import get_tool_registry

# Get the singleton registry instance
registry = get_tool_registry()
```

---

## Configuration API

The configuration system manages API keys, tool settings, and application parameters.

### Config Class

Located in `research_agent/utils/config.py`

#### Core Configuration

##### LLM Provider Settings

```python
from research_agent.utils.config import get_config

config = get_config()

# OpenAI settings
openai_key = config.openai_api_key
openai_model = config.openai_model  # Default: "gpt-4o-mini"

# Anthropic settings
anthropic_key = config.anthropic_api_key
anthropic_model = config.anthropic_model  # Default: "claude-3-5-sonnet-20241022"
```

##### Search Provider Settings

```python
# Search provider selection
search_provider = config.search_provider  # "exa", "tavily", "firecrawl", "parallel"

# Search provider API keys
exa_key = config.exa_api_key
tavily_key = config.tavily_api_key
firecrawl_key = config.firecrawl_api_key
parallel_key = config.parallel_api_key
```

##### Specialized Tool API Keys

```python
# X/Twitter search
xai_key = config.xai_api_key

# Weather data
weather_key = config.openweather_api_key

# Flight tracking
flight_key = config.aviationstack_api_key

# Stock data
stock_key = config.alphavantage_api_key

# Cryptocurrency data
crypto_key = config.coingecko_api_key

# Map services
maps_key = config.google_maps_api_key
```

##### Application Settings

```python
# Logging
log_level = config.log_level  # "DEBUG", "INFO", "WARNING", "ERROR"

# Research limits
max_tasks = config.max_research_tasks  # Default: 15
max_tool_calls = config.max_tool_calls  # Default: 15
max_results = config.max_search_results  # Default: 8

# Content processing
max_chars = config.content_max_chars  # Default: 3000
```

#### Tool Configuration

##### Enabled Tools

```python
# Get list of enabled tools
enabled_tools = config.enabled_tools

# Check if a specific tool is enabled
if "x_search" in enabled_tools:
    print("X search is enabled")
```

##### Setting Enabled Tools

Via environment variable:
```bash
# Enable specific tools
export ENABLED_TOOLS="web_search,code_executor,x_search,youtube_search"

# Enable all tools
export ENABLED_TOOLS="all"
```

Via code:
```python
import os
os.environ["ENABLED_TOOLS"] = "web_search,x_search,youtube_search"

# Reload config
from research_agent.utils.config import get_config
config = get_config()
```

#### Configuration Validation

The configuration system automatically validates required API keys:

```python
from research_agent.utils.config import get_config

try:
    config = get_config()
    # Configuration is valid
except ValueError as e:
    # Missing required API keys
    print(f"Configuration error: {e}")
```

---

## Tool Management

### Enabling/Disabling Tools at Runtime

#### Using the Registry

```python
from research_agent.clients.tool_registry import get_tool_registry

registry = get_tool_registry()

# Enable a tool
registry.enable_tool("x_search")

# Disable a tool
registry.disable_tool("flight_tracker")

# Get current enabled tools
enabled = registry.get_enabled_tools()
```

#### Using Configuration

```python
from research_agent.utils.config import get_config

config = get_config()

# Check enabled tools
print(f"Enabled tools: {config.enabled_tools}")

# Modify at runtime (affects new agent instances)
import os
os.environ["ENABLED_TOOLS"] = "web_search,x_search"
```

### Tool Filtering

The agent automatically filters tools based on configuration:

```python
from research_agent.agent.research_agent import DeepResearchAgent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")
agent = DeepResearchAgent(llm=llm)

# Agent only uses enabled tools from registry
# Tools are filtered in __init__ method
```

### Custom Tool Registration

Register custom tools programmatically:

```python
from langchain_core.tools import tool
from research_agent.clients.tool_registry import get_tool_registry

@tool
async def my_custom_search(query: str) -> dict:
    """Custom search tool."""
    # Implementation
    return {"results": []}

# Register the tool
registry = get_tool_registry()
registry.register("custom_search", my_custom_search, enabled=True)
```

---

## Agent API

### DeepResearchAgent Class

Located in `research_agent/agent/research_agent.py`

#### Initialization

```python
from research_agent.agent.research_agent import DeepResearchAgent
from langchain_openai import ChatOpenAI

# Create LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

# Create agent with default settings
agent = DeepResearchAgent(llm=llm)

# Create agent with specific search provider
agent = DeepResearchAgent(
    llm=llm,
    search_provider="exa"
)

# Create agent with custom memory client
from research_agent.memory.supermemory_client import SupermemoryClient
memory = SupermemoryClient()
agent = DeepResearchAgent(
    llm=llm,
    memory_client=memory
)
```

#### Research Method

```python
async def research(
    query: str,
    user_id: Optional[str] = None
) -> ResearchResult
```

Execute a research query.

**Parameters**:
- `query` (str): The research question or topic
- `user_id` (str, optional): User ID for memory isolation

**Returns**: `ResearchResult` object with findings

**Example**:
```python
import asyncio

async def main():
    agent = DeepResearchAgent(llm=llm)
    result = await agent.research(
        query="What are the latest developments in quantum computing?",
        user_id="user123"
    )
    
    print(f"Query: {result.query}")
    print(f"Findings: {result.text}")
    print(f"Sources: {len(result.sources)}")
    print(f"Execution time: {result.execution_time}s")

asyncio.run(main())
```

#### Tool Access

```python
# Get tools used by the agent
agent_tools = agent.tools

# Check which tools are available
tool_names = [tool.name for tool in agent_tools]
print(f"Available tools: {tool_names}")
```

---

## Examples

### Example 1: Basic Agent with Selective Tools

```python
import asyncio
import os
from langchain_openai import ChatOpenAI
from research_agent.agent.research_agent import DeepResearchAgent

# Enable only specific tools
os.environ["ENABLED_TOOLS"] = "web_search,x_search,youtube_search"

async def main():
    llm = ChatOpenAI(model="gpt-4o-mini")
    agent = DeepResearchAgent(llm=llm, search_provider="exa")
    
    result = await agent.research("Latest AI news on Twitter and YouTube")
    
    print(f"Found {len(result.sources)} sources")
    for source in result.sources:
        print(f"- {source.title}: {source.url}")

asyncio.run(main())
```

### Example 2: Dynamic Tool Management

```python
from research_agent.clients.tool_registry import get_tool_registry
from research_agent.agent.research_agent import DeepResearchAgent
from langchain_openai import ChatOpenAI

# Get registry
registry = get_tool_registry()

# Disable expensive tools
registry.disable_tool("flight_tracker")
registry.disable_tool("stock_chart")

# Enable only needed tools
registry.enable_tool("web_search")
registry.enable_tool("x_search")
registry.enable_tool("weather")

# Create agent (will use only enabled tools)
llm = ChatOpenAI(model="gpt-4o-mini")
agent = DeepResearchAgent(llm=llm)

# Verify tools
print(f"Agent has {len(agent.tools)} tools enabled")
```

### Example 3: Custom Tool Registration

```python
from langchain_core.tools import tool
from research_agent.clients.tool_registry import get_tool_registry
from research_agent.agent.research_agent import DeepResearchAgent
from langchain_openai import ChatOpenAI

# Define custom tool
@tool
async def custom_news_search(query: str, category: str = "technology") -> dict:
    """Search news articles by category."""
    # Custom implementation
    return {
        "query": query,
        "category": category,
        "articles": []
    }

# Register tool
registry = get_tool_registry()
registry.register("custom_news", custom_news_search, enabled=True)

# Create agent (includes custom tool)
llm = ChatOpenAI(model="gpt-4o-mini")
agent = DeepResearchAgent(llm=llm)

# Use agent with custom tool
result = await agent.research("Latest technology news")
```

### Example 4: Configuration-Based Tool Control

```python
import os
from research_agent.utils.config import get_config
from research_agent.agent.research_agent import DeepResearchAgent
from langchain_openai import ChatOpenAI

# Set configuration via environment
os.environ["ENABLED_TOOLS"] = "web_search,academic_search,reddit_search"
os.environ["MAX_SEARCH_RESULTS"] = "10"
os.environ["MAX_TOOL_CALLS"] = "20"

# Get config
config = get_config()
print(f"Enabled tools: {config.enabled_tools}")
print(f"Max results: {config.max_search_results}")

# Create agent with config
llm = ChatOpenAI(model="gpt-4o-mini")
agent = DeepResearchAgent(llm=llm)

# Research with configured settings
result = await agent.research("Machine learning research papers")
```

### Example 5: Tool Registry Inspection

```python
from research_agent.clients.tool_registry import get_tool_registry

registry = get_tool_registry()

# List all registered tools
all_tools = registry.list_all_tools()
print("All registered tools:")
for name, enabled in all_tools.items():
    status = "✓" if enabled else "✗"
    print(f"  {status} {name}")

# Get only enabled tools
enabled_tools = registry.get_enabled_tools()
print(f"\nEnabled tools count: {len(enabled_tools)}")

# Enable/disable specific tools
print("\nEnabling x_search and youtube_search...")
registry.enable_tool("x_search")
registry.enable_tool("youtube_search")

print("Disabling flight_tracker...")
registry.disable_tool("flight_tracker")

# Verify changes
updated_tools = registry.list_all_tools()
print("\nUpdated tool status:")
for name, enabled in updated_tools.items():
    status = "✓" if enabled else "✗"
    print(f"  {status} {name}")
```

### Example 6: Environment-Based Configuration

Create a `.env` file:

```bash
# .env file
OPENAI_API_KEY=sk-...
EXA_API_KEY=...
XAI_API_KEY=...
TAVILY_API_KEY=...

# Enable specific tools
ENABLED_TOOLS=web_search,x_search,youtube_search,reddit_search,academic_search,weather

# Configuration
SEARCH_PROVIDER=exa
LOG_LEVEL=INFO
MAX_TOOL_CALLS=20
```

Python code:

```python
from dotenv import load_dotenv
from research_agent.utils.config import get_config
from research_agent.agent.research_agent import DeepResearchAgent
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# Get configuration
config = get_config()

# Create agent
llm = ChatOpenAI(model="gpt-4o-mini")
agent = DeepResearchAgent(
    llm=llm,
    search_provider=config.search_provider
)

# Research
result = await agent.research("Your research query")
```

### Example 7: Programmatic Tool Filtering

```python
from research_agent.clients.tool_registry import get_tool_registry
from research_agent.agent.research_agent import DeepResearchAgent
from langchain_openai import ChatOpenAI

def configure_tools_for_task(task_type: str):
    """Configure tools based on task type."""
    registry = get_tool_registry()
    
    # Disable all tools first
    for tool_name in registry.list_all_tools():
        registry.disable_tool(tool_name)
    
    # Enable tools based on task
    if task_type == "social_media_research":
        registry.enable_tool("web_search")
        registry.enable_tool("x_search")
        registry.enable_tool("reddit_search")
        registry.enable_tool("youtube_search")
    
    elif task_type == "academic_research":
        registry.enable_tool("web_search")
        registry.enable_tool("academic_search")
    
    elif task_type == "market_research":
        registry.enable_tool("web_search")
        registry.enable_tool("stock_chart")
        registry.enable_tool("crypto_data")
        registry.enable_tool("currency_converter")
    
    elif task_type == "travel_research":
        registry.enable_tool("web_search")
        registry.enable_tool("weather")
        registry.enable_tool("flight_tracker")
        registry.enable_tool("geocode_location")

# Configure for social media research
configure_tools_for_task("social_media_research")

# Create agent
llm = ChatOpenAI(model="gpt-4o-mini")
agent = DeepResearchAgent(llm=llm)

# Research
result = await agent.research("What are people saying about AI on social media?")
```

---

## API Reference Summary

### Key Classes

- `ToolRegistry`: Manages tool registration and enablement
- `Config`: Manages application configuration and API keys
- `DeepResearchAgent`: Main agent class for research execution
- `ResearchResult`: Result object containing research findings

### Key Functions

- `get_tool_registry()`: Get the global tool registry instance
- `get_config()`: Get the global configuration instance
- `register_tool()`: Decorator for automatic tool registration

### Configuration Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLED_TOOLS` | Comma-separated list of enabled tools | Core tools only |
| `SEARCH_PROVIDER` | Search provider to use | `exa` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAX_RESEARCH_TASKS` | Maximum research tasks | `15` |
| `MAX_TOOL_CALLS` | Maximum tool calls | `15` |
| `MAX_SEARCH_RESULTS` | Maximum search results | `8` |
| `CONTENT_MAX_CHARS` | Maximum content characters | `3000` |

### Tool Names

Core tools:
- `web_search`
- `code_executor`
- `memory_search`

Specialized search tools:
- `x_search`
- `youtube_search`
- `reddit_search`
- `academic_search`

Utility tools:
- `convert_currency`
- `datetime_operations`
- `get_weather`
- `track_flight`
- `get_stock_data`
- `get_crypto_data`
- `get_crypto_market_overview`
- `geocode_location`
- `reverse_geocode`
- `calculate_distance`

---

## Additional Resources

- [Tool Catalog](TOOLS.md) - Detailed tool descriptions and usage
- [README](README.md) - Getting started guide
- [Requirements](.kiro/specs/tool-integration/requirements.md) - Feature requirements
- [Design Document](.kiro/specs/tool-integration/design.md) - Architecture and design

For more information or support, please open an issue on GitHub.
