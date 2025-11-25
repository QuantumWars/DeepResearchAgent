"""Academic paper search tool using Exa API."""

import asyncio
from typing import List, Optional, Dict, Any
from langchain_core.tools import tool

from research_agent.utils.models import AcademicResult
from research_agent.utils.logger import get_logger
from research_agent.utils.config import get_config

logger = get_logger(__name__)


@tool
async def academic_search(
    queries: List[str],
    max_results: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Search academic papers and research using Exa API.
    
    This tool searches for academic papers, research articles, and scholarly content.
    It extracts paper abstracts, cleans titles, and deduplicates results by URL.
    Multiple queries are executed in parallel for efficiency.
    
    Args:
        queries: List of search queries (1-5 queries)
        max_results: Maximum results per query (default: 20 for each query)
        
    Returns:
        Dictionary containing:
        - searches: List of search results, each with query and results
        
    Examples:
        >>> result = await academic_search(["quantum computing", "machine learning"])
        >>> result = await academic_search(
        ...     ["neural networks"],
        ...     max_results=[30]
        ... )
    """
    logger.info(
        f"Starting academic search",
        extra={"context": {
            "queries": queries,
            "query_count": len(queries)
        }}
    )
    
    # Validate queries
    if not queries or len(queries) == 0:
        logger.warning("No queries provided for academic search")
        return {"searches": []}
    
    if len(queries) > 5:
        logger.warning(f"Too many queries ({len(queries)}), limiting to 5")
        queries = queries[:5]
    
    # Prepare max_results list
    if not max_results:
        max_results = [20] * len(queries)
    elif len(max_results) < len(queries):
        # Pad with default value
        max_results = max_results + [20] * (len(queries) - len(max_results))
    
    try:
        # Execute searches in parallel
        logger.info(
            f"Executing {len(queries)} academic searches in parallel",
            extra={"context": {"query_count": len(queries)}}
        )
        
        tasks = [
            _execute_academic_search(
                query=query,
                max_results=max_results[i]
            )
            for i, query in enumerate(queries)
        ]
        
        searches = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log errors
        valid_searches = []
        for i, result in enumerate(searches):
            if isinstance(result, Exception):
                logger.error(
                    f"Academic search failed for query '{queries[i]}': {str(result)}",
                    exc_info=result,
                    extra={"context": {
                        "query": queries[i],
                        "error": str(result)
                    }}
                )
            else:
                valid_searches.append(result)
        
        logger.info(
            f"Academic search completed",
            extra={"context": {
                "total_queries": len(queries),
                "successful_searches": len(valid_searches),
                "failed_searches": len(queries) - len(valid_searches)
            }}
        )
        
        return {"searches": valid_searches}
        
    except Exception as e:
        logger.error(
            f"Academic search failed: {str(e)}",
            exc_info=True,
            extra={"context": {
                "queries": queries,
                "error": str(e)
            }}
        )
        # Return empty results instead of raising
        return {"searches": []}


async def _execute_academic_search(
    query: str,
    max_results: int
) -> Dict[str, Any]:
    """Execute a single academic search query.
    
    Args:
        query: Search query
        max_results: Maximum results to return
        
    Returns:
        Dictionary with query and results list
        
    Raises:
        Exception: If the search fails
    """
    logger.debug(
        f"Executing academic search for query: {query}",
        extra={"context": {"query": query, "max_results": max_results}}
    )
    
    try:
        # Import Exa client
        try:
            from exa_py import Exa
        except ImportError:
            logger.error("Exa package not installed. Install with: pip install exa-py")
            raise ImportError("exa-py package is required for academic search")
        
        # Get API key from config
        config = get_config()
        if not config.exa_api_key:
            raise ValueError("EXA_API_KEY is required for academic search")
        
        # Create Exa client
        exa = Exa(api_key=config.exa_api_key)
        
        # Execute search with research paper category and summary
        search_results = exa.search_and_contents(
            query=query,
            type="auto",
            num_results=max_results,
            category="research paper",
            text={"max_characters": 2000},
            summary={"query": "Abstract of the paper"}
        )
        
        # Process results and deduplicate by URL
        seen_urls = set()
        processed = []
        
        for paper in search_results.results:
            try:
                # Skip if no summary or already seen
                if not paper.summary or paper.url in seen_urls:
                    continue
                
                seen_urls.add(paper.url)
                
                # Create AcademicResult (validators will clean title and summary)
                academic_result = AcademicResult(
                    title=paper.title or "Untitled",
                    url=paper.url,
                    summary=paper.summary,
                    published_date=paper.published_date if hasattr(paper, 'published_date') else None,
                    author=paper.author if hasattr(paper, 'author') else None
                )
                
                processed.append(academic_result)
                
            except Exception as e:
                logger.warning(
                    f"Failed to parse academic result: {str(e)}",
                    extra={"context": {"paper_url": paper.url if hasattr(paper, 'url') else 'unknown'}}
                )
                continue
        
        logger.debug(
            f"Academic search completed for query: {query}",
            extra={"context": {
                "query": query,
                "results_count": len(processed)
            }}
        )
        
        return {
            "query": query,
            "results": processed
        }
        
    except Exception as e:
        logger.error(
            f"Failed to execute academic search for query '{query}': {str(e)}",
            exc_info=True,
            extra={"context": {
                "query": query,
                "error": str(e)
            }}
        )
        # Return empty results instead of raising
        return {
            "query": query,
            "results": []
        }
