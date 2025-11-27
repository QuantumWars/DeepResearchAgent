"""
Real implementations of search tools using actual APIs.
Uncomment and use these once you have API keys configured.
"""
import os
from typing import Optional, List, Dict, Any
from agno.tools import Toolkit

class SearchToolsReal(Toolkit):
    def __init__(self):
        super().__init__(name="search_tools_real")
        self.register(self.exa_search)
        self.register(self.tavily_search)
        self.register(self.official_api_search)

    def exa_search(self, query: str, num_results: int = 3, start_published_date: Optional[str] = None) -> str:
        """
        Search using Exa (formerly Metaphor) for high-precision results.
        
        Args:
            query: The search query.
            num_results: Number of results to return.
            start_published_date: Filter for results published after this date (YYYY-MM-DD).
            
        Returns:
            JSON string of search results.
        """
        try:
            from exa_py import Exa
            
            api_key = os.getenv("EXA_API_KEY")
            if not api_key:
                return f"[MOCK] Exa search results for '{query}' (No API key)"
            
            exa = Exa(api_key=api_key)
            
            # Build search parameters (only include non-None values)
            search_kwargs = {
                "text": True,
                "num_results": num_results,
            }
            
            if start_published_date:
                search_kwargs["start_published_date"] = start_published_date
            
            # Use search_and_contents method (correct API)
            results = exa.search_and_contents(query, **search_kwargs)
            
            # Format results to match expected structure
            formatted = []
            for result in results.results:
                item = {
                    "title": result.title,
                    "url": result.url,
                }
                if hasattr(result, 'published_date') and result.published_date:
                    item["published_date"] = result.published_date
                if hasattr(result, 'author') and result.author:
                    item["author"] = result.author
                if hasattr(result, 'score') and result.score:
                    item["score"] = result.score
                if hasattr(result, 'text') and result.text:
                    item["text"] = result.text[:1000]  # Limit text length
                
                formatted.append(item)
            
            import json
            return json.dumps(formatted, indent=2)
            
        except ImportError:
            return "[ERROR] exa_py not installed. Run: pip install exa-py"
        except Exception as e:
            return f"[ERROR] Exa search failed: {str(e)}"


    def tavily_search(self, query: str, max_results: int = 3) -> str:
        """
        Search using Tavily for broad web coverage and news.
        
        Args:
            query: The search query.
            max_results: Number of results to return.
            
        Returns:
            JSON string of search results.
        """
        try:
            from tavily import TavilyClient
            
            api_key = os.getenv("TAVILY_API_KEY")
            if not api_key:
                return f"[MOCK] Tavily search results for '{query}' (No API key)"
            
            tavily = TavilyClient(api_key=api_key)
            
            results = tavily.search(
                query=query,
                max_results=max_results,
                search_depth="advanced"
            )
            
            # Format results
            formatted = []
            for result in results.get('results', []):
                formatted.append({
                    "title": result.get("title"),
                    "url": result.get("url"),
                    "content": result.get("content"),
                    "score": result.get("score"),
                    "published_date": result.get("published_date")
                })
            
            import json
            return json.dumps(formatted, indent=2)
            
        except ImportError:
            return "[ERROR] tavily-python not installed. Run: pip install tavily-python"
        except Exception as e:
            return f"[ERROR] Tavily search failed: {str(e)}"

    def official_api_search(self, source: str, endpoint: str, params: Dict[str, Any] = {}) -> str:
        """
        Query official APIs for authoritative data.
        
        Args:
            source: The source name (e.g., 'whitehouse.gov').
            endpoint: The API endpoint.
            params: Query parameters.
            
        Returns:
            JSON string of API response.
        """
        # This would need specific implementations for each official source
        return f"[MOCK] Official API result from {source}/{endpoint} with params {params}"
