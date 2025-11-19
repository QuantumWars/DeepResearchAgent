"""Trafilatura scraper tool implementation."""

import logging
from typing import Optional

import trafilatura

from registry.base_tool import BaseScraperTool
from models.tool_schemas import ScrapedContent

logger = logging.getLogger(__name__)


class TrafilaturaScraper(BaseScraperTool):
    """Trafilatura-based web scraper implementation."""
    
    name = "trafilatura"
    priority = 10
    
    def __init__(self, include_comments: bool = False, include_tables: bool = True, 
                 deduplicate: bool = True):
        """
        Initialize Trafilatura scraper.
        
        Args:
            include_comments: Whether to include comments in extracted content
            include_tables: Whether to include tables in extracted content
            deduplicate: Whether to deduplicate extracted content
        """
        self.include_comments = include_comments
        self.include_tables = include_tables
        self.deduplicate = deduplicate
        logger.debug("Trafilatura scraper initialized")
    
    def scrape(self, url: str) -> ScrapedContent:
        """
        Extract content from URL using Trafilatura.
        
        Args:
            url: URL to scrape
            
        Returns:
            ScrapedContent object with extracted content or error information
        """
        try:
            logger.info(f"Scraping URL with Trafilatura: {url}")
            
            # Download the webpage
            downloaded = trafilatura.fetch_url(url)
            
            if not downloaded:
                logger.warning(f"Failed to download content from {url}")
                return ScrapedContent(
                    url=url,
                    content="",
                    success=False,
                    error_msg="Failed to download content from URL"
                )
            
            # Extract content with configured options
            extracted = trafilatura.extract(
                downloaded,
                include_comments=self.include_comments,
                include_tables=self.include_tables,
                deduplicate=self.deduplicate
            )
            
            if not extracted:
                logger.warning(f"Failed to extract content from {url}")
                return ScrapedContent(
                    url=url,
                    content="",
                    success=False,
                    error_msg="Failed to extract content from downloaded page"
                )
            
            logger.info(f"Successfully scraped {len(extracted)} characters from {url}")
            
            return ScrapedContent(
                url=url,
                content=extracted,
                success=True,
                metadata={
                    "content_length": len(extracted),
                    "scraper": "trafilatura"
                }
            )
            
        except Exception as e:
            logger.error(f"Trafilatura scraping failed for {url}: {e}")
            return ScrapedContent(
                url=url,
                content="",
                success=False,
                error_msg=str(e)
            )
