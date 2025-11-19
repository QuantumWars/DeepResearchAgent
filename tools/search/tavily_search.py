"""Tavily search tool implementation."""

import os
import logging
from typing import List

from tavily import TavilyClient

from registry.base_tool import BaseSearchTool
from models.tool_schemas import SearchResult

logger = logging.getLogger(__name__)


class TavilySearch(BaseSearchTool):
    """Tavily Search API implementation."""
    
    name = "tavily"
    priority = 10
    requires_api_key = True
    
    def __init__(self, api_key: str = None):
        """
        Initialize Tavily Search client.
        
        Args:
            api_key: Tavily API key (optional, will try to load from environment)
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            logger.warning("Tavily API key not found in config or environment")
            self.client = None
        else:
            try:
                self.client = TavilyClient(api_key=self.api_key)
                logger.debug("Tavily client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Tavily client: {e}")
                self.client = None
    
    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        Execute search via Tavily API.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects, empty list on failure
        """
        if not self.client:
            logger.error("Tavily client not initialized, cannot perform search")
            return []
        
        try:
            logger.info(f"Executing Tavily search for query: {query}")
            
            # Call Tavily API
            response = self.client.search(
                query=query,
                max_results=max_results
            )
            
            # Parse response into SearchResult objects
            results = []
            if response and "results" in response:
                for item in response["results"][:max_results]:
                    result = SearchResult(
                        url=item.get("url", ""),
                        title=item.get("title", ""),
                        snippet=item.get("content", ""),
                        relevance_score=item.get("score")
                    )
                    results.append(result)
            
            logger.info(f"Tavily search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return []
