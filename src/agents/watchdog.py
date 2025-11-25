"""
Layer 7: The Watchdog (Meta-Analytical Observer)
Counter-intelligence and self-correction - detecting info-ops and our own biases.
"""

from typing import Dict, Any, List
from ..core.base_agent import BaseAgent
from ..core.dossier import InvestigationDossier
from ..core.tools import ToolKit


class WatchdogAgent(BaseAgent):
    """
    Monitors for information warfare signatures and checks the system's own biases.
    The newsroom's ombudsman and security officer combined.
    """
    
    def __init__(self, toolkit: ToolKit):
        super().__init__(
            name="Watchdog",
            description="Meta-analysis and bias detection agent"
        )
        self.toolkit = toolkit
    
    async def analyze(self, dossier: InvestigationDossier) -> Dict[str, Any]:
        """Perform meta-analysis and bias checks"""
        
        # Detect information warfare signatures
        infowar_analysis = await self._detect_infowar_signatures(dossier)
        
        # Check for cognitive biases in our own analysis
        bias_check = self._check_own_biases(dossier)
        
        # Identify unknown unknowns
        unknowns = self._identify_unknowns(dossier)
        
        # Assess investigation completeness
        completeness = self._assess_completeness(dossier)
        
        findings = {
            "infowar_signatures": infowar_analysis,
            "bias_check": bias_check,
            "unknown_unknowns": unknowns,
            "completeness_score": completeness,
            "meta_warnings": self._generate_warnings(infowar_analysis, bias_check, unknowns)
        }
        
        # Add warnings to red flags
        for warning in findings['meta_warnings']:
            if warning not in dossier.red_flags:
                dossier.red_flags.append(warning)
        
        self.log_finding(
            f"Infowar risk: {infowar_analysis.get('risk_score', 0):.2f}, "
            f"bias warnings: {len(bias_check.get('warnings', []))}"
        )
        
        return findings
    
    async def _detect_infowar_signatures(self, dossier: InvestigationDossier) -> Dict[str, Any]:
        """Detect coordinated inauthentic behavior and information operations"""
        
        # Analyze amplification patterns
        sources = [e.source for e in dossier.evidence_log]
        amplification = await self.toolkit.bot_detection.analyze_amplification(
            dossier.claim, 
            sources
        )
        
        # Check for coordinated timing
        coordinated_timing = self._check_coordinated_timing(dossier)
        
        # Check for strategic framing
        strategic_framing = self._check_strategic_framing(dossier.claim)
        
        # Calculate overall risk score
        risk_score = (
            amplification.get('bot_probability', 0) * 0.4 +
            amplification.get('coordination_score', 0) * 0.3 +
            (1.0 if coordinated_timing else 0.0) * 0.2 +
            (1.0 if strategic_framing else 0.0) * 0.1
        )
        
        return {
            "risk_score": risk_score,
            "bot_probability": amplification.get('bot_probability', 0),
            "coordination_detected": amplification.get('coordination_score', 0) > 0.5,
            "coordinated_timing": coordinated_timing,
            "strategic_framing": strategic_framing,
            "suspicious_patterns": amplification.get('suspicious_patterns', [])
        }
    
    def _check_coordinated_timing(self, dossier: InvestigationDossier) -> bool:
        """Check if claim emerged in coordinated fashion"""
        
        # Check if claim appeared simultaneously across multiple sources
        if len(dossier.evidence_log) < 3:
            return False
        
        # Simple heuristic: if all evidence is very recent and from multiple sources
        # In production: check actual timestamps
        
        sources = set(e.source for e in dossier.evidence_log)
        if len(sources) >= 3:
            # Multiple sources appearing quickly could indicate coordination
            return True
        
        return False
    
    def _check_strategic_framing(self, claim: str) -> bool:
        """Check for strategic framing typical of info-ops"""
        
        claim_lower = claim.lower()
        
        # Emotional manipulation
        emotional_triggers = [
            'outrage', 'shocking', 'horrifying', 'terrifying',
            'unbelievable', 'scandal', 'crisis'
        ]
        
        # Divisive framing
        divisive_frames = [
            'us vs them', 'they want', 'they don\'t want you to know',
            'the truth about', 'what they\'re hiding'
        ]
        
        # Check for these patterns
        has_emotional = any(trigger in claim_lower for trigger in emotional_triggers)
        has_divisive = any(frame in claim_lower for frame in divisive_frames)
        
        return has_emotional and has_divisive
    
    def _check_own_biases(self, dossier: InvestigationDossier) -> Dict[str, Any]:
        """Check for cognitive biases in our own analysis"""
        
        warnings = []
        
        # Confirmation bias check
        if dossier.hypotheses:
            top_hypothesis = dossier.get_top_hypothesis()
            if top_hypothesis and top_hypothesis.confidence > 0.7:
                # Check if we're only looking for supporting evidence
                support_ratio = len(top_hypothesis.supporting_evidence) / max(
                    len(dossier.evidence_log), 1
                )
                if support_ratio > 0.8:
                    warnings.append("Possible confirmation bias - mostly supporting evidence")
        
        # Availability heuristic
        if len(dossier.evidence_log) < 3:
            warnings.append("Limited evidence - may be relying on availability heuristic")
        
        # Anchoring bias
        initial_skepticism = dossier.skepticism_level
        current_confidence = dossier.confidence_matrix.overall_confidence
        
        # If initial skepticism was high but we haven't found much evidence either way
        if initial_skepticism > 0.7 and len(dossier.evidence_log) < 5:
            warnings.append("Possible anchoring on initial skepticism")
        
        # Source diversity check
        if dossier.evidence_log:
            unique_sources = len(set(e.source for e in dossier.evidence_log))
            if unique_sources < 3:
                warnings.append("Limited source diversity - may have echo chamber effect")
        
        return {
            "warnings": warnings,
            "bias_risk": len(warnings) / 4  # Normalize to 0-1
        }
    
    def _identify_unknowns(self, dossier: InvestigationDossier) -> List[str]:
        """Identify what we might be missing (unknown unknowns)"""
        
        unknowns = []
        
        # Language barriers
        if not self._check_multilingual_search(dossier):
            unknowns.append("Potential language barriers - only English sources checked")
        
        # Access limitations
        if not self._check_paywalled_sources(dossier):
            unknowns.append("May be missing paywalled/subscription content")
        
        # Cultural context
        if self._involves_foreign_context(dossier.claim):
            unknowns.append("Claim involves foreign context - may lack cultural understanding")
        
        # Technical expertise
        if self._requires_technical_expertise(dossier.claim):
            unknowns.append("Claim requires technical expertise - may need specialist review")
        
        # Classified/restricted information
        if self._involves_restricted_info(dossier.claim):
            unknowns.append("May involve classified or restricted information")
        
        return unknowns
    
    def _check_multilingual_search(self, dossier: InvestigationDossier) -> bool:
        """Check if we searched in multiple languages"""
        # Placeholder - in production, check if search was multilingual
        return False
    
    def _check_paywalled_sources(self, dossier: InvestigationDossier) -> bool:
        """Check if we accessed paywalled sources"""
        # Placeholder - in production, check for academic/paywalled sources
        return False
    
    def _involves_foreign_context(self, claim: str) -> bool:
        """Check if claim involves foreign countries/cultures"""
        foreign_indicators = [
            'china', 'russia', 'iran', 'north korea',
            'middle east', 'asia', 'europe', 'africa'
        ]
        return any(indicator in claim.lower() for indicator in foreign_indicators)
    
    def _requires_technical_expertise(self, claim: str) -> bool:
        """Check if claim requires specialized technical knowledge"""
        technical_domains = [
            'quantum', 'nuclear', 'genetic', 'cryptographic',
            'algorithm', 'protocol', 'molecular', 'biochemical'
        ]
        return any(domain in claim.lower() for domain in technical_domains)
    
    def _involves_restricted_info(self, claim: str) -> bool:
        """Check if claim might involve classified information"""
        restricted_indicators = [
            'classified', 'secret', 'intelligence', 'military',
            'national security', 'confidential'
        ]
        return any(indicator in claim.lower() for indicator in restricted_indicators)
    
    def _assess_completeness(self, dossier: InvestigationDossier) -> float:
        """Assess how complete our investigation is"""
        
        score = 0.0
        max_score = 0.0
        
        # Evidence quantity
        max_score += 1.0
        score += min(len(dossier.evidence_log) / 10, 1.0)
        
        # Source diversity
        max_score += 1.0
        if dossier.evidence_log:
            unique_sources = len(set(e.source for e in dossier.evidence_log))
            score += min(unique_sources / 5, 1.0)
        
        # All layers executed
        max_score += 1.0
        expected_layers = ['Gatekeeper', 'Profiler', 'Investigator', 'Historian', 'Judge', 'Logician']
        executed_layers = len([l for l in expected_layers if l in dossier.layer_findings])
        score += executed_layers / len(expected_layers)
        
        # Hypotheses generated
        max_score += 1.0
        score += min(len(dossier.hypotheses) / 3, 1.0)
        
        return score / max_score if max_score > 0 else 0.0
    
    def _generate_warnings(self, infowar: Dict, bias: Dict, unknowns: List[str]) -> List[str]:
        """Generate meta-warnings for the investigation"""
        
        warnings = []
        
        # Information warfare warnings
        if infowar.get('risk_score', 0) > 0.6:
            warnings.append("HIGH RISK: Possible coordinated information operation detected")
        elif infowar.get('risk_score', 0) > 0.4:
            warnings.append("MODERATE RISK: Some indicators of coordinated amplification")
        
        # Bias warnings
        if bias.get('bias_risk', 0) > 0.5:
            warnings.append("CAUTION: Multiple cognitive bias indicators in analysis")
        
        # Unknown unknowns
        if len(unknowns) > 2:
            warnings.append(f"INCOMPLETE: {len(unknowns)} potential knowledge gaps identified")
        
        return warnings
