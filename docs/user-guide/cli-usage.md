# CLI Usage Guide

This guide covers how to use the Deep Research Agent from the command line interface.

## Basic Usage

```bash
python main.py "What is quantum computing?"
```

## Command Line Options

### Basic Options

- `query`: The research question or topic (required)
- `--provider`: Search provider to use (exa, tavily, firecrawl, parallel)
- `--user-id`: User ID for memory isolation (optional)
- `--format`: Output format (text, json) - default: text
- `--output`: Save results to file
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Examples

#### Basic Research
```bash
# Simple research query
python main.py "What is quantum computing?"

# With specific search provider
python main.py "AI trends 2024" --provider tavily

# With user ID for memory
python main.py "Machine learning basics" --user-id user123
```

#### Output Options
```bash
# JSON output format
python main.py "Climate change" --format json

# Save to file
python main.py "Python async" --output results.txt
```

#### Debug Mode
```bash
# Enable debug logging
python main.py "Research topic" --log-level DEBUG
```

## Environment Variables

The CLI respects all environment variables defined in the [Configuration Guide](../configuration/environment-variables.md).

## Output Formats

### Text Format (Default)
```
Research Query: What is quantum computing?

Sources:
1. [Title] - URL

Findings:
[Comprehensive research summary...]
```

### JSON Format
```json
{
  "query": "What is quantum computing?",
  "text": "Research findings...",
  "sources": [...],
  "execution_time": 45.2
}
```

## Troubleshooting

See the [Tool Catalog](../tools/tool-catalog.md#troubleshooting-guide) for troubleshooting common issues.

## Integration with Scripts

### Bash Script
```bash
#!/bin/bash
QUERY="Latest AI developments"
OUTPUT="ai_research_$(date +%Y%m%d).txt"

python main.py "$QUERY" --output "$OUTPUT" --format json
echo "Research saved to $OUTPUT"
```

### Python Script
```python
import subprocess
import json

def run_research(query):
    result = subprocess.run([
        'python', 'main.py', query, '--format', 'json'
    ], capture_output=True, text=True)

    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        raise Exception(f"Research failed: {result.stderr}")

# Usage
research_result = run_research("quantum computing applications")
print(f"Found {len(research_result['sources'])} sources")
```