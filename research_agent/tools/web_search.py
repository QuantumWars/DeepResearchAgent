"""Web search tool for the research agent using LangChain tool decorator."""

from typing import List, Optional
from langchain_core.tools import tool

from research_agent.utils.models import SearchResult, SearchCategory
from research_agent.utils.logger import get_logger
from research_agent.utils.content_processor import deduplicate_results, truncate_content
from research_agent.strategies.factory import (
    create_search_strategy,
    create_fallback_strategy,
)
from research_agent.strategies.content_enrichment import enrich_with_content
from research_agent.utils.config import get_config


logger = get_logger(__name__)


@tool
async def web_search(
    query: str,
    category: Optional[str] = None,
    include_domains: Optional[List[str]] = None,
    max_results: int = 8
) -> List[SearchResult]:
    """
    Search the web for information using configured search provider.
    
    This tool searches the web and retrieves full content from discovered sources.
    It automatically enriches results with full content using a fallback mechanism
    and deduplicates results by domain and URL.
    
    Args:
        query: Search query (5-15 words recommended for best results)
        category: Optional search category filter. Valid values:
                 - "news": News articles
                 - "company": Company information
                 - "research paper": Academic research papers
                 - "github": GitHub repositories
                 - "financial report": Financial reports and filings
        include_domains: Optional list of domains to filter results (e.g., ["example.com"])
        max_results: Maximum number of results to return (default 8, max 20)
        
    Returns:
        List of SearchResult objects with title, url, content, and metadata.
        Results are deduplicated by domain (one result per domain) and URL.
        
    Examples:
        >>> results = await web_search("quantum computing applications")
        >>> results = await web_search("AI news", category="news")
        >>> results = await web_search("python", include_domains=["github.com"])
    """
    logger.info(
        f"Starting web search",
        extra={"context": {
            "query": query,
            "category": category,
            "include_domains": include_domains,
            "max_results": max_results
        }}
    )
    
    try:
        # Get configuration
        config = get_config()
        
        # Validate and convert category
        search_category = None
        if category:
            try:
                search_category = SearchCategory(category.lower())
            except ValueError:
                logger.warning(
                    f"Invalid category '{category}', ignoring",
                    extra={"context": {"category": category}}
                )
        
        # Limit max_results to configured maximum
        max_results = min(max_results, config.max_search_results)
        
        # Get search strategy from configuration
        strategy = create_search_strategy()
        logger.debug(
            f"Using search strategy: {strategy.__class__.__name__}",
            extra={"context": {"strategy": strategy.__class__.__name__}}
        )
        
        # Execute search
        logger.info(
            f"Executing search with {strategy.__class__.__name__}",
            extra={"context": {"query": query}}
        )
        
        results = await strategy.search(
            query=query,
            category=search_category,
            include_domains=include_domains,
            max_results=max_results
        )
        
        logger.info(
            f"Search completed",
            extra={"context": {
                "query": query,
                "results_count": len(results)
            }}
        )
        
        if not results:
            logger.warning(
                f"No results found for query",
                extra={"context": {"query": query}}
            )
            return []
        
        # Enrich results with full content using fallback mechanism
        logger.info(
            f"Enriching {len(results)} results with content",
            extra={"context": {"results_count": len(results)}}
        )
        
        try:
            fallback_strategy = create_fallback_strategy(config.search_provider)
            enriched_results = await enrich_with_content(
                results=results,
                primary_strategy=strategy,
                fallback_strategy=fallback_strategy
            )
        except Exception as e:
            logger.error(
                f"Content enrichment failed, using original results: {str(e)}",
                exc_info=True,
                extra={"context": {"error": str(e)}}
            )
            enriched_results = results
        
        # Truncate content to configured maximum
        for result in enriched_results:
            if result.content:
                result.content = truncate_content(
                    result.content,
                    max_length=config.content_max_chars
                )
        
        # Deduplicate results by domain and URL
        logger.debug(
            f"Deduplicating results",
            extra={"context": {"before_dedup": len(enriched_results)}}
        )
        
        deduplicated_results = deduplicate_results(
            enriched_results,
            by_domain=True,
            by_url=True
        )
        
        logger.info(
            f"Web search completed successfully",
            extra={"context": {
                "query": query,
                "initial_results": len(results),
                "enriched_results": len(enriched_results),
                "final_results": len(deduplicated_results)
            }}
        )
        
        return deduplicated_results
        
    except Exception as e:
        logger.error(
            f"Web search failed for query '{query}': {str(e)}",
            exc_info=True,
            extra={"context": {
                "query": query,
                "error": str(e)
            }}
        )
        # Return empty results instead of raising to allow agent to continue
        return []
