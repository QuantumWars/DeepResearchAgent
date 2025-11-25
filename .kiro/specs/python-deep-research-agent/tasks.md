# Implementation Plan

## Overview

This implementation plan breaks down the Python Deep Research Agent into discrete, manageable coding tasks. Each task builds incrementally on previous work, ensuring the system can be tested at each stage.

---

## Tasks

- [x] 1. Project Setup and Core Infrastructure
  - Create project structure with all necessary directories (agent/, tools/, strategies/, memory/, utils/, api/)
  - Set up Python package with pyproject.toml and dependencies (langchain, fastapi, httpx, pydantic, etc.)
  - Create configuration management system using environment variables
  - Implement structured logging with log levels and context
  - _Requirements: 1.4, 10.1, 10.2, 10.3, 14.1, 14.2, 14.3_

- [x] 1.1 Create base data models
  - Implement Pydantic models for SearchResult, ResearchTask, ResearchPlan, CodeExecutionResult, ResearchResult, Memory
  - Add validation rules (min/max lengths, item counts)
  - Create SearchCategory enum
  - _Requirements: 1.5, 11.5_

- [x] 1.2 Set up configuration system
  - Create Config class to load and validate environment variables
  - Implement API key validation at startup
  - Add configuration for search provider selection, log level, max tasks
  - Provide sensible defaults for optional settings
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 1.3 Implement logging infrastructure
  - Set up structured logging with timestamps and context
  - Configure log levels (INFO, DEBUG, ERROR)
  - Add logging decorators for function entry/exit
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

- [x] 2. Content Processing Utilities
  - Implement URL domain extraction function
  - Create title cleaning function (remove brackets, parentheses, extra spaces)
  - Build deduplication function for results by domain and URL
  - Add content truncation utility (limit to 3000 characters)
  - Create favicon URL generator
  - _Requirements: 4.4, 11.1, 11.2, 11.4_

- [x] 3. Search Strategy Base and Implementations
  - Create SearchStrategy abstract base class with search() and get_content() methods
  - Implement ExaSearchStrategy with search and content retrieval
  - Implement TavilySearchStrategy with search and content retrieval
  - Implement FirecrawlSearchStrategy with search and content retrieval
  - Implement ParallelSearchStrategy with search and content retrieval
  - Add strategy factory function to select provider based on configuration
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3.1 Implement Exa search strategy
  - Initialize Exa client with API key
  - Implement search() method with category, domain filters, max results
  - Implement get_content() method with 3000 character limit
  - Handle API errors gracefully and log failures
  - Return SearchResult objects with all metadata
  - _Requirements: 3.2, 4.2, 4.4, 5.3, 5.4, 9.1, 9.2_

- [x] 3.2 Implement Tavily search strategy
  - Initialize Tavily client with API key
  - Implement search() with topic (general/news), search depth, max results
  - Process and validate image URLs
  - Handle API errors and return empty results on failure
  - _Requirements: 3.2, 4.2, 4.5, 9.1, 9.2_

- [x] 3.3 Implement Firecrawl search strategy
  - Initialize Firecrawl client with API key
  - Implement search() with sources (web, news, images)
  - Process web, news, and image results separately
  - Deduplicate and combine results
  - _Requirements: 3.2, 4.2, 4.4, 9.1, 9.2_

- [x] 3.4 Implement Parallel AI search strategy
  - Initialize Parallel AI client with API key
  - Implement search() with processor quality (base/pro)
  - Combine Parallel AI search with Firecrawl images
  - Handle batch processing for multiple queries
  - _Requirements: 3.2, 4.2, 4.5, 9.1, 9.2_

- [x] 3.5 Implement content retrieval with fallback
  - Create enrich_with_content() function
  - Try primary strategy (Exa) first for all URLs
  - Collect failed URLs and retry with fallback strategy (Firecrawl)
  - Merge results and return enriched SearchResult objects
  - Log all retrieval attempts and failures
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 9.3, 9.4_

- [x] 4. Web Search Tool (LangChain Tool)
  - Create web_search tool using @tool decorator
  - Accept query, category, include_domains, max_results parameters
  - Get search strategy from configuration
  - Execute search and enrich with content
  - Deduplicate results by domain and URL
  - Return list of SearchResult objects
  - Handle errors gracefully and log failures
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 9.1, 9.2, 9.3_

- [x] 5. Code Execution Tool (LangChain Tool)
  - Create execute_python_code tool using @tool decorator
  - Accept title and code parameters
  - Detect required libraries from imports
  - Create sandbox environment (Daytona or similar)
  - Install missing libraries in sandbox
  - Execute code and capture output
  - Extract charts from execution artifacts
  - Clean up sandbox after execution
  - Return CodeExecutionResult with output, errors, charts
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 9.1, 9.2_

- [x] 6. Supermemory Integration
  - Create SupermemoryClient class with async HTTP client
  - Implement store_research() method to save research results
  - Implement search() method to query memories
  - Tag memories with user_id and session_id
  - Handle API errors and log failures
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 6.1 Create memory search tool
  - Create search_memories tool using @tool decorator
  - Accept query, user_id, limit parameters
  - Call SupermemoryClient.search() with container tags
  - Return list of Memory objects
  - _Requirements: 12.1, 12.4, 12.5_

- [x] 7. Research Planner
  - Create ResearchPlanner class with LLM
  - Implement create_plan() method using structured output
  - Build planning prompt with query and context
  - Validate plan has 1-5 topics with 3-5 tasks each
  - Enforce total task limit of 15
  - Return ResearchPlan object
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 8. Streaming Callback Handler
  - Create ResearchStreamingCallback class extending AsyncCallbackHandler
  - Implement on_tool_start() to emit tool start events
  - Implement on_tool_end() to emit tool completion events
  - Implement on_agent_action() to emit agent action events
  - Add event queue for async event handling
  - Include timestamps in all events
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 9. Deep Research Agent Core
  - Create DeepResearchAgent class
  - Initialize with LLM, search provider, memory client, stream handler
  - Implement research() method as main entry point
  - Create _create_research_plan() method using ResearchPlanner
  - Create _create_agent_executor() method with LangChain AgentExecutor
  - Configure agent with all tools (web_search, execute_python_code, search_memories)
  - Set up streaming callbacks
  - Enforce step limit (15 max tool calls)
  - _Requirements: 1.1, 1.2, 1.3, 1.6, 1.7, 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 9.1 Implement autonomous research execution
  - Execute agent with research plan as initial prompt
  - Let agent autonomously select and call tools
  - Collect all tool results and sources
  - Aggregate and deduplicate sources by URL
  - Limit source content to 3000 characters in final results
  - Return ResearchResult with text, sources, charts, tool_results
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 9.2 Add memory storage after research
  - After research completes, store results in Supermemory
  - Tag with user_id and session_id
  - Store each source as a separate memory
  - Include metadata (title, URL, published_date, session_id)
  - Handle storage errors gracefully
  - _Requirements: 12.1, 12.2, 12.3_

- [x] 10. FastAPI Application Setup
  - Create FastAPI app with CORS middleware
  - Define ResearchRequest model (query, user_id)
  - Create health check endpoint
  - Add error handling middleware
  - Configure logging for API requests
  - _Requirements: 8.1, 8.2, 8.3, 9.1, 9.2_

- [x] 10.1 Implement streaming SSE endpoint
  - Create /research/stream POST endpoint
  - Accept ResearchRequest in request body
  - Create event queue for streaming
  - Initialize ResearchStreamingCallback with event queue
  - Start research in background task
  - Stream events as Server-Sent Events (SSE)
  - Send final result when research completes
  - Handle errors and send error events
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 11. Performance Optimizations
  - Implement async operations for all I/O (search, content retrieval, API calls)
  - Add connection pooling to HTTP clients (max_connections=100, max_keepalive_connections=20)
  - Implement parallel search execution for multiple queries
  - Add caching for content retrieval (1 hour TTL)
  - Use asyncio.gather() for concurrent operations
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 12. Error Handling and Resilience
  - Create custom exception classes (ResearchError, SearchProviderError, ContentRetrievalError, CodeExecutionError)
  - Wrap all external API calls in try-except blocks
  - Log errors with full context (query, provider, error message, stack trace)
  - Return empty results on search failures instead of raising
  - Return partial results on research failures
  - Add retry logic with exponential backoff for transient failures
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 13. Testing Suite
  - Write unit tests for content processing utilities (deduplication, title cleaning, domain extraction)
  - Write unit tests for each search strategy (mock API responses)
  - Write unit tests for research planner (mock LLM responses)
  - Write integration tests for full research flow
  - Write tests for error handling and fallback mechanisms
  - Add pytest fixtures for common test data
  - _Requirements: All requirements_

- [x] 14. Documentation
  - Write README with installation instructions
  - Document environment variables and configuration
  - Add API endpoint documentation
  - Create usage examples for CLI and API
  - Document search strategy selection
  - Add troubleshooting guide
  - _Requirements: 10.5_

- [x] 15. Docker and Deployment
  - Create Dockerfile with Python 3.11
  - Add docker-compose.yml for local development
  - Create .env.example with all required variables
  - Add health check endpoint for container orchestration
  - Document deployment process
  - _Requirements: All requirements_

- [x] 16. CLI Entry Point
  - Create main.py CLI script
  - Accept query as command-line argument
  - Initialize agent with configuration
  - Execute research and print results
  - Add options for search provider, log level, output format
  - _Requirements: 1.1, 1.2, 1.3_

---

## Task Execution Notes

- Tasks should be executed in order as they build on each other
- Each task should be tested before moving to the next
- Optional tasks (marked with *) can be skipped for MVP
- All tasks reference specific requirements from requirements.md
- Focus on core functionality first, then add optimizations and tests
