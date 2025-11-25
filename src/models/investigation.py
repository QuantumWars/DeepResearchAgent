"""Investigation models for structured outputs."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class InvestigationDecision(BaseModel):
    """Decision about whether to continue investigating."""
    continue_investigation: bool = Field(description="Whether to continue investigating")
    reasoning: str = Field(description="Reasoning for the decision")
    links_to_follow: List[str] = Field(default_factory=list, description="URLs to investigate next")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this decision")


class PageFinding(BaseModel):
    """A single page finding from investigation."""
    url: str = Field(description="URL of the page")
    title: str = Field(description="Page title")
    content_preview: str = Field(description="Preview of content (first 500 chars)")
    relevance_score: float = Field(ge=0.0, le=1.0, description="Relevance to investigation query")
    depth: int = Field(description="Depth in the investigation tree")
    key_points: List[str] = Field(default_factory=list, description="Key points extracted from page")


class InvestigationResult(BaseModel):
    """Complete investigation result."""
    query: str = Field(description="Original investigation query")
    pages_visited: int = Field(description="Number of pages visited")
    total_content_length: int = Field(description="Total characters of content gathered")
    findings: List[PageFinding] = Field(description="All page findings")
    key_insights: List[str] = Field(default_factory=list, description="Key insights from investigation")
    evidence_summary: str = Field(description="Summary of evidence found")
    confidence: float = Field(ge=0.0, le=1.0, description="Overall confidence in findings")


class LinkWithContext(BaseModel):
    """A link with its surrounding context."""
    url: str = Field(description="The URL")
    text: str = Field(description="Link text")
    context: str = Field(description="Surrounding text context")
    relevance_score: float = Field(ge=0.0, le=1.0, description="Relevance to query")
