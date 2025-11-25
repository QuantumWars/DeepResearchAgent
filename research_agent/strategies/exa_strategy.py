"""Exa search strategy implementation."""

from typing import List, Optional
from exa_py import Exa

from research_agent.utils.models import SearchResult, SearchCategory
from research_agent.utils.logger import get_logger
from research_agent.utils.content_processor import clean_title, generate_favicon_url
from .base import SearchStrategy


logger = get_logger(__name__)


class ExaSearchStrategy(SearchStrategy):
    """Search strategy implementation using Exa API."""
    
    def __init__(self, api_key: str):
        """
        Initialize Exa search strategy.
        
        Args:
            api_key: Exa API key
        """
        self.client = Exa(api_key=api_key)
        logger.info("Initialized Exa search strategy")
    
    async def search(
        self,
        query: str,
        category: Optional[SearchCategory] = None,
        include_domains: Optional[List[str]] = None,
        max_results: int = 8
    ) -> List[SearchResult]:
        """
        Execute search using Exa API.
        
        Args:
            query: Search query string
            category: Optional category filter
            include_domains: Optional list of domains to filter results
            max_results: Maximum number of results (default 8)
            
        Returns:
            List of SearchResult objects
        """
        try:
            logger.info(
                f"Executing Exa search",
                extra={"context": {
                    "query": query,
                    "category": category.value if category else None,
                    "max_results": max_results,
                    "include_domains": include_domains
                }}
            )
            
            # Build search parameters
            search_params = {
                "query": query,
                "num_results": max_results,
                "type": "auto",
                "text": True,
                "livecrawl": "preferred"
            }
            
            # Add category if specified
            if category:
                search_params["category"] = category.value
            
            # Add domain filters if specified
            if include_domains:
                search_params["include_domains"] = include_domains
            
            # Execute search with content
            response = self.client.search_and_contents(**search_params)
            
            # Process results
            results = []
            for r in response.results:
                # Skip results without text content
                if not r.text or not r.text.strip():
                    continue
                
                result = SearchResult(
                    title=clean_title(r.title) if r.title else self._extract_title_from_url(r.url),
                    url=r.url,
                    content=r.text[:1000] if r.text else "",  # Initial content preview
                    published_date=r.published_date if hasattr(r, 'published_date') else None,
                    author=r.author if hasattr(r, 'author') else None,
                    favicon=r.favicon if hasattr(r, 'favicon') and r.favicon else generate_favicon_url(r.url)
                )
                results.append(result)
            
            logger.info(
                f"Exa search completed",
                extra={"context": {"query": query, "results_count": len(results)}}
            )
            
            return results
            
        except Exception as e:
            logger.error(
                f"Exa search failed: {str(e)}",
                exc_info=True,
                extra={"context": {"query": query, "error": str(e)}}
            )
            return []
    
    async def get_content(
        self,
        urls: List[str]
    ) -> List[SearchResult]:
        """
        Retrieve full content for URLs using Exa.
        
        Args:
            urls: List of URLs to retrieve content from
            
        Returns:
            List of SearchResult objects with full content (max 3000 chars)
        """
        if not urls:
            return []
        
        try:
            logger.info(
                f"Retrieving content from {len(urls)} URLs with Exa",
                extra={"context": {"url_count": len(urls)}}
            )
            
            # Get content with 3000 character limit
            response = self.client.get_contents(
                urls,
                text={"max_characters": 3000},
                livecrawl="preferred"
            )
            
            # Process results
            results = []
            for r in response.results:
                # Skip results without text content
                if not r.text or not r.text.strip():
                    logger.debug(
                        f"Skipping URL with no content: {r.url}",
                        extra={"context": {"url": r.url}}
                    )
                    continue
                
                result = SearchResult(
                    title=clean_title(r.title) if r.title else self._extract_title_from_url(r.url),
                    url=r.url,
                    content=r.text,
                    published_date=r.published_date if hasattr(r, 'published_date') else None,
                    author=r.author if hasattr(r, 'author') else None,
                    favicon=r.favicon if hasattr(r, 'favicon') and r.favicon else generate_favicon_url(r.url)
                )
                results.append(result)
            
            logger.info(
                f"Content retrieval completed",
                extra={"context": {
                    "requested_urls": len(urls),
                    "successful_results": len(results)
                }}
            )
            
            return results
            
        except Exception as e:
            logger.error(
                f"Exa content retrieval failed: {str(e)}",
                exc_info=True,
                extra={"context": {"url_count": len(urls), "error": str(e)}}
            )
            return []
    
    def _extract_title_from_url(self, url: str) -> str:
        """
        Extract a title from a URL when no title is available.
        
        Args:
            url: URL string
            
        Returns:
            Extracted title
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            # Use the path or domain as title
            if parsed.path and parsed.path != '/':
                title = parsed.path.strip('/').replace('-', ' ').replace('_', ' ')
                return title.title()
            else:
                return parsed.netloc
        except Exception:
            return url
