"""
Layer 8: The Editor (Confidence Calibration & Output)
Final synthesis and verdict - the editor-in-chief's publishing decision.
"""

from typing import Dict, Any
from ..core.base_agent import BaseAgent
from ..core.dossier import InvestigationDossier, TruthValue, EvidenceTier


class EditorAgent(BaseAgent):
    """
    Synthesizes all findings into a final verdict with calibrated confidence.
    The editor-in-chief making the final call on what to publish.
    """
    
    def __init__(self):
        super().__init__(
            name="Editor",
            description="Final synthesis and verdict agent"
        )
    
    async def analyze(self, dossier: InvestigationDossier) -> Dict[str, Any]:
        """Synthesize all findings into final verdict"""
        
        # Calculate final truth value
        truth_value = self._determine_truth_value(dossier)
        dossier.truth_value = truth_value
        
        # Generate caveats
        caveats = self._generate_caveats(dossier)
        dossier.caveats.extend(caveats)
        
        # Identify what could change the assessment
        change_factors = self._identify_change_factors(dossier)
        
        # Generate executive summary
        summary = self._generate_summary(dossier)
        
        # Recommendations for further investigation
        recommendations = self._generate_recommendations(dossier)
        
        findings = {
            "truth_value": truth_value.value,
            "confidence": dossier.confidence_matrix.overall_confidence,
            "summary": summary,
            "caveats": caveats,
            "change_factors": change_factors,
            "recommendations": recommendations,
            "ready_to_publish": self._is_ready_to_publish(dossier)
        }
        
        self.log_finding(
            f"Final verdict: {truth_value.value}, "
            f"confidence: {dossier.confidence_matrix.overall_confidence:.2f}"
        )
        
        return findings
    
    def _determine_truth_value(self, dossier: InvestigationDossier) -> TruthValue:
        """Determine the final truth value based on all evidence"""
        
        confidence = dossier.confidence_matrix.overall_confidence
        
        # Get evidence strength from Judge's findings
        judge_findings = dossier.layer_findings.get('Judge', {})
        evidence_score = judge_findings.get('weighted_score', 0.5)
        
        # Get logical coherence from Logician
        logician_findings = dossier.layer_findings.get('Logician', {})
        coherence = logician_findings.get('coherence_score', 0.5)
        
        # Get corroboration from Investigator
        investigator_findings = dossier.layer_findings.get('Investigator', {})
        corroboration = investigator_findings.get('corroboration_strength', 0.5)
        
        # Check for contradictions
        contradictions = investigator_findings.get('contradictions_found', 0)
        
        # Check for high-tier evidence
        tier1_count = len(dossier.get_evidence_by_tier(EvidenceTier.TIER_1_PRIMARY))
        tier2_count = len(dossier.get_evidence_by_tier(EvidenceTier.TIER_2_EXPERT))
        
        # Decision logic
        
        # CONFIRMED: High confidence + high-tier evidence + high corroboration
        if (confidence >= 0.8 and 
            (tier1_count >= 2 or tier2_count >= 3) and 
            corroboration >= 0.7 and 
            coherence >= 0.7):
            return TruthValue.CONFIRMED
        
        # FALSE: Strong counter-evidence or major logical flaws
        if (coherence < 0.3 or 
            contradictions > 3 or 
            (evidence_score < 0.3 and confidence < 0.4)):
            return TruthValue.FALSE
        
        # HIGHLY_LIKELY: Good evidence and coherence
        if (confidence >= 0.7 and 
            evidence_score >= 0.6 and 
            coherence >= 0.6):
            return TruthValue.HIGHLY_LIKELY
        
        # UNLIKELY: Poor evidence or coherence
        if (confidence < 0.4 or 
            evidence_score < 0.4 or 
            coherence < 0.4):
            return TruthValue.UNLIKELY
        
        # UNCLEAR: Contradictory evidence
        if contradictions >= 2 or abs(evidence_score - 0.5) < 0.1:
            return TruthValue.UNCLEAR
        
        # PROBABLE: Default for moderate evidence
        return TruthValue.PROBABLE
    
    def _generate_caveats(self, dossier: InvestigationDossier) -> list:
        """Generate caveats about the assessment"""
        
        caveats = []
        
        # Evidence quantity caveat
        if len(dossier.evidence_log) < 5:
            caveats.append("Limited evidence available - assessment based on few sources")
        
        # Source diversity caveat
        unique_sources = len(set(e.source for e in dossier.evidence_log))
        if unique_sources < 3:
            caveats.append("Limited source diversity - verification from few independent sources")
        
        # Expertise caveat
        profiler_findings = dossier.layer_findings.get('Profiler', {})
        if profiler_findings.get('average_authority', 0) < 0.5:
            caveats.append("Sources have limited established authority in this domain")
        
        # Logical coherence caveat
        logician_findings = dossier.layer_findings.get('Logician', {})
        if logician_findings.get('coherence_score', 1.0) < 0.6:
            caveats.append("Some logical inconsistencies detected in the narrative")
        
        # Information warfare caveat
        watchdog_findings = dossier.layer_findings.get('Watchdog', {})
        infowar_risk = watchdog_findings.get('infowar_signatures', {}).get('risk_score', 0)
        if infowar_risk > 0.5:
            caveats.append("Indicators of coordinated amplification detected")
        
        # Unknown unknowns caveat
        unknowns = watchdog_findings.get('unknown_unknowns', [])
        if len(unknowns) > 0:
            caveats.append(f"Potential knowledge gaps: {', '.join(unknowns[:2])}")
        
        return caveats
    
    def _identify_change_factors(self, dossier: InvestigationDossier) -> list:
        """Identify what new information could change the assessment"""
        
        factors = []
        
        # Need for primary sources
        tier1_count = len(dossier.get_evidence_by_tier(EvidenceTier.TIER_1_PRIMARY))
        if tier1_count == 0:
            factors.append("Access to primary source documents")
        
        # Need for expert analysis
        tier2_count = len(dossier.get_evidence_by_tier(EvidenceTier.TIER_2_EXPERT))
        if tier2_count < 2:
            factors.append("Expert analysis from domain specialists")
        
        # Unanswered questions
        if dossier.unanswered_questions:
            factors.append(f"Answers to: {dossier.unanswered_questions[0]}")
        
        # Missing context
        historian_findings = dossier.layer_findings.get('Historian', {})
        if historian_findings.get('missing_information'):
            factors.append("Additional context or background information")
        
        # Contradictions to resolve
        investigator_findings = dossier.layer_findings.get('Investigator', {})
        if investigator_findings.get('contradictions_found', 0) > 0:
            factors.append("Resolution of contradictory evidence")
        
        return factors
    
    def _generate_summary(self, dossier: InvestigationDossier) -> str:
        """Generate executive summary of the investigation"""
        
        summary_parts = []
        
        # Claim and verdict
        summary_parts.append(
            f"**Claim**: {dossier.claim}\n\n"
            f"**Verdict**: {dossier.truth_value.value.upper()}\n"
            f"**Confidence**: {dossier.confidence_matrix.overall_confidence:.0%}\n"
        )
        
        # Evidence summary
        summary_parts.append(
            f"\n**Evidence**: {len(dossier.evidence_log)} sources analyzed, "
            f"{len(set(e.source for e in dossier.evidence_log))} unique sources"
        )
        
        # Key findings
        if dossier.red_flags:
            summary_parts.append(f"\n**Red Flags**: {len(dossier.red_flags)} identified")
        
        # Top hypothesis
        top_hyp = dossier.get_top_hypothesis()
        if top_hyp:
            summary_parts.append(f"\n**Leading Theory**: {top_hyp.description}")
        
        return ''.join(summary_parts)
    
    def _generate_recommendations(self, dossier: InvestigationDossier) -> list:
        """Generate recommendations for further investigation"""
        
        recommendations = []
        
        confidence = dossier.confidence_matrix.overall_confidence
        
        # Low confidence recommendations
        if confidence < 0.5:
            recommendations.append("Seek additional independent sources")
            recommendations.append("Consult domain experts")
        
        # Evidence quality recommendations
        judge_findings = dossier.layer_findings.get('Judge', {})
        if judge_findings.get('quality_assessment', {}).get('avg_quality', 1.0) < 0.5:
            recommendations.append("Prioritize higher-tier evidence sources")
        
        # Logical issues recommendations
        logician_findings = dossier.layer_findings.get('Logician', {})
        if logician_findings.get('logical_fallacies'):
            recommendations.append("Address logical fallacies in the claim")
        
        # Information warfare recommendations
        watchdog_findings = dossier.layer_findings.get('Watchdog', {})
        if watchdog_findings.get('infowar_signatures', {}).get('risk_score', 0) > 0.5:
            recommendations.append("Investigate potential coordinated amplification")
            recommendations.append("Verify source authenticity")
        
        # Strategy-specific recommendations
        if dossier.strategy.value == 'scientific_claim':
            recommendations.append("Verify peer review status")
            recommendations.append("Check for replication studies")
        elif dossier.strategy.value == 'statistical_claim':
            recommendations.append("Verify data sources and methodology")
            recommendations.append("Consult statistician for analysis")
        
        return recommendations
    
    def _is_ready_to_publish(self, dossier: InvestigationDossier) -> bool:
        """Determine if the investigation is complete enough to publish"""
        
        # Minimum requirements for publication
        min_evidence = 3
        min_confidence = 0.4
        min_sources = 2
        
        has_enough_evidence = len(dossier.evidence_log) >= min_evidence
        has_enough_confidence = dossier.confidence_matrix.overall_confidence >= min_confidence
        has_diverse_sources = len(set(e.source for e in dossier.evidence_log)) >= min_sources
        
        # Can't publish if major red flags
        watchdog_findings = dossier.layer_findings.get('Watchdog', {})
        has_major_warnings = any(
            'HIGH RISK' in warning 
            for warning in watchdog_findings.get('meta_warnings', [])
        )
        
        return (has_enough_evidence and 
                has_enough_confidence and 
                has_diverse_sources and 
                not has_major_warnings)
