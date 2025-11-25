"""
Layer 3: The Investigator (Cross-Verification Engine)
The "feet on the street" - finding independent corroboration through triangulation.
"""

from typing import Dict, Any, List
from ..core.base_agent import BaseAgent
from ..core.dossier import InvestigationDossier, Evidence, EvidenceTier
from ..core.tools import ToolKit, SearchResult


class InvestigatorAgent(BaseAgent):
    """
    Seeks independent verification through diverse sources.
    Detects circular reporting and finds genuine corroboration.
    """
    
    def __init__(self, toolkit: ToolKit):
        super().__init__(
            name="Investigator",
            description="Cross-verification and triangulation agent"
        )
        self.toolkit = toolkit
    
    async def analyze(self, dossier: InvestigationDossier) -> Dict[str, Any]:
        """Find independent sources to verify or contradict the claim"""
        
        # Search for corroborating evidence
        search_results = await self._search_for_evidence(dossier.claim)
        
        # Analyze diversity of sources
        diversity_score = self._assess_source_diversity(search_results)
        
        # Detect circular reporting
        circular_reporting = self._detect_circular_reporting(search_results)
        
        # Find corroboration and contradictions
        corroboration = self._analyze_corroboration(search_results, dossier.claim)
        contradictions = self._find_contradictions(search_results, dossier.claim)
        
        # Add evidence to dossier
        for result in search_results[:5]:  # Top 5 results
            evidence = Evidence(
                content=result.snippet,
                source=result.source,
                tier=self._determine_evidence_tier(result),
                reliability_score=result.relevance_score,
                url=result.url
            )
            dossier.add_evidence(evidence)
        
        findings = {
            "sources_found": len(search_results),
            "diversity_score": diversity_score,
            "circular_reporting_detected": circular_reporting,
            "corroboration_strength": corroboration,
            "contradictions_found": len(contradictions),
            "contradictions": contradictions,
            "independent_verification": diversity_score > 0.6 and not circular_reporting
        }
        
        self.log_finding(
            f"Found {len(search_results)} sources, diversity: {diversity_score:.2f}, "
            f"corroboration: {corroboration:.2f}"
        )
        
        if circular_reporting:
            dossier.red_flags.append("Circular reporting detected - sources citing each other")
        
        return findings
    
    async def _search_for_evidence(self, claim: str) -> List[SearchResult]:
        """Search for evidence related to the claim"""
        
        # Extract key terms for search
        search_query = self._extract_search_terms(claim)
        
        # Perform web search
        results = await self.toolkit.web_search(search_query, max_results=10)
        
        # Also search news specifically
        news_results = await self.toolkit.search.news_search(search_query, max_results=5)
        
        # Combine results
        all_results = results + news_results
        
        return all_results
    
    def _extract_search_terms(self, claim: str) -> str:
        """Extract key terms from claim for searching"""
        # Simple implementation - in production, use NLP for better extraction
        # Remove common words and keep important terms
        
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        words = claim.lower().split()
        key_terms = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Take first 5-7 key terms
        return ' '.join(key_terms[:7])
    
    def _assess_source_diversity(self, results: List[SearchResult]) -> float:
        """Assess geographic and ideological diversity of sources"""
        if not results:
            return 0.0
        
        # Extract unique domains
        domains = set()
        for result in results:
            # Extract domain from URL
            if result.url:
                domain = result.url.split('/')[2] if '/' in result.url else result.url
                domains.add(domain)
        
        # More unique domains = higher diversity
        diversity = len(domains) / len(results)
        
        return min(diversity, 1.0)
    
    def _detect_circular_reporting(self, results: List[SearchResult]) -> bool:
        """Detect if sources are citing each other rather than independent verification"""
        
        # Check if multiple results have very similar snippets
        # This suggests they're copying from the same source
        
        if len(results) < 2:
            return False
        
        # Simple heuristic: check for exact phrase repetition
        snippets = [r.snippet.lower() for r in results]
        
        for i, snippet1 in enumerate(snippets):
            for snippet2 in snippets[i+1:]:
                # Check for significant overlap
                words1 = set(snippet1.split())
                words2 = set(snippet2.split())
                
                if len(words1) > 0 and len(words2) > 0:
                    overlap = len(words1 & words2) / min(len(words1), len(words2))
                    
                    # If >70% overlap, likely circular
                    if overlap > 0.7:
                        return True
        
        return False
    
    def _analyze_corroboration(self, results: List[SearchResult], claim: str) -> float:
        """Analyze strength of corroboration"""
        if not results:
            return 0.0
        
        # Count how many results support the claim
        # Simple heuristic: check for key terms from claim in results
        
        claim_terms = set(claim.lower().split())
        supporting_count = 0
        
        for result in results:
            result_terms = set(result.snippet.lower().split())
            overlap = len(claim_terms & result_terms) / len(claim_terms) if claim_terms else 0
            
            if overlap > 0.3:  # At least 30% term overlap
                supporting_count += 1
        
        corroboration_strength = supporting_count / len(results)
        return corroboration_strength
    
    def _find_contradictions(self, results: List[SearchResult], claim: str) -> List[str]:
        """Find contradictory information in search results"""
        contradictions = []
        
        # Look for contradiction markers
        contradiction_markers = [
            'however', 'but', 'false', 'incorrect', 'debunked',
            'misleading', 'not true', 'actually', 'contrary to'
        ]
        
        for result in results:
            snippet_lower = result.snippet.lower()
            
            for marker in contradiction_markers:
                if marker in snippet_lower:
                    contradictions.append(f"{result.source}: {result.snippet[:100]}...")
                    break
        
        return contradictions
    
    def _determine_evidence_tier(self, result: SearchResult) -> EvidenceTier:
        """Determine the tier of evidence based on source"""
        
        source_lower = result.source.lower()
        url_lower = result.url.lower() if result.url else ""
        
        # Tier 1: Primary sources
        if any(marker in url_lower for marker in ['.gov', 'official', 'original']):
            return EvidenceTier.TIER_1_PRIMARY
        
        # Tier 2: Expert analysis
        if any(marker in source_lower for marker in ['expert', 'professor', 'researcher', 'journal']):
            return EvidenceTier.TIER_2_EXPERT
        
        # Tier 3: Credible reporting
        if any(marker in source_lower for marker in ['news', 'times', 'post', 'reuters', 'ap']):
            return EvidenceTier.TIER_3_CREDIBLE
        
        # Tier 4: Secondary analysis
        if any(marker in source_lower for marker in ['blog', 'opinion', 'commentary']):
            return EvidenceTier.TIER_4_SECONDARY
        
        # Default to Tier 5
        return EvidenceTier.TIER_5_UNVERIFIED
