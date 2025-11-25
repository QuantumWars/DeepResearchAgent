# Implementation Plan

## Overview

This implementation plan breaks down the tool integration work into discrete, manageable coding tasks. The plan follows a phased approach: first implementing core search tools, then utility tools, and finally integration and testing.

---

## Tasks

- [x] 1. Setup Tool Infrastructure
  - Create `research_agent/clients/` directory for API client wrappers
  - Implement `ToolRegistry` class in `research_agent/clients/tool_registry.py`
  - Add tool registration decorator and global registry instance
  - Update `Config` class with new API key fields and enabled_tools list
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 7.1, 7.2, 7.3_

- [x] 2. Implement X/Twitter Search Tool
  - [x] 2.1 Create XAI client wrapper
    - Implement `XAIClient` class in `research_agent/clients/xai_client.py`
    - Add `search_with_grok()` method with retry logic and rate limiting
    - Handle authentication and request formatting
    - _Requirements: 1.6, 7.4, 10.1, 10.2, 10.4_

  - [x] 2.2 Implement X search tool
    - Create `x_search()` tool in `research_agent/tools/x_search.py`
    - Implement multi-query parallel execution
    - Add date range handling (default 15 days)
    - Implement handle filtering (include/exclude)
    - Add engagement filtering (favorites, views)
    - Return structured results with citations and sources
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.7, 8.1, 8.2, 8.3_

  - [x] 2.3 Add X search data models
    - Create `XPost` and `XSearchResult` Pydantic models
    - Add validation for handle formats and date ranges
    - _Requirements: 9.1, 9.2_

- [x] 3. Implement YouTube Search Tool
  - [x] 3.1 Create YouTube client utilities
    - Implement video ID extraction function
    - Implement transcript fetching using `youtube-transcript-api`
    - Implement timestamp generation from captions
    - Add date range calculation helper
    - _Requirements: 2.3, 2.4, 2.6_

  - [x] 3.2 Implement YouTube search tool
    - Create `youtube_search()` tool in `research_agent/tools/youtube_search.py`
    - Use Exa API with YouTube domain filtering
    - Implement time range filtering (day, week, month, year, anytime)
    - Extract video transcripts for each result
    - Generate chapter timestamps (30 per video)
    - Process videos in batches to avoid rate limits
    - Deduplicate by video ID
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 8.5_

  - [x] 3.3 Add YouTube data models
    - Create `VideoResult` and `VideoTimestamp` Pydantic models
    - Add validation for video IDs and URLs
    - _Requirements: 9.1, 9.2_

- [x] 4. Implement Reddit Search Tool
  - [x] 4.1 Implement Reddit search tool
    - Create `reddit_search()` tool in `research_agent/tools/reddit_search.py`
    - Use Tavily API with Reddit domain filtering
    - Implement multi-query parallel execution
    - Add time range filtering per query
    - Extract subreddit from post URLs
    - Return post content, scores, and metadata
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 8.1, 8.2, 8.3_

  - [x] 4.2 Add Reddit data models
    - Create `RedditResult` Pydantic model
    - Add subreddit extraction and validation
    - _Requirements: 9.1, 9.2, 9.3_

- [x] 5. Implement Academic Search Tool
  - [x] 5.1 Implement academic search tool
    - Create `academic_search()` tool in `research_agent/tools/academic_search.py`
    - Use Exa API with research paper category
    - Implement multi-query parallel execution
    - Extract paper abstracts using summary functionality
    - Clean paper titles (remove brackets)
    - Deduplicate by URL
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 8.1, 8.2, 8.3_

  - [x] 5.2 Add academic data models
    - Create `AcademicResult` Pydantic model
    - Add validation for paper metadata
    - _Requirements: 9.1, 9.2_


- [x] 6. Implement Utility Tools
  - [x] 6.1 Implement currency converter tool
    - Create `currency_converter.py` in `research_agent/tools/`
    - Use exchangerate-api or similar service
    - Support major currencies
    - Cache exchange rates (1 hour TTL)
    - _Requirements: 5.1, 7.3, 8.5_

  - [x] 6.2 Implement datetime tool
    - Create `datetime_tool.py` in `research_agent/tools/`
    - Support timezone conversion using pytz
    - Support duration calculations
    - Support date formatting
    - _Requirements: 5.2, 9.4_

  - [x] 6.3 Implement weather tool
    - Create `weather_tool.py` in `research_agent/tools/`
    - Use OpenWeatherMap API
    - Support current weather and forecasts
    - Return temperature, conditions, and alerts
    - _Requirements: 5.3, 7.3_

  - [x] 6.4 Implement flight tracker tool
    - Create `flight_tracker.py` in `research_agent/tools/`
    - Use AviationStack API
    - Support flight number lookup
    - Return status, delays, and gate information
    - _Requirements: 5.4, 7.3_

  - [x] 6.5 Implement stock chart tool
    - Create `stock_chart.py` in `research_agent/tools/`
    - Use yfinance or Alpha Vantage API
    - Support various time periods and intervals
    - Return price data and basic indicators
    - _Requirements: 5.5, 7.3_

  - [x] 6.6 Implement crypto tools
    - Create `crypto_tools.py` in `research_agent/tools/`
    - Use CoinGecko API
    - Support price lookup and market data
    - Return price, volume, and market cap
    - _Requirements: 5.6, 7.3_

  - [x] 6.7 Implement map tools
    - Create `map_tools.py` in `research_agent/tools/`
    - Use Google Maps API or similar
    - Support geocoding (address to coordinates)
    - Support reverse geocoding
    - _Requirements: 5.7, 7.3_

- [x] 7. Update Agent Integration
  - [x] 7.1 Update DeepResearchAgent to use tool registry
    - Modify `__init__` to get tools from registry
    - Update `_create_agent_executor` to use registered tools
    - Add tool filtering based on enabled_tools config
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 7.2 Update configuration system
    - Add all new API key fields to Config class
    - Add enabled_tools configuration
    - Validate required API keys based on enabled tools
    - Update .env.example with new variables
    - _Requirements: 7.1, 7.2, 7.3, 7.5_

  - [x] 7.3 Register all tools in registry
    - Update `research_agent/tools/__init__.py` to import and register all tools
    - Set default enabled/disabled state for each tool
    - Ensure tools are registered before agent initialization
    - _Requirements: 6.1, 6.2, 6.3_

- [x] 8. Error Handling and Resilience
  - [x] 8.1 Implement retry logic for API clients
    - Add exponential backoff for transient failures
    - Handle rate limiting (429 errors)
    - Add timeout handling
    - _Requirements: 10.1, 10.2, 10.4_

  - [x] 8.2 Add comprehensive error handling to all tools
    - Wrap all API calls in try-except blocks
    - Return empty results on failures instead of raising
    - Log errors with full context
    - _Requirements: 10.1, 10.2, 10.3, 10.5_

  - [x] 8.3 Implement API client connection pooling
    - Create `APIClientManager` class
    - Manage HTTP client instances with pooling
    - Add cleanup methods for graceful shutdown
    - _Requirements: 7.3, 8.5_

- [x] 9. Performance Optimizations
  - [x] 9.1 Implement parallel query execution
    - Create generic `execute_multi_query_tool` helper
    - Add semaphore-based concurrency control (limit 5 concurrent)
    - Use asyncio.gather with exception handling
    - _Requirements: 8.1, 8.2, 8.3, 8.5_

  - [x] 9.2 Add caching for expensive operations
    - Cache video transcripts (1 hour TTL)
    - Cache exchange rates (1 hour TTL)
    - Cache weather data (30 minutes TTL)
    - Use aiocache for async caching
    - _Requirements: 8.5_

  - [x] 9.3 Optimize batch processing
    - Implement batch processing for YouTube videos
    - Add delays between batches to respect rate limits
    - Process in chunks of 5 videos
    - _Requirements: 2.6, 8.5_


- [x] 10. Testing Suite
  - [x] 10.1 Write unit tests for X search tool
    - Mock XAI client responses
    - Test multi-query execution
    - Test date range handling
    - Test handle filtering
    - Test error handling
    - _Requirements: 11.1, 11.3, 11.4_

  - [x] 10.2 Write unit tests for YouTube search tool
    - Mock Exa API responses
    - Mock youtube-transcript-api
    - Test transcript extraction
    - Test timestamp generation
    - Test batch processing
    - Test deduplication
    - _Requirements: 11.1, 11.3, 11.4_

  - [x] 10.3 Write unit tests for Reddit search tool
    - Mock Tavily API responses
    - Test multi-query execution
    - Test subreddit extraction
    - Test time range filtering
    - _Requirements: 11.1, 11.3, 11.4_

  - [x] 10.4 Write unit tests for Academic search tool
    - Mock Exa API responses
    - Test paper deduplication
    - Test title and summary cleaning
    - _Requirements: 11.1, 11.3, 11.4_

  - [x] 10.5 Write unit tests for utility tools
    - Test currency converter with mock rates
    - Test datetime operations
    - Test weather API integration
    - Test flight tracker
    - Test stock data retrieval
    - Test crypto data retrieval
    - Test geocoding
    - _Requirements: 11.1, 11.3, 11.4_

  - [x] 10.6 Write integration tests
    - Test full research flow with new tools enabled
    - Test tool registry functionality
    - Test agent with selective tool enabling
    - Test error handling across tools
    - _Requirements: 11.2, 11.4_

  - [x] 10.7 Write schema validation tests
    - Test all Pydantic models
    - Test input validation
    - Test output format consistency
    - _Requirements: 11.3_

- [x] 11. Documentation
  - [x] 11.1 Document new tools
    - Add docstrings to all new tools
    - Document parameters and return types
    - Add usage examples for each tool
    - _Requirements: 12.1, 12.2_

  - [x] 11.2 Update README
    - Add new tools to feature list
    - Document new API key requirements
    - Add setup instructions for new dependencies
    - _Requirements: 12.1, 12.3_

  - [x] 11.3 Create tool catalog
    - Create `TOOLS.md` with descriptions of all tools
    - Document rate limits and constraints
    - Add troubleshooting guide
    - _Requirements: 12.1, 12.4, 12.5_

  - [x] 11.4 Update API documentation
    - Document tool registry API
    - Document configuration options
    - Add examples of enabling/disabling tools
    - _Requirements: 12.1, 12.2_

- [x] 12. Deployment Updates
  - [x] 12.1 Update requirements.txt
    - Add xai-sdk
    - Add youtube-transcript-api
    - Add yfinance
    - Add pytz
    - Add aiocache
    - Add any other new dependencies
    - _Requirements: 7.1, 7.2_

  - [x] 12.2 Update Dockerfile
    - Install new Python dependencies
    - Add any system dependencies if needed
    - _Requirements: 7.1_

  - [x] 12.3 Update .env.example
    - Add all new API key placeholders
    - Add ENABLED_TOOLS configuration example
    - Document optional vs required keys
    - _Requirements: 7.2, 12.3_

  - [x] 12.4 Update docker-compose.yml
    - Add new environment variables
    - Update service configuration if needed
    - _Requirements: 7.2_

---

## Task Execution Notes

- Tasks should be executed in order as they build on each other
- Phase 1 (Tasks 1-5): Core search tools - highest priority
- Phase 2 (Tasks 6): Utility tools - can be done incrementally
- Phase 3 (Tasks 7-9): Integration and optimization - after core tools work
- Phase 4 (Tasks 10-12): Testing and documentation - final polish
- Optional tasks (marked with *) focus on testing and can be skipped for MVP
- Each tool should be tested individually before moving to the next
- All tasks reference specific requirements from requirements.md
