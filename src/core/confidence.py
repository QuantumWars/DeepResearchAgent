from typing import List
from src.models.schemas import Evidence, Claim

class ConfidenceScorer:
    def calculate_confidence(self, evidence_set: List[Evidence], claim: Claim) -> float:
        """
        Calculate overall confidence score (0-1) for claim verdict
        """
        scores = {
            'source_quality': self.score_source_quality(evidence_set),
            'source_agreement': self.score_source_agreement(evidence_set),
            'source_diversity': self.score_source_diversity(evidence_set),
            'temporal_consistency': self.score_temporal_consistency(evidence_set),
            'logical_coherence': self.score_logical_coherence(evidence_set, claim),
            'primary_source_presence': self.score_primary_sources(evidence_set)
        }

        # Weighted combination
        weights = {
            'source_quality': 0.30,
            'source_agreement': 0.25,
            'source_diversity': 0.15,
            'temporal_consistency': 0.10,
            'logical_coherence': 0.10,
            'primary_source_presence': 0.10
        }

        final_confidence = sum(
            scores[factor] * weights[factor]
            for factor in scores
        )

        # Apply penalties for concerning patterns
        final_confidence *= self.apply_penalties(evidence_set)

        return min(max(final_confidence, 0.0), 1.0)

    def score_source_quality(self, evidence_set: List[Evidence]) -> float:
        """
        Average source tier score
        """
        tier_scores = {
            1: 1.0,   # Primary/Official
            2: 0.8,   # Expert/Academic
            3: 0.6,   # Credible News
            4: 0.4,   # Secondary
            5: 0.2    # Unreliable
        }

        if not evidence_set:
            return 0.0

        avg_tier_score = sum(
            tier_scores.get(e.source_tier, 0.2)
            for e in evidence_set
        ) / len(evidence_set)

        return avg_tier_score

    def score_source_agreement(self, evidence_set: List[Evidence]) -> float:
        """
        How well sources agree on the claim
        """
        if len(evidence_set) < 2:
            return 0.5  # Insufficient sources penalty

        verdicts = [e.verdict for e in evidence_set]
        if not verdicts:
            return 0.0
            
        most_common = max(set(verdicts), key=verdicts.count)
        agreement_ratio = verdicts.count(most_common) / len(verdicts)

        return agreement_ratio

    def score_source_diversity(self, evidence_set: List[Evidence]) -> float:
        """
        Diversity of source types (prevents echo chamber)
        """
        # Simplified: using source name as proxy for type/origin diversity
        sources = set(e.source for e in evidence_set)
        diversity_score = min(len(sources) / 4, 1.0)  # Cap at 4 distinct sources

        return diversity_score
    
    def score_temporal_consistency(self, evidence_set: List[Evidence]) -> float:
        # Placeholder logic
        return 1.0

    def score_logical_coherence(self, evidence_set: List[Evidence], claim: Claim) -> float:
        # Placeholder logic
        return 1.0

    def score_primary_sources(self, evidence_set: List[Evidence]) -> float:
        if any(e.source_tier == 1 for e in evidence_set):
            return 1.0
        return 0.0

    def apply_penalties(self, evidence_set: List[Evidence]) -> float:
        """
        Reduce confidence for concerning patterns
        """
        penalty_multiplier = 1.0

        # No primary sources penalty
        if not any(e.source_tier == 1 for e in evidence_set):
            penalty_multiplier *= 0.8

        # Single source penalty
        if len(evidence_set) == 1:
            penalty_multiplier *= 0.7

        # Contradiction penalty
        verdicts = [e.verdict for e in evidence_set]
        if len(set(verdicts)) > 1:
            contradiction_ratio = 1 - (max(verdicts.count(v) for v in set(verdicts)) / len(verdicts))
            penalty_multiplier *= (1 - contradiction_ratio * 0.5)

        return penalty_multiplier
