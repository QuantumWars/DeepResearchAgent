# Design Document

## Overview

The Deep Research Framework is a plugin-based agentic system built on LangGraph that orchestrates multi-step research workflows. The architecture follows a strict separation of concerns with four distinct layers: a tool-agnostic core orchestration layer, a plugin registry system, pluggable tool implementations, and Pydantic-based data models. This design enables users to swap search providers, scrapers, and LLM backends through configuration changes without modifying core logic.

The system executes research through a state machine workflow: query decomposition (planning), information retrieval, completeness evaluation (reflection), and structured synthesis with citations. The framework supports automatic fallback chains where alternative tools are tried sequentially on failure, comprehensive logging for debugging, and extensibility through a simple file-based plugin system.

## Architecture

### Layered Architecture

The framework implements a four-layer architecture that enforces modularity and extensibility:

**Layer 1 - Core Orchestration (Tool-Agnostic)**
- State management using TypedDict schemas
- LangGraph-based workflow with conditional routing
- Node implementations that delegate to registry
- No direct imports of specific tool implementations

**Layer 2 - Tool Registry (Plugin System)**
- Automatic tool discovery via directory scanning
- Priority-based tool selection
- Fallback chain management
- Configuration-driven tool initialization

**Layer 3 - Tool Implementations (Pluggable Modules)**
- Search tools (Tavily, Serper, Brave)
- Scraper tools (Trafilatura, Playwright, BeautifulSoup)
- LLM tools (LiteLLM with model routing)
- Custom user-defined tools

**Layer 4 - Models & Schemas (Validation)**
- Pydantic models for citations and tool I/O
- Type-safe state definitions
- Structured output schemas for LLM responses

### Dependency Flow

```
User Query → Orchestrator → Graph → Nodes → Registry → Tools → External APIs
                                      ↓
                                    State (TypedDict)
                                      ↓
                                  Tool Execution Log
```

The dependency flow is strictly unidirectional: core components depend on abstractions (base classes), never on concrete implementations. Tools are injected at runtime through the registry, enabling complete decoupling.

### Configuration-Driven Design

All tool selection, priority ordering, and fallback chains are defined in `tool_config.yaml`. The configuration loader parses this file at startup and initializes the registry accordingly. This design allows users to:
- Switch from Tavily to Serper by changing one line
- Reorder fallback chains without code changes
- Enable/disable tools declaratively
- Reference environment variables for API keys


## Components and Interfaces

### Tool Registry System

**Purpose**: Central hub for tool discovery, registration, and retrieval with fallback support.

**Key Classes**:

```python
class ToolRegistry:
    """Manages tool lifecycle and provides access to registered tools."""
    
    _tools: Dict[str, Dict[str, BaseTool]]  # category -> {name: tool_instance}
    _fallback_chains: Dict[str, List[str]]  # category -> [tool_names]
    _config: Dict  # Loaded from YAML
```

**Core Methods**:
- `register_tool(tool_class, category, priority)`: Adds a tool to the registry
- `get_tool(category, name=None)`: Returns highest priority tool or specific named tool
- `get_tool_chain(category)`: Returns ordered list of tools for fallback
- `discover_tools(directory)`: Scans directory and auto-registers tools
- `from_config(config_path)`: Factory method that loads config and initializes registry

**Discovery Algorithm**:
1. Scan `tools/` directory recursively
2. Import all Python modules
3. Inspect classes for base class inheritance
4. Extract metadata (name, priority, category)
5. Instantiate with config parameters
6. Register in appropriate category

**Fallback Chain Logic**:
When a node requests a tool chain, the registry returns tools sorted by priority. If the primary tool fails, the node iterates to the next tool in the chain until success or exhaustion.


### Base Tool Interfaces

**BaseSearchTool**:
```python
class BaseSearchTool(ABC):
    name: str
    priority: int
    requires_api_key: bool
    
    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Execute search and return results."""
        pass
```

**SearchResult Schema**:
```python
class SearchResult(BaseModel):
    url: str
    title: str
    snippet: str
    relevance_score: Optional[float] = None
```

**BaseScraperTool**:
```python
class BaseScraperTool(ABC):
    name: str
    priority: int
    
    @abstractmethod
    def scrape(self, url: str) -> ScrapedContent:
        """Extract content from URL."""
        pass
```

**ScrapedContent Schema**:
```python
class ScrapedContent(BaseModel):
    url: str
    content: str
    success: bool
    error_msg: Optional[str] = None
    metadata: Optional[Dict] = None
```

**BaseLLMTool**:
```python
class BaseLLMTool(ABC):
    name: str
    
    @abstractmethod
    def generate(
        self, 
        prompt: str, 
        model_type: ModelType,
        structured_output_schema: Optional[Type[BaseModel]] = None
    ) -> Union[str, BaseModel]:
        """Generate text or structured output."""
        pass

class ModelType(Enum):
    FAST = "fast"
    BALANCED = "balanced"
    POWERFUL = "powerful"
```

**BaseCustomTool**:
```python
class BaseCustomTool(ABC):
    name: str
    description: str
    
    @abstractmethod
    def execute(self, input_data: Dict) -> Dict:
        """Execute custom logic."""
        pass
```

All tools must handle errors gracefully by catching exceptions, logging them, and returning empty/failed results rather than propagating exceptions.


### Core Nodes

**Planner Node**:
- **Input**: State with original_query
- **Process**: 
  - Requests fast LLM from registry
  - Generates prompt for query decomposition
  - Calls LLM to break query into 3-5 sub-questions
  - Logs tool usage
- **Output**: State with research_plan populated
- **Error Handling**: If LLM fails, returns state with empty plan and logs error

**Retrieval Node**:
- **Input**: State with research_plan
- **Process**:
  - Requests search tool chain from registry
  - For each sub-question in plan:
    - Tries search tools in priority order until success
    - Collects top N URLs from results
  - Requests scraper tool chain from registry
  - For each URL:
    - Tries scrapers in priority order until content extracted
    - Stores successful scrapes in retrieved_documents
  - Logs all tool attempts and outcomes
- **Output**: State with retrieved_documents populated
- **Error Handling**: Continues with partial results if some tools fail

**Reflection Node**:
- **Input**: State with original_query, research_plan, retrieved_documents
- **Process**:
  - Requests balanced LLM from registry
  - Generates prompt with query, plan, and retrieved content
  - Asks LLM to identify information gaps
  - Increments research_loop_count
  - Logs tool usage
- **Output**: State with gaps_identified populated
- **Error Handling**: If LLM fails, assumes research is complete

**Synthesis Node**:
- **Input**: State with all fields populated
- **Process**:
  - Requests powerful LLM from registry
  - Generates prompt with full context
  - Defines structured output schema for report with citations
  - Calls LLM with structured output
  - Formats final report with inline citations and references section
  - Logs tool usage
- **Output**: State with final_report populated
- **Error Handling**: If structured output fails, falls back to unstructured generation


### State Graph Workflow

**Graph Structure**:
```
START → planner_node → retrieval_node → reflection_node → decision_node
                                              ↓                ↓
                                         (gaps found)    (complete)
                                              ↓                ↓
                                       retrieval_node   synthesis_node → END
```

**Conditional Routing Logic**:
The decision node evaluates:
1. If `gaps_identified` is not empty AND `research_loop_count < MAX_LOOPS` (default 3):
   - Route back to retrieval_node
2. Otherwise:
   - Route to synthesis_node

**State Transitions**:
- Each node receives the full state
- Nodes update specific fields
- State is passed to next node
- Final state contains complete research history

**Graph Builder**:
```python
def create_research_graph(registry: ToolRegistry) -> CompiledGraph:
    """Build LangGraph workflow with registry-injected nodes."""
    
    workflow = StateGraph(ResearchState)
    
    # Add nodes with registry dependency injection
    workflow.add_node("planner", lambda state: planner_node(state, registry))
    workflow.add_node("retrieval", lambda state: retrieval_node(state, registry))
    workflow.add_node("reflection", lambda state: reflection_node(state, registry))
    workflow.add_node("synthesis", lambda state: synthesis_node(state, registry))
    
    # Define edges
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "retrieval")
    workflow.add_edge("retrieval", "reflection")
    
    # Conditional routing
    workflow.add_conditional_edges(
        "reflection",
        should_continue_research,
        {
            "continue": "retrieval",
            "synthesize": "synthesis"
        }
    )
    
    workflow.add_edge("synthesis", END)
    
    return workflow.compile()
```


### Orchestrator

**Purpose**: High-level interface for executing research workflows.

**Design**:
```python
class ResearchOrchestrator:
    """Main entry point for research execution."""
    
    def __init__(self, config_path: str = "config/tool_config.yaml"):
        """Initialize with configuration."""
        self.config = load_config(config_path)
        self.registry = ToolRegistry.from_config(self.config)
        self.graph = create_research_graph(self.registry)
        self.logger = setup_logger()
    
    def research(
        self, 
        query: str, 
        custom_tools: Optional[List[BaseTool]] = None,
        max_loops: int = 3
    ) -> ResearchResult:
        """Execute complete research workflow."""
        
        # Register custom tools if provided
        if custom_tools:
            for tool in custom_tools:
                self.registry.register_tool(tool)
        
        # Initialize state
        initial_state = {
            "original_query": query,
            "research_plan": None,
            "gaps_identified": None,
            "retrieved_documents": [],
            "research_loop_count": 0,
            "final_report": None,
            "tool_execution_log": [],
            "max_loops": max_loops
        }
        
        # Execute graph
        final_state = self.graph.invoke(initial_state)
        
        # Log summary
        self.logger.info(f"Research complete. Used {len(final_state['tool_execution_log'])} tool calls")
        
        return ResearchResult(
            report=final_state["final_report"],
            sources=final_state["retrieved_documents"],
            execution_log=final_state["tool_execution_log"]
        )
```

**ResearchResult Schema**:
```python
class ResearchResult(BaseModel):
    report: str
    sources: List[Dict]
    execution_log: List[Dict]
    
    def save(self, filepath: str):
        """Save report to file."""
        pass
    
    def get_citations(self) -> List[Citation]:
        """Extract citations from report."""
        pass
```


## Data Models

### State Schema

```python
class ResearchState(TypedDict):
    """Complete state for research workflow."""
    original_query: str
    research_plan: Optional[List[str]]
    gaps_identified: Optional[str]
    retrieved_documents: List[Dict[str, Any]]
    research_loop_count: int
    final_report: Optional[str]
    tool_execution_log: List[Dict[str, Any]]
    max_loops: int
```

**Field Descriptions**:
- `original_query`: User's initial research question
- `research_plan`: List of sub-questions generated by planner
- `gaps_identified`: String describing missing information (empty if complete)
- `retrieved_documents`: List of {url, content, title, source_tool} dicts
- `research_loop_count`: Number of retrieval-reflection cycles executed
- `final_report`: Markdown-formatted report with citations
- `tool_execution_log`: List of {timestamp, node, tool_name, success, details} dicts
- `max_loops`: Maximum allowed research iterations

### Citation Models

```python
class Citation(BaseModel):
    """Single citation reference."""
    id: str  # e.g., "[1]"
    url: str
    title: str
    excerpt: str  # Relevant quote from source
    accessed_at: datetime

class CitedReport(BaseModel):
    """Structured report with citations."""
    title: str
    summary: str
    sections: List[ReportSection]
    references: List[Citation]

class ReportSection(BaseModel):
    """Section of report with inline citations."""
    heading: str
    content: str  # Contains [1], [2] citation markers
    citation_ids: List[str]
```

### Tool Schemas

```python
class ToolExecutionLog(BaseModel):
    """Log entry for tool usage."""
    timestamp: datetime
    node: str
    tool_category: str
    tool_name: str
    success: bool
    error_msg: Optional[str] = None
    metadata: Dict[str, Any] = {}

class ToolConfig(BaseModel):
    """Configuration for a single tool."""
    name: str
    enabled: bool
    priority: int
    api_key: Optional[str] = None
    extra_params: Dict[str, Any] = {}
```


## Error Handling

### Tool-Level Error Handling

**Pattern**: All tools implement try-except blocks that catch exceptions, log errors, and return empty/failed results.

```python
def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
    """Search with graceful error handling."""
    try:
        # API call
        response = self.client.search(query, max_results)
        return self._parse_results(response)
    except APIError as e:
        self.logger.error(f"{self.name} API error: {e}")
        return []
    except Exception as e:
        self.logger.error(f"{self.name} unexpected error: {e}")
        return []
```

**Rationale**: Prevents single tool failures from crashing the entire workflow. Enables fallback chain to activate.

### Node-Level Error Handling

**Pattern**: Nodes check for empty results from tools and handle gracefully.

```python
def retrieval_node(state: ResearchState, registry: ToolRegistry) -> ResearchState:
    """Retrieval with fallback chain."""
    search_chain = registry.get_tool_chain("search")
    
    results = []
    for search_tool in search_chain:
        try:
            results = search_tool.search(state["research_plan"][0])
            if results:
                log_tool_success(state, "search", search_tool.name)
                break
        except Exception as e:
            log_tool_failure(state, "search", search_tool.name, str(e))
            continue
    
    if not results:
        logger.warning("All search tools failed, continuing with empty results")
    
    # Continue processing...
```

### Graph-Level Error Handling

**Pattern**: Graph execution wrapped in try-except with state preservation.

```python
def research(self, query: str) -> ResearchResult:
    """Execute with error recovery."""
    try:
        final_state = self.graph.invoke(initial_state)
        return ResearchResult.from_state(final_state)
    except Exception as e:
        self.logger.error(f"Graph execution failed: {e}")
        # Return partial results if available
        return ResearchResult(
            report="Research incomplete due to error",
            sources=[],
            execution_log=[]
        )
```

### Logging Strategy

**Levels**:
- `DEBUG`: Tool discovery, registration details
- `INFO`: Node transitions, successful tool calls
- `WARNING`: Tool failures with fallback activation
- `ERROR`: Unrecoverable errors, missing configuration

**Log Format**:
```
[timestamp] [level] [component] message
2024-11-14 10:30:15 INFO [retrieval_node] Using tavily for search
2024-11-14 10:30:16 WARNING [retrieval_node] tavily failed, trying serper
2024-11-14 10:30:17 INFO [retrieval_node] serper succeeded, retrieved 5 results
```


## Testing Strategy

### Unit Testing

**Tool Tests**:
- Mock external APIs (Tavily, Serper, etc.)
- Test error handling with simulated failures
- Verify return schemas match base class contracts
- Test priority and metadata attributes

```python
def test_tavily_search_success(mock_tavily_client):
    """Test successful search returns correct schema."""
    tool = TavilySearch(api_key="test")
    results = tool.search("test query", max_results=3)
    
    assert len(results) <= 3
    assert all(isinstance(r, SearchResult) for r in results)
    assert all(r.url and r.title for r in results)

def test_tavily_search_failure(mock_tavily_client):
    """Test API failure returns empty list."""
    mock_tavily_client.side_effect = APIError("Rate limit")
    tool = TavilySearch(api_key="test")
    results = tool.search("test query")
    
    assert results == []
```

**Registry Tests**:
- Test tool discovery from directory
- Test priority-based selection
- Test fallback chain ordering
- Test configuration loading

```python
def test_registry_fallback_chain():
    """Test fallback chain returns tools in priority order."""
    registry = ToolRegistry()
    registry.register_tool(TavilySearch, "search", priority=10)
    registry.register_tool(SerperSearch, "search", priority=5)
    
    chain = registry.get_tool_chain("search")
    
    assert len(chain) == 2
    assert chain[0].name == "tavily"
    assert chain[1].name == "serper"
```

**Node Tests**:
- Mock registry to return test tools
- Test state transformations
- Test error handling with failed tools
- Verify logging calls

```python
def test_planner_node_updates_state(mock_registry):
    """Test planner populates research_plan."""
    mock_llm = Mock(spec=BaseLLMTool)
    mock_llm.generate.return_value = "1. Question A\n2. Question B"
    mock_registry.get_tool.return_value = mock_llm
    
    state = {"original_query": "test", "research_plan": None}
    result = planner_node(state, mock_registry)
    
    assert result["research_plan"] is not None
    assert len(result["research_plan"]) == 2
```


### Integration Testing

**Graph Execution Tests**:
- Mock all external APIs
- Test complete workflow from query to report
- Verify state transitions through all nodes
- Test conditional routing (continue vs. synthesize)
- Test max loop limit enforcement

```python
def test_full_research_workflow(mock_all_tools):
    """Test complete research execution."""
    orchestrator = ResearchOrchestrator("test_config.yaml")
    result = orchestrator.research("What is quantum computing?")
    
    assert result.report is not None
    assert len(result.sources) > 0
    assert len(result.execution_log) > 0
    assert "quantum" in result.report.lower()
```

**Fallback Chain Tests**:
- Simulate primary tool failure
- Verify secondary tool is called
- Test exhaustion of all tools in chain
- Verify logging of fallback activations

```python
def test_search_fallback_activation(mock_registry):
    """Test fallback when primary search fails."""
    tavily = Mock(spec=BaseSearchTool)
    tavily.search.return_value = []  # Simulate failure
    
    serper = Mock(spec=BaseSearchTool)
    serper.search.return_value = [SearchResult(...)]
    
    mock_registry.get_tool_chain.return_value = [tavily, serper]
    
    state = {"research_plan": ["test query"], "retrieved_documents": []}
    result = retrieval_node(state, mock_registry)
    
    assert tavily.search.called
    assert serper.search.called
    assert len(result["retrieved_documents"]) > 0
```

### Configuration Testing

**YAML Loading Tests**:
- Test valid configuration parsing
- Test invalid configuration handling
- Test environment variable substitution
- Test missing required fields

```python
def test_config_env_var_substitution():
    """Test API key loaded from environment."""
    os.environ["TAVILY_API_KEY"] = "test_key"
    config = load_config("config/tool_config.yaml")
    
    assert config["search_tools"]["tavily"]["api_key"] == "test_key"
```

### Manual Testing Checklist

- [ ] Run with default config (Tavily + Trafilatura)
- [ ] Swap to Serper in config, verify it's used
- [ ] Disable primary tool, verify fallback activates
- [ ] Add custom tool, verify auto-discovery
- [ ] Test with missing API key, verify graceful failure
- [ ] Test with invalid query, verify error handling
- [ ] Review logs for clarity and completeness
- [ ] Verify citations in final report


## Extension Patterns

### Adding a New Search Tool

**Steps**:
1. Create `tools/search/my_search.py`
2. Import `BaseSearchTool` from `registry.base_tool`
3. Implement required methods and metadata
4. Add configuration to `tool_config.yaml`

**Example**:
```python
# tools/search/brave_search.py
from registry.base_tool import BaseSearchTool
from models.tool_schemas import SearchResult
import os
import logging

logger = logging.getLogger(__name__)

class BraveSearch(BaseSearchTool):
    """Brave Search API implementation."""
    
    name = "brave"
    priority = 3
    requires_api_key = True
    
    def __init__(self, api_key: str = None):
        """Initialize Brave Search client."""
        self.api_key = api_key or os.getenv("BRAVE_API_KEY")
        if not self.api_key:
            logger.warning("Brave API key not found")
    
    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Execute search via Brave API."""
        try:
            # Implementation
            response = self._call_api(query, max_results)
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"Brave search failed: {e}")
            return []
```

**Configuration**:
```yaml
search_tools:
  fallback_chain:
    - tavily
    - serper
    - brave  # Add to chain
  brave:
    priority: 3
    enabled: true
    api_key: env:BRAVE_API_KEY
```

### Adding a Custom Processing Tool

**Use Case**: Add domain-specific processing (e.g., PDF extraction, data transformation)

**Steps**:
1. Create `tools/custom/pdf_extractor.py`
2. Inherit from `BaseCustomTool`
3. Implement `execute()` method
4. Register in code or config

**Example**:
```python
# tools/custom/pdf_extractor.py
from registry.base_tool import BaseCustomTool
import PyPDF2

class PDFExtractor(BaseCustomTool):
    """Extract text from PDF URLs."""
    
    name = "pdf_extractor"
    description = "Extracts text content from PDF files"
    
    def execute(self, input_data: Dict) -> Dict:
        """Extract text from PDF URL."""
        url = input_data.get("url")
        try:
            # Download and extract
            text = self._extract_pdf(url)
            return {"success": True, "content": text}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

**Usage in Custom Node**:
```python
def custom_retrieval_node(state, registry):
    """Enhanced retrieval with PDF support."""
    pdf_tool = registry.get_tool("custom", "pdf_extractor")
    
    for doc in state["retrieved_documents"]:
        if doc["url"].endswith(".pdf"):
            result = pdf_tool.execute({"url": doc["url"]})
            if result["success"]:
                doc["content"] = result["content"]
    
    return state
```


### Customizing the Workflow

**Adding a New Node**:

Users can extend the graph with custom nodes for domain-specific logic.

**Example - Adding a Fact-Checking Node**:
```python
def fact_check_node(state: ResearchState, registry: ToolRegistry) -> ResearchState:
    """Verify claims against retrieved documents."""
    llm = registry.get_tool("llm")
    
    prompt = f"""
    Review these claims and verify against sources:
    Claims: {state['final_report']}
    Sources: {state['retrieved_documents']}
    
    Flag any unsupported claims.
    """
    
    verification = llm.generate(prompt, ModelType.BALANCED)
    state["verification_report"] = verification
    
    return state

# Add to graph
def create_custom_graph(registry):
    workflow = StateGraph(ResearchState)
    # ... standard nodes ...
    workflow.add_node("fact_check", lambda s: fact_check_node(s, registry))
    workflow.add_edge("synthesis", "fact_check")
    workflow.add_edge("fact_check", END)
    return workflow.compile()
```

**Modifying Prompts**:

Prompts are defined in node implementations. Users can subclass nodes or modify prompt templates.

```python
# Custom planner with different decomposition strategy
def custom_planner_node(state, registry):
    """Planner with domain-specific prompt."""
    llm = registry.get_tool("llm")
    
    custom_prompt = f"""
    You are a medical research assistant.
    Break down this medical query into specific sub-questions:
    {state['original_query']}
    
    Focus on: symptoms, causes, treatments, recent research.
    """
    
    plan = llm.generate(custom_prompt, ModelType.FAST)
    state["research_plan"] = parse_plan(plan)
    return state
```

### Configuration Customization

**Custom Model Routing**:
```yaml
llm_tools:
  routing:
    fast: claude-3-haiku-20240307
    balanced: claude-3-sonnet-20240229
    powerful: claude-3-opus-20240229
  provider: litellm
  extra_params:
    temperature: 0.7
    max_tokens: 4000
```

**Custom Scraper Settings**:
```yaml
scraper_tools:
  trafilatura:
    priority: 10
    enabled: true
    extra_params:
      include_comments: false
      include_tables: true
      deduplicate: true
  playwright:
    priority: 5
    enabled: true
    extra_params:
      headless: true
      timeout: 30000
      wait_for: networkidle
```


## Design Decisions and Rationale

### Why Plugin Architecture?

**Decision**: Use registry pattern with auto-discovery instead of hardcoded imports.

**Rationale**: 
- Enables users to add tools without modifying core code
- Supports A/B testing of different providers
- Allows configuration-driven tool selection
- Facilitates testing with mock tools
- Reduces coupling between layers

**Trade-off**: Slightly more complex initialization, but massive gain in flexibility.

### Why TypedDict for State?

**Decision**: Use TypedDict instead of Pydantic BaseModel for state.

**Rationale**:
- LangGraph requires dict-like state for graph execution
- TypedDict provides type hints without runtime overhead
- Simpler serialization for graph checkpointing
- Easier to extend with custom fields

**Trade-off**: Less runtime validation than Pydantic, but better graph compatibility.

### Why Fallback Chains?

**Decision**: Implement automatic fallback instead of failing on first error.

**Rationale**:
- External APIs are unreliable (rate limits, downtime)
- Research should continue even if preferred tool fails
- Users shouldn't need to manually retry with different tools
- Improves overall system reliability

**Trade-off**: Increased latency if primary tool fails, but better success rate.

### Why Separate LLM Model Types?

**Decision**: Route to different models based on task complexity (fast/balanced/powerful).

**Rationale**:
- Planning is simple, doesn't need expensive model
- Synthesis is complex, benefits from powerful model
- Significant cost savings (10x difference between models)
- Faster execution for simple tasks

**Trade-off**: More configuration complexity, but better cost/performance balance.

### Why Configuration-Driven?

**Decision**: Use YAML config instead of code-based configuration.

**Rationale**:
- Non-developers can modify tool selection
- Easy to version control different configurations
- Supports environment-specific configs (dev/prod)
- No code changes needed for tool swapping

**Trade-off**: Need to maintain config schema, but much more flexible.

### Why Structured Output for Synthesis?

**Decision**: Use Pydantic schemas for LLM output instead of free-form text.

**Rationale**:
- Guarantees citation format consistency
- Enables programmatic access to report sections
- Reduces parsing errors
- Supports downstream processing

**Trade-off**: Requires LLM that supports structured output, but worth the constraint.


## Implementation Considerations

### Performance Optimization

**Parallel Scraping**:
- Retrieval node can scrape multiple URLs concurrently
- Use `asyncio` or `ThreadPoolExecutor` for I/O-bound operations
- Limit concurrency to avoid overwhelming servers (max 5 concurrent)

**Caching**:
- Cache search results by query hash
- Cache scraped content by URL
- Use TTL of 24 hours for research freshness
- Implement in-memory cache with LRU eviction

**Streaming**:
- Stream LLM responses for synthesis node
- Show progress to user during long research
- Enable early termination if needed

### Security Considerations

**API Key Management**:
- Never commit API keys to version control
- Load from environment variables or secure vault
- Validate keys at startup, fail fast if missing
- Support key rotation without code changes

**Input Validation**:
- Sanitize user queries to prevent injection
- Validate URLs before scraping
- Limit query length and complexity
- Rate limit research requests

**Content Safety**:
- Filter malicious URLs from search results
- Sanitize scraped HTML to prevent XSS
- Validate LLM outputs for harmful content
- Log all external requests for audit

### Scalability Considerations

**Stateless Design**:
- Orchestrator instances are stateless
- State stored in graph execution context
- Enables horizontal scaling of research workers

**Resource Limits**:
- Max documents per research: 20
- Max research loops: 3
- Max scrape size: 100KB per page
- Timeout per tool call: 30 seconds

**Monitoring**:
- Track tool success/failure rates
- Monitor API quota usage
- Alert on repeated failures
- Log execution times per node


## Workflow Diagrams

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Layer                          │
│  ResearchOrchestrator.research("query") → ResearchResult    │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                      Core Layer                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Planner  │→ │Retrieval │→ │Reflection│→ │Synthesis │   │
│  │   Node   │  │   Node   │  │   Node   │  │   Node   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │              │             │          │
│       └─────────────┴──────────────┴─────────────┘          │
│                         │                                    │
│                    ToolRegistry                              │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                     Tool Layer                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Tavily  │  │Trafilatura│ │ LiteLLM  │  │  Custom  │   │
│  │  Search  │  │  Scraper  │ │   Tool   │  │   Tools  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
┌───────▼─────────────▼─────────────▼─────────────▼──────────┐
│                    External APIs                            │
│     Tavily API    Web Servers    OpenAI API    Custom APIs │
└─────────────────────────────────────────────────────────────┘
```

### Research Workflow State Machine

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Planner   │
                    │ (Fast LLM)  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Retrieval  │
                    │(Search+Scrape)│
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ Reflection  │
                    │(Balanced LLM)│
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Decision   │
                    └──┬───────┬──┘
                       │       │
            Gaps Found │       │ Complete
            Loop < Max │       │
                       │       │
                    ┌──▼───┐   │
                    │ Loop │   │
                    │ Back │   │
                    └──┬───┘   │
                       │       │
                       └───┐   │
                           │   │
                    ┌──────▼───▼──┐
                    │  Synthesis  │
                    │(Powerful LLM)│
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │     END     │
                    └─────────────┘
```

### Tool Fallback Chain

```
Node requests tool
       │
       ▼
┌──────────────┐
│Get Tool Chain│
│from Registry │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Try Tool #1   │
│(Highest Pri) │
└──┬───────┬───┘
   │       │
Success    Failure
   │       │
   │       ▼
   │  ┌──────────────┐
   │  │Try Tool #2   │
   │  │(Next in Chain)│
   │  └──┬───────┬───┘
   │     │       │
   │  Success   Failure
   │     │       │
   │     │       ▼
   │     │  ┌──────────────┐
   │     │  │Try Tool #3   │
   │     │  └──┬───────┬───┘
   │     │     │       │
   │     │  Success   All Failed
   │     │     │       │
   ▼     ▼     ▼       ▼
┌──────────────────────────┐
│Return Results or Empty   │
└──────────────────────────┘
```


## Summary

This design implements a modular, extensible deep research framework with clear separation of concerns across four architectural layers. The core orchestration layer remains completely tool-agnostic, delegating all external interactions to a plugin registry system that supports automatic tool discovery, priority-based selection, and fallback chains.

Key design strengths:
- **Modularity**: Tools can be added/removed without touching core code
- **Reliability**: Automatic fallback chains handle tool failures gracefully
- **Flexibility**: Configuration-driven tool selection enables easy swapping
- **Extensibility**: Simple file-based plugin system for custom tools
- **Debuggability**: Comprehensive logging and execution tracking
- **Type Safety**: Pydantic models and TypedDict ensure data consistency

The LangGraph-based workflow orchestrates four main nodes (planner, retrieval, reflection, synthesis) with conditional routing that enables iterative research refinement. The system balances cost and performance through intelligent LLM model routing, uses structured output for consistent citation formatting, and implements graceful error handling at every layer.

This architecture supports the framework's goal of being a reusable, production-ready system rather than a single-use script, with clear extension points for domain-specific customization while maintaining a clean, maintainable core.
