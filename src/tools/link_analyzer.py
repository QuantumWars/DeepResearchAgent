"""Enhanced link extraction with context awareness.

This module provides intelligent link extraction that considers the text
context around links to determine relevance to a query.
"""

from typing import Dict, Any, List, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


def extract_links_with_context(html_content: str, base_url: str, query: str = "") -> List[Dict[str, Any]]:
    """
    Extract links with their surrounding text context.
    
    Args:
        html_content: The HTML content to parse
        base_url: The base URL to resolve relative links
        query: Optional query to score link relevance
        
    Returns:
        List of dictionaries with link info and context
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        links_with_context = []
        
        # Find all anchor tags
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']
            
            # Skip anchors, javascript, mailto, etc.
            if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
                continue
            
            # Convert to absolute URL
            absolute_url = urljoin(base_url, href)
            
            # Only include http/https URLs
            parsed = urlparse(absolute_url)
            if parsed.scheme not in ['http', 'https']:
                continue
            
            # Get link text
            link_text = link_tag.get_text(strip=True)
            
            # Get surrounding context (parent paragraph or div)
            context = ""
            parent = link_tag.find_parent(['p', 'div', 'article', 'section'])
            if parent:
                context = parent.get_text(strip=True)[:300]  # First 300 chars
            
            # Calculate relevance score if query provided
            relevance_score = 0.0
            if query:
                relevance_score = calculate_relevance(link_text, context, absolute_url, query)
            
            links_with_context.append({
                'url': absolute_url,
                'text': link_text,
                'context': context,
                'relevance_score': relevance_score
            })
        
        # Remove duplicates (same URL)
        seen_urls = set()
        unique_links = []
        for link in links_with_context:
            if link['url'] not in seen_urls:
                seen_urls.add(link['url'])
                unique_links.append(link)
        
        # Sort by relevance if query provided
        if query:
            unique_links.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return unique_links
        
    except Exception as e:
        print(f"Error extracting links with context: {e}")
        return []


def calculate_relevance(link_text: str, context: str, url: str, query: str) -> float:
    """
    Calculate how relevant a link is to the query.
    
    Args:
        link_text: The text of the link
        context: Surrounding text context
        url: The URL
        query: The search query
        
    Returns:
        Relevance score (0.0 to 1.0)
    """
    score = 0.0
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
    query_words = {w for w in query_words if w not in stop_words and len(w) > 2}
    
    if not query_words:
        return 0.0
    
    # Check link text (highest weight)
    link_text_lower = link_text.lower()
    link_text_words = set(link_text_lower.split())
    matching_in_text = len(query_words & link_text_words)
    if matching_in_text > 0:
        score += 0.5 * (matching_in_text / len(query_words))
    
    # Check context (medium weight)
    context_lower = context.lower()
    context_words = set(context_lower.split())
    matching_in_context = len(query_words & context_words)
    if matching_in_context > 0:
        score += 0.3 * (matching_in_context / len(query_words))
    
    # Check URL (lower weight)
    url_lower = url.lower()
    matching_in_url = sum(1 for word in query_words if word in url_lower)
    if matching_in_url > 0:
        score += 0.2 * (matching_in_url / len(query_words))
    
    return min(score, 1.0)  # Cap at 1.0


def filter_relevant_links(
    links: List[Dict[str, Any]], 
    query: str,
    min_relevance: float = 0.1,
    max_links: int = 10
) -> List[Dict[str, Any]]:
    """
    Filter links based on relevance to query.
    
    Args:
        links: List of link dictionaries with relevance scores
        query: The search query
        min_relevance: Minimum relevance score to include
        max_links: Maximum number of links to return
        
    Returns:
        Filtered and sorted list of relevant links
    """
    # Filter by minimum relevance
    relevant = [link for link in links if link['relevance_score'] >= min_relevance]
    
    # Return top N
    return relevant[:max_links]


if __name__ == "__main__":
    # Test with a real example
    import requests
    
    test_url = "https://www.aljazeera.com/news/2025/11/21/explosion-at-glue-factory-in-eastern-pakistan-kills-at-least-16"
    test_query = "factory explosion investigation"
    
    print(f"Testing context-aware link extraction")
    print(f"URL: {test_url}")
    print(f"Query: {test_query}\n")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    response = requests.get(test_url, headers=headers, timeout=10)
    
    # Extract links with context
    links = extract_links_with_context(response.text, test_url, test_query)
    
    print(f"Total links found: {len(links)}\n")
    
    # Filter for relevant links
    relevant_links = filter_relevant_links(links, test_query, min_relevance=0.1, max_links=10)
    
    print(f"Relevant links (score >= 0.1): {len(relevant_links)}\n")
    
    if relevant_links:
        print("Top 10 most relevant links:")
        for i, link in enumerate(relevant_links, 1):
            print(f"\n{i}. [{link['text'][:50]}]")
            print(f"   URL: {link['url'][:80]}...")
            print(f"   Score: {link['relevance_score']:.3f}")
            if link['context']:
                print(f"   Context: {link['context'][:100]}...")
