# Implementation Plan

- [x] 1. Set up project structure and dependencies
  - Create directory structure for core/, registry/, tools/, models/, config/, utils/, examples/
  - Create requirements.txt with core dependencies (langgraph, pydantic, pyyaml)
  - Create main.py entry point
  - Create .env.example file for API key configuration
  - _Requirements: 1.1, 2.1, 3.1_

- [x] 2. Implement base tool interfaces and data models
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 12.1_

- [x] 2.1 Create Pydantic models for tool schemas
  - Implement SearchResult model with url, title, snippet, relevance_score fields
  - Implement ScrapedContent model with url, content, success, error_msg, metadata fields
  - Implement Citation model with id, url, title, excerpt, accessed_at fields
  - Implement CitedReport, ReportSection models for structured output
  - Implement ToolExecutionLog and ToolConfig models
  - _Requirements: 2.1, 2.2, 12.1_

- [x] 2.2 Create abstract base tool classes
  - Implement BaseSearchTool with abstract search() method
  - Implement BaseScraperTool with abstract scrape() method
  - Implement BaseLLMTool with abstract generate() method and ModelType enum
  - Implement BaseCustomTool with abstract execute() method
  - Add metadata attributes (name, priority, requires_api_key) to all base classes
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 3. Implement configuration system
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3.1 Create YAML configuration loader
  - Implement load_config() function to parse tool_config.yaml
  - Add environment variable substitution for API keys (env:VAR_NAME pattern)
  - Add validation for required configuration fields
  - Handle missing or malformed configuration files gracefully
  - _Requirements: 3.1, 3.4_

- [x] 3.2 Create default tool_config.yaml
  - Define search_tools section with tavily and serper configurations
  - Define scraper_tools section with trafilatura and playwright configurations
  - Define llm_tools section with model routing (fast/balanced/powerful)
  - Define fallback chains for each tool category
  - Include priority levels and enabled flags for each tool
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 4. Implement tool registry system
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 4.1 Create ToolRegistry class
  - Implement __init__ with internal data structures (_tools, _fallback_chains, _config)
  - Implement register_tool() method to add tools to registry
  - Implement get_tool() method to retrieve tool by category and optional name
  - Implement get_tool_chain() method to return fallback chain for category
  - Implement from_config() class method to initialize from YAML configuration
  - _Requirements: 1.2, 1.3, 1.4_

- [x] 4.2 Implement tool discovery mechanism
  - Implement discover_tools() method to scan tools/ directory recursively
  - Add logic to import Python modules and inspect classes
  - Filter classes that inherit from base tool interfaces
  - Extract metadata (name, priority, category) from tool classes
  - Instantiate tools with configuration parameters
  - Register discovered tools automatically
  - _Requirements: 1.1, 1.5_

- [x] 5. Implement state management
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 5.1 Create ResearchState TypedDict
  - Define TypedDict with original_query, research_plan, gaps_identified fields
  - Add retrieved_documents, research_loop_count, final_report fields
  - Add tool_execution_log and max_loops fields
  - Add type hints for all fields (str, Optional[List[str]], List[Dict], int, etc.)
  - _Requirements: 5.1, 5.3, 5.4, 5.5_

- [x] 5.2 Create utility functions for state logging
  - Implement log_tool_success() to add successful tool execution to log
  - Implement log_tool_failure() to add failed tool execution to log
  - Include timestamp, node, tool_category, tool_name, success, error_msg in logs
  - _Requirements: 5.3, 11.3_

- [-] 6. Implement search tools
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 6.1 Implement Tavily search tool
  - Create TavilySearch class inheriting from BaseSearchTool
  - Implement __init__ to load API key from environment or config
  - Implement search() method with tavily-python client
  - Parse API response into List[SearchResult]
  - Add try-except error handling that logs errors and returns empty list
  - Set metadata: name="tavily", priority=10, requires_api_key=True
  - _Requirements: 7.1, 7.3, 7.4, 2.5_

- [x] 6.2 Implement Serper search tool
  - Create SerperSearch class inheriting from BaseSearchTool
  - Implement __init__ to load API key from environment or config
  - Implement search() method with google-search-results client
  - Parse API response into List[SearchResult]
  - Add try-except error handling that logs errors and returns empty list
  - Set metadata: name="serper", priority=5, requires_api_key=True
  - _Requirements: 7.2, 7.3, 7.4, 2.5_

- [x] 7. Implement scraper tools
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 7.1 Implement Trafilatura scraper tool
  - Create TrafilaturaScr aper class inheriting from BaseScraperTool
  - Implement __init__ with any configuration parameters
  - Implement scrape() method using trafilatura library
  - Return ScrapedContent with url, content, success=True on success
  - Add try-except error handling that returns ScrapedContent with success=False
  - Set metadata: name="trafilatura", priority=10
  - _Requirements: 8.1, 8.3, 8.4, 2.5_

- [x] 7.2 Implement Playwright scraper tool
  - Create PlaywrightScraper class inheriting from BaseScraperTool
  - Implement __init__ with configuration (headless, timeout, wait_for)
  - Implement scrape() method using playwright library
  - Handle JavaScript-heavy sites by waiting for network idle
  - Return ScrapedContent with url, content, success=True on success
  - Add try-except error handling that returns ScrapedContent with success=False
  - Set metadata: name="playwright", priority=5
  - _Requirements: 8.2, 8.3, 8.4, 2.5_

- [x] 8. Implement LLM tool
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 8.1 Create LiteLLM tool implementation
  - Create LiteLLMTool class inheriting from BaseLLMTool
  - Implement __init__ to load model routing configuration (fast/balanced/powerful)
  - Implement generate() method that routes to appropriate model based on ModelType
  - Add support for structured output using Pydantic schemas
  - Add try-except error handling that logs errors and raises exceptions
  - Set metadata: name="litellm"
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 9. Implement core workflow nodes
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 9.1 Implement planner node
  - Create planner_node() function accepting state and registry parameters
  - Request fast LLM from registry using get_tool("llm")
  - Generate prompt for query decomposition into 3-5 sub-questions
  - Call LLM generate() with prompt and ModelType.FAST
  - Parse LLM response into list of sub-questions
  - Update state["research_plan"] with sub-questions
  - Log tool usage to state["tool_execution_log"]
  - Handle LLM failures by returning state with empty plan
  - _Requirements: 4.1, 5.3, 11.1_

- [x] 9.2 Implement retrieval node
  - Create retrieval_node() function accepting state and registry parameters
  - Request search tool chain from registry using get_tool_chain("search")
  - For each sub-question in research_plan, iterate through search tools until success
  - Collect top 5 URLs from successful search results
  - Request scraper tool chain from registry using get_tool_chain("scraper")
  - For each URL, iterate through scraper tools until content extracted
  - Store successful scrapes in state["retrieved_documents"] as dicts with url, content, title
  - Log all tool attempts (success and failure) to state["tool_execution_log"]
  - Continue with partial results if some tools fail
  - _Requirements: 4.2, 7.5, 8.5, 11.1, 11.2_

- [x] 9.3 Implement reflection node
  - Create reflection_node() function accepting state and registry parameters
  - Request balanced LLM from registry using get_tool("llm")
  - Generate prompt with original_query, research_plan, and retrieved_documents
  - Ask LLM to identify information gaps or confirm completeness
  - Call LLM generate() with prompt and ModelType.BALANCED
  - Update state["gaps_identified"] with LLM response
  - Increment state["research_loop_count"]
  - Log tool usage to state["tool_execution_log"]
  - Handle LLM failures by setting gaps_identified to empty (assume complete)
  - _Requirements: 4.3, 5.4, 11.1_

- [x] 9.4 Implement synthesis node
  - Create synthesis_node() function accepting state and registry parameters
  - Request powerful LLM from registry using get_tool("llm")
  - Generate prompt with full context (query, plan, documents)
  - Define CitedReport Pydantic schema for structured output
  - Call LLM generate() with prompt, ModelType.POWERFUL, and schema
  - Format final report with inline citations [1], [2] and references section
  - Update state["final_report"] with formatted report
  - Log tool usage to state["tool_execution_log"]
  - Fall back to unstructured generation if structured output fails
  - _Requirements: 4.4, 12.2, 12.3, 12.4, 12.5_

- [x] 9.5 Implement conditional routing function
  - Create should_continue_research() function accepting state parameter
  - Check if gaps_identified is not empty
  - Check if research_loop_count < max_loops
  - Return "continue" if both conditions true, otherwise "synthesize"
  - _Requirements: 6.4_

- [x] 10. Implement graph builder
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 10.1 Create LangGraph workflow
  - Create create_research_graph() function accepting registry parameter
  - Initialize StateGraph with ResearchState TypedDict
  - Add planner node with lambda wrapping planner_node(state, registry)
  - Add retrieval node with lambda wrapping retrieval_node(state, registry)
  - Add reflection node with lambda wrapping reflection_node(state, registry)
  - Add synthesis node with lambda wrapping synthesis_node(state, registry)
  - Add edge from START to planner
  - Add edge from planner to retrieval
  - Add edge from retrieval to reflection
  - Add conditional edges from reflection using should_continue_research()
  - Map "continue" to retrieval and "synthesize" to synthesis
  - Add edge from synthesis to END
  - Compile and return graph
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 11. Implement orchestrator
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 11.4_

- [x] 11.1 Create ResearchOrchestrator class
  - Implement __init__ accepting config_path parameter (default: "config/tool_config.yaml")
  - Load configuration using load_config()
  - Initialize ToolRegistry using from_config()
  - Create graph using create_research_graph(registry)
  - Set up logger using Python logging module
  - _Requirements: 3.1, 1.1, 6.1_

- [x] 11.2 Implement research() method
  - Accept query, custom_tools (optional), and max_loops parameters
  - Register custom_tools if provided
  - Initialize state dict with all required fields
  - Set original_query to query parameter
  - Set max_loops to parameter value
  - Initialize empty lists and None values for other fields
  - Invoke graph with initial state
  - Extract final_report, retrieved_documents, tool_execution_log from final state
  - Log summary of research execution
  - Return ResearchResult with report, sources, execution_log
  - Wrap in try-except to handle graph execution failures gracefully
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 11.4_

- [x] 11.3 Create ResearchResult class
  - Implement ResearchResult Pydantic model with report, sources, execution_log fields
  - Implement save() method to write report to file
  - Implement get_citations() method to extract Citation objects from report
  - _Requirements: 12.1, 12.5_

- [x] 12. Implement logging and utilities
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 12.1 Set up structured logging
  - Create setup_logger() function in utils/
  - Configure logging with format: [timestamp] [level] [component] message
  - Set appropriate log levels (DEBUG, INFO, WARNING, ERROR)
  - Return configured logger instance
  - _Requirements: 11.5_

- [x] 12.2 Create formatting utilities
  - Implement format_citations() to convert documents to citation format
  - Implement parse_plan() to extract sub-questions from LLM response
  - Add any other formatting helpers needed by nodes
  - _Requirements: 12.2, 12.5_

- [x] 13. Add second search tool (Serper already implemented in 6.2)
  - _Requirements: 7.2, 7.5_

- [x] 14. Add second scraper tool (Playwright already implemented in 7.2)
  - _Requirements: 8.2, 8.5_

- [x] 15. Create custom tool example
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 15.1 Implement example custom tool
  - Create examples/custom_tool_example.py
  - Implement PDFExtractor class inheriting from BaseCustomTool
  - Demonstrate execute() method implementation
  - Show how to handle errors and return results
  - Add comments explaining the extension pattern
  - _Requirements: 10.2, 10.5_

- [x] 15.2 Create usage example script
  - Create examples/basic_research.py demonstrating basic usage
  - Show how to initialize ResearchOrchestrator
  - Show how to call research() method with a query
  - Show how to access results and save report
  - Add example of registering custom tool
  - _Requirements: 10.1, 10.3_

- [x] 16. Create documentation
  - _Requirements: 10.5_

- [x] 16.1 Write README.md
  - Add project overview and architecture description
  - Add installation instructions
  - Add quick start guide with code examples
  - Add configuration guide for tool_config.yaml
  - Add section on adding custom tools
  - Add API reference for main classes
  - Add troubleshooting section
  - _Requirements: 10.5_

- [x] 16.2 Add inline documentation
  - Ensure all functions have Google-style docstrings
  - Add type hints to all function parameters and returns
  - Add comments explaining "why" for complex logic
  - Document all configuration options in tool_config.yaml
  - _Requirements: 10.5_
