"""Journalist's Mind Fact-Checking System"""

__version__ = "0.1.0"
__author__ = "Fact-Checking Research Team"

from src.core import InvestigationOrchestrator, ToolKit, InvestigationDossier
from src.agents import (
    GatekeeperAgent,
    ProfilerAgent,
    InvestigatorAgent,
    HistorianAgent,
    JudgeAgent,
    LogicianAgent,
    WatchdogAgent,
    EditorAgent
)

__all__ = [
    'InvestigationOrchestrator',
    'ToolKit',
    'InvestigationDossier',
    'GatekeeperAgent',
    'ProfilerAgent',
    'InvestigatorAgent',
    'HistorianAgent',
    'JudgeAgent',
    'LogicianAgent',
    'WatchdogAgent',
    'EditorAgent'
]
