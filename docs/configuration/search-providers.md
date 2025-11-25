# Search Providers Configuration

This document covers the configuration and usage of different search providers in the Deep Research Agent.

## Supported Search Providers

### 1. Exa (Recommended)
**Best for**: Comprehensive web search with high-quality content retrieval

**Features:**
- Advanced content extraction
- Intelligent result ranking
- Academic and professional content
- High-quality source attribution

**Configuration:**
```bash
# Environment variable
EXA_API_KEY=your_exa_api_key

# Set as default provider
SEARCH_PROVIDER=exa
```

**Rate Limits:**
- Free Tier: 1,000 requests/month
- Higher tiers available

**Strengths:**
- Best content quality
- Comprehensive coverage
- Good for research and academic content

**Weaknesses:**
- Limited free tier
- Slower response times for complex queries

### 2. Tavily
**Best for**: News, real-time information, and current events

**Features:**
- Real-time search results
- News article prioritization
- Social media integration
- Fast response times

**Configuration:**
```bash
# Environment variable
TAVILY_API_KEY=your_tavily_api_key

# Set as default provider
SEARCH_PROVIDER=tavily
```

**Rate Limits:**
- Free Tier: 1,000 requests/month

**Strengths:**
- Excellent for current events
- Fast response times
- Good news source coverage

**Weaknesses:**
- Limited historical content
- Less comprehensive than Exa

### 3. Firecrawl
**Best for**: Web scraping and content extraction from specific URLs

**Features:**
- Advanced web scraping
- JavaScript rendering
- Content cleaning
- Bulk URL processing

**Configuration:**
```bash
# Environment variable
FIRECRAWL_API_KEY=your_firecrawl_api_key

# Set as default provider
SEARCH_PROVIDER=firecrawl
```

**Rate Limits:**
- Varies by plan

**Strengths:**
- Excellent for specific websites
- Handles dynamic content
- Clean content extraction

**Weaknesses:**
- Slower for general search
- More expensive for large-scale use

### 4. Parallel AI
**Best for**: AI-powered search with quality options

**Features:**
- AI-enhanced search results
- Quality filtering options
- Advanced relevance ranking
- Multiple search modes

**Configuration:**
```bash
# Environment variable
PARALLEL_API_KEY=your_parallel_api_key

# Set as default provider
SEARCH_PROVIDER=parallel
```

**Rate Limits:**
- Varies by plan

**Strengths:**
- Advanced AI features
- Quality control options
- Good for specific domains

**Weaknesses:**
- More complex configuration
- Higher cost

## Configuration Examples

### Basic Setup with Exa
```bash
# .env file
OPENAI_API_KEY=sk-...
EXA_API_KEY=your_exa_key
SEARCH_PROVIDER=exa
ENABLED_TOOLS=web_search,code_executor,memory_search
```

### Multi-Provider Setup
```bash
# .env file
OPENAI_API_KEY=sk-...
EXA_API_KEY=your_exa_key
TAVILY_API_KEY=your_tavily_key
SEARCH_PROVIDER=exa  # Primary provider
```

### Real-time News Setup with Tavily
```bash
# .env file
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=your_tavily_key
SEARCH_PROVIDER=tavily
ENABLED_TOOLS=web_search,x_search,reddit_search
```

### Web Scraping Setup with Firecrawl
```bash
# .env file
OPENAI_API_KEY=sk-...
FIRECRAWL_API_KEY=your_firecrawl_key
SEARCH_PROVIDER=firecrawl
ENABLED_TOOLS=web_search,code_executor,academic_search
```

## Provider Selection Guidelines

### Choose Exa when:
- You need comprehensive research
- Quality of content is most important
- Academic or professional research
- You have budget for API calls

### Choose Tavily when:
- Real-time information is critical
- News and current events focus
- Faster response times needed
- Limited budget

### Choose Firecrawl when:
- Specific website content needed
- Dynamic content extraction
- Web scraping requirements
- Bulk URL processing

### Choose Parallel AI when:
- Advanced AI features needed
- Quality control is important
- Specific domain expertise
- Complex search requirements

## Runtime Provider Switching

### Via Environment Variable
```python
import os
from research_agent.agent.research_agent import DeepResearchAgent
from langchain_openai import ChatOpenAI

# Switch to Tavily for current events
os.environ["SEARCH_PROVIDER"] = "tavily"

llm = ChatOpenAI(model="gpt-4o-mini")
agent = DeepResearchAgent(llm=llm)
```

### Via Configuration
```python
from research_agent.agent.research_agent import DeepResearchAgent

# Specify provider during agent creation
llm = ChatOpenAI(model="gpt-4o-mini")

# Use different providers for different use cases
general_agent = DeepResearchAgent(llm=llm, search_provider="exa")
news_agent = DeepResearchAgent(llm=llm, search_provider="tavily")
scraping_agent = DeepResearchAgent(llm=llm, search_provider="firecrawl")
```

## Provider-Specific Features

### Exa Features

#### Category Filtering
```python
# Exa supports category-based search
results = await web_search(
    query="machine learning",
    category="research"  # research, news, wikipedia, etc.
)
```

#### Content Enrichment
- Automatic content extraction
- Metadata enrichment
- Source attribution

#### Domain Filtering
```python
# Search specific domains
results = await web_search(
    query="AI research",
    include_domains=["arxiv.org", "nature.com"]
)
```

### Tavily Features

#### Time-based Search
```python
# Recent results only
results = await web_search(
    query="technology news",
    time_range="day"  # day, week, month, year
)
```

#### News Focus
- Real-time news indexing
- Social media integration
- Trending topics

### Firecrawl Features

#### URL-specific Search
```python
# Search specific URLs
results = await web_search(
    query="content analysis",
    urls=["https://example.com/article"]
)
```

#### JavaScript Rendering
- Dynamic content extraction
- Single-page application support
- Heavy web page processing

## Performance Comparison

| Provider | Speed | Content Quality | Cost | Best For |
|----------|-------|----------------|------|----------|
| Exa | Medium | High | Medium | Research, Academic |
| Tavily | Fast | Good | Low | News, Current Events |
| Firecrawl | Slow | Variable | High | Web Scraping |
| Parallel AI | Medium | High | High | AI-enhanced Search |

## Fallback Configuration

### Primary with Fallback
```python
from research_agent.strategies.factory import SearchStrategyFactory

# Configure fallback chain
factory = SearchStrategyFactory()
factory.set_primary("exa")
factory.set_fallback("tavily")

# Will try exa first, then tavily on failure
search_strategy = factory.create_strategy()
```

### Load Balancing
```python
# Round-robin between providers
providers = ["exa", "tavily", "exa"]
for i, query in enumerate(queries):
    provider = providers[i % len(providers)]
    os.environ["SEARCH_PROVIDER"] = provider
    # Process query with current provider
```

## Testing Search Providers

### Provider Test Script
```python
import asyncio
import os
from research_agent.strategies.factory import SearchStrategyFactory

async def test_provider(provider_name):
    """Test a specific search provider"""
    os.environ["SEARCH_PROVIDER"] = provider_name

    try:
        factory = SearchStrategyFactory()
        strategy = factory.create_strategy()

        results = await strategy.search(
            query="artificial intelligence",
            max_results=5
        )

        print(f"✅ {provider_name}: Found {len(results)} results")
        for result in results[:2]:
            print(f"   - {result.title[:50]}...")

        return True

    except Exception as e:
        print(f"❌ {provider_name}: Error - {e}")
        return False

async def test_all_providers():
    """Test all configured providers"""
    providers = ["exa", "tavily", "firecrawl", "parallel"]

    for provider in providers:
        await test_provider(provider)

if __name__ == "__main__":
    asyncio.run(test_all_providers())
```

## Troubleshooting Search Providers

### Common Issues

#### API Key Errors
```
ValueError: API key for search provider 'exa' is required
```
**Solution**: Set the appropriate API key environment variable

#### Provider Not Available
```
ValueError: Search provider 'unknown' not supported
```
**Solution**: Use one of the supported providers: exa, tavily, firecrawl, parallel

#### Rate Limiting
```
429 Too Many Requests
```
**Solution**:
- Implement retry logic
- Reduce request frequency
- Upgrade API plan

#### Empty Results
```
No results found for query
```
**Solution**:
- Check query specificity
- Try different provider
- Verify API permissions

### Debug Mode
```bash
# Enable debug logging for search operations
export LOG_LEVEL=DEBUG

# Run with verbose output
python main.py "test query" --log-level DEBUG
```

## Best Practices

### 1. Choose the Right Provider
- Match provider to use case
- Consider cost constraints
- Evaluate performance requirements

### 2. Handle Failures Gracefully
- Implement fallback mechanisms
- Use retry logic with exponential backoff
- Monitor provider health

### 3. Optimize for Cost
- Use appropriate max_results limits
- Implement caching for repeated queries
- Monitor usage patterns

### 4. Quality Control
- Validate search results
- Filter low-quality sources
- Use domain filtering when appropriate

### 5. Performance Optimization
- Use async operations
- Implement request batching
- Cache frequently accessed content

## Monitoring and Metrics

### Track Provider Performance
```python
import time
from research_agent.utils.logger import get_logger

logger = get_logger(__name__)

async def timed_search(provider, query):
    start_time = time.time()

    try:
        results = await search_with_provider(provider, query)
        duration = time.time() - start_time

        logger.info(f"{provider}: {len(results)} results in {duration:.2f}s")

        return results

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"{provider}: Failed after {duration:.2f}s - {e}")

        raise
```

### Usage Analytics
- Track request volumes per provider
- Monitor response times
- Analyze success/failure rates
- Optimize provider selection based on performance