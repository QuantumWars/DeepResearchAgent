"""Playwright scraper tool implementation."""

import logging
from typing import Optional

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from registry.base_tool import BaseScraperTool
from models.tool_schemas import ScrapedContent

logger = logging.getLogger(__name__)


class PlaywrightScraper(BaseScraperTool):
    """Playwright-based web scraper for JavaScript-heavy sites."""
    
    name = "playwright"
    priority = 5
    
    def __init__(self, headless: bool = True, timeout: int = 30000, 
                 wait_for: str = "networkidle"):
        """
        Initialize Playwright scraper.
        
        Args:
            headless: Whether to run browser in headless mode
            timeout: Timeout in milliseconds for page operations
            wait_for: Wait condition ('load', 'domcontentloaded', 'networkidle')
        """
        self.headless = headless
        self.timeout = timeout
        self.wait_for = wait_for
        logger.debug(f"Playwright scraper initialized (headless={headless}, timeout={timeout}ms)")
    
    def scrape(self, url: str) -> ScrapedContent:
        """
        Extract content from URL using Playwright.
        
        Handles JavaScript-heavy sites by waiting for network idle.
        
        Args:
            url: URL to scrape
            
        Returns:
            ScrapedContent object with extracted content or error information
        """
        try:
            logger.info(f"Scraping URL with Playwright: {url}")
            
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(headless=self.headless)
                
                try:
                    # Create new page
                    page = browser.new_page()
                    page.set_default_timeout(self.timeout)
                    
                    # Navigate to URL and wait for specified condition
                    page.goto(url, wait_until=self.wait_for)
                    
                    # Extract text content from body
                    content = page.inner_text('body')
                    
                    if not content or len(content.strip()) == 0:
                        logger.warning(f"No content extracted from {url}")
                        return ScrapedContent(
                            url=url,
                            content="",
                            success=False,
                            error_msg="No content found on page"
                        )
                    
                    logger.info(f"Successfully scraped {len(content)} characters from {url}")
                    
                    return ScrapedContent(
                        url=url,
                        content=content,
                        success=True,
                        metadata={
                            "content_length": len(content),
                            "scraper": "playwright",
                            "wait_condition": self.wait_for
                        }
                    )
                    
                finally:
                    browser.close()
                    
        except PlaywrightTimeoutError as e:
            logger.error(f"Playwright timeout for {url}: {e}")
            return ScrapedContent(
                url=url,
                content="",
                success=False,
                error_msg=f"Timeout after {self.timeout}ms"
            )
            
        except Exception as e:
            logger.error(f"Playwright scraping failed for {url}: {e}")
            return ScrapedContent(
                url=url,
                content="",
                success=False,
                error_msg=str(e)
            )
