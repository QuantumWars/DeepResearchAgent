"""xAI Grok API client for X/Twitter search functionality."""

import asyncio
from typing import Dict, Any, Optional, List
import httpx
from research_agent.utils.logger import get_logger
from research_agent.utils.config import get_config
from research_agent.utils.retry import retry_async, RetryConfig

logger = get_logger(__name__)


class XAIClient:
    """Client for interacting with xAI Grok API.
    
    This client provides methods for searching X (Twitter) posts using
    the Grok API with live search capabilities. It includes retry logic,
    rate limiting handling, and proper error management.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the xAI client.
        
        Args:
            api_key: xAI API key. If not provided, will be loaded from config.
        """
        self.api_key = api_key or get_config().xai_api_key
        if not self.api_key:
            raise ValueError("XAI_API_KEY is required for X search functionality")
        
        self.base_url = "https://api.x.ai/v1"
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=httpx.Timeout(60.0, connect=10.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
        logger.debug("Initialized XAI client")
    
    async def search_with_grok(
        self,
        query: str,
        start_date: str,
        end_date: str,
        max_results: int = 15,
        include_x_handles: Optional[List[str]] = None,
        exclude_x_handles: Optional[List[str]] = None,
        post_favorites_count: Optional[int] = None,
        post_view_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute X search using Grok API with retry logic.
        
        Args:
            query: Search query string
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            max_results: Maximum number of results to return (default: 15)
            include_x_handles: List of X handles to include in search
            exclude_x_handles: List of X handles to exclude from search
            post_favorites_count: Minimum favorites count filter
            post_view_count: Minimum view count filter
            
        Returns:
            Dictionary containing search results with content, citations, and sources
            
        Raises:
            httpx.HTTPError: If the request fails after all retries
        """
        logger.info(
            f"Executing X search with Grok",
            extra={"context": {
                "query": query,
                "date_range": f"{start_date} to {end_date}",
                "max_results": max_results
            }}
        )
        
        # Build search parameters
        search_params = {
            "mode": "on",
            "from_date": start_date,
            "to_date": end_date,
            "max_search_results": max_results,
            "return_citations": True,
            "sources": [self._build_x_source_filter(
                include_x_handles,
                exclude_x_handles,
                post_favorites_count,
                post_view_count
            )]
        }
        
        # Build request payload
        payload = {
            "model": "grok-2-latest",
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ],
            "search_parameters": search_params
        }
        
        # Execute with retry logic using centralized retry utility
        retry_config = RetryConfig(
            max_retries=3,
            initial_backoff=1.0,
            max_backoff=60.0,
            exponential_base=2.0,
            retry_on_timeout=True,
            retry_on_connection_error=True,
            retry_on_rate_limit=True
        )
        
        async def _make_request():
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        
        result = await retry_async(
            _make_request,
            config=retry_config,
            context={"query": query, "operation": "x_search"}
        )
        
        logger.info(
            f"X search completed successfully",
            extra={"context": {"query": query}}
        )
        
        return result
    
    def _build_x_source_filter(
        self,
        include_x_handles: Optional[List[str]],
        exclude_x_handles: Optional[List[str]],
        post_favorites_count: Optional[int],
        post_view_count: Optional[int]
    ) -> Dict[str, Any]:
        """Build X source filter parameters.
        
        Args:
            include_x_handles: Handles to include
            exclude_x_handles: Handles to exclude
            post_favorites_count: Minimum favorites
            post_view_count: Minimum views
            
        Returns:
            Dictionary with X source filter parameters
        """
        source_filter = {"type": "x"}
        
        if include_x_handles:
            # Ensure handles start with @
            formatted_handles = [
                h if h.startswith('@') else f'@{h}'
                for h in include_x_handles
            ]
            source_filter["include_x_handles"] = formatted_handles
        
        if exclude_x_handles:
            # Ensure handles start with @
            formatted_handles = [
                h if h.startswith('@') else f'@{h}'
                for h in exclude_x_handles
            ]
            source_filter["exclude_x_handles"] = formatted_handles
        
        if post_favorites_count is not None:
            source_filter["post_favorites_count"] = post_favorites_count
        
        if post_view_count is not None:
            source_filter["post_view_count"] = post_view_count
        
        return source_filter
    
    async def close(self) -> None:
        """Close the HTTP client connection."""
        await self.client.aclose()
        logger.debug("Closed XAI client")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
