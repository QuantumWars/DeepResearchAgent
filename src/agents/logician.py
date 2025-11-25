"""
Layer 6: The Logician (Logical Consistency Auditor)
Stress-tests the narrative for internal coherence and plausibility.
"""

from typing import Dict, Any, List
import re
from ..core.base_agent import BaseAgent
from ..core.dossier import InvestigationDossier


class LogicianAgent(BaseAgent):
    """
    Checks for logical consistency, timeline feasibility, and statistical plausibility.
    The fact-checker's internal BS detector.
    """
    
    def __init__(self):
        super().__init__(
            name="Logician",
            description="Logical consistency and plausibility checker"
        )
    
    async def analyze(self, dossier: InvestigationDossier) -> Dict[str, Any]:
        """Audit the claim for logical consistency"""
        
        # Temporal logic check
        temporal_check = self._check_temporal_logic(dossier.claim)
        
        # Quantitative logic check
        quantitative_check = self._check_quantitative_logic(dossier.claim)
        
        # Narrative logic check
        narrative_check = self._check_narrative_logic(dossier)
        
        # Calculate overall coherence score
        coherence_score = self._calculate_coherence(temporal_check, quantitative_check, narrative_check)
        
        # Update confidence matrix
        dossier.confidence_matrix.logical_coherence = coherence_score
        
        # Identify logical fallacies
        fallacies = self._identify_fallacies(dossier.claim)
        
        findings = {
            "temporal_logic": temporal_check,
            "quantitative_logic": quantitative_check,
            "narrative_logic": narrative_check,
            "coherence_score": coherence_score,
            "logical_fallacies": fallacies,
            "passes_logic_test": coherence_score >= 0.6 and len(fallacies) == 0
        }
        
        self.log_finding(
            f"Coherence score: {coherence_score:.2f}, "
            f"fallacies found: {len(fallacies)}"
        )
        
        # Add logical issues to red flags
        if coherence_score < 0.5:
            dossier.red_flags.append("Low logical coherence score")
        
        for fallacy in fallacies:
            dossier.red_flags.append(f"Logical fallacy: {fallacy}")
        
        return findings
    
    def _check_temporal_logic(self, claim: str) -> Dict[str, Any]:
        """Check timeline feasibility and causal sequences"""
        
        issues = []
        plausible = True
        
        # Extract dates and times
        dates = re.findall(r'\b\d{4}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b', claim)
        
        if len(dates) >= 2:
            # Check if dates are in logical order
            # Simplified - in production, parse and compare actual dates
            pass
        
        # Check for impossible timeframes
        impossible_timeframes = [
            (r'(\d+)\s*years?\s+ago.*yesterday', "Contradictory timeframes"),
            (r'future.*past', "Temporal contradiction"),
            (r'before.*after.*before', "Circular timeline")
        ]
        
        for pattern, issue in impossible_timeframes:
            if re.search(pattern, claim, re.IGNORECASE):
                issues.append(issue)
                plausible = False
        
        # Check for causal impossibilities
        if 'because' in claim.lower() or 'caused' in claim.lower():
            # In production: check if cause precedes effect
            pass
        
        return {
            "plausible": plausible,
            "issues": issues,
            "dates_found": len(dates)
        }
    
    def _check_quantitative_logic(self, claim: str) -> Dict[str, Any]:
        """Check if numbers and statistics make sense"""
        
        issues = []
        plausible = True
        
        # Extract numbers
        numbers = re.findall(r'\b\d+(?:\.\d+)?', claim)
        percentages = re.findall(r'\b\d+(?:\.\d+)?%', claim)
        
        # Check for impossible percentages
        for pct in percentages:
            value = float(pct.replace('%', ''))
            if value > 100:
                issues.append(f"Impossible percentage: {pct}")
                plausible = False
            elif value < 0:
                issues.append(f"Negative percentage: {pct}")
                plausible = False
        
        # Check for scale inconsistencies
        if len(numbers) >= 2:
            nums = [float(n) for n in numbers if self._is_number(n)]
            if nums:
                max_num = max(nums)
                min_num = min(nums)
                
                # Check for unrealistic scales
                if max_num > 0 and min_num > 0:
                    ratio = max_num / min_num
                    if ratio > 1000000:  # More than million-fold difference
                        issues.append("Extreme scale difference in numbers")
        
        # Check for statistical red flags
        stat_red_flags = [
            (r'100%\s+of', "Absolute claim (100%)"),
            (r'0%\s+of', "Absolute claim (0%)"),
            (r'exactly\s+\d+', "Suspiciously exact number")
        ]
        
        for pattern, flag in stat_red_flags:
            if re.search(pattern, claim, re.IGNORECASE):
                issues.append(flag)
        
        return {
            "plausible": plausible,
            "issues": issues,
            "numbers_found": len(numbers),
            "percentages_found": len(percentages)
        }
    
    def _check_narrative_logic(self, dossier: InvestigationDossier) -> Dict[str, Any]:
        """Check if the narrative makes sense"""
        
        issues = []
        coherent = True
        
        claim_lower = dossier.claim.lower()
        
        # Check for motivation consistency
        if 'because' in claim_lower or 'in order to' in claim_lower:
            # Check if stated motivation makes sense
            # Simplified heuristic
            if any(word in claim_lower for word in ['secretly', 'hidden', 'conspiracy']):
                issues.append("Conspiratorial motivation without evidence")
        
        # Check for action-goal alignment
        # If claim states someone did X to achieve Y, does X logically lead to Y?
        
        # Check evidence against hypotheses
        if dossier.hypotheses:
            top_hypothesis = dossier.get_top_hypothesis()
            if top_hypothesis:
                # Check if evidence supports the hypothesis
                support_ratio = len(top_hypothesis.supporting_evidence) / max(
                    len(top_hypothesis.supporting_evidence) + len(top_hypothesis.contradicting_evidence), 
                    1
                )
                
                if support_ratio < 0.3:
                    issues.append("Top hypothesis lacks supporting evidence")
                    coherent = False
        
        return {
            "coherent": coherent,
            "issues": issues
        }
    
    def _calculate_coherence(self, temporal: Dict, quantitative: Dict, narrative: Dict) -> float:
        """Calculate overall logical coherence score"""
        
        scores = []
        
        # Temporal coherence
        scores.append(1.0 if temporal['plausible'] else 0.3)
        
        # Quantitative coherence
        scores.append(1.0 if quantitative['plausible'] else 0.3)
        
        # Narrative coherence
        scores.append(1.0 if narrative['coherent'] else 0.4)
        
        # Average with penalty for issues
        base_score = sum(scores) / len(scores)
        
        total_issues = len(temporal['issues']) + len(quantitative['issues']) + len(narrative['issues'])
        penalty = min(total_issues * 0.1, 0.4)
        
        return max(base_score - penalty, 0.0)
    
    def _identify_fallacies(self, claim: str) -> List[str]:
        """Identify common logical fallacies"""
        
        fallacies = []
        claim_lower = claim.lower()
        
        # Ad hominem
        if re.search(r'\b(stupid|idiot|fool|moron)\b', claim_lower):
            fallacies.append("Ad hominem attack")
        
        # False dichotomy
        if re.search(r'\b(either|or)\b.*\b(either|or)\b', claim_lower):
            fallacies.append("Possible false dichotomy")
        
        # Appeal to authority (without credentials)
        if re.search(r'experts? say', claim_lower) and not re.search(r'dr\.|professor|phd', claim_lower):
            fallacies.append("Vague appeal to authority")
        
        # Slippery slope
        if re.search(r'if.*then.*then.*then', claim_lower):
            fallacies.append("Possible slippery slope")
        
        # Hasty generalization
        if re.search(r'\b(all|every|always|never)\b', claim_lower):
            fallacies.append("Possible hasty generalization (absolutist language)")
        
        # Circular reasoning
        if re.search(r'because.*because', claim_lower):
            fallacies.append("Possible circular reasoning")
        
        return fallacies
    
    def _is_number(self, s: str) -> bool:
        """Check if string is a valid number"""
        try:
            float(s)
            return True
        except ValueError:
            return False
