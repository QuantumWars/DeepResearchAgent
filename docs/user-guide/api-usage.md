# API Usage Guide

This guide covers how to use the Deep Research Agent REST API and Python API.

## Starting the API Server

### Development Mode
```bash
python -m research_agent.api.main
```

### Production Mode with uvicorn
```bash
uvicorn research_agent.api.main:app --host 0.0.0.0 --port 8000
```

### Docker
```bash
docker-compose up
```

## REST API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Streaming Research
```bash
curl -X POST http://localhost:8000/research/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "What is quantum computing?", "user_id": "user123"}' \
  --no-buffer
```

#### Response Format (Server-Sent Events)
```
data: {"type": "start", "query": "What is quantum computing?"}

data: {"type": "tool_start", "tool": "web_search", "input": "quantum computing basics"}

data: {"type": "tool_end", "output": "[SearchResult(...)]"}

data: {"type": "complete", "result": {...}}
```

### Non-Streaming Research
```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "AI trends 2024", "user_id": "user456"}'
```

## Python API Usage

### Basic Usage
```python
import asyncio
from langchain_openai import ChatOpenAI
from research_agent.agent.research_agent import DeepResearchAgent

async def main():
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    # Create agent
    agent = DeepResearchAgent(llm=llm)

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

asyncio.run(main())
```

### Advanced Usage with Custom Configuration

```python
from research_agent.agent.research_agent import DeepResearchAgent
from research_agent.memory.supermemory_client import SupermemoryClient
from research_agent.utils.config import get_config
from langchain_openai import ChatOpenAI

async def advanced_research():
    # Load configuration
    config = get_config()

    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o-mini")

    # Initialize memory client (optional)
    memory = SupermemoryClient()

    # Create agent with custom settings
    agent = DeepResearchAgent(
        llm=llm,
        search_provider=config.search_provider,
        memory_client=memory
    )

    # Execute research with streaming
    result = await agent.research(
        query="Latest developments in AI",
        user_id="research_user"
    )

    return result
```

### Tool Registry Integration

```python
from research_agent.clients.tool_registry import get_tool_registry

async def tool_management_example():
    # Get the tool registry
    registry = get_tool_registry()

    # List all available tools
    all_tools = registry.list_all_tools()
    print("Available tools:", list(all_tools.keys()))

    # Enable/disable tools
    registry.enable_tool("x_search")
    registry.disable_tool("flight_tracker")

    # Get enabled tools
    enabled_tools = registry.get_enabled_tools()
    print(f"Enabled tools: {len(enabled_tools)}")
```

### Configuration-Based Tool Control

```python
import os
from research_agent.agent.research_agent import DeepResearchAgent
from langchain_openai import ChatOpenAI

# Set enabled tools via environment
os.environ["ENABLED_TOOLS"] = "web_search,x_search,youtube_search,academic_search"

async def selective_tools_research():
    llm = ChatOpenAI(model="gpt-4o-mini")

    # Agent will only use enabled tools
    agent = DeepResearchAgent(llm=llm)

    result = await agent.research(
        "AI research on social media platforms",
        user_id="social_media_user"
    )

    return result
```

## Error Handling

```python
import asyncio
from research_agent.agent.research_agent import DeepResearchAgent
from research_agent.utils.config import get_config
from langchain_openai import ChatOpenAI

async def robust_research():
    try:
        # Validate configuration first
        config = get_config()

        # Initialize agent
        llm = ChatOpenAI(model="gpt-4o-mini")
        agent = DeepResearchAgent(llm=llm)

        # Execute research
        result = await agent.research("Your query here")

        return result

    except ValueError as e:
        print(f"Configuration error: {e}")
        # Handle missing API keys or invalid configuration
    except Exception as e:
        print(f"Research error: {e}")
        # Handle other research errors

# Usage
asyncio.run(robust_research())
```

## Client Libraries

### JavaScript/TypeScript Example

```javascript
class ResearchAgentClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    async research(query, userId = null) {
        const response = await fetch(`${this.baseUrl}/research`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query,
                user_id: userId
            })
        });

        if (!response.ok) {
            throw new Error(`Research failed: ${response.statusText}`);
        }

        return await response.json();
    }

    async streamResearch(query, userId = null, onData, onComplete, onError) {
        const response = await fetch(`${this.baseUrl}/research/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query,
                user_id: userId
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));

                            if (data.type === 'complete') {
                                onComplete(data.result);
                            } else if (onData) {
                                onData(data);
                            }
                        } catch (e) {
                            console.error('Error parsing SSE data:', e);
                        }
                    }
                }
            }
        } catch (error) {
            if (onError) onError(error);
        }
    }
}

// Usage
const client = new ResearchAgentClient();

// Non-streaming
const result = await client.research("What is quantum computing?");

// Streaming
await client.streamResearch(
    "AI trends 2024",
    "user123",
    (data) => console.log('Progress:', data),
    (result) => console.log('Complete:', result),
    (error) => console.error('Error:', error)
);
```

## Rate Limiting and Performance

### Best Practices
1. **Batch Requests**: Use streaming for real-time updates
2. **Cache Results**: Implement client-side caching for repeated queries
3. **Error Handling**: Implement retry logic with exponential backoff
4. **Connection Pooling**: Reuse HTTP connections for multiple requests

### Rate Limit Information
See the [Tool Catalog](../tools/tool-catalog.md#rate-limits-and-constraints) for detailed rate limit information.

## Security Considerations

- **API Keys**: Never expose API keys in client-side code
- **Input Validation**: Validate all user inputs before processing
- **Rate Limiting**: Implement client-side rate limiting to prevent abuse
- **HTTPS**: Use HTTPS in production environments

## Testing the API

```bash
# Health check
curl http://localhost:8000/health

# Simple research
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}'

# With user ID
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "user_id": "test_user"}'
```