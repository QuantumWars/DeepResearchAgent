"""
Agno tools wrapper for the Deep Research Framework.
"""

import logging
from typing import Optional, List, Dict, Any
from agno.tools import Toolkit

from tools.search.tavily_search import TavilySearch
from tools.scraper.playwright_scraper import PlaywrightScraper
from tools.scraper.trafilatura_scraper import TrafilaturaScraper

logger = logging.getLogger(__name__)

class ResearchTools(Toolkit):
    def __init__(self, 
                 search_api_key: Optional[str] = None,
                 scraper_headless: bool = True):
        super().__init__(name="research_tools")
        
        # Initialize existing tools
        self.search_tool = TavilySearch(api_key=search_api_key)
        self.scraper_tool = PlaywrightScraper(headless=scraper_headless)
        self.fallback_scraper = TrafilaturaScraper()
        
        # Register methods
        self.register(self.search_google)
        self.register(self.scrape_website)

    def search_google(self, query: str, max_results: int = 5) -> str:
        """
        Search Google for the given query.
        
        Args:
            query: The search query.
            max_results: Maximum number of results to return (default: 5).
            
        Returns:
            A formatted string containing search results with titles, URLs, and snippets.
        """
        try:
            results = self.search_tool.search(query, max_results=max_results)
            
            if not results:
                return "No results found."
            
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_results.append(
                    f"{i}. {result.title}\n   URL: {result.url}\n   Snippet: {result.snippet}"
                )
            
            return "\n\n".join(formatted_results)
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return f"Error performing search: {str(e)}"

    def scrape_website(self, url: str) -> str:
        """
        Scrape the content of a website.
        
        Args:
            url: The URL of the website to scrape.
            
        Returns:
            The text content of the website.
        """
        try:
            # Try Playwright first
            result = self.scraper_tool.scrape(url)
            
            if result.success:
                logger.info(f"Successfully scraped {url} with Playwright")
                return result.content
            else:
                # Fallback to Trafilatura
                logger.warning(f"Playwright failed for {url}, trying Trafilatura fallback")
                fallback_result = self.fallback_scraper.scrape(url)
                
                if fallback_result.success:
                    logger.info(f"Successfully scraped {url} with Trafilatura")
                    return fallback_result.content
                else:
                    return f"Error scraping {url}: Both Playwright and Trafilatura failed"
                
        except Exception as e:
            # If Playwright throws an exception, try Trafilatura
            logger.warning(f"Playwright exception for {url}: {e}, trying Trafilatura fallback")
            try:
                fallback_result = self.fallback_scraper.scrape(url)
                if fallback_result.success:
                    logger.info(f"Successfully scraped {url} with Trafilatura (after Playwright exception)")
                    return fallback_result.content
                else:
                    return f"Error scraping {url}: {fallback_result.error_msg}"
            except Exception as fallback_e:
                logger.error(f"Both scrapers failed for {url}: {e}, {fallback_e}")
                return f"Error scraping website: {str(e)}"
