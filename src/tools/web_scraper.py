"""Web scraping tools for deep content analysis.
This module implements tools for extracting full text content from URLs
using Trafilatura, which is optimized for article extraction.
"""
import trafilatura
from typing import Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
def scrape_url_content(url: str) -> Dict[str, Any]:
    """
    Scrape and extract the main text content from a URL.
    
    Args:
        url: The URL to scrape
        
    Returns:
        Dictionary with extracted content and metadata
    """
    # Common headers to look like a real browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    try:
        # First, fetch the HTML content using requests
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        html_content = response.text
        # Method 1: Try Trafilatura first (best for articles)
        try:
            # Extract with Trafilatura
            content = trafilatura.extract(
                html_content,
                include_comments=False,
                include_tables=True,
                include_links=False,
                favor_precision=True
            )
            
            if content:
                # Extract metadata
                metadata = trafilatura.extract_metadata(html_content)
                meta_dict = {}
                if metadata:
                    meta_dict = {
                        "title": metadata.title,
                        "author": metadata.author,
                        "date": metadata.date,
                        "hostname": metadata.sitename
                    }
                
                return {
                    "url": url,
                    "content": content,
                    "metadata": meta_dict,
                    "length": len(content),
                    "success": True,
                    "method": "trafilatura"
                }
        except Exception as e:
            print(f"Trafilatura extraction failed: {e}")
            # Continue to fallback
        # Method 2: Fallback to BeautifulSoup (simpler, less precise but robust)
        print("Falling back to BeautifulSoup extraction...")
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        # Get text
        text = soup.get_text()
        
        # Break into lines and remove leading/trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        content = '\n'.join(chunk for chunk in chunks if chunk)
        
        if content:
            return {
                "url": url,
                "content": content,
                "metadata": {"title": soup.title.string if soup.title else ""},
                "length": len(content),
                "success": True,
                "method": "beautifulsoup"
            }
            
        return {
            "url": url,
            "content": "",
            "error": "All extraction methods failed",
            "success": False
        }
        
    except Exception as e:
        return {
            "url": url,
            "content": "",
            "error": str(e),
            "success": False
        }
def extract_links(html_content: str, base_url: str) -> list[str]:
    """
    Extract all links from HTML content.
    
    Args:
        html_content: The HTML content to parse
        base_url: The base URL to resolve relative links
        
    Returns:
        List of absolute URLs found in the content
    """
    from urllib.parse import urljoin, urlparse
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        # Find all anchor tags
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Skip anchors, javascript, mailto, etc.
            if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
                continue
                
            # Convert to absolute URL
            absolute_url = urljoin(base_url, href)
            
            # Only include http/https URLs
            parsed = urlparse(absolute_url)
            if parsed.scheme in ['http', 'https']:
                links.append(absolute_url)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
        
        return unique_links
        
    except Exception as e:
        print(f"Error extracting links: {e}")
        return []
if __name__ == "__main__":
    # Test the scraper
    test_url = "https://www.aljazeera.com/news/2025/11/21/explosion-at-glue-factory-in-eastern-pakistan-kills-at-least-16"
    print(f"Testing scraper on {test_url}...")
    result = scrape_url_content(test_url)
    
    print(f"Success: {result['success']}")
    print(f"Content length: {result.get('length', 0)}")
    print(f"Content preview: {result.get('content', '')[:100]}...")
    print(result.get('content'))