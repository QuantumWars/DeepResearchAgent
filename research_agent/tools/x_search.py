"""X (Twitter) search tool using xAI Grok API."""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from langchain_core.tools import tool

from research_agent.clients.xai_client import XAIClient
from research_agent.utils.models import XPost, XSearchResult
from research_agent.utils.logger import get_logger
from research_agent.utils.config import get_config

logger = get_logger(__name__)


@tool
async def x_search(
    queries: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    include_x_handles: Optional[List[str]] = None,
    exclude_x_handles: Optional[List[str]] = None,
    post_favorites_count: Optional[int] = None,
    post_view_count: Optional[int] = None,
    max_results: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Search X (Twitter) posts using xAI Grok API with live search capabilities.
    
    This tool searches X for posts matching the given queries and filters.
    It supports date range filtering, handle filtering, and engagement metrics.
    Multiple queries are executed in parallel for efficiency.
    
    Args:
        queries: List of search queries (1-5 queries)
        start_date: Start date in YYYY-MM-DD format (default: 15 days ago)
        end_date: End date in YYYY-MM-DD format (default: today)
        include_x_handles: X handles to include in search (max 10, with or without @)
        exclude_x_handles: X handles to exclude from search (max 10, with or without @)
        post_favorites_count: Minimum number of favorites required
        post_view_count: Minimum number of views required
        max_results: Maximum results per query (default: 15 for each query)
        
    Returns:
        Dictionary containing:
        - searches: List of XSearchResult objects with content, citations, and sources
        - date_range: Date range used for the search
        - handles: List of handles used in filtering
        
    Examples:
        >>> result = await x_search(["AI news", "machine learning"])
        >>> result = await x_search(
        ...     ["python"],
        ...     include_x_handles=["@elonmusk"],
        ...     post_favorites_count=100
        ... )
    """
    logger.info(
        f"Starting X search",
        extra={"context": {
            "queries": queries,
            "query_count": len(queries),
            "start_date": start_date,
            "end_date": end_date
        }}
    )
    
    # Validate queries
    if not queries or len(queries) == 0:
        logger.warning("No queries provided for X search")
        return {
            "searches": [],
            "date_range": "",
            "handles": []
        }
    
    if len(queries) > 5:
        logger.warning(f"Too many queries ({len(queries)}), limiting to 5")
        queries = queries[:5]
    
    # Validate handles
    if include_x_handles and len(include_x_handles) > 10:
        logger.warning(f"Too many include handles ({len(include_x_handles)}), limiting to 10")
        include_x_handles = include_x_handles[:10]
    
    if exclude_x_handles and len(exclude_x_handles) > 10:
        logger.warning(f"Too many exclude handles ({len(exclude_x_handles)}), limiting to 10")
        exclude_x_handles = exclude_x_handles[:10]
    
    # Set default date range (15 days)
    if not start_date:
        start_date = (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    date_range_str = f"{start_date} to {end_date}"
    
    # Prepare max_results list
    if not max_results:
        max_results = [15] * len(queries)
    elif len(max_results) < len(queries):
        # Pad with default value
        max_results = max_results + [15] * (len(queries) - len(max_results))
    
    try:
        # Create XAI client
        client = XAIClient()
        
        # Execute searches in parallel
        logger.info(
            f"Executing {len(queries)} X searches in parallel",
            extra={"context": {"query_count": len(queries)}}
        )
        
        tasks = [
            _execute_x_search(
                client=client,
                query=query,
                start_date=start_date,
                end_date=end_date,
                include_x_handles=include_x_handles,
                exclude_x_handles=exclude_x_handles,
                post_favorites_count=post_favorites_count,
                post_view_count=post_view_count,
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
                    f"X search failed for query '{queries[i]}': {str(result)}",
                    exc_info=result,
                    extra={"context": {
                        "query": queries[i],
                        "error": str(result)
                    }}
                )
            else:
                valid_searches.append(result)
        
        # Close client
        await client.close()
        
        logger.info(
            f"X search completed",
            extra={"context": {
                "total_queries": len(queries),
                "successful_searches": len(valid_searches),
                "failed_searches": len(queries) - len(valid_searches)
            }}
        )
        
        # Collect all handles used
        all_handles = []
        if include_x_handles:
            all_handles.extend(include_x_handles)
        if exclude_x_handles:
            all_handles.extend(exclude_x_handles)
        
        return {
            "searches": valid_searches,
            "date_range": date_range_str,
            "handles": all_handles
        }
        
    except Exception as e:
        logger.error(
            f"X search failed: {str(e)}",
            exc_info=True,
            extra={"context": {
                "queries": queries,
                "error": str(e)
            }}
        )
        # Return empty results instead of raising
        return {
            "searches": [],
            "date_range": date_range_str,
            "handles": include_x_handles or exclude_x_handles or []
        }


async def _execute_x_search(
    client: XAIClient,
    query: str,
    start_date: str,
    end_date: str,
    include_x_handles: Optional[List[str]],
    exclude_x_handles: Optional[List[str]],
    post_favorites_count: Optional[int],
    post_view_count: Optional[int],
    max_results: int
) -> XSearchResult:
    """Execute a single X search query.
    
    Args:
        client: XAI client instance
        query: Search query
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        include_x_handles: Handles to include
        exclude_x_handles: Handles to exclude
        post_favorites_count: Minimum favorites
        post_view_count: Minimum views
        max_results: Maximum results to return
        
    Returns:
        XSearchResult with content, citations, and sources
        
    Raises:
        Exception: If the search fails
    """
    logger.debug(
        f"Executing X search for query: {query}",
        extra={"context": {"query": query}}
    )
    
    try:
        # Execute search with Grok
        response = await client.search_with_grok(
            query=query,
            start_date=start_date,
            end_date=end_date,
            max_results=max_results,
            include_x_handles=include_x_handles,
            exclude_x_handles=exclude_x_handles,
            post_favorites_count=post_favorites_count,
            post_view_count=post_view_count
        )
        
        # Extract content from response
        content = ""
        if "choices" in response and len(response["choices"]) > 0:
            message = response["choices"][0].get("message", {})
            content = message.get("content", "")
        
        # Extract citations
        citations = response.get("citations", [])
        
        # Extract sources and convert to XPost objects
        sources = []
        if "sources" in response:
            for source in response["sources"]:
                if source.get("type") == "x":
                    try:
                        post = XPost(
                            text=source.get("text", ""),
                            link=source.get("link", source.get("url", "")),
                            favorites=source.get("favorites"),
                            views=source.get("views"),
                            author=source.get("author")
                        )
                        sources.append(post)
                    except Exception as e:
                        logger.warning(
                            f"Failed to parse X post: {str(e)}",
                            extra={"context": {"source": source}}
                        )
                        continue
        
        # Create result
        result = XSearchResult(
            content=content or "No content returned from search",
            citations=citations,
            sources=sources,
            query=query,
            date_range=f"{start_date} to {end_date}",
            handles=include_x_handles or exclude_x_handles or []
        )
        
        logger.debug(
            f"X search completed for query: {query}",
            extra={"context": {
                "query": query,
                "sources_count": len(sources),
                "citations_count": len(citations)
            }}
        )
        
        return result
        
    except Exception as e:
        logger.error(
            f"Failed to execute X search for query '{query}': {str(e)}",
            exc_info=True,
            extra={"context": {
                "query": query,
                "error": str(e)
            }}
        )
        raise
