"""Reddit search tool using Tavily API."""

import asyncio
import re
from typing import List, Optional, Dict, Any, Literal
from langchain_core.tools import tool

from research_agent.utils.models import RedditResult
from research_agent.utils.logger import get_logger
from research_agent.utils.config import get_config

logger = get_logger(__name__)


@tool
async def reddit_search(
    queries: List[str],
    max_results: Optional[List[int]] = None,
    time_range: Optional[List[Literal['day', 'week', 'month', 'year']]] = None
) -> Dict[str, Any]:
    """
    Search Reddit content using Tavily API with Reddit domain filtering.
    
    This tool searches Reddit for posts and comments matching the given queries.
    It supports time range filtering and returns post content, scores, and metadata.
    Multiple queries are executed in parallel for efficiency.
    
    Args:
        queries: List of search queries (1-5 queries)
        max_results: Maximum results per query (default: 20 for each query)
        time_range: Time range per query - 'day', 'week', 'month', or 'year' (default: 'week')
        
    Returns:
        Dictionary containing:
        - searches: List of search results, each with query, results, and time_range
        
    Examples:
        >>> result = await reddit_search(["python programming", "machine learning"])
        >>> result = await reddit_search(
        ...     ["AI news"],
        ...     max_results=[30],
        ...     time_range=["day"]
        ... )
    """
    logger.info(
        f"Starting Reddit search",
        extra={"context": {
            "queries": queries,
            "query_count": len(queries)
        }}
    )
    
    # Validate queries
    if not queries or len(queries) == 0:
        logger.warning("No queries provided for Reddit search")
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
    
    # Prepare time_range list
    if not time_range:
        time_range = ['week'] * len(queries)
    elif len(time_range) < len(queries):
        # Pad with default value
        time_range = time_range + ['week'] * (len(queries) - len(time_range))
    
    try:
        # Execute searches in parallel
        logger.info(
            f"Executing {len(queries)} Reddit searches in parallel",
            extra={"context": {"query_count": len(queries)}}
        )
        
        tasks = [
            _execute_reddit_search(
                query=query,
                max_results=max_results[i],
                time_range=time_range[i]
            )
            for i, query in enumerate(queries)
        ]
        
        searches = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log errors
        valid_searches = []
        for i, result in enumerate(searches):
            if isinstance(result, Exception):
                logger.error(
                    f"Reddit search failed for query '{queries[i]}': {str(result)}",
                    exc_info=result,
                    extra={"context": {
                        "query": queries[i],
                        "error": str(result)
                    }}
                )
            else:
                valid_searches.append(result)
        
        logger.info(
            f"Reddit search completed",
            extra={"context": {
                "total_queries": len(queries),
                "successful_searches": len(valid_searches),
                "failed_searches": len(queries) - len(valid_searches)
            }}
        )
        
        return {"searches": valid_searches}
        
    except Exception as e:
        logger.error(
            f"Reddit search failed: {str(e)}",
            exc_info=True,
            extra={"context": {
                "queries": queries,
                "error": str(e)
            }}
        )
        # Return empty results instead of raising
        return {"searches": []}


async def _execute_reddit_search(
    query: str,
    max_results: int,
    time_range: str
) -> Dict[str, Any]:
    """Execute a single Reddit search query.
    
    Args:
        query: Search query
        max_results: Maximum results to return
        time_range: Time range filter ('day', 'week', 'month', 'year')
        
    Returns:
        Dictionary with query, results list, and time_range
        
    Raises:
        Exception: If the search fails
    """
    logger.debug(
        f"Executing Reddit search for query: {query}",
        extra={"context": {"query": query, "time_range": time_range}}
    )
    
    try:
        # Import Tavily client
        try:
            from tavily import TavilyClient
        except ImportError:
            logger.error("Tavily package not installed. Install with: pip install tavily-python")
            raise ImportError("tavily-python package is required for Reddit search")
        
        # Get API key from config
        config = get_config()
        if not config.tavily_api_key:
            raise ValueError("TAVILY_API_KEY is required for Reddit search")
        
        # Create Tavily client
        tavily = TavilyClient(api_key=config.tavily_api_key)
        
        # Execute search with Reddit domain filtering
        # Request more results than needed to account for filtering
        search_results = tavily.search(
            query=query,
            max_results=max(20, max_results),
            search_depth='advanced',
            include_raw_content=True,
            topic='general',
            include_domains=['reddit.com'],
            days=_time_range_to_days(time_range)
        )
        
        # Process results
        processed = []
        for result in search_results.get('results', []):
            try:
                url = result.get('url', '')
                
                # Check if it's a Reddit post (has /comments/ in URL)
                is_post = '/comments/' in url
                
                # Extract subreddit from URL
                subreddit = _extract_subreddit(url)
                
                # Create RedditResult
                reddit_result = RedditResult(
                    url=url,
                    title=result.get('title', ''),
                    content=result.get('content', result.get('raw_content', '')),
                    score=result.get('score', 0.0),
                    published_date=result.get('published_date'),
                    subreddit=subreddit,
                    is_reddit_post=is_post
                )
                
                processed.append(reddit_result)
                
            except Exception as e:
                logger.warning(
                    f"Failed to parse Reddit result: {str(e)}",
                    extra={"context": {"result": result}}
                )
                continue
        
        # Limit to requested max_results
        processed = processed[:max_results]
        
        logger.debug(
            f"Reddit search completed for query: {query}",
            extra={"context": {
                "query": query,
                "results_count": len(processed),
                "time_range": time_range
            }}
        )
        
        return {
            "query": query,
            "results": processed,
            "time_range": time_range
        }
        
    except Exception as e:
        logger.error(
            f"Failed to execute Reddit search for query '{query}': {str(e)}",
            exc_info=True,
            extra={"context": {
                "query": query,
                "error": str(e)
            }}
        )
        # Return empty results instead of raising
        return {
            "query": query,
            "results": [],
            "time_range": time_range
        }


def _extract_subreddit(url: str) -> str:
    """Extract subreddit name from Reddit URL.
    
    Args:
        url: Reddit URL
        
    Returns:
        Subreddit name (without r/ prefix), or 'unknown' if not found
    """
    # Pattern to match /r/subreddit_name/ in URL
    match = re.search(r'reddit\.com/r/([^/]+)', url, re.IGNORECASE)
    if match:
        return match.group(1)
    return 'unknown'


def _time_range_to_days(time_range: str) -> Optional[int]:
    """Convert time range string to number of days.
    
    Args:
        time_range: Time range ('day', 'week', 'month', 'year')
        
    Returns:
        Number of days, or None for no limit
    """
    time_map = {
        'day': 1,
        'week': 7,
        'month': 30,
        'year': 365
    }
    return time_map.get(time_range.lower())
