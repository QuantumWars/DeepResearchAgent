"""Search strategy implementations for the research agent."""

from .base import SearchStrategy
from .exa_strategy import ExaSearchStrategy
from .tavily_strategy import TavilySearchStrategy
from .firecrawl_strategy import FirecrawlSearchStrategy
from .parallel_strategy import ParallelSearchStrategy
from .content_enrichment import enrich_with_content
from .factory import (
    create_search_strategy,
    create_fallback_strategy,
    get_search_strategy
)


__all__ = [
    # Base class
    "SearchStrategy",
    
    # Strategy implementations
    "ExaSearchStrategy",
    "TavilySearchStrategy",
    "FirecrawlSearchStrategy",
    "ParallelSearchStrategy",
    
    # Content enrichment
    "enrich_with_content",
    
    # Factory functions
    "create_search_strategy",
    "create_fallback_strategy",
    "get_search_strategy",
]
