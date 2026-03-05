"""LangGraph workflow builder for the Deep Research Framework.

This module creates the research workflow graph that orchestrates the
multi-step research process: planning, retrieval, reflection, and synthesis.
"""

import logging
from langgraph.graph import StateGraph, START, END

from core.state import ResearchState
from core.workflow_nodes import (
    planner_node,
    retrieval_node,
    reflection_node,
    synthesis_node,
    should_continue_research
)
from registry.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


def create_research_graph(registry: ToolRegistry):
    """
    Build LangGraph workflow with registry-injected nodes.
    
    Creates a state machine that executes the research workflow:
    1. Planner: Decomposes query into sub-questions
    2. Retrieval: Searches and scrapes content
    3. Reflection: Evaluates completeness and identifies gaps
    4. Conditional routing: Continue research or proceed to synthesis
    5. Synthesis: Generates final cited report
    
    The graph uses conditional routing to loop back to retrieval if gaps
    are identified, up to a maximum number of iterations.
    
    Args:
        registry: ToolRegistry instance for tool access
    
    Returns:
        Compiled LangGraph workflow ready for execution
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
    
    Example:
        >>> registry = ToolRegistry.from_config()
        >>> graph = create_research_graph(registry)
        >>> result = graph.invoke(initial_state)
    """
    logger.info("Building research workflow graph")
    
    # Initialize StateGraph with ResearchState TypedDict
    workflow = StateGraph(ResearchState)
    
    # Add nodes with lambda wrapping to inject registry dependency
    workflow.add_node("planner", lambda state: planner_node(state, registry))
    workflow.add_node("retrieval", lambda state: retrieval_node(state, registry))
    workflow.add_node("reflection", lambda state: reflection_node(state, registry))
    workflow.add_node("synthesis", lambda state: synthesis_node(state, registry))
    
    logger.debug("Added workflow nodes: planner, retrieval, reflection, synthesis")
    
    # Define linear edges
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "retrieval")
    workflow.add_edge("retrieval", "reflection")
    
    logger.debug("Added linear edges: START -> planner -> retrieval -> reflection")
    
    # Add conditional edges from reflection
    workflow.add_conditional_edges(
        "reflection",
        should_continue_research,
        {
            "continue": "retrieval",
            "synthesize": "synthesis"
        }
    )
    
    logger.debug("Added conditional routing from reflection")
    
    # Add edge from synthesis to END
    workflow.add_edge("synthesis", END)
    
    logger.debug("Added final edge: synthesis -> END")
    
    # Compile and return the graph
    compiled_graph = workflow.compile()
    
    logger.info("Research workflow graph compiled successfully")
    
    return compiled_graph
