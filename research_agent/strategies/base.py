"""Base class for search strategies."""

from abc import ABC, abstractmethod
from typing import List, Optional

from research_agent.utils.models import SearchResult, SearchCategory


class SearchStrategy(ABC):
    """Abstract base class for search strategy implementations."""
    
    @abstractmethod
    async def search(
        self,
        query: str,
        category: Optional[SearchCategory] = None,
        include_domains: Optional[List[str]] = None,
        max_results: int = 8
    ) -> List[SearchResult]:
        """
        Execute a search query and return results.
        
        Args:
            query: Search query string
            category: Optional category filter (news, company, research_paper, etc.)
            include_domains: Optional list of domains to filter results
            max_results: Maximum number of results to return (default 8)
            
        Returns:
            List of SearchResult objects with metadata
            
        Raises:
            Should handle errors gracefully and return empty list on failure
        """
        pass
    
    @abstractmethod
    async def get_content(
        self,
        urls: List[str]
    ) -> List[SearchResult]:
        """
        Retrieve full content for a list of URLs.
        
        Args:
            urls: List of URLs to retrieve content from
            
        Returns:
            List of SearchResult objects with full content
            
        Raises:
            Should handle errors gracefully and return empty list on failure
        """
        pass
