"""
Layer 5: The Judge (Evidence Hierarchy Manager)
Weighs evidence quality and resolves conflicts based on tier system.
"""

from typing import Dict, Any, List
from collections import defaultdict
from ..core.base_agent import BaseAgent
from ..core.dossier import InvestigationDossier, Evidence, EvidenceTier


class JudgeAgent(BaseAgent):
    """
    Weighs evidence based on hierarchy and resolves contradictions.
    The arbiter of what evidence is admissible and how much weight it carries.
    """
    
    def __init__(self):
        super().__init__(
            name="Judge",
            description="Evidence hierarchy and weighing agent"
        )
        
        # Tier weights for scoring
        self.tier_weights = {
            EvidenceTier.TIER_1_PRIMARY: 1.0,
            EvidenceTier.TIER_2_EXPERT: 0.8,
            EvidenceTier.TIER_3_CREDIBLE: 0.6,
            EvidenceTier.TIER_4_SECONDARY: 0.4,
            EvidenceTier.TIER_5_UNVERIFIED: 0.2
        }
    
    async def analyze(self, dossier: InvestigationDossier) -> Dict[str, Any]:
        """Weigh all evidence and resolve conflicts"""
        
        # Categorize evidence by tier
        evidence_by_tier = self._categorize_by_tier(dossier.evidence_log)
        
        # Calculate weighted evidence score
        evidence_score = self._calculate_evidence_score(dossier.evidence_log)
        
        # Resolve contradictions
        contradictions = self._identify_contradictions(dossier.evidence_log)
        resolution = self._resolve_contradictions(contradictions)
        
        # Assess evidence quality
        quality_assessment = self._assess_evidence_quality(dossier.evidence_log)
        
        # Update confidence matrix
        dossier.confidence_matrix.source_quality = quality_assessment['avg_quality']
        dossier.confidence_matrix.evidence_quantity = min(len(dossier.evidence_log) / 10, 1.0)
        dossier.confidence_matrix.evidence_independence = self._assess_independence(dossier.evidence_log)
        
        findings = {
            "total_evidence": len(dossier.evidence_log),
            "evidence_by_tier": {tier.name: len(evidence_by_tier.get(tier, [])) for tier in EvidenceTier},
            "weighted_score": evidence_score,
            "quality_assessment": quality_assessment,
            "contradictions_found": len(contradictions),
            "contradiction_resolution": resolution,
            "evidence_strength": self._categorize_strength(evidence_score)
        }
        
        self.log_finding(
            f"Analyzed {len(dossier.evidence_log)} pieces of evidence, "
            f"weighted score: {evidence_score:.2f}, strength: {findings['evidence_strength']}"
        )
        
        return findings
    
    def _categorize_by_tier(self, evidence_log: List[Evidence]) -> Dict[EvidenceTier, List[Evidence]]:
        """Organize evidence by tier"""
        categorized = defaultdict(list)
        
        for evidence in evidence_log:
            categorized[evidence.tier].append(evidence)
        
        return dict(categorized)
    
    def _calculate_evidence_score(self, evidence_log: List[Evidence]) -> float:
        """Calculate weighted evidence score"""
        if not evidence_log:
            return 0.0
        
        total_weight = 0.0
        total_score = 0.0
        
        for evidence in evidence_log:
            tier_weight = self.tier_weights[evidence.tier]
            evidence_weight = tier_weight * evidence.reliability_score
            
            total_weight += tier_weight
            total_score += evidence_weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _assess_evidence_quality(self, evidence_log: List[Evidence]) -> Dict[str, Any]:
        """Assess overall quality of evidence"""
        if not evidence_log:
            return {
                'avg_quality': 0.0,
                'high_quality_count': 0,
                'low_quality_count': 0
            }
        
        # Calculate average tier quality
        tier_scores = [self.tier_weights[e.tier] for e in evidence_log]
        avg_tier_quality = sum(tier_scores) / len(tier_scores)
        
        # Calculate average reliability
        avg_reliability = sum(e.reliability_score for e in evidence_log) / len(evidence_log)
        
        # Combined quality score
        avg_quality = (avg_tier_quality + avg_reliability) / 2
        
        # Count high and low quality evidence
        high_quality = sum(1 for e in evidence_log if self.tier_weights[e.tier] >= 0.8)
        low_quality = sum(1 for e in evidence_log if self.tier_weights[e.tier] <= 0.4)
        
        return {
            'avg_quality': avg_quality,
            'avg_tier_quality': avg_tier_quality,
            'avg_reliability': avg_reliability,
            'high_quality_count': high_quality,
            'low_quality_count': low_quality
        }
    
    def _assess_independence(self, evidence_log: List[Evidence]) -> float:
        """Assess how independent the evidence sources are"""
        if len(evidence_log) < 2:
            return 0.5
        
        # Count unique sources
        unique_sources = len(set(e.source for e in evidence_log))
        
        # Independence score based on source diversity
        independence = unique_sources / len(evidence_log)
        
        return min(independence, 1.0)
    
    def _identify_contradictions(self, evidence_log: List[Evidence]) -> List[Dict[str, Any]]:
        """Identify contradictory evidence"""
        contradictions = []
        
        # Simple heuristic: look for evidence with very different content
        # In production, use NLP for semantic contradiction detection
        
        for i, e1 in enumerate(evidence_log):
            for e2 in evidence_log[i+1:]:
                # Check for contradiction markers
                if self._check_contradiction(e1.content, e2.content):
                    contradictions.append({
                        'evidence1': e1,
                        'evidence2': e2,
                        'tier1': e1.tier,
                        'tier2': e2.tier
                    })
        
        return contradictions
    
    def _check_contradiction(self, content1: str, content2: str) -> bool:
        """Check if two pieces of content contradict each other"""
        # Simple heuristic based on negation words
        negation_words = ['not', 'false', 'incorrect', 'wrong', 'debunked', 'no']
        
        c1_lower = content1.lower()
        c2_lower = content2.lower()
        
        # If one has negation and they share key terms, likely contradictory
        c1_has_negation = any(word in c1_lower for word in negation_words)
        c2_has_negation = any(word in c2_lower for word in negation_words)
        
        if c1_has_negation != c2_has_negation:
            # Check for shared terms
            words1 = set(c1_lower.split())
            words2 = set(c2_lower.split())
            overlap = len(words1 & words2) / min(len(words1), len(words2)) if words1 and words2 else 0
            
            return overlap > 0.3
        
        return False
    
    def _resolve_contradictions(self, contradictions: List[Dict[str, Any]]) -> List[str]:
        """Resolve contradictions based on evidence tier"""
        resolutions = []
        
        for contradiction in contradictions:
            e1 = contradiction['evidence1']
            e2 = contradiction['evidence2']
            
            # Higher tier wins
            tier1_weight = self.tier_weights[e1.tier]
            tier2_weight = self.tier_weights[e2.tier]
            
            if tier1_weight > tier2_weight:
                resolutions.append(
                    f"Contradiction resolved in favor of {e1.source} "
                    f"(Tier {e1.tier.value} > Tier {e2.tier.value})"
                )
            elif tier2_weight > tier1_weight:
                resolutions.append(
                    f"Contradiction resolved in favor of {e2.source} "
                    f"(Tier {e2.tier.value} > Tier {e1.tier.value})"
                )
            else:
                # Same tier - use reliability score
                if e1.reliability_score > e2.reliability_score:
                    resolutions.append(
                        f"Contradiction resolved in favor of {e1.source} "
                        f"(higher reliability: {e1.reliability_score:.2f})"
                    )
                else:
                    resolutions.append(
                        f"Contradiction unresolved - equal tier and reliability"
                    )
        
        return resolutions
    
    def _categorize_strength(self, score: float) -> str:
        """Categorize evidence strength"""
        if score >= 0.8:
            return "Very Strong"
        elif score >= 0.6:
            return "Strong"
        elif score >= 0.4:
            return "Moderate"
        elif score >= 0.2:
            return "Weak"
        else:
            return "Very Weak"
