# Tool Catalog

This document provides a comprehensive catalog of all available tools in the Deep Research Agent, including their descriptions, parameters, rate limits, and usage examples.

## Table of Contents

- [Core Research Tools](#core-research-tools)
- [Specialized Search Tools](#specialized-search-tools)
- [Utility Tools](#utility-tools)
- [Tool Configuration](#tool-configuration)
- [Rate Limits and Constraints](#rate-limits-and-constraints)
- [Troubleshooting Guide](#troubleshooting-guide)

---

## Core Research Tools

### web_search

**Description**: General web search using configurable search providers (Exa, Tavily, Firecrawl, or Parallel AI).

**Parameters**:
- `query` (str): Search query
- `max_results` (int, optional): Maximum number of results (default: 8)

**API Key Required**: Yes (depends on selected provider)
- Exa: `EXA_API_KEY`
- Tavily: `TAVILY_API_KEY`
- Firecrawl: `FIRECRAWL_API_KEY`
- Parallel AI: `PARALLEL_API_KEY`

**Rate Limits**: Varies by provider
- Exa: 1000 requests/month (free tier)
- Tavily: 1000 requests/month (free tier)
- Firecrawl: Varies by plan
- Parallel AI: Varies by plan

**Example**:
```python
result = await web_search("quantum computing applications")
```

---

### code_executor

**Description**: Execute Python code in a sandboxed environment for data analysis and visualizations.

**Parameters**:
- `code` (str): Python code to execute

**API Key Required**: Optional (`DAYTONA_API_KEY` for sandboxed execution)

**Rate Limits**: Depends on Daytona plan if using sandboxed execution

**Example**:
```python
code = """
import matplotlib.pyplot as plt
data = [1, 2, 3, 4, 5]
plt.plot(data)
plt.title('Sample Plot')
plt.savefig('output.png')
"""
result = await code_executor(code)
```

---

### memory_search

**Description**: Search stored research memories using Supermemory.

**Parameters**:
- `query` (str): Search query
- `user_id` (str, optional): User ID for filtering

**API Key Required**: Yes (`SUPERMEMORY_API_KEY`)

**Rate Limits**: Varies by Supermemory plan

**Example**:
```python
result = await memory_search("previous research on AI", user_id="user123")
```

---

## Specialized Search Tools

### x_search

**Description**: Search X (Twitter) posts using xAI Grok API with live search capabilities. Supports date range filtering, handle filtering, and engagement metrics.

**Parameters**:
- `queries` (List[str]): List of search queries (1-5)
- `start_date` (str, optional): Start date in YYYY-MM-DD format (default: 15 days ago)
- `end_date` (str, optional): End date in YYYY-MM-DD format (default: today)
- `include_x_handles` (List[str], optional): X handles to include (max 10)
- `exclude_x_handles` (List[str], optional): X handles to exclude (max 10)
- `post_favorites_count` (int, optional): Minimum favorites required
- `post_view_count` (int, optional): Minimum views required
- `max_results` (List[int], optional): Max results per query (default: 15)

**API Key Required**: Yes (`XAI_API_KEY`)

**Rate Limits**: 
- Free tier: 60 requests/minute
- Paid tier: Higher limits based on plan

**Example**:
```python
result = await x_search(
    queries=["AI news", "machine learning"],
    include_x_handles=["@openai", "@anthropicai"],
    post_favorites_count=100
)
```

---

### youtube_search

**Description**: Search YouTube videos and extract transcripts with chapter timestamps using Exa API.

**Parameters**:
- `query` (str): Search query
- `time_range` (str): Time range filter - 'day', 'week', 'month', 'year', or 'anytime' (default: 'week')

**API Key Required**: Yes (`EXA_API_KEY`)

**Rate Limits**: 
- Exa: 1000 requests/month (free tier)
- YouTube Transcript API: No official limit, but rate limiting recommended

**Constraints**:
- Returns up to 5 videos per search
- Transcripts only available for videos with captions
- Processes videos in batches of 5 with 0.5s delay

**Example**:
```python
result = await youtube_search("Python tutorial", time_range="week")
```

---

### reddit_search

**Description**: Search Reddit posts and comments using Tavily API with Reddit domain filtering.

**Parameters**:
- `queries` (List[str]): List of search queries (1-5)
- `max_results` (List[int], optional): Max results per query (default: 20)
- `time_range` (List[str], optional): Time range per query - 'day', 'week', 'month', 'year' (default: 'week')

**API Key Required**: Yes (`TAVILY_API_KEY`)

**Rate Limits**: 
- Tavily: 1000 requests/month (free tier)

**Example**:
```python
result = await reddit_search(
    queries=["python programming", "machine learning"],
    max_results=[30, 20],
    time_range=["week", "month"]
)
```

---

### academic_search

**Description**: Search academic papers and research articles using Exa API with research paper category filtering.

**Parameters**:
- `queries` (List[str]): List of search queries (1-5)
- `max_results` (List[int], optional): Max results per query (default: 20)

**API Key Required**: Yes (`EXA_API_KEY`)

**Rate Limits**: 
- Exa: 1000 requests/month (free tier)

**Features**:
- Extracts paper abstracts
- Deduplicates by URL
- Cleans titles and summaries

**Example**:
```python
result = await academic_search(
    queries=["quantum computing", "neural networks"],
    max_results=[30, 25]
)
```

---

## Utility Tools

### convert_currency

**Description**: Convert currency from one type to another using live exchange rates.

**Parameters**:
- `amount` (float): Amount to convert (must be positive)
- `from_currency` (str): Source currency code (e.g., "USD", "EUR")
- `to_currency` (str): Target currency code (e.g., "USD", "EUR")

**API Key Required**: No (uses free exchangerate-api.com)

**Rate Limits**: 
- Free tier: 1500 requests/month

**Caching**: Exchange rates cached for 1 hour

**Example**:
```python
result = await convert_currency(100, "USD", "EUR")
```

---

### datetime_operations

**Description**: Perform various datetime operations including timezone conversion, duration calculations, and formatting.

**Parameters**:
- `operation` (str): Type of operation - 'convert_timezone', 'calculate_duration', 'format_date', 'current_time'
- `datetime_str` (str, optional): DateTime string (ISO format)
- `from_timezone` (str, optional): Source timezone
- `to_timezone` (str, optional): Target timezone
- `start_datetime` (str, optional): Start datetime for duration
- `end_datetime` (str, optional): End datetime for duration
- `format_string` (str, optional): Python strftime format
- `timezone` (str, optional): Timezone for current_time

**API Key Required**: No

**Rate Limits**: None

**Example**:
```python
# Convert timezone
result = await datetime_operations(
    operation="convert_timezone",
    datetime_str="2024-01-15T10:30:00",
    from_timezone="America/New_York",
    to_timezone="Europe/London"
)

# Calculate duration
result = await datetime_operations(
    operation="calculate_duration",
    start_datetime="2024-01-15T10:00:00",
    end_datetime="2024-01-15T14:30:00"
)
```

---

### get_weather

**Description**: Get current weather and forecast for a location using OpenWeatherMap API.

**Parameters**:
- `location` (str): Location name or coordinates "lat,lon"
- `forecast_days` (int): Number of forecast days (1-5, default: 1)
- `units` (str): Temperature units - "metric", "imperial", or "standard" (default: "metric")

**API Key Required**: Yes (`OPENWEATHER_API_KEY`)

**Rate Limits**: 
- Free tier: 1000 calls/day, 60 calls/minute

**Caching**: Weather data cached for 30 minutes

**Example**:
```python
result = await get_weather("London", forecast_days=3, units="metric")
```

---

### track_flight

**Description**: Track flight status and information using AviationStack API.

**Parameters**:
- `flight_number` (str): Flight number (e.g., "AA100", "BA456")
- `date` (str, optional): Flight date in YYYY-MM-DD format (default: today)

**API Key Required**: Yes (`AVIATIONSTACK_API_KEY`)

**Rate Limits**: 
- Free tier: 100 requests/month
- Paid tiers: Higher limits based on plan

**Example**:
```python
result = await track_flight("AA100", date="2024-01-15")
```

---

### get_stock_data

**Description**: Get stock market data including price history and basic indicators using yfinance.

**Parameters**:
- `symbol` (str): Stock ticker symbol (e.g., "AAPL", "GOOGL")
- `period` (str): Time period - "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max" (default: "1d")
- `interval` (str): Data interval - "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo" (default: "1h")

**API Key Required**: Optional (`ALPHAVANTAGE_API_KEY` for alternative data source)

**Rate Limits**: 
- yfinance: No official limit, but rate limiting recommended
- Alpha Vantage: 5 requests/minute, 500 requests/day (free tier)

**Constraints**:
- Intraday data (< 1d interval) limited to last 60 days

**Example**:
```python
result = await get_stock_data("AAPL", period="1mo", interval="1d")
```

---

### get_crypto_data

**Description**: Get cryptocurrency price and market data using CoinGecko API.

**Parameters**:
- `symbol` (str): Cryptocurrency symbol or ID (e.g., "bitcoin", "eth")
- `vs_currency` (str): Currency to compare against (default: "usd")
- `include_market_data` (bool): Include detailed market data (default: True)

**API Key Required**: Optional (`COINGECKO_API_KEY` for higher rate limits)

**Rate Limits**: 
- Free tier (no key): 10-30 calls/minute
- With API key: 500 calls/minute

**Example**:
```python
result = await get_crypto_data("bitcoin", vs_currency="usd")
```

---

### get_crypto_market_overview

**Description**: Get overview of top cryptocurrencies by market cap.

**Parameters**:
- `vs_currency` (str): Currency to compare against (default: "usd")
- `top_n` (int): Number of top cryptocurrencies (1-250, default: 10)

**API Key Required**: Optional (`COINGECKO_API_KEY` for higher rate limits)

**Rate Limits**: Same as get_crypto_data

**Example**:
```python
result = await get_crypto_market_overview(vs_currency="usd", top_n=20)
```

---

### geocode_location

**Description**: Geocode an address to coordinates using OpenStreetMap Nominatim.

**Parameters**:
- `address` (str): Address to geocode
- `limit` (int): Maximum results (1-10, default: 1)

**API Key Required**: No (uses free OpenStreetMap Nominatim)

**Rate Limits**: 
- 1 request per second
- Usage policy: https://operations.osmfoundation.org/policies/nominatim/

**Example**:
```python
result = await geocode_location("Eiffel Tower, Paris")
```

---

### reverse_geocode

**Description**: Reverse geocode coordinates to an address using OpenStreetMap Nominatim.

**Parameters**:
- `latitude` (float): Latitude coordinate (-90 to 90)
- `longitude` (float): Longitude coordinate (-180 to 180)
- `zoom` (int): Detail level (3=country, 10=city, 18=building, default: 18)

**API Key Required**: No

**Rate Limits**: Same as geocode_location

**Example**:
```python
result = await reverse_geocode(48.8584, 2.2945)  # Eiffel Tower
```

---

### calculate_distance

**Description**: Calculate distance between two geographic coordinates using Haversine formula.

**Parameters**:
- `lat1` (float): Latitude of first point
- `lon1` (float): Longitude of first point
- `lat2` (float): Latitude of second point
- `lon2` (float): Longitude of second point
- `unit` (str): Distance unit - "km", "miles", "meters" (default: "km")

**API Key Required**: No

**Rate Limits**: None

**Example**:
```python
result = await calculate_distance(48.8584, 2.2945, 40.7580, -73.9855)  # Paris to NYC
```

---

## Tool Configuration

### Enabling/Disabling Tools

Tools can be selectively enabled or disabled using the `ENABLED_TOOLS` environment variable:

```bash
# Enable specific tools (comma-separated)
ENABLED_TOOLS=web_search,code_executor,x_search,youtube_search,weather

# Enable all tools
ENABLED_TOOLS=all

# Disable all optional tools (only core tools)
ENABLED_TOOLS=web_search,code_executor,memory_search
```

### Tool Registry

The tool registry system automatically discovers and registers tools. Tools are registered in `research_agent/tools/__init__.py`:

```python
from research_agent.clients.tool_registry import get_tool_registry

# Tools are automatically registered when imported
registry = get_tool_registry()
enabled_tools = registry.get_enabled_tools()
```

### Configuration Validation

The system validates that required API keys are present for enabled tools:

```python
from research_agent.utils.config import get_config

config = get_config()
# Raises ValueError if required keys are missing for enabled tools
```

---

## Rate Limits and Constraints

### General Guidelines

1. **Respect API Rate Limits**: All tools implement rate limiting and retry logic
2. **Use Caching**: Tools cache results where appropriate to reduce API calls
3. **Batch Processing**: Multi-query tools process requests in parallel with concurrency limits
4. **Error Handling**: Tools return empty results on failure instead of raising exceptions

### Rate Limit Summary

| Tool | Free Tier Limit | Caching | Notes |
|------|----------------|---------|-------|
| web_search (Exa) | 1000/month | No | Best for comprehensive search |
| web_search (Tavily) | 1000/month | No | Best for news/real-time |
| x_search | 60/minute | No | Requires xAI API key |
| youtube_search | 1000/month | 1 hour | Uses Exa API |
| reddit_search | 1000/month | No | Uses Tavily API |
| academic_search | 1000/month | No | Uses Exa API |
| convert_currency | 1500/month | 1 hour | Free, no key required |
| get_weather | 1000/day | 30 min | 60 calls/minute |
| track_flight | 100/month | No | Very limited free tier |
| get_stock_data | Unlimited* | No | *Rate limiting recommended |
| get_crypto_data | 10-30/minute | No | Higher with API key |
| geocode_location | 1/second | No | OpenStreetMap policy |

### Concurrency Limits

- Multi-query tools: Maximum 5 concurrent requests
- YouTube video processing: Batch size of 5 with 0.5s delay
- All tools: Exponential backoff on rate limit errors

---

## Troubleshooting Guide

### Common Issues

#### API Key Errors

**Problem**: `ValueError: API key for X is required`

**Solution**: 
1. Check that the API key is set in your `.env` file
2. Verify the key is valid and not expired
3. Ensure the tool is enabled in `ENABLED_TOOLS`

```bash
# Check your .env file
cat .env | grep XAI_API_KEY

# Test with a simple query
python -c "from research_agent.utils.config import get_config; print(get_config().xai_api_key)"
```

#### Rate Limit Errors

**Problem**: `429 Too Many Requests` or rate limit exceeded

**Solution**:
1. Wait before retrying (tools implement exponential backoff)
2. Reduce the number of concurrent requests
3. Enable caching where available
4. Consider upgrading to a paid API tier

```python
# Reduce concurrent requests
config.max_concurrent_requests = 3

# Enable debug logging to see rate limit details
LOG_LEVEL=DEBUG
```

#### Empty Results

**Problem**: Tool returns empty results or no data

**Solution**:
1. Check that the query is valid and specific enough
2. Verify the API service is operational
3. Check API key permissions and quotas
4. Review logs for detailed error messages

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python main.py "your query" --log-level DEBUG
```

#### Transcript Not Available (YouTube)

**Problem**: YouTube videos return without transcripts

**Solution**:
- Not all videos have captions/transcripts available
- Try searching for videos with "CC" (closed captions)
- Check if the video has auto-generated captions enabled
- This is a limitation of the YouTube platform, not the tool

#### Location Not Found (Geocoding)

**Problem**: Geocoding returns "Location not found"

**Solution**:
1. Make the address more specific (include city, country)
2. Try alternative address formats
3. Use coordinates if address is ambiguous
4. Check for typos in the address

```python
# Instead of "Main Street"
result = await geocode_location("123 Main Street, Springfield, MA, USA")

# Or use coordinates directly
result = await reverse_geocode(42.1015, -72.5898)
```

#### Stock Symbol Not Found

**Problem**: Stock data returns "Symbol not found"

**Solution**:
1. Verify the ticker symbol is correct
2. Use the exchange-specific symbol if needed (e.g., "AAPL" not "Apple")
3. Check if the stock is publicly traded
4. Try searching on Yahoo Finance first to confirm the symbol

#### Cryptocurrency Not Found

**Problem**: Crypto data returns "Cryptocurrency not found"

**Solution**:
1. Use the full name (e.g., "bitcoin" instead of "BTC")
2. Check the symbol mapping in the tool documentation
3. Search on CoinGecko.com to find the correct ID
4. Common mappings: btc→bitcoin, eth→ethereum, sol→solana

### Debug Mode

Enable comprehensive logging for troubleshooting:

```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Or in .env file
LOG_LEVEL=DEBUG

# Run with debug output
python main.py "your query" --log-level DEBUG 2>&1 | tee debug.log
```

### Getting Help

1. **Check Logs**: Review application logs for detailed error messages
2. **API Status**: Check the status page of the API service
3. **Documentation**: Review the API provider's documentation
4. **GitHub Issues**: Search for similar issues or create a new one
5. **API Support**: Contact the API provider's support team

### Performance Tips

1. **Use Caching**: Enable caching for frequently accessed data
2. **Batch Requests**: Use multi-query tools to process multiple queries efficiently
3. **Selective Tools**: Only enable tools you need to reduce overhead
4. **Rate Limiting**: Implement delays between requests if hitting rate limits
5. **Async Operations**: Tools use async/await for optimal performance

---

## Additional Resources

- [API Documentation](docs/API.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Requirements Document](.kiro/specs/tool-integration/requirements.md)
- [Design Document](.kiro/specs/tool-integration/design.md)

For more information or support, please open an issue on GitHub.
