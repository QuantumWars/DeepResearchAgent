"""
Layer 4: The Historian (Context & Historical Intelligence)
Provides the "why" and "before" - pattern recognition and motivation analysis.
"""

from typing import Dict, Any, List
from datetime import datetime
from ..core.base_agent import BaseAgent
from ..core.dossier import InvestigationDossier, Hypothesis
from ..core.tools import ToolKit


class HistorianAgent(BaseAgent):
    """
    Analyzes historical context, patterns, and motivations.
    The institutional memory of the newsroom.
    """
    
    def __init__(self, toolkit: ToolKit):
        super().__init__(
            name="Historian",
            description="Context and historical pattern analysis agent"
        )
        self.toolkit = toolkit
    
    async def analyze(self, dossier: InvestigationDossier) -> Dict[str, Any]:
        """Analyze historical context and patterns"""
        
        # Search for similar historical claims
        similar_claims = await self._find_similar_claims(dossier.claim)
        
        # Analyze timing
        timing_analysis = self._analyze_timing(dossier)
        
        # Cui bono analysis (who benefits?)
        beneficiaries = self._analyze_beneficiaries(dossier.claim, dossier.context)
        
        # Identify missing information
        missing_info = self._identify_missing_information(dossier)
        
        # Generate historical hypotheses
        hypotheses = self._generate_hypotheses(dossier, similar_claims, beneficiaries)
        
        for hypothesis in hypotheses:
            dossier.hypotheses.append(hypothesis)
        
        # Add missing info to dossier
        dossier.unanswered_questions.extend(missing_info)
        
        findings = {
            "similar_claims_found": len(similar_claims),
            "timing_suspicious": timing_analysis['suspicious'],
            "timing_context": timing_analysis['context'],
            "potential_beneficiaries": beneficiaries,
            "missing_information": missing_info,
            "hypotheses_generated": len(hypotheses)
        }
        
        self.log_finding(
            f"Found {len(similar_claims)} similar claims, "
            f"timing {'suspicious' if timing_analysis['suspicious'] else 'normal'}"
        )
        
        return findings
    
    async def _find_similar_claims(self, claim: str) -> List[Dict[str, Any]]:
        """Search for historically similar claims"""
        
        # Search fact-check database
        previous_checks = await self.toolkit.fact_check_db.check_claim(claim)
        
        # Search archives
        archive_results = await self.toolkit.search.archive_search(claim, max_results=5)
        
        similar = []
        
        for check in previous_checks:
            similar.append({
                'claim': check.get('claim', ''),
                'verdict': check.get('verdict', ''),
                'date': check.get('date', ''),
                'source': 'fact_check_db'
            })
        
        for result in archive_results:
            similar.append({
                'claim': result.snippet,
                'url': result.url,
                'date': 'unknown',
                'source': 'archive'
            })
        
        return similar
    
    def _analyze_timing(self, dossier: InvestigationDossier) -> Dict[str, Any]:
        """Analyze the timing of the claim"""
        
        suspicious = False
        context = []
        
        # Check if claim emerged during significant events
        # This is a simplified version - production would check against event database
        
        claim_lower = dossier.claim.lower()
        
        # Election timing
        if any(word in claim_lower for word in ['election', 'vote', 'candidate']):
            context.append("Claim relates to electoral politics")
            suspicious = True
        
        # Crisis timing
        if any(word in claim_lower for word in ['crisis', 'emergency', 'urgent', 'breaking']):
            context.append("Claim emerged during crisis or urgent situation")
            suspicious = True
        
        # Financial timing
        if any(word in claim_lower for word in ['stock', 'market', 'investment', 'crash']):
            context.append("Claim relates to financial markets")
            suspicious = True
        
        return {
            'suspicious': suspicious,
            'context': context
        }
    
    def _analyze_beneficiaries(self, claim: str, context: str) -> List[str]:
        """Cui bono? Who benefits if this claim is believed?"""
        
        beneficiaries = []
        claim_lower = claim.lower()
        
        # Political beneficiaries
        if any(word in claim_lower for word in ['democrat', 'republican', 'party', 'candidate']):
            beneficiaries.append("Political parties/candidates")
        
        # Commercial beneficiaries
        if any(word in claim_lower for word in ['product', 'buy', 'sale', 'discount', 'offer']):
            beneficiaries.append("Commercial entities/sellers")
        
        # Industry beneficiaries
        industries = {
            'pharmaceutical': ['drug', 'vaccine', 'medicine', 'pharmaceutical'],
            'energy': ['oil', 'gas', 'coal', 'energy'],
            'tech': ['technology', 'software', 'app', 'platform'],
            'financial': ['bank', 'investment', 'financial', 'fund']
        }
        
        for industry, keywords in industries.items():
            if any(keyword in claim_lower for keyword in keywords):
                beneficiaries.append(f"{industry.capitalize()} industry")
        
        # Ideological beneficiaries
        if any(word in claim_lower for word in ['liberal', 'conservative', 'progressive', 'traditional']):
            beneficiaries.append("Ideological movements")
        
        return beneficiaries if beneficiaries else ["Unclear beneficiaries"]
    
    def _identify_missing_information(self, dossier: InvestigationDossier) -> List[str]:
        """Identify what's conspicuously absent"""
        
        missing = []
        
        # Check for missing attribution
        if not any(marker in dossier.claim.lower() for marker in ['according to', 'said', 'reported', 'study']):
            missing.append("No clear attribution or source cited")
        
        # Check for missing methodology
        if any(word in dossier.claim.lower() for word in ['study', 'research', 'data']):
            if not any(method in dossier.claim.lower() for method in ['sample', 'methodology', 'participants']):
                missing.append("Study/research mentioned but no methodology details")
        
        # Check for missing dates
        if any(word in dossier.claim.lower() for word in ['happened', 'occurred', 'took place']):
            import re
            if not re.search(r'\b\d{4}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b', dossier.claim):
                missing.append("Event mentioned but no specific date provided")
        
        # Check for missing numbers
        if any(word in dossier.claim.lower() for word in ['increase', 'decrease', 'more', 'less', 'higher', 'lower']):
            import re
            if not re.search(r'\d+(?:\.\d+)?%?', dossier.claim):
                missing.append("Comparative claim but no specific numbers")
        
        # Check for missing context in evidence
        if len(dossier.evidence_log) < 2:
            missing.append("Insufficient independent evidence")
        
        return missing
    
    def _generate_hypotheses(self, dossier: InvestigationDossier, 
                            similar_claims: List[Dict], 
                            beneficiaries: List[str]) -> List[Hypothesis]:
        """Generate working hypotheses about the claim"""
        
        hypotheses = []
        
        # Hypothesis 1: Claim is accurate
        h1 = Hypothesis(
            description="The claim is substantially accurate as stated",
            confidence=0.5  # Neutral starting point
        )
        hypotheses.append(h1)
        
        # Hypothesis 2: Claim is misleading/lacks context
        if dossier.layer_findings.get('Gatekeeper', {}).get('red_flags'):
            h2 = Hypothesis(
                description="The claim is technically true but misleading due to missing context",
                confidence=0.6
            )
            hypotheses.append(h2)
        
        # Hypothesis 3: Claim is recycled misinformation
        if similar_claims:
            h3 = Hypothesis(
                description="The claim is a recycled version of previous misinformation",
                confidence=0.4
            )
            hypotheses.append(h3)
        
        # Hypothesis 4: Claim serves specific interests
        if beneficiaries and beneficiaries != ["Unclear beneficiaries"]:
            h4 = Hypothesis(
                description=f"The claim serves the interests of: {', '.join(beneficiaries)}",
                confidence=0.5
            )
            hypotheses.append(h4)
        
        return hypotheses
