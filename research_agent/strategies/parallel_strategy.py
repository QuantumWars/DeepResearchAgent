"""Parallel AI search strategy implementation."""

from typing import List, Optional
import httpx

from research_agent.utils.models import SearchResult, SearchCategory
from research_agent.utils.logger import get_logger
from research_agent.utils.content_processor import clean_title, generate_favicon_url, deduplicate_by_url
from .base import SearchStrategy


logger = get_logger(__name__)


class ParallelSearchStrategy(SearchStrategy):
    """Search strategy implementation using Parallel AI API."""
    
    def __init__(self, api_key: str, firecrawl_api_key: Optional[str] = None):
        """
        Initialize Parallel AI search strategy.
        
        Args:
            api_key: Parallel AI API key
            firecrawl_api_key: Optional Firecrawl API key for image search
        """
        self.api_key = api_key
        self.base_url = "https://api.parallel.ai/v1"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )
        
        # Optional Firecrawl integration for images
        self.firecrawl_client = None
        if firecrawl_api_key:
            try:
                from firecrawl import FirecrawlApp
                self.firecrawl_client = FirecrawlApp(api_key=firecrawl_api_key)
            except ImportError:
                logger.warning("Firecrawl not available for image search")
        
        logger.info("Initialized Parallel AI search strategy")
    
    async def search(
        self,
        query: str,
        category: Optional[SearchCategory] = None,
        include_domains: Optional[List[str]] = None,
        max_results: int = 8
    ) -> List[SearchResult]:
        """
        Execute search using Parallel AI API.
        
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
                f"Executing Parallel AI search",
                extra={"context": {
                    "query": query,
                    "category": category.value if category else None,
                    "max_results": max_results,
                    "include_domains": include_domains
                }}
            )
            
            # Determine processor quality (use "pro" for better results)
            processor_quality = "pro"
            
            # Build search request
            search_payload = {
                "query": query,
                "max_results": max_results,
                "processor": processor_quality
            }
            
            # Add domain filters if specified
            if include_domains:
                search_payload["domains"] = include_domains
            
            # Execute search
            response = await self.client.post("/search", json=search_payload)
            response.raise_for_status()
            data = response.json()
            
            # Process results
            results = []
            for r in data.get("results", []):
                content = r.get("content", "") or r.get("snippet", "")
                
                result = SearchResult(
                    title=clean_title(r.get("title", "")) or self._extract_title_from_url(r.get("url", "")),
                    url=r.get("url", ""),
                    content=content[:1000] if content else "",  # Initial content preview
                    published_date=r.get("published_date"),
                    author=r.get("author"),
                    favicon=generate_favicon_url(r.get("url", ""))
                )
                results.append(result)
            
            # Optionally add images from Firecrawl if available
            if self.firecrawl_client and len(results) < max_results:
                try:
                    image_results = await self._get_firecrawl_images(query, max_results - len(results))
                    results.extend(image_results)
                except Exception as img_error:
                    logger.warning(
                        f"Failed to fetch images from Firecrawl: {str(img_error)}",
                        extra={"context": {"error": str(img_error)}}
                    )
            
            # Deduplicate results
            deduplicated = deduplicate_by_url(results)
            
            logger.info(
                f"Parallel AI search completed",
                extra={"context": {"query": query, "results_count": len(deduplicated)}}
            )
            
            return deduplicated
            
        except Exception as e:
            logger.error(
                f"Parallel AI search failed: {str(e)}",
                exc_info=True,
                extra={"context": {"query": query, "error": str(e)}}
            )
            return []
    
    async def get_content(
        self,
        urls: List[str]
    ) -> List[SearchResult]:
        """
        Retrieve full content for URLs using Parallel AI.
        
        Args:
            urls: List of URLs to retrieve content from
            
        Returns:
            List of SearchResult objects with full content (max 3000 chars)
        """
        if not urls:
            return []
        
        try:
            logger.info(
                f"Retrieving content from {len(urls)} URLs with Parallel AI",
                extra={"context": {"url_count": len(urls)}}
            )
            
            # Batch process URLs
            batch_payload = {
                "urls": urls,
                "max_characters": 3000
            }
            
            response = await self.client.post("/content/batch", json=batch_payload)
            response.raise_for_status()
            data = response.json()
            
            # Process results
            results = []
            for r in data.get("results", []):
                content = r.get("content", "")
                
                # Skip if no content
                if not content or not content.strip():
                    logger.debug(
                        f"Skipping URL with no content: {r.get('url')}",
                        extra={"context": {"url": r.get("url")}}
                    )
                    continue
                
                result = SearchResult(
                    title=clean_title(r.get("title", "")) or self._extract_title_from_url(r.get("url", "")),
                    url=r.get("url", ""),
                    content=content,
                    published_date=r.get("published_date"),
                    author=r.get("author"),
                    favicon=generate_favicon_url(r.get("url", ""))
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
                f"Parallel AI content retrieval failed: {str(e)}",
                exc_info=True,
                extra={"context": {"url_count": len(urls), "error": str(e)}}
            )
            return []
    
    async def _get_firecrawl_images(self, query: str, max_results: int) -> List[SearchResult]:
        """
        Get image results from Firecrawl.
        
        Args:
            query: Search query
            max_results: Maximum number of image results
            
        Returns:
            List of SearchResult objects with image URLs
        """
        if not self.firecrawl_client:
            return []
        
        try:
            # Search for images using Firecrawl
            response = self.firecrawl_client.search(
                query,
                limit=max_results,
                sources=["images"]
            )
            
            results = []
            for r in response.get("data", []):
                if r.get("type") == "image":
                    result = SearchResult(
                        title=clean_title(r.get("title", "")) or "Image Result",
                        url=r.get("url", ""),
                        content=r.get("description", ""),
                        published_date=None,
                        author=None,
                        favicon=generate_favicon_url(r.get("url", ""))
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.warning(
                f"Firecrawl image search failed: {str(e)}",
                extra={"context": {"query": query, "error": str(e)}}
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
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
