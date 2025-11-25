"""Content enrichment utilities with fallback mechanisms."""

from typing import List, Set
from research_agent.utils.models import SearchResult
from research_agent.utils.logger import get_logger
from .base import SearchStrategy


logger = get_logger(__name__)


async def enrich_with_content(
    results: List[SearchResult],
    primary_strategy: SearchStrategy,
    fallback_strategy: SearchStrategy
) -> List[SearchResult]:
    """
    Enrich search results with full content using primary and fallback strategies.
    
    This function attempts to retrieve full content for search results using a primary
    strategy (e.g., Exa). For any URLs that fail with the primary strategy, it retries
    using a fallback strategy (e.g., Firecrawl).
    
    Args:
        results: List of search results to enrich with content
        primary_strategy: Primary search strategy to use for content retrieval
        fallback_strategy: Fallback strategy to use if primary fails
        
    Returns:
        List of SearchResult objects enriched with full content
        
    Example:
        >>> exa = ExaSearchStrategy(api_key="...")
        >>> firecrawl = FirecrawlSearchStrategy(api_key="...")
        >>> results = await web_search("quantum computing")
        >>> enriched = await enrich_with_content(results, exa, firecrawl)
    """
    if not results:
        return []
    
    urls = [r.url for r in results]
    
    logger.info(
        f"Enriching {len(urls)} results with content",
        extra={"context": {
            "url_count": len(urls),
            "primary_strategy": primary_strategy.__class__.__name__,
            "fallback_strategy": fallback_strategy.__class__.__name__
        }}
    )
    
    # Try primary strategy first
    enriched_results = []
    failed_urls = []
    
    try:
        logger.debug(
            f"Attempting content retrieval with primary strategy: {primary_strategy.__class__.__name__}",
            extra={"context": {"url_count": len(urls)}}
        )
        
        primary_results = await primary_strategy.get_content(urls)
        
        # Track which URLs succeeded
        enriched_urls: Set[str] = {r.url for r in primary_results if r.content and r.content.strip()}
        enriched_results.extend([r for r in primary_results if r.url in enriched_urls])
        
        # Identify failed URLs
        failed_urls = [url for url in urls if url not in enriched_urls]
        
        logger.info(
            f"Primary strategy completed",
            extra={"context": {
                "successful": len(enriched_urls),
                "failed": len(failed_urls)
            }}
        )
        
    except Exception as e:
        logger.error(
            f"Primary content retrieval failed: {str(e)}",
            exc_info=True,
            extra={"context": {
                "strategy": primary_strategy.__class__.__name__,
                "error": str(e)
            }}
        )
        # All URLs failed with primary strategy
        failed_urls = urls
    
    # Try fallback strategy for failed URLs
    if failed_urls:
        logger.info(
            f"Retrying {len(failed_urls)} failed URLs with fallback strategy: {fallback_strategy.__class__.__name__}",
            extra={"context": {"failed_url_count": len(failed_urls)}}
        )
        
        try:
            fallback_results = await fallback_strategy.get_content(failed_urls)
            
            # Add successful fallback results
            fallback_success = [r for r in fallback_results if r.content and r.content.strip()]
            enriched_results.extend(fallback_success)
            
            logger.info(
                f"Fallback strategy completed",
                extra={"context": {
                    "attempted": len(failed_urls),
                    "successful": len(fallback_success)
                }}
            )
            
        except Exception as e:
            logger.error(
                f"Fallback content retrieval failed: {str(e)}",
                exc_info=True,
                extra={"context": {
                    "strategy": fallback_strategy.__class__.__name__,
                    "error": str(e)
                }}
            )
    
    # Merge enriched results with original results
    # For URLs that failed both strategies, keep the original result
    enriched_map = {r.url: r for r in enriched_results}
    
    final_results = []
    for original in results:
        if original.url in enriched_map:
            # Use enriched version
            final_results.append(enriched_map[original.url])
        else:
            # Keep original (no content retrieved)
            logger.debug(
                f"No content retrieved for URL: {original.url}",
                extra={"context": {"url": original.url}}
            )
            final_results.append(original)
    
    logger.info(
        f"Content enrichment completed",
        extra={"context": {
            "total_results": len(final_results),
            "enriched": len(enriched_results),
            "original": len(results)
        }}
    )
    
    return final_results
