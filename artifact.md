<create_artifact identifier="deep-research-framework-spec" type="text/markdown" title="Deep Research Framework - Technical Specification">
# Deep Research Framework - Technical Specification

## I. System Architecture Overview

### Design Philosophy
Build a **plugin-based framework** where the core orchestration layer is tool-agnostic. Any search provider, scraper, or custom tool can be registered and swapped without modifying core logic.

### Architectural Layers
```
Layer 1: Core (graph, state, orchestration) - tool-agnostic
Layer 2: Tool Registry (plugin system) - discovers and registers tools
Layer 3: Tool Implementations (search, scraper, custom) - pluggable modules
Layer 4: Models & Schemas (Pydantic contracts) - validation
```

---

## II. Project Structure

```
deep-research-framework/
├── core/
│   ├── graph.py              # StateGraph builder (tool-agnostic)
│   ├── state.py              # State schema
│   ├── nodes.py              # Node implementations (delegates to tools)
│   └── orchestrator.py       # Main execution engine
├── registry/
│   ├── tool_registry.py      # Tool discovery & registration system
│   └── base_tool.py          # Abstract base classes for tools
├── tools/
│   ├── search/
│   │   ├── base_search.py    # Abstract search interface
│   │   ├── tavily.py         # Tavily implementation
│   │   ├── serper.py         # Serper implementation
│   │   └── brave.py          # Brave Search implementation
│   ├── scrapers/
│   │   ├── base_scraper.py   # Abstract scraper interface
│   │   ├── trafilatura_scraper.py
│   │   ├── playwright_scraper.py
│   │   └── beautifulsoup_scraper.py
│   ├── llm/
│   │   ├── base_llm.py       # Abstract LLM interface
│   │   ├── litellm_client.py
│   │   └── langchain_client.py
│   └── custom/               # User can add any custom tools here
│       └── __init__.py
├── models/
│   ├── citations.py          # Pydantic citation models
│   └── tool_schemas.py       # Tool input/output schemas
├── config/
│   ├── settings.py           # Configuration
│   └── tool_config.yaml      # Tool registration config
├── utils/
│   ├── formatters.py
│   └── validators.py
├── examples/
│   └── custom_tool_example.py
├── tests/
├── main.py
├── requirements.txt
└── README.md
```

---

## III. Core Component Specifications

### A. Tool Registry System (`registry/tool_registry.py`)

**Purpose**: Automatic tool discovery, registration, and selection

**Requirements**:
1. **Auto-discovery**: Scan `tools/` directory and register all tools implementing base interfaces
2. **Priority system**: Tools can have priority levels (1-10). Higher priority tried first
3. **Fallback chain**: If Tool A fails, automatically try Tool B
4. **Runtime registration**: Allow adding tools programmatically without restart
5. **Configuration-driven**: Load tool preferences from `tool_config.yaml`

**Key Methods**:
```python
class ToolRegistry:
    def register_tool(tool_class, category, priority)
    def get_tool(category, name=None) -> BaseTool
    def get_all_tools(category) -> List[BaseTool]
    def get_tool_chain(category) -> List[BaseTool]  # Returns fallback chain
```

---

### B. Abstract Base Tool Classes (`registry/base_tool.py`)

**Purpose**: Define contracts that all tools must implement

**Base Classes Needed**:

1. **BaseSearchTool**
   - Method: `search(query: str, max_results: int) -> List[SearchResult]`
   - SearchResult schema: `{url, title, snippet, relevance_score}`
   
2. **BaseScraperTool**
   - Method: `scrape(url: str) -> ScrapedContent`
   - ScrapedContent schema: `{url, content, success, error_msg}`
   
3. **BaseLLMTool**
   - Method: `generate(prompt, model_type, structured_output_schema)`
   - ModelType enum: `FAST, BALANCED, POWERFUL`

4. **BaseCustomTool**
   - Method: `execute(input_data: Dict) -> Dict`
   - For user-defined tools

**All tools must**:
- Inherit from appropriate base class
- Implement required methods
- Handle errors gracefully (return, don't crash)
- Include metadata: `name`, `description`, `priority`, `requires_api_key`

---

### C. Core Nodes (`core/nodes.py`)

**Critical Requirement**: Nodes must NOT import specific tools. They request tools from registry.

**Implementation Pattern**:
```python
# WRONG - hardcoded dependency
from tools.search.tavily import TavilySearch

# CORRECT - registry lookup
search_tool = ToolRegistry.get_tool("search")
```

**Node Specifications**:

1. **planner_node**
   - Gets: Fast LLM from registry
   - Does: Query decomposition
   - Returns: Updated state with research_plan

2. **retrieval_node**
   - Gets: Search tool chain + scraper chain from registry
   - Does: Executes searches, tries scrapers until success
   - Returns: Updated state with retrieved_documents

3. **reflection_node**
   - Gets: Balanced LLM from registry
   - Does: Evaluates completeness
   - Returns: Updated state with gaps_identified

4. **synthesis_node**
   - Gets: Powerful LLM from registry
   - Does: Structured output generation
   - Returns: Final report with citations

---

### D. Configuration System (`config/tool_config.yaml`)

**Purpose**: Declarative tool configuration without code changes

**Structure**:
```yaml
search_tools:
  default: tavily
  fallback_chain:
    - tavily
    - serper
    - brave
  tavily:
    priority: 10
    enabled: true
    api_key: env:TAVILY_API_KEY
  serper:
    priority: 5
    enabled: true
    api_key: env:SERPER_API_KEY

scraper_tools:
  default: trafilatura
  fallback_chain:
    - trafilatura
    - playwright
  trafilatura:
    priority: 10
    enabled: true
  playwright:
    priority: 3
    enabled: true
    headless: true

llm_tools:
  routing:
    fast: gpt-4o-mini
    balanced: gpt-4o-mini
    powerful: gpt-4o
  provider: litellm
```

**The system reads this at startup and configures the registry accordingly.**

---

## IV. Implementation Requirements

### 1. State Management (`core/state.py`)

**Must use TypedDict with these exact fields**:
- `original_query: str`
- `research_plan: Optional[List[str]]`
- `gaps_identified: Optional[str]`
- `retrieved_documents: List[Dict]`
- `research_loop_count: int`
- `final_report: Optional[str]`

Add `tool_execution_log: List[Dict]` for debugging which tools were used.

---

### 2. Tool Implementation Pattern

**Every tool file must follow this structure**:

```python
from registry.base_tool import BaseSearchTool  # or BaseScraper, etc.

class MyCustomSearch(BaseSearchTool):
    """Docstring explaining what this tool does."""
    
    name = "my_custom_search"
    priority = 5
    requires_api_key = True
    
    def __init__(self, api_key: str = None):
        """Initialize with configuration."""
        self.api_key = api_key or os.getenv("MY_SEARCH_KEY")
    
    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Implementation with error handling."""
        try:
            # Implementation here
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []  # Return empty, don't crash
```

---

### 3. Graph Builder (`core/graph.py`)

**Must build graph dynamically** without hardcoded tool references:

```python
def create_research_graph(config_path: str = "config/tool_config.yaml"):
    """Build graph using tools from registry."""
    
    # Load configuration
    # Initialize registry
    # Register all tools
    # Build StateGraph
    # Return compiled graph
```

---

### 4. Orchestrator (`core/orchestrator.py`)

**Main execution interface**:

```python
class ResearchOrchestrator:
    def __init__(self, config_path: str):
        self.graph = create_research_graph(config_path)
        self.registry = ToolRegistry.from_config(config_path)
    
    def research(self, query: str, custom_tools: List = None) -> str:
        """Execute research with optional custom tools."""
        # Register custom tools if provided
        # Run graph
        # Return report
```

---

## V. Extension Points for Users

### Adding Custom Search Tool

1. Create `tools/search/my_search.py`
2. Inherit from `BaseSearchTool`
3. Implement `search()` method
4. Add to `tool_config.yaml`:
   ```yaml
   my_search:
     priority: 8
     enabled: true
   ```
5. Restart - automatically discovered and registered

### Adding Custom Processing Tool

1. Create `tools/custom/my_processor.py`
2. Inherit from `BaseCustomTool`
3. Implement `execute()` method
4. Register in code or config
5. Access in custom node via `ToolRegistry.get_tool("custom", "my_processor")`

---

## VI. Critical Implementation Rules

### Code Quality
1. **Every function**: Type hints + docstring (Google style)
2. **Error handling**: Try-except in all tool methods, log and return gracefully
3. **No nested complexity**: Max 2 levels of nesting in functions
4. **Single responsibility**: One function = one clear purpose
5. **Comments**: Explain "why", not "what" (code shows what)

### Modularity Rules
1. **Zero hardcoded imports** of specific tools in core layer
2. **All tool access** through registry
3. **Configuration-driven** behavior (no magic values in code)
4. **Interfaces first**: Define base class before implementing tools
5. **Dependency injection**: Pass registry/config to constructors

### Testing Requirements
1. **Mock registry** for unit tests (don't call real APIs)
2. **Test each tool** independently
3. **Test fallback chain**: Ensure Tool B activates when Tool A fails
4. **Integration test**: Full graph execution with mocked tools

---

## VII. Success Criteria

The framework must:
1. ✓ Run with Tavily + Trafilatura (default config)
2. ✓ Swap to Serper + Playwright by editing YAML only
3. ✓ Accept custom tool in `tools/custom/` without modifying core
4. ✓ Automatically try fallback tools on failure
5. ✓ Generate report with proper citations
6. ✓ Log which tools were used for each operation

---

## VIII. Development Sequence

**Phase 1: Foundation**
1. Define all base classes (`registry/base_tool.py`)
2. Implement tool registry system
3. Create state schema
4. Build configuration loader

**Phase 2: Core Tools**
5. Implement one tool per category (Tavily, Trafilatura, LiteLLM)
6. Test tool registration and discovery
7. Verify fallback chain logic

**Phase 3: Orchestration**
8. Build graph nodes (using registry, not imports)
9. Wire conditional routing
10. Create orchestrator interface

**Phase 4: Extensions**
11. Add 2nd search tool (Serper)
12. Add 2nd scraper (Playwright)
13. Create custom tool example
14. Document extension process

**Phase 5: Polish**
15. Add comprehensive logging
16. Write tests for each component
17. Create example scripts
18. Write user documentation

---

## IX. Dependencies

### Core
- langgraph>=0.2.0
- pydantic>=2.9.0
- pyyaml>=6.0

### Default Tools
- tavily-python>=0.5.0
- trafilatura>=1.12.0
- litellm>=1.45.0

### Optional Tools (user installs as needed)
- playwright>=1.40.0
- google-search-results>=2.4.0
- beautifulsoup4>=4.12.0

---

**Build this as a reusable framework, not a single-use script. Think Django, not notebook.**
</create_artifact>

This specification defines a **true framework architecture** where:

1. **Core is tool-agnostic** - nodes request tools from registry, never import directly
2. **Plugin system** - tools auto-discovered from file structure
3. **Config-driven** - swap tools via YAML without code changes
4. **Extensible** - users add tools by creating files in `tools/` directory
5. **Fallback chains** - automatic tool switching on failure

Kiro Claude can implement this spec exactly, creating a modular system where you can drop in any search API or scraper without touching core orchestration logic.