"""
Base Agent: The foundation for all cognitive layer agents.
Each agent is a specialist that analyzes one aspect of the claim.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .dossier import InvestigationDossier
import logging

logging.basicConfig(level=logging.INFO)


class BaseAgent(ABC):
    """
    Abstract base class for all fact-checking agents.
    Each agent represents a cognitive layer in the journalist's mind.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"Agent.{name}")
    
    @abstractmethod
    async def analyze(self, dossier: InvestigationDossier) -> Dict[str, Any]:
        """
        Analyze the dossier and return findings.
        
        Args:
            dossier: The shared investigation state
            
        Returns:
            Dictionary of findings specific to this agent's role
        """
        pass
    
    async def execute(self, dossier: InvestigationDossier) -> InvestigationDossier:
        """
        Execute the agent's analysis and update the dossier.
        
        Args:
            dossier: The investigation dossier to analyze
            
        Returns:
            Updated dossier with this agent's findings
        """
        self.logger.info(f"🔍 {self.name} starting analysis...")
        
        try:
            findings = await self.analyze(dossier)
            dossier.add_layer_finding(self.name, findings)
            self.logger.info(f"✅ {self.name} completed analysis")
            return dossier
        except Exception as e:
            self.logger.error(f"❌ {self.name} encountered error: {str(e)}")
            dossier.add_layer_finding(self.name, {
                "error": str(e),
                "status": "failed"
            })
            return dossier
    
    def log_finding(self, message: str, level: str = "info"):
        """Log a finding with appropriate level"""
        if level == "warning":
            self.logger.warning(f"⚠️  {message}")
        elif level == "error":
            self.logger.error(f"❌ {message}")
        else:
            self.logger.info(f"📝 {message}")


class AgentConfig:
    """Configuration for agent behavior"""
    
    def __init__(self, 
                 max_sources: int = 10,
                 timeout_seconds: int = 30,
                 min_confidence_threshold: float = 0.3,
                 enable_web_search: bool = True,
                 enable_archive_search: bool = True):
        self.max_sources = max_sources
        self.timeout_seconds = timeout_seconds
        self.min_confidence_threshold = min_confidence_threshold
        self.enable_web_search = enable_web_search
        self.enable_archive_search = enable_archive_search
