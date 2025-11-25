"""Tavily search strategy implementation."""

from typing import List, Optional
from tavily import TavilyClient

from research_agent.utils.models import SearchResult, SearchCategory
from research_agent.utils.logger import get_logger
from research_agent.utils.content_processor import clean_title, generate_favicon_url
from .base import SearchStrategy


logger = get_logger(__name__)


class TavilySearchStrategy(SearchStrategy):
    """Search strategy implementation using Tavily API."""
    
    def __init__(self, api_key: str):
        """
        Initialize Tavily search strategy.
        
        Args:
            api_key: Tavily API key
        """
        self.client = TavilyClient(api_key=api_key)
        logger.info("Initialized Tavily search strategy")
    
    async def search(
        self,
        query: str,
        category: Optional[SearchCategory] = None,
        include_domains: Optional[List[str]] = None,
        max_results: int = 8
    ) -> List[SearchResult]:
        """
        Execute search using Tavily API.
        
        Args:
            query: Search query string
            category: Optional category filter (used to determine topic)
            include_domains: Optional list of domains to filter results
            max_results: Maximum number of results (default 8)
            
        Returns:
            List of SearchResult objects
        """
        try:
            logger.info(
                f"Executing Tavily search",
                extra={"context": {
                    "query": query,
                    "category": category.value if category else None,
                    "max_results": max_results,
                    "include_domains": include_domains
                }}
            )
            
            # Determine topic based on category
            topic = "news" if category == SearchCategory.NEWS else "general"
            
            # Build search parameters
            search_params = {
                "query": query,
                "max_results": max_results,
                "topic": topic,
                "search_depth": "advanced",
                "include_images": True,
                "include_answer": False,
                "include_raw_content": True
            }
            
            # Add domain filters if specified
            if include_domains:
                search_params["include_domains"] = include_domains
            
            # Execute search
            response = self.client.search(**search_params)
            
            # Process results
            results = []
            for r in response.get("results", []):
                # Validate image URLs if present
                images = []
                if "images" in r and r["images"]:
                    images = [img for img in r["images"] if self._is_valid_image_url(img)]
                
                # Get content from raw_content or content field
                content = r.get("raw_content", "") or r.get("content", "")
                
                result = SearchResult(
                    title=clean_title(r.get("title", "")) or self._extract_title_from_url(r.get("url", "")),
                    url=r.get("url", ""),
                    content=content[:1000] if content else "",  # Initial content preview
                    published_date=r.get("published_date"),
                    author=None,  # Tavily doesn't provide author
                    favicon=generate_favicon_url(r.get("url", ""))
                )
                results.append(result)
            
            logger.info(
                f"Tavily search completed",
                extra={"context": {"query": query, "results_count": len(results)}}
            )
            
            return results
            
        except Exception as e:
            logger.error(
                f"Tavily search failed: {str(e)}",
                exc_info=True,
                extra={"context": {"query": query, "error": str(e)}}
            )
            return []
    
    async def get_content(
        self,
        urls: List[str]
    ) -> List[SearchResult]:
        """
        Retrieve full content for URLs using Tavily.
        
        Note: Tavily doesn't have a dedicated content retrieval endpoint,
        so this method returns empty results. Use as fallback with other strategies.
        
        Args:
            urls: List of URLs to retrieve content from
            
        Returns:
            Empty list (Tavily doesn't support direct content retrieval)
        """
        logger.debug(
            f"Tavily does not support direct content retrieval for {len(urls)} URLs",
            extra={"context": {"url_count": len(urls)}}
        )
        return []
    
    def _is_valid_image_url(self, url: str) -> bool:
        """
        Validate that an image URL is properly formatted.
        
        Args:
            url: Image URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        if not url or not isinstance(url, str):
            return False
        
        # Check if URL starts with http/https
        if not url.startswith(("http://", "https://")):
            return False
        
        # Check if URL has a valid image extension
        valid_extensions = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg")
        url_lower = url.lower()
        
        # Check extension or if it's from a known image service
        has_extension = any(url_lower.endswith(ext) for ext in valid_extensions)
        is_image_service = any(service in url_lower for service in ["imgur", "cloudinary", "unsplash"])
        
        return has_extension or is_image_service
    
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
