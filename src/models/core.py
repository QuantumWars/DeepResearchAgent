"""Data models for the fact-checking system."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """Evidence collected from a specialist agent."""
    source: str = Field(description="Source of the evidence")
    content: str = Field(description="Content or summary of the evidence")
    confidence: float = Field(description="Confidence score (0-1)", ge=0, le=1)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ClaimAnalysis(BaseModel):
    """Analysis result from a specialist agent."""
    claim: str = Field(description="The claim being analyzed")
    verdict: str = Field(description="Verdict: TRUE, FALSE, PARTIALLY_TRUE, UNVERIFIABLE")
    evidence: List[Evidence] = Field(default_factory=list, description="Supporting evidence")
    confidence: float = Field(description="Overall confidence (0-1)", ge=0, le=1)
    reasoning: str = Field(description="Reasoning behind the verdict")
    agent_name: str = Field(description="Name of the agent that produced this analysis")


class RoutingDecision(BaseModel):
    """Decision about which agent should handle a claim."""
    claim: str = Field(description="The claim to route")
    target_agent: str = Field(description="Name of the target agent")
    reasoning: str = Field(description="Why this agent was chosen")
    confidence: float = Field(description="Confidence in routing decision", ge=0, le=1)


class FinalVerdict(BaseModel):
    """Final synthesized verdict from all agents."""
    claim: str = Field(description="The original claim")
    verdict: str = Field(description="Final verdict")
    confidence: float = Field(description="Overall confidence", ge=0, le=1)
    supporting_evidence: List[Evidence] = Field(default_factory=list)
    agent_analyses: List[ClaimAnalysis] = Field(default_factory=list)
    summary: str = Field(description="Human-readable summary")


class AtomicNote(BaseModel):
    """A discrete unit of information stored in memory."""
    content: str = Field(description="The core information/fact")
    tags: List[str] = Field(default_factory=list, description="Keywords for retrieval")
    source_url: Optional[str] = Field(None, description="Origin URL")
    confidence: float = Field(description="Confidence in this specific fact (0-1)", ge=0, le=1)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extra context")
    timestamp: str = Field(description="ISO timestamp of creation")


class ClaimReview(BaseModel):
    """Structured fact-check verdict based on Schema.org ClaimReview."""
    claim_reviewed: str = Field(description="The claim being checked")
    item_reviewed: Optional[str] = Field(None, description="Context/Source of the claim")
    review_rating: str = Field(description="Verdict: TRUE, FALSE, etc.")
    rating_score: int = Field(description="Numerical score (1-5)")
    review_body: str = Field(description="Detailed reasoning")
    author: str = Field(description="Agent name")
    date_published: str = Field(description="ISO date")
    url: Optional[str] = Field(None, description="URL of the fact check if published")

