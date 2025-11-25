"""Core components for the fact-checking system"""

from .dossier import (
    InvestigationDossier,
    Evidence,
    EvidenceTier,
    SourceProfile,
    Hypothesis,
    TruthValue,
    InvestigationStrategy,
    ConfidenceMatrix
)
from .base_agent import BaseAgent, AgentConfig
from .tools import ToolKit, SearchResult
from .orchestrator import InvestigationOrchestrator

__all__ = [
    'InvestigationDossier',
    'Evidence',
    'EvidenceTier',
    'SourceProfile',
    'Hypothesis',
    'TruthValue',
    'InvestigationStrategy',
    'ConfidenceMatrix',
    'BaseAgent',
    'AgentConfig',
    'ToolKit',
    'SearchResult',
    'InvestigationOrchestrator'
]
