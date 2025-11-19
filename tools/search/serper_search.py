"""Serper (Google Search) tool implementation."""

import os
import logging
from typing import List
import requests

from registry.base_tool import BaseSearchTool
from models.tool_schemas import SearchResult

logger = logging.getLogger(__name__)


class SerperSearch(BaseSearchTool):
    """
    Serper (Google Search) API implementation.
    
    Uses the Serper.dev API to perform Google searches.
    Requires a Serper API key from https://serper.dev
    """
    
    name = "serper"
    priority = 5
    requires_api_key = True
    
    def __init__(self, api_key: str = None, extra_params: dict = None):
        """
        Initialize Serper Search client.
        
        Args:
            api_key: Serper API key (optional, will try to load from environment)
            extra_params: Additional configuration parameters (country, language, max_results)
        """
        self.api_key = api_key or os.getenv("SERPER_API_KEY")
        self.extra_params = extra_params or {}
        
        if not self.api_key:
            logger.warning("Serper API key not found in config or environment")
        else:
            logger.debug("Serper client initialized successfully")
    
    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        Execute search via Serper (Google Search) API.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects, empty list on failure
        """
        if not self.api_key:
            logger.error("Serper API key not available, cannot perform search")
            return []
        
        try:
            logger.info(f"Executing Serper search for query: {query}")
            
            # Serper API endpoint
            url = "https://google.serper.dev/search"
            
            # Prepare request payload
            payload = {
                "q": query,
                "num": max_results
            }
            
            # Add optional parameters from config
            if "country" in self.extra_params:
                payload["gl"] = self.extra_params["country"]
            if "language" in self.extra_params:
                payload["hl"] = self.extra_params["language"]
            
            # Prepare headers with API key
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Make API request
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse response into SearchResult objects
            results = []
            if data and "organic" in data:
                for item in data["organic"][:max_results]:
                    result = SearchResult(
                        url=item.get("link", ""),
                        title=item.get("title", ""),
                        snippet=item.get("snippet", ""),
                        relevance_score=item.get("position")  # Use position as relevance indicator
                    )
                    results.append(result)
            
            logger.info(f"Serper search returned {len(results)} results")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Serper API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Serper search failed: {e}")
            return []
