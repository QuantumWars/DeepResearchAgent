# Environment Variables Configuration

This document covers all environment variables used to configure the Deep Research Agent.

## Required Environment Variables

At least one LLM provider and one search provider are required.

### LLM Providers (at least one required)

```bash
# OpenAI (recommended)
OPENAI_API_KEY=sk-...

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-...
```

### Search Providers (at least one required)

```bash
# Exa (recommended for comprehensive search)
EXA_API_KEY=...

# Tavily (good for news/real-time)
TAVILY_API_KEY=...

# Firecrawl (web scraping)
FIRECRAWL_API_KEY=...

# Parallel AI (AI-powered search)
PARALLEL_API_KEY=...
```

## Optional Environment Variables

### Memory Storage

```bash
# Supermemory integration (optional)
SUPERMEMORY_API_KEY=...
SUPERMEMORY_BASE_URL=https://api.supermemory.ai
```

### Specialized Tool API Keys

```bash
# X/Twitter search (via xAI Grok)
XAI_API_KEY=...

# Weather data
OPENWEATHER_API_KEY=...

# Flight tracking
AVIATIONSTACK_API_KEY=...

# Stock market data
ALPHAVANTAGE_API_KEY=...

# Cryptocurrency data (optional, free tier available)
COINGECKO_API_KEY=...

# Map services (optional, uses free services by default)
GOOGLE_MAPS_API_KEY=...

# Code execution sandbox (optional)
DAYTONA_API_KEY=...
```

### Application Configuration

```bash
# Search provider selection
SEARCH_PROVIDER=exa  # exa, tavily, firecrawl, or parallel

# Logging configuration
LOG_LEVEL=INFO       # DEBUG, INFO, WARNING, ERROR

# Research limits
MAX_RESEARCH_TASKS=15
MAX_TOOL_CALLS=15
MAX_SEARCH_RESULTS=8
CONTENT_MAX_CHARS=3000

# Tool configuration
ENABLED_TOOLS=web_search,code_executor,memory_search,x_search,youtube_search,reddit_search,academic_search
```

## Tool Configuration

### Enabling Specific Tools

```bash
# Enable only specific tools (comma-separated)
ENABLED_TOOLS=web_search,code_executor,x_search,youtube_search,weather

# Enable all tools
ENABLED_TOOLS=all

# Core tools only (minimal setup)
ENABLED_TOOLS=web_search,code_executor,memory_search
```

### Available Tools

**Core Tools:**
- `web_search` - General web search
- `code_executor` - Python code execution
- `memory_search` - Supermemory search

**Specialized Search Tools:**
- `x_search` - X/Twitter search
- `youtube_search` - YouTube video search
- `reddit_search` - Reddit content search
- `academic_search` - Academic paper search

**Utility Tools:**
- `convert_currency` - Currency conversion
- `datetime_operations` - DateTime utilities
- `get_weather` - Weather data
- `track_flight` - Flight tracking
- `get_stock_data` - Stock market data
- `get_crypto_data` - Cryptocurrency data
- `get_crypto_market_overview` - Crypto market overview
- `geocode_location` - Geocoding
- `reverse_geocode` - Reverse geocoding
- `calculate_distance` - Distance calculation

## Configuration Examples

### Basic Setup (Minimal)

```bash
# .env file
OPENAI_API_KEY=sk-...
EXA_API_KEY=...

# Only core tools
ENABLED_TOOLS=web_search,code_executor,memory_search
```

### Full Featured Setup

```bash
# .env file
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# All search providers
EXA_API_KEY=...
TAVILY_API_KEY=...
FIRECRAWL_API_KEY=...
PARALLEL_API_KEY=...

# Memory
SUPERMEMORY_API_KEY=...

# Specialized tools
XAI_API_KEY=...
OPENWEATHER_API_KEY=...
AVIATIONSTACK_API_KEY=...
ALPHAVANTAGE_API_KEY=...
COINGECKO_API_KEY=...

# Configuration
SEARCH_PROVIDER=exa
LOG_LEVEL=INFO
ENABLED_TOOLS=all
```

### Social Media Research Setup

```bash
# .env file
OPENAI_API_KEY=sk-...
EXA_API_KEY=...
XAI_API_KEY=...

# Enable social media tools
ENABLED_TOOLS=web_search,x_search,youtube_search,reddit_search,code_executor

# Configuration
SEARCH_PROVIDER=exa
MAX_SEARCH_RESULTS=15
```

### Academic Research Setup

```bash
# .env file
ANTHROPIC_API_KEY=sk-ant-...
EXA_API_KEY=...

# Enable academic tools
ENABLED_TOOLS=web_search,academic_search,code_executor,memory_search

# Configuration
SEARCH_PROVIDER=exa
MAX_SEARCH_RESULTS=20
CONTENT_MAX_CHARS=5000
```

## Loading Configuration

The application automatically loads environment variables from:

1. System environment variables
2. `.env` file in the project root
3. `.env` file in the `research_agent/` directory

### Using dotenv

```python
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Now you can access environment variables
import os
api_key = os.getenv("OPENAI_API_KEY")
```

## Configuration Validation

The system validates configuration on startup:

```python
from research_agent.utils.config import get_config

try:
    config = get_config()
    print("Configuration is valid")
    print(f"Enabled tools: {config.enabled_tools}")
except ValueError as e:
    print(f"Configuration error: {e}")
```

## Security Considerations

### API Key Security

1. **Never commit API keys to version control**
2. **Use environment variables or secure secret management**
3. **Rotate API keys regularly**
4. **Use least-privilege access for API keys**

### Environment File Security

```bash
# Add .env to .gitignore
echo ".env" >> .gitignore

# Set proper permissions
chmod 600 .env
```

## Troubleshooting

### Common Configuration Errors

**Missing required API keys:**
```
ValueError: Configuration validation failed: At least one LLM API key required
```
Solution: Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

**Search provider not configured:**
```
ValueError: API key for search provider 'exa' is required
```
Solution: Set the appropriate search provider API key

**Invalid tool names:**
```
Warning: Unknown tool 'invalid_tool_name' in ENABLED_TOOLS
```
Solution: Check the list of available tool names above

### Debug Mode

Enable debug logging to troubleshoot configuration:

```bash
# Set log level to DEBUG
LOG_LEVEL=DEBUG

# Run the application
python main.py "test query" --log-level DEBUG
```

### Testing Configuration

```python
# Test configuration script
import os
from research_agent.utils.config import get_config

def test_config():
    try:
        config = get_config()

        print("✅ Configuration loaded successfully")
        print(f"LLM Provider: {'OpenAI' if config.openai_api_key else 'Anthropic' if config.anthropic_api_key else 'None'}")
        print(f"Search Provider: {config.search_provider}")
        print(f"Enabled Tools: {config.enabled_tools}")
        print(f"Log Level: {config.log_level}")

        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

if __name__ == "__main__":
    test_config()
```