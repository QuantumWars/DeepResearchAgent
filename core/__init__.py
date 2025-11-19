"""Core module for the Deep Research Framework."""

# Legacy LangGraph-based implementation (commented out for Agno migration)
# from core.orchestrator import ResearchOrchestrator, ResearchResult
# from core.graph import create_research_graph
# from core.state import ResearchState
# from core.workflow_nodes import (
#     planner_node,
#     retrieval_node,
#     reflection_node,
#     synthesis_node,
#     should_continue_research
# )

# New Agno-based implementation
from core.agno_orchestrator import AgnoResearchOrchestrator
from core.orchestrator import ResearchResult  # Keep for compatibility

__all__ = [
    # Legacy (commented)
    # "ResearchOrchestrator",
    # "ResearchResult",
    # "create_research_graph",
    # "ResearchState",
    # "planner_node",
    # "retrieval_node",
    # "reflection_node",
    # "synthesis_node",
    # "should_continue_research",
    
    # New
    "AgnoResearchOrchestrator",
    "ResearchResult",
]
