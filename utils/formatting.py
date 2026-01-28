"""Formatting utilities for the Deep Research Framework.

This module provides helper functions for formatting citations, parsing LLM
responses, and other text processing tasks used by workflow nodes.
"""

import re
from datetime import datetime
from typing import Any, Dict, List
from models.tool_schemas import Citation


def format_citations(documents: List[Dict[str, Any]]) -> str:
    """
    Convert a list of document dictionaries to formatted citation text.
    
    Creates numbered citations in a standard format suitable for inclusion
    in research reports.
    
    Args:
        documents: List of document dictionaries with keys:
                   - url: Document URL
                   - title: Document title
                   - content: Document content (optional, for excerpt)
                   - source_tool: Tool used to retrieve (optional)
    
    Returns:
        Formatted citation string with numbered references
    
    Examples:
        >>> docs = [
        ...     {"url": "https://example.com", "title": "Example Article"},
        ...     {"url": "https://test.com", "title": "Test Page"}
        ... ]
        >>> print(format_citations(docs))
        [1] Example Article - https://example.com
        [2] Test Page - https://test.com
    
    Requirements: 12.2, 12.5
    """
    if not documents:
        return "No citations available."
    
    citations = []
    for idx, doc in enumerate(documents, start=1):
        title = doc.get("title", "Untitled")
        url = doc.get("url", "N/A")
        citations.append(f"[{idx}] {title} - {url}")
    
    return "\n".join(citations)


def format_citations_detailed(documents: List[Dict[str, Any]]) -> str:
    """
    Convert documents to detailed citation format with excerpts.
    
    Creates numbered citations with additional metadata including excerpts
    and retrieval information.
    
    Args:
        documents: List of document dictionaries
    
    Returns:
        Detailed formatted citation string
    
    Examples:
        >>> docs = [{"url": "https://example.com", "title": "Article",
        ...          "content": "This is the content...", "source_tool": "tavily"}]
        >>> print(format_citations_detailed(docs))
        [1] Article
            URL: https://example.com
            Source: tavily
            Excerpt: This is the content...
    """
    if not documents:
        return "No citations available."
    
    citations = []
    for idx, doc in enumerate(documents, start=1):
        title = doc.get("title", "Untitled")
        url = doc.get("url", "N/A")
        source = doc.get("source_tool", "unknown")
        content = doc.get("content", "")
        
        # Create excerpt (first 200 characters)
        excerpt = content[:200] + "..." if len(content) > 200 else content
        
        citation_text = f"[{idx}] {title}\n"
        citation_text += f"    URL: {url}\n"
        citation_text += f"    Source: {source}\n"
        if excerpt:
            citation_text += f"    Excerpt: {excerpt}\n"
        
        citations.append(citation_text)
    
    return "\n".join(citations)


def create_citation_objects(documents: List[Dict[str, Any]]) -> List[Citation]:
    """
    Convert document dictionaries to Citation Pydantic models.
    
    Args:
        documents: List of document dictionaries
    
    Returns:
        List of Citation model instances
    
    Examples:
        >>> docs = [{"url": "https://example.com", "title": "Article",
        ...          "content": "Content here"}]
        >>> citations = create_citation_objects(docs)
        >>> citations[0].id
        '1'
    """
    citations = []
    for idx, doc in enumerate(documents, start=1):
        content = doc.get("content", "")
        excerpt = content[:300] + "..." if len(content) > 300 else content
        
        citation = Citation(
            id=str(idx),
            url=doc.get("url", ""),
            title=doc.get("title", "Untitled"),
            excerpt=excerpt,
            accessed_at=datetime.now()
        )
        citations.append(citation)
    
    return citations


def parse_plan(llm_response: str) -> List[str]:
    """
    Extract sub-questions from LLM response text.
    
    Parses numbered or bulleted lists from LLM output and extracts clean
    sub-questions. Handles various formatting styles:
    - "1. Question"
    - "1) Question"
    - "- Question"
    - "• Question"
    
    Args:
        llm_response: Raw text response from LLM containing sub-questions
    
    Returns:
        List of cleaned sub-question strings
    
    Examples:
        >>> response = '''
        ... 1. What is machine learning?
        ... 2. How does deep learning work?
        ... 3. What are neural networks?
        ... '''
        >>> parse_plan(response)
        ['What is machine learning?', 'How does deep learning work?', 
         'What are neural networks?']
        
        >>> response = "- First question\\n- Second question"
        >>> parse_plan(response)
        ['First question', 'Second question']
    
    Requirements: 12.2, 12.5
    """
    if not llm_response or not llm_response.strip():
        return []
    
    sub_questions = []
    
    # Split by lines and process each
    for line in llm_response.strip().split('\n'):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Remove common list markers and numbering
        # Patterns: "1.", "1)", "•", "-", "*", etc.
        cleaned = re.sub(r'^[\d]+[\.\)]\s*', '', line)  # Remove "1. " or "1) "
        cleaned = re.sub(r'^[•\-\*]\s*', '', cleaned)   # Remove "• ", "- ", "* "
        cleaned = cleaned.strip()
        
        # Only add non-empty, substantial questions
        if cleaned and len(cleaned) > 5:
            sub_questions.append(cleaned)
    
    return sub_questions


def parse_numbered_list(text: str) -> List[str]:
    """
    Extract items from a numbered list in text.
    
    Generic utility for parsing any numbered list format.
    
    Args:
        text: Text containing numbered list
    
    Returns:
        List of extracted items
    
    Examples:
        >>> text = "1. First item\\n2. Second item\\n3. Third item"
        >>> parse_numbered_list(text)
        ['First item', 'Second item', 'Third item']
    """
    return parse_plan(text)


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        suffix: String to append when truncated (default: "...")
    
    Returns:
        Truncated text with suffix if needed
    
    Examples:
        >>> truncate_text("This is a long text", max_length=10)
        'This is a ...'
        
        >>> truncate_text("Short", max_length=10)
        'Short'
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_document_summary(doc: Dict[str, Any], max_content_length: int = 500) -> str:
    """
    Create a formatted summary of a document for display or logging.
    
    Args:
        doc: Document dictionary with url, title, content, etc.
        max_content_length: Maximum length for content preview
    
    Returns:
        Formatted document summary string
    
    Examples:
        >>> doc = {"url": "https://example.com", "title": "Article",
        ...        "content": "Long content here..."}
        >>> print(format_document_summary(doc))
        Title: Article
        URL: https://example.com
        Content: Long content here...
    """
    title = doc.get("title", "Untitled")
    url = doc.get("url", "N/A")
    content = doc.get("content", "")
    
    content_preview = truncate_text(content, max_content_length)
    
    summary = f"Title: {title}\n"
    summary += f"URL: {url}\n"
    if content_preview:
        summary += f"Content: {content_preview}\n"
    
    return summary


def extract_urls_from_text(text: str) -> List[str]:
    """
    Extract all URLs from a text string.
    
    Args:
        text: Text containing URLs
    
    Returns:
        List of extracted URLs
    
    Examples:
        >>> text = "Check https://example.com and http://test.org"
        >>> extract_urls_from_text(text)
        ['https://example.com', 'http://test.org']
    """
    if not text:
        return []
    
    # URL pattern matching http:// or https://
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text)
    
    return urls


def clean_whitespace(text: str) -> str:
    """
    Clean excessive whitespace from text.
    
    Removes multiple consecutive spaces, tabs, and newlines while preserving
    single spaces and paragraph breaks.
    
    Args:
        text: Text to clean
    
    Returns:
        Cleaned text
    
    Examples:
        >>> clean_whitespace("Too    many   spaces")
        'Too many spaces'
        
        >>> clean_whitespace("Line1\\n\\n\\nLine2")
        'Line1\\n\\nLine2'
    """
    if not text:
        return ""
    
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Replace multiple newlines with double newline (paragraph break)
    text = re.sub(r'\n\n+', '\n\n', text)
    
    # Remove trailing/leading whitespace
    text = text.strip()
    
    return text
