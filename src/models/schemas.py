from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class Claim(BaseModel):
    original_text: str
    claimed_by: Optional[str] = None
    claim_date: Optional[str] = None
    verification_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))

class SubClaim(BaseModel):
    id: str
    text: str
    claim_type: Literal["FACTUAL", "STATISTICAL", "TEMPORAL", "COMPARATIVE", "CONTEXTUAL", "MULTIMEDIA"] = "FACTUAL"
    verdict: Optional[str] = None
    confidence: float = 0.0
    evidence_count: int = 0

class Evidence(BaseModel):
    source: str
    source_tier: int = Field(..., ge=1, le=5)
    url: Optional[str] = None
    published: Optional[str] = None
    excerpt: str
    relevance: str
    supports: List[str] = []
    contradicts: List[str] = []
    verdict: Literal["TRUE", "FALSE", "PARTIAL", "UNCERTAIN"] = "UNCERTAIN"
    confidence: float = 0.0

class TimelineEvent(BaseModel):
    date: str
    event: str
    data: Dict[str, Any] = {}
    sources: List[str] = []
    confidence: float = 0.0
    flag: Optional[str] = None

class Contradiction(BaseModel):
    type: str
    description: str
    resolution: Optional[str] = None
    confidence_impact: float = 0.0
    values: List[Any] = []

class Resolution(BaseModel):
    type: str
    explanation: str
    confidence: float
    needs_more_evidence: bool = False
    search_suggestions: List[str] = []

class Verdict(BaseModel):
    status: str
    confidence: float
    summary: str

class InvestigationResult(BaseModel):
    claim: Claim
    verdict: Verdict
    sub_claims: List[SubClaim] = []
    timeline: List[TimelineEvent] = []
    evidence_summary: Dict[str, Any] = {}
    key_evidence: List[Evidence] = []
    contradictions: List[Contradiction] = []
    investigation_metadata: Dict[str, Any] = {}
    caveats: List[str] = []
    recommended_actions: List[str] = []

class SearchQuery(BaseModel):
    tool: str
    query: str
    priority: int
    params: Dict[str, Any] = {}
    requires_precision: bool = False
    requires_breadth: bool = False
    official_source_available: bool = False
    api_source: Optional[str] = None
    endpoint: Optional[str] = None

class SearchPlan(BaseModel):
    sub_claim_id: str
    queries: List[SearchQuery]
    expected_evidence_type: List[str]
    recursion_likely: bool = False

class Evaluation(BaseModel):
    confidence: float
    has_contradictions: bool = False
    critical_gaps: bool = False
    timeline_conflicts: bool = False
    primary_source_count: int = 0
    contradictions: List[Contradiction] = []
    timeline_gaps: List[Any] = []
    context_missing: bool = False
    needs_comparison: bool = False
