"""Pydantic models for tool schemas and data structures.

This module defines all data models used throughout the Deep Research Framework
for type-safe validation and structured data handling.

Requirements: 2.1, 2.2, 12.1
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """
    Model for search tool results.
    
    Represents a single search result returned by search tools like Tavily or Serper.
    
    Attributes:
        url: The URL of the search result
        title: The title of the page or article
        snippet: A brief excerpt or description of the content
        relevance_score: Optional relevance score (0.0-1.0) if provided by search API
    
    Requirements: 2.1, 7.3
    """
    url: str
    title: str
    snippet: str
    relevance_score: Optional[float] = None


class ScrapedContent(BaseModel):
    """
    Model for scraped web content.
    
    Represents the result of a web scraping operation, including success status
    and error information if the scraping failed.
    
    Attributes:
        url: The URL that was scraped
        content: The extracted text content (empty string if failed)
        success: Whether the scraping operation succeeded
        error_msg: Error message if scraping failed, None otherwise
        metadata: Optional additional metadata about the scraping operation
    
    Requirements: 2.2, 8.3
    """
    url: str
    content: str
    success: bool
    error_msg: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Citation(BaseModel):
    """
    Model for a single citation reference.
    
    Represents a citation to a source document in the research report.
    
    Attributes:
        id: Citation identifier (e.g., "1", "2") used in inline citations [1], [2]
        url: The URL of the cited source
        title: The title of the cited source
        excerpt: A relevant excerpt from the source
        accessed_at: Timestamp when the source was accessed
    
    Requirements: 12.1, 12.2
    """
    id: str
    url: str
    title: str
    excerpt: str
    accessed_at: datetime


class ReportSection(BaseModel):
    """
    Model for a section of the research report.
    
    Represents a single section in the structured research report with its
    content and associated citations.
    
    Attributes:
        heading: The section heading/title
        content: The section content with inline citation markers [1], [2]
        citation_ids: List of citation IDs referenced in this section
    
    Requirements: 12.1, 12.3
    """
    heading: str
    content: str
    citation_ids: List[str] = Field(default_factory=list)


class CitedReport(BaseModel):
    """
    Model for structured report with citations.
    
    Represents a complete research report with structured sections and
    properly formatted citations.
    
    Attributes:
        title: The report title
        summary: A brief summary of the research findings
        sections: List of report sections with content and citations
        references: List of all citations referenced in the report
    
    Requirements: 12.1, 12.2, 12.3, 12.4
    """
    title: str
    summary: str
    sections: List[ReportSection]
    references: List[Citation]


class ToolExecutionLog(BaseModel):
    """
    Model for logging tool execution.
    
    Records information about a tool execution for debugging and analysis.
    
    Attributes:
        timestamp: When the tool was executed
        node: Which workflow node executed the tool (e.g., "planner", "retrieval")
        tool_category: Category of tool (e.g., "search", "scraper", "llm")
        tool_name: Specific tool name (e.g., "tavily", "trafilatura")
        success: Whether the tool execution succeeded
        error_msg: Error message if execution failed, None otherwise
        metadata: Additional metadata about the execution
    
    Requirements: 5.3, 11.3
    """
    timestamp: datetime
    node: str
    tool_category: str
    tool_name: str
    success: bool
    error_msg: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolConfig(BaseModel):
    """
    Model for tool configuration.
    
    Represents the configuration for a single tool loaded from YAML.
    
    Attributes:
        name: Tool name
        enabled: Whether the tool is enabled
        priority: Tool priority (higher = tried first in fallback chain)
        api_key: Optional API key for the tool
        extra_params: Additional tool-specific configuration parameters
    
    Requirements: 3.1, 3.2
    """
    name: str
    enabled: bool
    priority: int
    api_key: Optional[str] = None
    extra_params: Dict[str, Any] = Field(default_factory=dict)
