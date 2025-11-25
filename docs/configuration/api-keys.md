# API Keys Setup Guide

This guide helps you obtain and configure API keys for all supported services.

## Required API Keys

You need at least one LLM provider and one search provider to use the Deep Research Agent.

### LLM Providers

#### OpenAI (Recommended)
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to [API Keys](https://platform.openai.com/api-keys)
4. Click "Create new secret key"
5. Copy the key (starts with `sk-`)

```bash
OPENAI_API_KEY=sk-...
```

#### Anthropic Claude
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to [API Keys](https://console.anthropic.com/api-keys)
4. Click "Create Key"
5. Copy the key (starts with `sk-ant-`)

```bash
ANTHROPIC_API_KEY=sk-ant-...
```

### Search Providers

#### Exa (Recommended for Comprehensive Search)
1. Go to [Exa API](https://exa.ai/api)
2. Sign up for free account
3. Navigate to API settings
4. Copy your API key

```bash
EXA_API_KEY=...
```

**Free Tier:** 1,000 requests/month

#### Tavily (Good for News/Real-time)
1. Go to [Tavily API](https://tavily.com/api)
2. Sign up for free account
3. Get your API key from dashboard

```bash
TAVILY_API_KEY=...
```

**Free Tier:** 1,000 requests/month

#### Firecrawl (Web Scraping)
1. Go to [Firecrawl](https://firecrawl.dev/)
2. Sign up for free account
3. Get your API key from dashboard

```bash
FIRECRAWL_API_KEY=...
```

#### Parallel AI (AI-powered Search)
1. Go to [Parallel AI](https://parallel.ai/)
2. Sign up for account
3. Get your API key

```bash
PARALLEL_API_KEY=...
```

## Optional API Keys

### Specialized Tools

#### X/Twitter Search (via xAI Grok)
1. Go to [x.ai](https://x.ai/)
2. Sign up for xAI access
3. Navigate to API settings
4. Get your API key

```bash
XAI_API_KEY=...
```

**Rate Limits:** 60 requests/minute (free tier)

#### Weather Data (OpenWeatherMap)
1. Go to [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for free account
3. Get API key from dashboard

```bash
OPENWEATHER_API_KEY=...
```

**Free Tier:** 1,000 calls/day, 60 calls/minute

#### Flight Tracking (AviationStack)
1. Go to [AviationStack](https://aviationstack.com/)
2. Sign up for free account
3. Get API key from dashboard

```bash
AVIATIONSTACK_API_KEY=...
```

**Free Tier:** 100 requests/month

#### Stock Market Data (Alpha Vantage)
1. Go to [Alpha Vantage](https://www.alphavantage.co/)
2. Sign up for free account
3. Get API key

```bash
ALPHAVANTAGE_API_KEY=...
```

**Free Tier:** 5 requests/minute, 500 requests/day

#### Cryptocurrency Data (CoinGecko - Optional)
1. Go to [CoinGecko API](https://www.coingecko.com/en/api)
2. Free tier works without API key
3. For higher limits, sign up and get API key

```bash
# Optional - free tier works without key
COINGECKO_API_KEY=...
```

**Free Tier:** 10-30 calls/minute
**With API Key:** 500 calls/minute

### Memory Storage

#### Supermemory (Optional)
1. Go to [Supermemory](https://supermemory.ai/)
2. Sign up for account
3. Get API key from settings

```bash
SUPERMEMORY_API_KEY=...
SUPERMEMORY_BASE_URL=https://api.supermemory.ai
```

### Map Services (Optional)

#### Google Maps (Optional - Free Alternatives Available)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Maps JavaScript API and Geocoding API
3. Create API key with proper restrictions

```bash
# Optional - free OpenStreetMap used by default
GOOGLE_MAPS_API_KEY=...
```

## Configuration Methods

### Method 1: Environment Variables

```bash
# Linux/macOS
export OPENAI_API_KEY="your-key-here"
export EXA_API_KEY="your-key-here"

# Windows PowerShell
$env:OPENAI_API_KEY="your-key-here"
$env:EXA_API_KEY="your-key-here"
```

### Method 2: .env File

Create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=sk-your-openai-key-here
EXA_API_KEY=your-exa-key-here

# Optional specialized tools
XAI_API_KEY=your-xai-key-here
OPENWEATHER_API_KEY=your-openweather-key-here
AVIATIONSTACK_API_KEY=your-aviationstack-key-here
ALPHAVANTAGE_API_KEY=your-alphavantage-key-here
COINGECKO_API_KEY=your-coingecko-key-here

# Optional memory
SUPERMEMORY_API_KEY=your-supermemory-key-here

# Configuration
SEARCH_PROVIDER=exa
ENABLED_TOOLS=all
LOG_LEVEL=INFO
```

### Method 3: Docker Environment

#### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  research-agent:
    build: .
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - EXA_API_KEY=${EXA_API_KEY}
      - XAI_API_KEY=${XAI_API_KEY}
    env_file:
      - .env
```

#### Docker Run
```bash
docker run \
  -e OPENAI_API_KEY="your-key-here" \
  -e EXA_API_KEY="your-key-here" \
  -v $(pwd)/.env:/app/.env \
  research-agent
```

## Security Best Practices

### 1. Never Commit API Keys
```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
echo "secrets/" >> .gitignore
```

### 2. Use Environment-Specific Keys
```bash
# Development
dev_openai_key="sk-dev-key..."

# Production
prod_openai_key="sk-prod-key..."
```

### 3. Restrict API Key Permissions
- **Least Privilege**: Only enable necessary permissions
- **IP Restrictions**: Restrict to specific IP addresses when possible
- **Usage Limits**: Set appropriate rate limits

### 4. Key Rotation
```python
# Example: Support for key rotation
import os

def get_api_key(service_name):
    primary_key = os.getenv(f"{service_name.upper()}_API_KEY")
    fallback_key = os.getenv(f"{service_name.upper()}_API_KEY_FALLBACK")

    # Try primary key first, then fallback
    return primary_key or fallback_key
```

## Testing API Keys

### Simple Test Script
```python
import os
import asyncio
from research_agent.utils.config import get_config
from research_agent.agent.research_agent import DeepResearchAgent
from langchain_openai import ChatOpenAI

async def test_configuration():
    try:
        # Test configuration loading
        config = get_config()
        print("✅ Configuration loaded successfully")

        # Test LLM connection
        llm = ChatOpenAI(model="gpt-4o-mini")
        response = await llm.ainvoke("Hello")
        print("✅ LLM connection successful")

        # Test search provider
        agent = DeepResearchAgent(llm=llm)
        print("✅ Search provider configured")

        print("🎉 All API keys are working correctly!")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please check your API key configuration")

if __name__ == "__main__":
    asyncio.run(test_configuration())
```

### Test Individual Services
```python
# Test OpenAI
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}]
)
print("OpenAI: ✅")

# Test Exa
import httpx
response = httpx.get(
    "https://api.exa.ai/search",
    params={"query": "test", "numResults": 1},
    headers={"x-api-key": os.getenv("EXA_API_KEY")}
)
print("Exa: ✅")
```

## Troubleshooting API Key Issues

### Common Problems

1. **Invalid API Key**
   ```
   Error: Invalid API key
   ```
   - Check for typos
   - Ensure key is not expired
   - Verify key has correct permissions

2. **Rate Limit Exceeded**
   ```
   Error: Rate limit exceeded
   ```
   - Wait before retrying
   - Check your usage limits
   - Consider upgrading to paid tier

3. **CORS Issues** (Browser only)
   ```
   Error: CORS policy error
   ```
   - Use API backend proxy
   - Check API key permissions

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python main.py "test query" --log-level DEBUG
```

## Cost Considerations

### Free Tiers Summary
| Service | Free Tier | Paid Benefits |
|---------|-----------|---------------|
| OpenAI | $5 credit | Higher limits, faster models |
| Exa | 1,000 requests/month | Higher volume, priority access |
| Tavily | 1,000 requests/month | Higher limits, better search |
| xAI | 60 requests/minute | Higher limits, better models |
| OpenWeather | 1,000 calls/day | Higher limits, historical data |
| AviationStack | 100 requests/month | Higher limits, real-time data |
| Alpha Vantage | 500 requests/day | Higher limits, intraday data |

### Cost Optimization Tips
1. **Use free tiers for development**
2. **Implement caching** to reduce API calls
3. **Choose appropriate tools** for your use case
4. **Monitor usage** regularly
5. **Set up alerts** for unusual usage

## Support

If you encounter issues with API keys:

1. **Check the service status** pages
2. **Review the service documentation**
3. **Contact the service provider's support**
4. **Check your billing status**
5. **Verify key permissions and restrictions**