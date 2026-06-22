# Deep Research Agent

A plugin-based agentic research framework built on [LangGraph](https://github.com/langchain-ai/langgraph). It decomposes a research question into sub-questions, retrieves and scrapes information from multiple sources, checks its own work for gaps, and synthesizes a structured, cited report — with every search provider, scraper, and LLM backend swappable through configuration.

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![LangGraph](https://img.shields.io/badge/orchestration-LangGraph-6f42c1)
![Status](https://img.shields.io/badge/status-active--development-yellow)

## Table of Contents

- [Why This Exists](#why-this-exists)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration Guide](#configuration-guide)
- [Adding Custom Tools](#adding-custom-tools)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Why This Exists

Most "research agent" scripts hard-code a single search API and a single model. This framework treats every external dependency — search, scraping, and LLM inference — as a pluggable, prioritized, fallback-capable tool, so a provider outage or missing API key degrades gracefully instead of breaking the run. The orchestration itself (planning → retrieval → reflection → synthesis) is a LangGraph state machine that knows nothing about which concrete tools it's calling.

## Features

- **Plugin architecture** — swap search providers, scrapers, and LLM backends entirely through YAML configuration, no code changes required.
- **Automatic fallback** — each tool category (search, scraper, LLM) has a priority-ordered fallback chain; if the top tool fails, the next one is tried automatically.
- **Iterative research loop** — the agent plans, retrieves, reflects on what's missing, and loops back to retrieval until the report is complete or `max_loops` is hit.
- **Structured citations** — reports carry inline `[n]` citations backed by a `Citation` model with URL, title, excerpt, and access timestamp.
- **Model routing** — routes planning/reflection/synthesis to different LLM tiers (`fast` / `balanced` / `powerful`) via [LiteLLM](https://github.com/BerriAI/litellm), so cheaper models handle cheaper steps.
- **Drop-in custom tools** — add a file to `tools/custom/`, subclass a base tool, and it's auto-discovered on startup.

## Architecture

The framework is organized into four layers:

1. **Core orchestration** (`core/`) — a tool-agnostic LangGraph state machine that drives the research loop.
2. **Tool registry** (`registry/`) — discovers, prioritizes, and selects tools, with fallback-chain resolution.
3. **Tool implementations** (`tools/`) — concrete search, scraper, LLM, and custom tool adapters.
4. **Data models** (`models/`) — Pydantic schemas for citations and tool I/O, so every tool boundary is type-checked.

### Research Workflow

```
Query → Planning → Retrieval → Reflection → Synthesis → Report
                       ↑            ↓
                       └─ (if gaps) ─┘
```

1. **Planning** — decomposes the query into 3–5 sub-questions using a fast LLM.
2. **Retrieval** — searches and scrapes content for each sub-question, trying tools down the fallback chain as needed.
3. **Reflection** — evaluates completeness against the original query and identifies remaining gaps.
4. **Synthesis** — once the reflection step is satisfied (or `max_loops` is reached), a powerful LLM generates the final cited report.

## Installation

### Prerequisites

- Python 3.8+
- pip (or conda)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/QuantumWars/DeepResearchAgent.git
cd DeepResearchAgent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install Playwright browsers (needed for JS-heavy sites)
playwright install

# 4. Configure API keys
cp .env.example .env
```

Then edit `.env` with the providers you plan to use:

```bash
# Search (at least one required)
TAVILY_API_KEY=your_tavily_key_here
SERPER_API_KEY=your_serper_key_here

# LLM (at least one required)
OPENAI_API_KEY=your_openai_key_here
# or
ANTHROPIC_API_KEY=your_anthropic_key_here
```

## Quick Start

### Command Line

```bash
# Basic research query
python main.py "What is quantum computing?"

# Save the report to a file
python main.py "Explain climate change" --output report.md

# Cap the number of retrieval/reflection loops
python main.py "AI safety research" --max-loops 2

# Verbose logging for debugging
python main.py "Machine learning basics" --verbose
```

### Programmatic Usage

```python
from core.orchestrator import ResearchOrchestrator

orchestrator = ResearchOrchestrator("config/tool_config.yaml")

result = orchestrator.research(
    query="What is quantum computing?",
    max_loops=3
)

print(result.report)
print(f"Sources: {len(result.sources)}")
print(f"Tool calls: {len(result.execution_log)}")

result.save("reports/quantum_computing.md")

for citation in result.get_citations():
    print(f"[{citation.id}] {citation.title} - {citation.url}")
```

### Using Custom Tools

```python
from core.orchestrator import ResearchOrchestrator
from registry.base_tool import BaseCustomTool

class PDFExtractor(BaseCustomTool):
    name = "pdf_extractor"
    description = "Extracts text from PDF files"

    def execute(self, input_data):
        url = input_data.get("url")
        # ... extraction logic ...
        return {"success": True, "content": extracted_text}

orchestrator = ResearchOrchestrator()
result = orchestrator.research(
    query="Research question",
    custom_tools=[PDFExtractor()]
)
```

## Configuration Guide

All tool selection, priority, and fallback behavior lives in `config/tool_config.yaml`.

### Search Tools

```yaml
search_tools:
  fallback_chain:      # tried in order until one succeeds
    - tavily
    - serper

  tavily:
    enabled: true
    priority: 10        # higher = tried first
    api_key: env:TAVILY_API_KEY
    extra_params:
      search_depth: basic  # or 'advanced'
      max_results: 5
```

Available: `tavily` (fast, AI-optimized — recommended), `serper` (Google Search API).

### Scraper Tools

```yaml
scraper_tools:
  fallback_chain:
    - trafilatura
    - playwright

  trafilatura:
    enabled: true
    priority: 10
    extra_params:
      include_tables: true
      deduplicate: true

  playwright:
    enabled: true
    priority: 5
    extra_params:
      headless: true
      timeout: 30000
      wait_for: networkidle
```

Available: `trafilatura` (fast, lightweight, for standard sites), `playwright` (full browser automation, for JS-heavy sites).

### LLM Tools

```yaml
llm_tools:
  routing:
    fast: gpt-3.5-turbo             # planning
    balanced: gpt-4-turbo-preview   # reflection
    powerful: gpt-4                 # synthesis

  provider: litellm
  extra_params:
    temperature: 0.7
    max_tokens: 4000
```

Supported providers (via LiteLLM): OpenAI, Anthropic, Cohere, and anything else LiteLLM speaks.

### Workflow Settings

```yaml
workflow:
  max_loops: 3              # maximum research iterations
  max_documents: 20         # maximum documents to retrieve
  max_scrape_size: 102400   # max bytes per page (100KB)
  tool_timeout: 30          # timeout per tool call (seconds)
```

### Environment Variables

`config/tool_config.yaml` references secrets with an `env:VAR_NAME` syntax, resolved from `.env`:

```bash
TAVILY_API_KEY=tvly-xxxxx
SERPER_API_KEY=xxxxx
OPENAI_API_KEY=sk-xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx
COHERE_API_KEY=xxxxx
```

## Adding Custom Tools

Drop a file in `tools/custom/` and subclass the appropriate base:

```python
# tools/custom/my_tool.py
from registry.base_tool import BaseCustomTool
import logging

logger = logging.getLogger(__name__)

class MyCustomTool(BaseCustomTool):
    """Description of what your tool does."""

    name = "my_tool"
    description = "Custom tool for specific task"

    def __init__(self, api_key=None, extra_params=None):
        self.api_key = api_key
        self.config = extra_params or {}
        logger.info(f"Initialized {self.name}")

    def execute(self, input_data):
        try:
            result = self._process(input_data)
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"{self.name} failed: {e}")
            return {"success": False, "error": str(e)}
```

No manual registration needed — the registry discovers and registers tools on startup. Optionally add config for it under `custom_tools:` in `tool_config.yaml`. Pick the right base class:

- `BaseSearchTool` — search providers
- `BaseScraperTool` — web scrapers
- `BaseLLMTool` — LLM integrations
- `BaseCustomTool` — everything else

See `examples/custom_tool_example.py` for a complete walkthrough.

## API Reference

### `ResearchOrchestrator`

```python
class ResearchOrchestrator:
    def __init__(self, config_path: str = "config/tool_config.yaml")

    def research(
        self,
        query: str,
        custom_tools: Optional[List[BaseTool]] = None,
        max_loops: int = 3
    ) -> ResearchResult
```

### `ResearchResult`

```python
class ResearchResult:
    report: str                 # markdown report with citations
    sources: List[dict]         # source documents
    execution_log: List[dict]   # tool execution history

    def save(self, filepath: str) -> None
    def get_citations(self) -> List[Citation]
```

### `ToolRegistry`

```python
class ToolRegistry:
    def register_tool(self, tool_instance: BaseTool, category: str, priority: Optional[int] = None) -> None
    def get_tool(self, category: str, name: Optional[str] = None) -> Optional[BaseTool]
    def get_tool_chain(self, category: str) -> List[BaseTool]

    @classmethod
    def from_config(cls, config_path: str) -> "ToolRegistry"

    def discover_tools(self, tools_directory: str = "tools") -> int
```

## Project Structure

```
DeepResearchAgent/
├── core/                      # Core orchestration layer
│   ├── orchestrator.py        # ResearchOrchestrator / ResearchResult
│   ├── graph.py                # LangGraph workflow definition
│   ├── workflow_nodes.py      # Planning/retrieval/reflection/synthesis nodes
│   └── state.py                # Shared research state
├── registry/                  # Tool registry system
│   ├── tool_registry.py       # Discovery, priority, fallback chains
│   └── base_tool.py            # Abstract base classes
├── tools/                     # Tool implementations
│   ├── search/                 # tavily_search.py, serper_search.py
│   ├── scraper/                # trafilatura_scraper.py, playwright_scraper.py
│   ├── llm/                    # litellm_tool.py
│   └── custom/                 # Your custom tools go here
├── models/                    # Pydantic schemas
│   └── tool_schemas.py
├── config/
│   └── tool_config.yaml
├── utils/                     # Config loading, logging, formatting helpers
├── examples/                  # Runnable usage examples
├── main.py                    # CLI entry point
├── requirements.txt
└── .env.example
```

## Testing

```bash
# End-to-end execution smoke test
python test_execution.py

# Usage examples double as integration checks
python examples/basic_research.py
python examples/custom_tool_example.py
python examples/test_orchestrator.py
```

See `TEST_RESULTS.md` and `test_report.md` for the latest recorded run output.

## Troubleshooting

**`Tool 'tavily' failed: API key not found`**
Check that `.env` exists, contains `TAVILY_API_KEY=tvly-xxxxx`, and that the process was restarted after adding it.

**All search tools failing**
Verify API key validity, internet connectivity, and rate limits; rerun with `--verbose` to see per-tool logs.

**Playwright scraper timing out**
Raise `timeout` under `playwright.extra_params` in `tool_config.yaml`, fall back to `trafilatura` for simpler sites, or check whether the target blocks automation.

**`ModuleNotFoundError: No module named 'langgraph'`**
`pip install -r requirements.txt`.

**`playwright._impl._api_types.Error: Executable doesn't exist`**
`playwright install`.

**Empty report**
Make the query more specific, confirm at least one search tool is healthy, check the verbose logs, or raise `--max-loops`.

**Research is slow**
Lower `max_loops`, reduce `max_results` on search tools, use faster models in `llm_tools.routing`, or trim the fallback chains.

Enable verbose logging for any of the above:

```bash
python main.py "query" --verbose
```

## Contributing

Contributions are welcome. Areas that could use help:

- Additional search providers (Brave, Bing, etc.)
- More scraper implementations
- New custom node implementations
- Performance optimizations
- Documentation improvements

Design docs live under `.kiro/specs/deep-research-framework/` if you want the full requirements/design/task breakdown behind the current implementation.

## License

No formal license has been selected yet. All rights reserved by QuantumWars until one is chosen — open an issue if you need clarification for a specific use case.
