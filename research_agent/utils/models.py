"""Pydantic models for data structures used throughout the research agent."""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from enum import Enum


class SearchCategory(str, Enum):
    """Categories for web search filtering."""
    NEWS = "news"
    COMPANY = "company"
    RESEARCH_PAPER = "research paper"
    GITHUB = "github"
    FINANCIAL_REPORT = "financial report"


class SearchResult(BaseModel):
    """Result from a web search with content and metadata."""
    title: str = Field(min_length=1, max_length=500)
    url: str = Field(min_length=1, max_length=2000)
    content: str = Field(default="", max_length=10000)
    published_date: Optional[str] = None
    author: Optional[str] = None
    favicon: Optional[str] = None


class ResearchTask(BaseModel):
    """A research topic with associated tasks."""
    title: str = Field(min_length=10, max_length=70)
    tasks: List[str] = Field(min_length=3, max_length=5)


class ResearchPlan(BaseModel):
    """Structured research plan with multiple topics and tasks."""
    topics: List[ResearchTask] = Field(min_length=1, max_length=5)
    
    @property
    def total_tasks(self) -> int:
        """Calculate total number of tasks across all topics."""
        return sum(len(topic.tasks) for topic in self.topics)
    
    @field_validator('topics')
    @classmethod
    def validate_task_limit(cls, v: List[ResearchTask]) -> List[ResearchTask]:
        """Ensure total tasks don't exceed 15."""
        total = sum(len(topic.tasks) for topic in v)
        if total > 15:
            raise ValueError(f"Total tasks ({total}) cannot exceed 15")
        return v


class CodeExecutionResult(BaseModel):
    """Result from executing Python code in a sandbox."""
    output: str = Field(default="")
    error: Optional[str] = None
    charts: List[Dict[str, Any]] = Field(default_factory=list)


class ResearchResult(BaseModel):
    """Complete research result with all gathered information."""
    query: str = Field(min_length=1, max_length=500)
    plan: Optional[ResearchPlan] = None
    text: str = Field(default="")
    sources: List[SearchResult] = Field(default_factory=list, max_length=100)
    charts: List[Dict[str, Any]] = Field(default_factory=list)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time: float = Field(default=0.0, ge=0.0)


class Memory(BaseModel):
    """Memory entry from Supermemory storage."""
    id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: float = Field(default=0.0, ge=0.0, le=1.0)


class XPost(BaseModel):
    """Individual X (Twitter) post data."""
    text: str = Field(min_length=1, max_length=5000)
    link: str = Field(min_length=1, max_length=2000)
    favorites: Optional[int] = Field(default=None, ge=0)
    views: Optional[int] = Field(default=None, ge=0)
    author: Optional[str] = Field(default=None, max_length=200)
    
    @field_validator('link')
    @classmethod
    def validate_link(cls, v: str) -> str:
        """Ensure link is a valid URL."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("Link must be a valid URL starting with http:// or https://")
        return v


class XSearchResult(BaseModel):
    """Result from X (Twitter) search with content and metadata."""
    content: str = Field(min_length=1, max_length=50000)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    sources: List[XPost] = Field(default_factory=list, max_length=100)
    query: str = Field(min_length=1, max_length=500)
    date_range: str = Field(min_length=1, max_length=100)
    handles: List[str] = Field(default_factory=list, max_length=20)
    
    @field_validator('handles')
    @classmethod
    def validate_handles(cls, v: List[str]) -> List[str]:
        """Validate X handle formats."""
        validated = []
        for handle in v:
            # Remove @ if present and validate format
            clean_handle = handle.lstrip('@')
            if not clean_handle:
                continue
            # X handles can contain letters, numbers, and underscores
            if not all(c.isalnum() or c == '_' for c in clean_handle):
                raise ValueError(f"Invalid X handle format: {handle}")
            validated.append(f"@{clean_handle}")
        return validated
    
    @field_validator('date_range')
    @classmethod
    def validate_date_range(cls, v: str) -> str:
        """Validate date range format."""
        # Expected format: "YYYY-MM-DD to YYYY-MM-DD"
        if ' to ' not in v:
            raise ValueError("Date range must be in format 'YYYY-MM-DD to YYYY-MM-DD'")
        return v


class VideoTimestamp(BaseModel):
    """Timestamp entry for a video chapter."""
    time: str = Field(min_length=1, max_length=20)  # Format: "1:23" or "1:23:45"
    title: str = Field(min_length=1, max_length=200)


class VideoResult(BaseModel):
    """Result from YouTube video search with transcript and metadata."""
    video_id: str = Field(min_length=1, max_length=20)
    url: str = Field(min_length=1, max_length=2000)
    title: Optional[str] = Field(default=None, max_length=500)
    thumbnail_url: Optional[str] = Field(default=None, max_length=2000)
    captions: Optional[str] = Field(default=None, max_length=100000)
    timestamps: Optional[List[str]] = Field(default=None, max_length=50)
    published_date: Optional[str] = Field(default=None, max_length=50)
    
    @field_validator('video_id')
    @classmethod
    def validate_video_id(cls, v: str) -> str:
        """Validate YouTube video ID format."""
        # YouTube video IDs are typically 11 characters (alphanumeric, dash, underscore)
        if not v or len(v) < 5 or len(v) > 20:
            raise ValueError("Invalid video ID length")
        # Allow alphanumeric, dash, and underscore
        if not all(c.isalnum() or c in '-_' for c in v):
            raise ValueError("Invalid video ID format")
        return v
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate YouTube URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        # Check if it's a YouTube URL
        if not any(domain in v.lower() for domain in ['youtube.com', 'youtu.be']):
            raise ValueError("URL must be a YouTube URL")
        return v


class RedditResult(BaseModel):
    """Result from Reddit search with post content and metadata."""
    url: str = Field(min_length=1, max_length=2000)
    title: str = Field(min_length=1, max_length=500)
    content: str = Field(default="", max_length=50000)
    score: float = Field(default=0.0)
    published_date: Optional[str] = Field(default=None, max_length=50)
    subreddit: str = Field(min_length=1, max_length=100)
    is_reddit_post: bool = Field(default=False)
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate Reddit URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        # Check if it's a Reddit URL
        if 'reddit.com' not in v.lower():
            raise ValueError("URL must be a Reddit URL")
        return v
    
    @field_validator('subreddit')
    @classmethod
    def validate_subreddit(cls, v: str) -> str:
        """Validate and normalize subreddit name."""
        # Remove r/ prefix if present
        clean_subreddit = v.lstrip('r/').strip()
        if not clean_subreddit:
            return 'unknown'
        # Subreddit names can contain letters, numbers, and underscores
        # Must be between 3-21 characters
        if len(clean_subreddit) < 2 or len(clean_subreddit) > 21:
            return clean_subreddit  # Return as-is if length is unusual
        # Allow alphanumeric and underscores
        if not all(c.isalnum() or c == '_' for c in clean_subreddit):
            return clean_subreddit  # Return as-is if format is unusual
        return clean_subreddit


class AcademicResult(BaseModel):
    """Result from academic paper search with metadata."""
    title: str = Field(min_length=1, max_length=500)
    url: str = Field(min_length=1, max_length=2000)
    summary: str = Field(default="", max_length=10000)
    published_date: Optional[str] = Field(default=None, max_length=50)
    author: Optional[str] = Field(default=None, max_length=500)
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v
    
    @field_validator('title')
    @classmethod
    def clean_title(cls, v: str) -> str:
        """Clean paper title by removing brackets and extra whitespace."""
        import re
        # Remove content in brackets like [PDF], [HTML], etc.
        cleaned = re.sub(r'\s*\[.*?\]\s*', '', v)
        # Remove extra whitespace
        cleaned = ' '.join(cleaned.split())
        return cleaned.strip()
    
    @field_validator('summary')
    @classmethod
    def clean_summary(cls, v: str) -> str:
        """Clean paper summary by removing common prefixes."""
        import re
        # Remove "Summary:" prefix (case-insensitive)
        cleaned = re.sub(r'^Summary:\s*', '', v, flags=re.IGNORECASE)
        # Remove "Abstract:" prefix (case-insensitive)
        cleaned = re.sub(r'^Abstract:\s*', '', cleaned, flags=re.IGNORECASE)
        # Remove extra whitespace
        cleaned = ' '.join(cleaned.split())
        return cleaned.strip()
