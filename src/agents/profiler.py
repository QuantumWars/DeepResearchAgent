"""
Layer 2: The Profiler (Source Evaluation Network)
Deep background check on sources - who are they and can we trust them?
"""

from typing import Dict, Any, List
from ..core.base_agent import BaseAgent
from ..core.dossier import InvestigationDossier, SourceProfile
from ..core.tools import ToolKit


class ProfilerAgent(BaseAgent):
    """
    Investigates the credibility, bias, and track record of sources.
    The journalist's Rolodex and institutional memory.
    """
    
    def __init__(self, toolkit: ToolKit):
        super().__init__(
            name="Profiler",
            description="Source credibility and bias evaluation agent"
        )
        self.toolkit = toolkit
        
        # Known bias indicators
        self.bias_keywords = {
            'left': ['progressive', 'liberal', 'left-wing', 'socialist'],
            'right': ['conservative', 'right-wing', 'traditional', 'libertarian'],
            'corporate': ['sponsored', 'partner', 'affiliate', 'advertisement'],
            'activist': ['advocacy', 'campaign', 'movement', 'grassroots']
        }
    
    async def analyze(self, dossier: InvestigationDossier) -> Dict[str, Any]:
        """Evaluate all sources mentioned in the claim"""
        
        # Extract sources from claim and existing evidence
        sources_to_profile = self._extract_sources(dossier)
        
        profiles = []
        for source_name in sources_to_profile:
            profile = await self._profile_source(source_name, dossier)
            dossier.add_source_profile(profile)
            profiles.append(profile)
        
        # Aggregate analysis
        avg_authority = sum(p.authority_score for p in profiles) / len(profiles) if profiles else 0.5
        total_conflicts = sum(len(p.conflicts_of_interest) for p in profiles)
        
        findings = {
            "sources_profiled": len(profiles),
            "average_authority": avg_authority,
            "total_conflicts_of_interest": total_conflicts,
            "bias_distribution": self._analyze_bias_distribution(profiles),
            "red_flags": self._identify_source_red_flags(profiles)
        }
        
        self.log_finding(
            f"Profiled {len(profiles)} sources, avg authority: {avg_authority:.2f}"
        )
        
        return findings
    
    def _extract_sources(self, dossier: InvestigationDossier) -> List[str]:
        """Extract source names from claim and evidence"""
        sources = set()
        
        # Primary source
        if dossier.source:
            sources.add(dossier.source)
        
        # Sources from evidence
        for evidence in dossier.evidence_log:
            sources.add(evidence.source)
        
        return list(sources)
    
    async def _profile_source(self, source_name: str, dossier: InvestigationDossier) -> SourceProfile:
        """Create detailed profile of a source"""
        
        # Authority assessment
        authority_score = self._assess_authority(source_name, dossier)
        
        # Bias detection
        bias_indicators = self._detect_bias(source_name, dossier.claim)
        
        # Conflicts of interest
        conflicts = self._identify_conflicts(source_name, dossier.claim)
        
        # Expertise domains
        expertise = self._identify_expertise(source_name)
        
        # Track record (placeholder - would query database in production)
        track_record = self._assess_track_record(source_name)
        
        profile = SourceProfile(
            name=source_name,
            authority_score=authority_score,
            bias_indicators=bias_indicators,
            track_record=track_record,
            conflicts_of_interest=conflicts,
            expertise_domains=expertise
        )
        
        return profile
    
    def _assess_authority(self, source_name: str, dossier: InvestigationDossier) -> float:
        """Assess the authority/credibility of a source"""
        score = 0.5  # Neutral baseline
        
        source_lower = source_name.lower()
        
        # Institutional sources
        institutional_markers = [
            'university', 'institute', 'journal', 'department',
            'agency', 'bureau', 'center', 'foundation'
        ]
        if any(marker in source_lower for marker in institutional_markers):
            score += 0.2
        
        # Academic credentials
        if any(title in source_lower for title in ['dr.', 'professor', 'phd']):
            score += 0.15
        
        # Government sources
        if any(gov in source_lower for gov in ['.gov', 'government', 'official']):
            score += 0.15
        
        # Peer-reviewed
        if 'peer-reviewed' in source_lower or 'peer reviewed' in source_lower:
            score += 0.2
        
        # Anonymous or vague sources (penalty)
        if any(vague in source_lower for vague in ['anonymous', 'unnamed', 'sources say']):
            score -= 0.3
        
        return max(0.0, min(score, 1.0))
    
    def _detect_bias(self, source_name: str, claim: str) -> List[str]:
        """Detect potential biases in the source"""
        biases = []
        
        source_lower = source_name.lower()
        claim_lower = claim.lower()
        
        # Check for ideological bias
        for bias_type, keywords in self.bias_keywords.items():
            if any(keyword in source_lower or keyword in claim_lower for keyword in keywords):
                biases.append(f"Potential {bias_type} bias")
        
        # Financial bias
        financial_indicators = ['sponsored', 'paid', 'advertisement', 'partner']
        if any(ind in source_lower for ind in financial_indicators):
            biases.append("Financial/commercial interest")
        
        return biases
    
    def _identify_conflicts(self, source_name: str, claim: str) -> List[str]:
        """Identify potential conflicts of interest"""
        conflicts = []
        
        source_lower = source_name.lower()
        claim_lower = claim.lower()
        
        # Industry conflicts
        if 'pharmaceutical' in source_lower and any(word in claim_lower for word in ['drug', 'vaccine', 'medicine']):
            conflicts.append("Pharmaceutical industry connection to medical claim")
        
        if 'oil' in source_lower or 'energy' in source_lower:
            if any(word in claim_lower for word in ['climate', 'environment', 'emissions']):
                conflicts.append("Energy industry connection to climate claim")
        
        # Political conflicts
        if any(pol in source_lower for pol in ['campaign', 'party', 'political']):
            conflicts.append("Political affiliation")
        
        return conflicts
    
    def _identify_expertise(self, source_name: str) -> List[str]:
        """Identify areas of expertise"""
        expertise = []
        
        source_lower = source_name.lower()
        
        # Domain expertise markers
        domains = {
            'medical': ['medical', 'health', 'doctor', 'physician', 'hospital'],
            'scientific': ['scientist', 'researcher', 'laboratory', 'research'],
            'economic': ['economist', 'economic', 'finance', 'financial'],
            'legal': ['lawyer', 'attorney', 'legal', 'court', 'judge'],
            'technical': ['engineer', 'technical', 'technology', 'computer']
        }
        
        for domain, keywords in domains.items():
            if any(keyword in source_lower for keyword in keywords):
                expertise.append(domain)
        
        return expertise
    
    def _assess_track_record(self, source_name: str) -> str:
        """Assess historical track record (placeholder)"""
        # In production: query fact-check database for previous claims by this source
        return "No prior record available"
    
    def _analyze_bias_distribution(self, profiles: List[SourceProfile]) -> Dict[str, int]:
        """Analyze the distribution of biases across sources"""
        bias_counts = {}
        
        for profile in profiles:
            for bias in profile.bias_indicators:
                bias_counts[bias] = bias_counts.get(bias, 0) + 1
        
        return bias_counts
    
    def _identify_source_red_flags(self, profiles: List[SourceProfile]) -> List[str]:
        """Identify red flags across all sources"""
        flags = []
        
        # All sources have low authority
        if profiles and all(p.authority_score < 0.4 for p in profiles):
            flags.append("All sources have low credibility scores")
        
        # All sources share same bias
        all_biases = [bias for p in profiles for bias in p.bias_indicators]
        if all_biases and len(set(all_biases)) == 1:
            flags.append(f"All sources share same bias: {all_biases[0]}")
        
        # Multiple conflicts of interest
        total_conflicts = sum(len(p.conflicts_of_interest) for p in profiles)
        if total_conflicts > 2:
            flags.append(f"Multiple conflicts of interest detected ({total_conflicts})")
        
        # No expertise in relevant domain
        if profiles and not any(p.expertise_domains for p in profiles):
            flags.append("No sources have identifiable expertise")
        
        return flags
