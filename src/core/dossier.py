"""
Investigation Dossier: The shared state object for fact-checking investigations.
This mimics the journalist's notebook - a living document that evolves as evidence accumulates.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class InvestigationStrategy(Enum):
    """Different pathways based on claim type"""
    BREAKING_NEWS = "breaking_news"
    HISTORICAL_CLAIM = "historical_claim"
    SCIENTIFIC_CLAIM = "scientific_claim"
    POLITICAL_CLAIM = "political_claim"
    STATISTICAL_CLAIM = "statistical_claim"
    GENERAL = "general"


class EvidenceTier(Enum):
    """Hierarchy of evidence quality"""
    TIER_1_PRIMARY = 1  # First-hand documents, direct observation, original data
    TIER_2_EXPERT = 2   # Expert analysis of primary sources
    TIER_3_CREDIBLE = 3 # Credible reporting citing primary
    TIER_4_SECONDARY = 4 # Secondary analysis
    TIER_5_UNVERIFIED = 5 # Anonymous/unverified claims


class TruthValue(Enum):
    """Final verdict categories"""
    CONFIRMED = "confirmed"
    HIGHLY_LIKELY = "highly_likely"
    PROBABLE = "probable"
    UNCLEAR = "unclear"
    UNLIKELY = "unlikely"
    FALSE = "false"
    PENDING = "pending"


@dataclass
class Evidence:
    """A single piece of evidence"""
    content: str
    source: str
    tier: EvidenceTier
    reliability_score: float  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self):
        return f"[Tier {self.tier.value}] {self.source}: {self.content[:100]}..."


@dataclass
class SourceProfile:
    """Detailed analysis of a source"""
    name: str
    authority_score: float  # 0.0 to 1.0
    bias_indicators: List[str] = field(default_factory=list)
    track_record: Optional[str] = None
    conflicts_of_interest: List[str] = field(default_factory=list)
    expertise_domains: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Hypothesis:
    """A working theory about the claim"""
    description: str
    supporting_evidence: List[Evidence] = field(default_factory=list)
    contradicting_evidence: List[Evidence] = field(default_factory=list)
    confidence: float = 0.5  # 0.0 to 1.0
    
    @property
    def net_support(self) -> float:
        """Calculate net support based on evidence"""
        support = sum(e.reliability_score for e in self.supporting_evidence)
        contradict = sum(e.reliability_score for e in self.contradicting_evidence)
        total = support + contradict
        return (support - contradict) / total if total > 0 else 0.0


@dataclass
class ConfidenceMatrix:
    """Multi-dimensional confidence scoring"""
    source_quality: float = 0.5  # Quality of sources
    evidence_quantity: float = 0.5  # Amount of evidence
    evidence_independence: float = 0.5  # How independent are sources
    logical_coherence: float = 0.5  # Internal consistency
    context_clarity: float = 0.5  # How well we understand context
    
    @property
    def overall_confidence(self) -> float:
        """Weighted average of all dimensions"""
        weights = {
            'source_quality': 0.3,
            'evidence_quantity': 0.15,
            'evidence_independence': 0.25,
            'logical_coherence': 0.2,
            'context_clarity': 0.1
        }
        return sum(getattr(self, k) * v for k, v in weights.items())


@dataclass
class InvestigationDossier:
    """
    The central shared state object passed between agents.
    This is the journalist's evolving understanding of the claim.
    """
    # Core claim information
    claim: str
    source: str
    context: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Investigation metadata
    priority_score: float = 0.5  # 0.0 to 1.0
    skepticism_level: float = 0.5  # 0.0 (trusting) to 1.0 (highly skeptical)
    strategy: InvestigationStrategy = InvestigationStrategy.GENERAL
    
    # Evidence and analysis
    evidence_log: List[Evidence] = field(default_factory=list)
    source_profiles: Dict[str, SourceProfile] = field(default_factory=dict)
    hypotheses: List[Hypothesis] = field(default_factory=list)
    
    # Findings from each layer
    layer_findings: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Confidence and verdict
    confidence_matrix: ConfidenceMatrix = field(default_factory=ConfidenceMatrix)
    truth_value: TruthValue = TruthValue.PENDING
    
    # Final output
    caveats: List[str] = field(default_factory=list)
    unanswered_questions: List[str] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)
    
    def add_evidence(self, evidence: Evidence):
        """Add evidence to the log"""
        self.evidence_log.append(evidence)
    
    def add_source_profile(self, profile: SourceProfile):
        """Add or update a source profile"""
        self.source_profiles[profile.name] = profile
    
    def add_layer_finding(self, layer_name: str, findings: Dict[str, Any]):
        """Record findings from a specific agent layer"""
        self.layer_findings[layer_name] = findings
    
    def get_evidence_by_tier(self, tier: EvidenceTier) -> List[Evidence]:
        """Get all evidence of a specific tier"""
        return [e for e in self.evidence_log if e.tier == tier]
    
    def get_top_hypothesis(self) -> Optional[Hypothesis]:
        """Get the hypothesis with highest confidence"""
        if not self.hypotheses:
            return None
        return max(self.hypotheses, key=lambda h: h.confidence)
    
    def summary(self) -> str:
        """Generate a human-readable summary"""
        return f"""
Investigation Dossier Summary
============================
Claim: {self.claim}
Source: {self.source}
Strategy: {self.strategy.value}
Priority: {self.priority_score:.2f}
Skepticism: {self.skepticism_level:.2f}

Evidence: {len(self.evidence_log)} pieces
  - Tier 1 (Primary): {len(self.get_evidence_by_tier(EvidenceTier.TIER_1_PRIMARY))}
  - Tier 2 (Expert): {len(self.get_evidence_by_tier(EvidenceTier.TIER_2_EXPERT))}
  - Tier 3 (Credible): {len(self.get_evidence_by_tier(EvidenceTier.TIER_3_CREDIBLE))}

Sources Profiled: {len(self.source_profiles)}
Hypotheses: {len(self.hypotheses)}

Overall Confidence: {self.confidence_matrix.overall_confidence:.2f}
Truth Value: {self.truth_value.value}

Red Flags: {len(self.red_flags)}
Caveats: {len(self.caveats)}
Unanswered Questions: {len(self.unanswered_questions)}
"""
