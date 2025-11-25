"""
Orchestrator: The Newsroom Manager
Coordinates all agents in parallel/iterative loops with dynamic adaptation.
"""

import asyncio
from typing import List, Dict, Any, Optional
import logging
from .dossier import InvestigationDossier, InvestigationStrategy
from .base_agent import BaseAgent
from .tools import ToolKit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Orchestrator")


class InvestigationOrchestrator:
    """
    Manages the fact-checking investigation workflow.
    Coordinates agents in parallel and handles dynamic adaptation.
    """
    
    def __init__(self, agents: Dict[str, BaseAgent], toolkit: ToolKit):
        """
        Initialize orchestrator with agents.
        
        Args:
            agents: Dictionary mapping agent names to agent instances
            toolkit: Shared toolkit for agents
        """
        self.agents = agents
        self.toolkit = toolkit
        self.logger = logger
    
    async def investigate(self, 
                         claim: str, 
                         source: str = "Unknown",
                         context: str = "") -> InvestigationDossier:
        """
        Run a complete fact-checking investigation.
        
        Args:
            claim: The claim to investigate
            source: Source of the claim
            context: Additional context
            
        Returns:
            Completed investigation dossier
        """
        self.logger.info("=" * 80)
        self.logger.info("🔍 STARTING INVESTIGATION")
        self.logger.info("=" * 80)
        self.logger.info(f"Claim: {claim}")
        self.logger.info(f"Source: {source}")
        
        # Initialize dossier
        dossier = InvestigationDossier(
            claim=claim,
            source=source,
            context=context
        )
        
        # Phase 1: Initial Assessment (Sequential - sets strategy)
        self.logger.info("\n📋 PHASE 1: Initial Assessment")
        dossier = await self._run_gatekeeper(dossier)
        
        # Phase 2: Core Investigation (Parallel)
        self.logger.info(f"\n🔬 PHASE 2: Core Investigation (Strategy: {dossier.strategy.value})")
        dossier = await self._run_core_investigation(dossier)
        
        # Phase 3: Analysis & Synthesis (Parallel)
        self.logger.info("\n⚖️  PHASE 3: Analysis & Synthesis")
        dossier = await self._run_analysis_phase(dossier)
        
        # Phase 4: Meta-Analysis & Final Verdict (Sequential)
        self.logger.info("\n🎯 PHASE 4: Meta-Analysis & Final Verdict")
        dossier = await self._run_final_phase(dossier)
        
        # Check if we need another iteration
        if self._needs_deeper_investigation(dossier):
            self.logger.info("\n🔄 TRIGGERING DEEPER INVESTIGATION")
            dossier = await self._run_deeper_investigation(dossier)
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info("✅ INVESTIGATION COMPLETE")
        self.logger.info("=" * 80)
        
        return dossier
    
    async def _run_gatekeeper(self, dossier: InvestigationDossier) -> InvestigationDossier:
        """Run the Gatekeeper agent"""
        if 'Gatekeeper' in self.agents:
            dossier = await self.agents['Gatekeeper'].execute(dossier)
        return dossier
    
    async def _run_core_investigation(self, dossier: InvestigationDossier) -> InvestigationDossier:
        """
        Run core investigation agents in parallel.
        Profiler, Investigator, and Historian work simultaneously.
        """
        tasks = []
        
        # These agents can run in parallel
        parallel_agents = ['Profiler', 'Investigator', 'Historian']
        
        for agent_name in parallel_agents:
            if agent_name in self.agents:
                tasks.append(self.agents[agent_name].execute(dossier))
        
        # Run in parallel and wait for all to complete
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All agents modify the same dossier, so we just take the last result
            # (they all update the same object)
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"Agent failed: {result}")
                else:
                    dossier = result
        
        return dossier
    
    async def _run_analysis_phase(self, dossier: InvestigationDossier) -> InvestigationDossier:
        """
        Run analysis agents in parallel.
        Judge and Logician analyze the collected evidence.
        """
        tasks = []
        
        parallel_agents = ['Judge', 'Logician']
        
        for agent_name in parallel_agents:
            if agent_name in self.agents:
                tasks.append(self.agents[agent_name].execute(dossier))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"Agent failed: {result}")
                else:
                    dossier = result
        
        return dossier
    
    async def _run_final_phase(self, dossier: InvestigationDossier) -> InvestigationDossier:
        """
        Run final phase sequentially.
        Watchdog checks for issues, then Editor makes final call.
        """
        # Watchdog first
        if 'Watchdog' in self.agents:
            dossier = await self.agents['Watchdog'].execute(dossier)
        
        # Editor last
        if 'Editor' in self.agents:
            dossier = await self.agents['Editor'].execute(dossier)
        
        return dossier
    
    def _needs_deeper_investigation(self, dossier: InvestigationDossier) -> bool:
        """
        Determine if we need another round of investigation.
        Feedback loop trigger.
        """
        # Low confidence triggers deeper investigation
        if dossier.confidence_matrix.overall_confidence < 0.4:
            return True
        
        # High-stakes claims with moderate confidence
        if dossier.priority_score > 0.7 and dossier.confidence_matrix.overall_confidence < 0.7:
            return True
        
        # Contradictions found
        investigator_findings = dossier.layer_findings.get('Investigator', {})
        if investigator_findings.get('contradictions_found', 0) > 2:
            return True
        
        # High information warfare risk
        watchdog_findings = dossier.layer_findings.get('Watchdog', {})
        infowar_risk = watchdog_findings.get('infowar_signatures', {}).get('risk_score', 0)
        if infowar_risk > 0.6:
            return True
        
        return False
    
    async def _run_deeper_investigation(self, dossier: InvestigationDossier) -> InvestigationDossier:
        """
        Run a deeper investigation round.
        Focus on areas that need more work.
        """
        # Identify weak areas
        weak_areas = self._identify_weak_areas(dossier)
        
        self.logger.info(f"Focusing on: {', '.join(weak_areas)}")
        
        # Re-run specific agents based on weak areas
        tasks = []
        
        for area in weak_areas:
            if area in self.agents:
                tasks.append(self.agents[area].execute(dossier))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if not isinstance(result, Exception):
                    dossier = result
        
        # Re-run final phase
        dossier = await self._run_final_phase(dossier)
        
        return dossier
    
    def _identify_weak_areas(self, dossier: InvestigationDossier) -> List[str]:
        """Identify which agents should run again"""
        weak_areas = []
        
        # Low source quality -> re-run Profiler and Investigator
        if dossier.confidence_matrix.source_quality < 0.5:
            weak_areas.extend(['Profiler', 'Investigator'])
        
        # Low evidence quantity -> re-run Investigator
        if dossier.confidence_matrix.evidence_quantity < 0.5:
            weak_areas.append('Investigator')
        
        # Low logical coherence -> re-run Logician
        if dossier.confidence_matrix.logical_coherence < 0.5:
            weak_areas.append('Logician')
        
        # Missing context -> re-run Historian
        if dossier.confidence_matrix.context_clarity < 0.5:
            weak_areas.append('Historian')
        
        return list(set(weak_areas))  # Remove duplicates
    
    def apply_strategy_adaptation(self, dossier: InvestigationDossier) -> Dict[str, Any]:
        """
        Apply strategy-specific adaptations based on claim type.
        This implements the "Dynamic Adaptation Rules" from the architecture.
        """
        strategy = dossier.strategy
        adaptations = {}
        
        if strategy == InvestigationStrategy.BREAKING_NEWS:
            adaptations = {
                'timeline': 'compressed',
                'source_preference': 'institutional',
                'uncertainty_flagging': 'prominent',
                'priority': 'high'
            }
            self.logger.info("📰 Applying BREAKING NEWS strategy")
        
        elif strategy == InvestigationStrategy.HISTORICAL_CLAIM:
            adaptations = {
                'archive_search': 'deep',
                'academic_sources': 'emphasized',
                'context_analysis': 'extensive',
                'timeline': 'extended'
            }
            self.logger.info("📚 Applying HISTORICAL CLAIM strategy")
        
        elif strategy == InvestigationStrategy.SCIENTIFIC_CLAIM:
            adaptations = {
                'methodology_scrutiny': 'high',
                'peer_review': 'essential',
                'expert_consultation': 'required',
                'data_verification': 'mandatory'
            }
            self.logger.info("🔬 Applying SCIENTIFIC CLAIM strategy")
        
        elif strategy == InvestigationStrategy.POLITICAL_CLAIM:
            adaptations = {
                'bias_vigilance': 'hyper',
                'opposing_perspectives': 'required',
                'motivation_analysis': 'critical',
                'source_diversity': 'mandatory'
            }
            self.logger.info("🏛️  Applying POLITICAL CLAIM strategy")
        
        elif strategy == InvestigationStrategy.STATISTICAL_CLAIM:
            adaptations = {
                'data_source_verification': 'required',
                'methodology_examination': 'detailed',
                'reproducibility_check': 'important',
                'expert_review': 'recommended'
            }
            self.logger.info("📊 Applying STATISTICAL CLAIM strategy")
        
        return adaptations
    
    def generate_report(self, dossier: InvestigationDossier) -> str:
        """Generate a comprehensive investigation report"""
        
        report = []
        report.append("=" * 80)
        report.append("FACT-CHECK INVESTIGATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Executive Summary (from Editor)
        editor_findings = dossier.layer_findings.get('Editor', {})
        if editor_findings.get('summary'):
            report.append(editor_findings['summary'])
            report.append("")
        
        # Evidence Summary
        report.append("EVIDENCE SUMMARY")
        report.append("-" * 80)
        report.append(f"Total Evidence: {len(dossier.evidence_log)}")
        report.append(f"Unique Sources: {len(set(e.source for e in dossier.evidence_log))}")
        report.append(f"Source Profiles: {len(dossier.source_profiles)}")
        report.append("")
        
        # Confidence Breakdown
        report.append("CONFIDENCE BREAKDOWN")
        report.append("-" * 80)
        cm = dossier.confidence_matrix
        report.append(f"Overall Confidence: {cm.overall_confidence:.0%}")
        report.append(f"  - Source Quality: {cm.source_quality:.0%}")
        report.append(f"  - Evidence Quantity: {cm.evidence_quantity:.0%}")
        report.append(f"  - Evidence Independence: {cm.evidence_independence:.0%}")
        report.append(f"  - Logical Coherence: {cm.logical_coherence:.0%}")
        report.append(f"  - Context Clarity: {cm.context_clarity:.0%}")
        report.append("")
        
        # Red Flags
        if dossier.red_flags:
            report.append("RED FLAGS")
            report.append("-" * 80)
            for flag in dossier.red_flags:
                report.append(f"⚠️  {flag}")
            report.append("")
        
        # Caveats
        if dossier.caveats:
            report.append("CAVEATS")
            report.append("-" * 80)
            for caveat in dossier.caveats:
                report.append(f"• {caveat}")
            report.append("")
        
        # Recommendations
        if editor_findings.get('recommendations'):
            report.append("RECOMMENDATIONS")
            report.append("-" * 80)
            for rec in editor_findings['recommendations']:
                report.append(f"→ {rec}")
            report.append("")
        
        report.append("=" * 80)
        
        return '\n'.join(report)
