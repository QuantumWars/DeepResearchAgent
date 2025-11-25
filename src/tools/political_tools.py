"""Political fact-checking tools using web search.

This module implements tools for retrieving political information
using the Tavily web search API.
"""

import os
from typing import List, Dict, Any
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

# Initialize Tavily client
tavily_api_key = os.getenv("TAVILY_API_KEY")
if tavily_api_key:
    tavily_client = TavilyClient(api_key=tavily_api_key)
else:
    tavily_client = None
    print("Warning: TAVILY_API_KEY not set. Political tools will not work.")


def political_web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Search for political information using Tavily web search.
    
    Args:
        query: Search query for political information
        max_results: Maximum number of results to return
        
    Returns:
        Dictionary with search results including URLs, titles, content, etc.
    """
    if not tavily_client:
        return {
            "source": "Tavily Web Search",
            "query": query,
            "results": [],
            "count": 0,
            "error": "TAVILY_API_KEY not configured"
        }
    
    try:
        # Search with focus on government and news sources
        search_results = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_domains=[
                "congress.gov",
                "govinfo.gov",
                "senate.gov",
                "house.gov",
                "whitehouse.gov",
                "politifact.com",
                "factcheck.org"
            ]
        )
        
        # Parse results
        results = []
        for result in search_results.get("results", []):
            results.append({
                "title": result.get("title", "No title"),
                "url": result.get("url", ""),
                "content": result.get("content", "No content"),
                "score": result.get("score", 0.5),
                "published_date": result.get("published_date", "Unknown")
            })
        
        return {
            "source": "Tavily Web Search",
            "query": query,
            "results": results,
            "count": len(results),
            "confidence": 0.7  # Moderate confidence for web search
        }
        
    except Exception as e:
        print(f"Error performing Tavily search: {e}")
        return {
            "source": "Tavily Web Search",
            "query": query,
            "results": [],
            "count": 0,
            "error": str(e)
        }


def assess_political_source(source_url: str, content: str) -> Dict[str, Any]:
    """
    Assess the credibility of a political source.
    
    Args:
        source_url: URL of the source
        content: Content from the source
        
    Returns:
        Dictionary with credibility assessment
    """
    credibility_score = 0.5  # Base score
    source_type = "general"
    factors = []
    
    # Check for official government sources
    if any(domain in source_url for domain in ["congress.gov", "senate.gov", "house.gov", "govinfo.gov"]):
        credibility_score += 0.4
        source_type = "official_government"
        factors.append("Official government source (highest credibility)")
    elif any(domain in source_url for domain in ["whitehouse.gov", "state.gov"]):
        credibility_score += 0.35
        source_type = "executive_branch"
        factors.append("Executive branch official source")
    elif any(domain in source_url for domain in ["politifact.com", "factcheck.org", "snopes.com"]):
        credibility_score += 0.3
        source_type = "fact_checker"
        factors.append("Professional fact-checking organization")
    elif any(domain in source_url for domain in [".gov"]):
        credibility_score += 0.25
        source_type = "government"
        factors.append("Government source")
    
    # Check for partisan language (simple heuristic)
    partisan_keywords = ["radical", "extreme", "socialist", "fascist", "corrupt"]
    if any(keyword in content.lower() for keyword in partisan_keywords):
        credibility_score -= 0.1
        factors.append("Contains potentially partisan language")
    
    # Cap at 1.0
    credibility_score = min(max(credibility_score, 0.0), 1.0)
    
    return {
        "url": source_url,
        "credibility_score": credibility_score,
        "source_type": source_type,
        "confidence": credibility_score,
        "assessment_factors": factors
    }


if __name__ == "__main__":
    # Test the tools
    print("Testing Political Web Search...")
    results = political_web_search("trump properties in dubai", max_results=3)
    
    print(f"\nFound {results['count']} results:")
    for result in results['results']:
        print(f"\n- {result['title']}")
        print(f"  URL: {result['url']}")
        print(f"  Score: {result['score']}")
        print(f"  Content: {result['content'][:200]}...")
        
        # Assess credibility
        assessment = assess_political_source(result['url'], result['content'])
        print(f"  Credibility: {assessment['credibility_score']:.2f} ({assessment['source_type']})")
