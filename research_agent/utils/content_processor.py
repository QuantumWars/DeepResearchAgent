"""Content processing utilities for cleaning, deduplicating, and formatting research data."""

import re
from typing import List, Set
from urllib.parse import urlparse

from .models import SearchResult


def extract_domain(url: str) -> str:
    """
    Extract the domain from a URL.
    
    Args:
        url: Full URL string
        
    Returns:
        Domain name (e.g., 'example.com')
        
    Examples:
        >>> extract_domain('https://www.example.com/path')
        'example.com'
        >>> extract_domain('http://subdomain.example.com:8080/path?query=1')
        'subdomain.example.com'
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        
        # Remove 'www.' prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain
    except Exception:
        # If parsing fails, return empty string
        return ""


def clean_title(title: str) -> str:
    """
    Clean a title by removing brackets, parentheses, and extra spaces.
    
    Args:
        title: Raw title string
        
    Returns:
        Cleaned title string
        
    Examples:
        >>> clean_title('Example Title [2024]')
        'Example Title'
        >>> clean_title('Title (with parentheses)  and   spaces')
        'Title and spaces'
    """
    if not title:
        return ""
    
    # Remove content within brackets and parentheses (including the brackets/parentheses)
    title = re.sub(r'\[.*?\]', '', title)
    title = re.sub(r'\(.*?\)', '', title)
    
    # Remove extra whitespace (multiple spaces, tabs, newlines)
    title = re.sub(r'\s+', ' ', title)
    
    # Strip leading and trailing whitespace
    title = title.strip()
    
    return title


def truncate_content(content: str, max_length: int = 3000) -> str:
    """
    Truncate content to a maximum length.
    
    Args:
        content: Content string to truncate
        max_length: Maximum length (default 3000 characters)
        
    Returns:
        Truncated content string
        
    Examples:
        >>> truncate_content('a' * 5000, 3000)
        'aaa...' (3000 characters total)
    """
    if not content:
        return ""
    
    if len(content) <= max_length:
        return content
    
    # Truncate and add ellipsis
    return content[:max_length - 3] + "..."


def generate_favicon_url(url: str) -> str:
    """
    Generate a favicon URL from a website URL.
    
    Args:
        url: Website URL
        
    Returns:
        Favicon URL using Google's favicon service
        
    Examples:
        >>> generate_favicon_url('https://www.example.com/path')
        'https://www.google.com/s2/favicons?domain=example.com&sz=128'
    """
    domain = extract_domain(url)
    if not domain:
        return ""
    
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"


def deduplicate_by_url(results: List[SearchResult]) -> List[SearchResult]:
    """
    Deduplicate search results by URL.
    
    Args:
        results: List of search results
        
    Returns:
        Deduplicated list with unique URLs
    """
    seen_urls: Set[str] = set()
    deduplicated: List[SearchResult] = []
    
    for result in results:
        if result.url not in seen_urls:
            seen_urls.add(result.url)
            deduplicated.append(result)
    
    return deduplicated


def deduplicate_by_domain(results: List[SearchResult]) -> List[SearchResult]:
    """
    Deduplicate search results by domain (one result per domain).
    
    Args:
        results: List of search results
        
    Returns:
        Deduplicated list with one result per domain
    """
    seen_domains: Set[str] = set()
    deduplicated: List[SearchResult] = []
    
    for result in results:
        domain = extract_domain(result.url)
        if domain and domain not in seen_domains:
            seen_domains.add(domain)
            deduplicated.append(result)
    
    return deduplicated


def deduplicate_results(
    results: List[SearchResult],
    by_domain: bool = True,
    by_url: bool = True
) -> List[SearchResult]:
    """
    Deduplicate search results by domain and/or URL.
    
    Args:
        results: List of search results
        by_domain: Whether to deduplicate by domain (default True)
        by_url: Whether to deduplicate by URL (default True)
        
    Returns:
        Deduplicated list of search results
        
    Note:
        If both by_domain and by_url are True, URL deduplication is applied first,
        then domain deduplication.
    """
    if not results:
        return []
    
    deduplicated = results
    
    # Apply URL deduplication first (more specific)
    if by_url:
        deduplicated = deduplicate_by_url(deduplicated)
    
    # Then apply domain deduplication (more aggressive)
    if by_domain:
        deduplicated = deduplicate_by_domain(deduplicated)
    
    return deduplicated
