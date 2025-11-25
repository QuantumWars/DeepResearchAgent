"""Firecrawl search strategy implementation."""

from typing import List, Optional
from firecrawl import FirecrawlApp

from research_agent.utils.models import SearchResult, SearchCategory
from research_agent.utils.logger import get_logger
from research_agent.utils.content_processor import clean_title, generate_favicon_url, deduplicate_by_url
from .base import SearchStrategy


logger = get_logger(__name__)


class FirecrawlSearchStrategy(SearchStrategy):
    """Search strategy implementation using Firecrawl API."""
    
    def __init__(self, api_key: str):
        """
        Initialize Firecrawl search strategy.
        
        Args:
            api_key: Firecrawl API key
        """
        self.client = FirecrawlApp(api_key=api_key)
        logger.info("Initialized Firecrawl search strategy")
    
    async def search(
        self,
        query: str,
        category: Optional[SearchCategory] = None,
        include_domains: Optional[List[str]] = None,
        max_results: int = 8
    ) -> List[SearchResult]:
        """
        Execute search using Firecrawl API.
        
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
                f"Executing Firecrawl search",
                extra={"context": {
                    "query": query,
                    "category": category.value if category else None,
                    "max_results": max_results,
                    "include_domains": include_domains
                }}
            )
            
            # Determine sources based on category
            sources = ["web"]
            if category == SearchCategory.NEWS:
                sources = ["news", "web"]
            
            # Build search parameters
            search_params = {
                "query": query,
                "limit": max_results,
                "lang": "en",
                "sources": sources
            }
            
            # Execute search
            response = self.client.search(query, **search_params)
            
            # Process different result types
            all_results = []
            
            # Process web results
            if "data" in response:
                for r in response["data"]:
                    # Skip if domain filter is specified and doesn't match
                    if include_domains:
                        from research_agent.utils.content_processor import extract_domain
                        domain = extract_domain(r.get("url", ""))
                        if domain not in include_domains:
                            continue
                    
                    content = r.get("markdown", "") or r.get("content", "")
                    
                    result = SearchResult(
                        title=clean_title(r.get("title", "")) or self._extract_title_from_url(r.get("url", "")),
                        url=r.get("url", ""),
                        content=content[:1000] if content else "",  # Initial content preview
                        published_date=r.get("publishedTime"),
                        author=r.get("author"),
                        favicon=generate_favicon_url(r.get("url", ""))
                    )
                    all_results.append(result)
            
            # Deduplicate and limit results
            deduplicated = deduplicate_by_url(all_results)
            limited_results = deduplicated[:max_results]
            
            logger.info(
                f"Firecrawl search completed",
                extra={"context": {"query": query, "results_count": len(limited_results)}}
            )
            
            return limited_results
            
        except Exception as e:
            logger.error(
                f"Firecrawl search failed: {str(e)}",
                exc_info=True,
                extra={"context": {"query": query, "error": str(e)}}
            )
            return []
    
    async def get_content(
        self,
        urls: List[str]
    ) -> List[SearchResult]:
        """
        Retrieve full content for URLs using Firecrawl.
        
        Args:
            urls: List of URLs to retrieve content from
            
        Returns:
            List of SearchResult objects with full content (max 3000 chars)
        """
        if not urls:
            return []
        
        try:
            logger.info(
                f"Retrieving content from {len(urls)} URLs with Firecrawl",
                extra={"context": {"url_count": len(urls)}}
            )
            
            results = []
            
            # Firecrawl processes URLs one at a time
            for url in urls:
                try:
                    # Scrape the URL
                    response = self.client.scrape_url(
                        url,
                        params={
                            "formats": ["markdown", "html"],
                            "onlyMainContent": True
                        }
                    )
                    
                    # Extract content
                    content = ""
                    if "markdown" in response:
                        content = response["markdown"]
                    elif "content" in response:
                        content = response["content"]
                    
                    # Skip if no content
                    if not content or not content.strip():
                        logger.debug(
                            f"Skipping URL with no content: {url}",
                            extra={"context": {"url": url}}
                        )
                        continue
                    
                    # Limit content to 3000 characters
                    content = content[:3000]
                    
                    # Extract metadata
                    metadata = response.get("metadata", {})
                    
                    result = SearchResult(
                        title=clean_title(metadata.get("title", "")) or self._extract_title_from_url(url),
                        url=url,
                        content=content,
                        published_date=metadata.get("publishedTime"),
                        author=metadata.get("author"),
                        favicon=generate_favicon_url(url)
                    )
                    results.append(result)
                    
                except Exception as url_error:
                    logger.warning(
                        f"Failed to retrieve content for URL: {url}",
                        extra={"context": {"url": url, "error": str(url_error)}}
                    )
                    continue
            
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
                f"Firecrawl content retrieval failed: {str(e)}",
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
