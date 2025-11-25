"""
Layer 1: The Gatekeeper (Initial Assessment Agent)
The "Smell Test" - rapid triage and initial skepticism calibration.
"""

from typing import Dict, Any
import re
from ..core.base_agent import BaseAgent
from ..core.dossier import InvestigationDossier, InvestigationStrategy


class GatekeeperAgent(BaseAgent):
    """
    First line of defense. Performs rapid assessment to determine:
    1. Is this worth checking?
    2. How skeptical should we be?
    3. What investigation strategy should we use?
    """
    
    def __init__(self):
        super().__init__(
            name="Gatekeeper",
            description="Initial assessment and triage agent"
        )
        
        # Red flag patterns
        self.disinfo_patterns = [
            r'\b(shocking|unbelievable|they don\'t want you to know)\b',
            r'\b(secret|hidden|cover-up|conspiracy)\b',
            r'\b(miracle|cure|guaranteed)\b',
            r'\b(always|never|everyone|no one)\b',  # Absolutist language
        ]
        
        # Credibility signals
        self.credibility_signals = [
            r'\b(study|research|according to|data shows)\b',
            r'\b(professor|dr\.|expert|scientist)\b',
            r'\b(university|institute|journal)\b',
        ]
    
    async def analyze(self, dossier: InvestigationDossier) -> Dict[str, Any]:
        """Perform initial assessment"""
        
        claim = dossier.claim.lower()
        
        # 1. Credibility Signals Scanner
        credibility_score = self._scan_credibility_signals(claim, dossier.source)
        
        # 2. Stakes Evaluator
        impact_score = self._evaluate_stakes(claim)
        
        # 3. Pattern Matcher
        disinfo_risk = self._match_disinfo_patterns(claim)
        
        # Calculate priority and skepticism
        priority = (impact_score + disinfo_risk) / 2
        skepticism = disinfo_risk * (1 - credibility_score)
        
        # Determine investigation strategy
        strategy = self._determine_strategy(claim, dossier.source)
        
        # Update dossier
        dossier.priority_score = priority
        dossier.skepticism_level = skepticism
        dossier.strategy = strategy
        
        findings = {
            "credibility_score": credibility_score,
            "impact_score": impact_score,
            "disinfo_risk": disinfo_risk,
            "priority": priority,
            "skepticism": skepticism,
            "strategy": strategy.value,
            "red_flags": self._identify_red_flags(claim),
            "verifiable_elements": self._identify_verifiable_elements(claim)
        }
        
        self.log_finding(
            f"Priority: {priority:.2f}, Skepticism: {skepticism:.2f}, Strategy: {strategy.value}"
        )
        
        return findings
    
    def _scan_credibility_signals(self, claim: str, source: str) -> float:
        """Scan for credibility signals in claim and source"""
        score = 0.5  # Neutral baseline
        
        # Check for credibility markers
        credibility_matches = sum(
            1 for pattern in self.credibility_signals 
            if re.search(pattern, claim, re.IGNORECASE)
        )
        
        # Boost score for credibility signals
        score += min(credibility_matches * 0.1, 0.3)
        
        # Check for specificity (dates, numbers, names)
        has_dates = bool(re.search(r'\b\d{4}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b', claim))
        has_numbers = bool(re.search(r'\b\d+(?:\.\d+)?%?\b', claim))
        has_names = bool(re.search(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', claim))
        
        specificity_score = sum([has_dates, has_numbers, has_names]) / 3
        score += specificity_score * 0.2
        
        return min(score, 1.0)
    
    def _evaluate_stakes(self, claim: str) -> float:
        """Evaluate potential impact if claim is false"""
        high_stakes_keywords = [
            'health', 'medical', 'vaccine', 'cure', 'deadly',
            'election', 'vote', 'fraud', 'illegal',
            'war', 'attack', 'threat', 'danger',
            'financial', 'stock', 'investment', 'crash'
        ]
        
        matches = sum(
            1 for keyword in high_stakes_keywords 
            if keyword in claim.lower()
        )
        
        return min(matches * 0.25, 1.0)
    
    def _match_disinfo_patterns(self, claim: str) -> float:
        """Check for common disinformation patterns"""
        matches = sum(
            1 for pattern in self.disinfo_patterns 
            if re.search(pattern, claim, re.IGNORECASE)
        )
        
        # More matches = higher risk
        return min(matches * 0.3, 1.0)
    
    def _determine_strategy(self, claim: str, source: str) -> InvestigationStrategy:
        """Determine which investigation pathway to use"""
        claim_lower = claim.lower()
        
        # Check for time-sensitive indicators
        breaking_indicators = ['breaking', 'just in', 'developing', 'alert']
        if any(ind in claim_lower for ind in breaking_indicators):
            return InvestigationStrategy.BREAKING_NEWS
        
        # Check for scientific claims
        science_indicators = ['study', 'research', 'scientist', 'data', 'experiment']
        if any(ind in claim_lower for ind in science_indicators):
            return InvestigationStrategy.SCIENTIFIC_CLAIM
        
        # Check for political claims
        political_indicators = ['election', 'vote', 'government', 'president', 'congress']
        if any(ind in claim_lower for ind in political_indicators):
            return InvestigationStrategy.POLITICAL_CLAIM
        
        # Check for statistical claims
        if re.search(r'\d+(?:\.\d+)?%', claim):
            return InvestigationStrategy.STATISTICAL_CLAIM
        
        # Check for historical claims
        if re.search(r'\b(19|20)\d{2}\b', claim):
            return InvestigationStrategy.HISTORICAL_CLAIM
        
        return InvestigationStrategy.GENERAL
    
    def _identify_red_flags(self, claim: str) -> list:
        """Identify specific red flags in the claim"""
        flags = []
        
        if re.search(r'\b(shocking|unbelievable)\b', claim, re.IGNORECASE):
            flags.append("Sensationalist language")
        
        if re.search(r'\b(always|never|everyone|no one)\b', claim, re.IGNORECASE):
            flags.append("Absolutist claims")
        
        if re.search(r'\b(they|them)\b.*\b(don\'t want|hiding|secret)\b', claim, re.IGNORECASE):
            flags.append("Conspiratorial framing")
        
        if not re.search(r'\b(according to|study|research|data)\b', claim, re.IGNORECASE):
            flags.append("No attribution to sources")
        
        return flags
    
    def _identify_verifiable_elements(self, claim: str) -> list:
        """Identify elements that can be verified"""
        elements = []
        
        # Dates
        dates = re.findall(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', claim, re.IGNORECASE)
        if dates:
            elements.extend([f"Date: {d}" for d in dates])
        
        # Numbers/Statistics
        numbers = re.findall(r'\b\d+(?:\.\d+)?%?\b', claim)
        if numbers:
            elements.extend([f"Number: {n}" for n in numbers[:3]])  # Limit to first 3
        
        # Proper names
        names = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', claim)
        if names:
            elements.extend([f"Name: {n}" for n in names[:3]])
        
        # Locations
        # Simple heuristic: capitalized words that might be places
        potential_locations = re.findall(r'\b[A-Z][a-z]+(?:, [A-Z][a-z]+)?\b', claim)
        if potential_locations:
            elements.extend([f"Location: {loc}" for loc in potential_locations[:2]])
        
        return elements
