"""Research orchestrator for the Deep Research Framework.

This module provides the high-level interface for executing research workflows.
The ResearchOrchestrator class manages the complete research lifecycle from
query to final report.
"""

import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import re

from pydantic import BaseModel, Field

from utils.config_loader import load_config
from registry.tool_registry import ToolRegistry, BaseTool
from core.graph import create_research_graph
from models.tool_schemas import Citation


logger = logging.getLogger(__name__)


class ResearchResult(BaseModel):
    """
    Result of a research execution.
    
    Contains the final report, source documents, and execution log for
    debugging and analysis.
    
    Attributes:
        report: Markdown-formatted research report with citations
        sources: List of source documents with url, content, title
        execution_log: List of tool execution records
    
    Requirements: 12.1, 12.5
    """
    report: str
    sources: List[dict] = Field(default_factory=list)
    execution_log: List[dict] = Field(default_factory=list)
    
    def save(self, filepath: str) -> None:
        """
        Save the research report to a file.
        
        Args:
            filepath: Path where the report should be saved
        
        Example:
            >>> result = orchestrator.research("quantum computing")
            >>> result.save("reports/quantum_computing.md")
        """
        output_path = Path(filepath)
        
        # Create parent directories if they don't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write report to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.report)
            
            # Optionally append metadata
            f.write("\n\n---\n\n")
            f.write(f"## Research Metadata\n\n")
            f.write(f"- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **Sources**: {len(self.sources)}\n")
            f.write(f"- **Tool Calls**: {len(self.execution_log)}\n")
        
        logger.info(f"Report saved to: {filepath}")
    
    def get_citations(self) -> List[Citation]:
        """
        Extract Citation objects from the report.
        
        Parses the report to find citation markers [1], [2], etc. and
        matches them with source documents to create Citation objects.
        
        Returns:
            List of Citation objects with id, url, title, excerpt
        
        Example:
            >>> result = orchestrator.research("quantum computing")
            >>> citations = result.get_citations()
            >>> for citation in citations:
            ...     print(f"[{citation.id}] {citation.title}")
        """
        citations = []
        
        # Find all citation markers in the report [1], [2], etc.
        citation_pattern = r'\[(\d+)\]'
        citation_ids = set(re.findall(citation_pattern, self.report))
        
        # Match citation IDs with sources
        for idx, source in enumerate(self.sources):
            citation_id = str(idx + 1)
            
            if citation_id in citation_ids:
                # Extract excerpt from content (first 200 chars)
                content = source.get('content', '')
                excerpt = content[:200] + "..." if len(content) > 200 else content
                
                citation = Citation(
                    id=citation_id,
                    url=source.get('url', ''),
                    title=source.get('title', 'Untitled'),
                    excerpt=excerpt,
                    accessed_at=datetime.now()
                )
                citations.append(citation)
        
        logger.debug(f"Extracted {len(citations)} citations from report")
        return citations


class ResearchOrchestrator:
    """
    Main orchestrator for executing research workflows.
    
    The orchestrator initializes the tool registry, creates the research graph,
    and provides a high-level interface for executing research queries.
    
    Attributes:
        config: Configuration dictionary loaded from YAML
        registry: ToolRegistry instance for tool access
        graph: Compiled LangGraph workflow
        logger: Logger instance for this orchestrator
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 11.4
    
    Example:
        >>> orchestrator = ResearchOrchestrator("config/tool_config.yaml")
        >>> result = orchestrator.research("What is quantum computing?")
        >>> print(result.report)
    """
    
    def __init__(self, config_path: str = "config/tool_config.yaml"):
        """
        Initialize the research orchestrator.
        
        Loads configuration, initializes the tool registry, discovers tools,
        creates the research graph, and sets up logging.
        
        Args:
            config_path: Path to YAML configuration file
        
        Raises:
            ConfigurationError: If configuration is invalid
            FileNotFoundError: If configuration file doesn't exist
        
        Requirements: 3.1, 1.1, 6.1
        """
        self.logger = logging.getLogger(f"{__name__}.ResearchOrchestrator")
        
        self.logger.info(f"Initializing ResearchOrchestrator with config: {config_path}")
        
        # Load configuration
        self.config = load_config(config_path)
        self.logger.debug("Configuration loaded successfully")
        
        # Initialize ToolRegistry from configuration
        self.registry = ToolRegistry.from_config(config_path)
        self.logger.debug("ToolRegistry initialized")
        
        # Discover and register tools from tools directory
        discovered_count = self.registry.discover_tools("tools")
        self.logger.info(f"Discovered and registered {discovered_count} tools")
        
        # Log registered tools
        registered_tools = self.registry.get_registered_tools()
        for category, tools in registered_tools.items():
            if tools:
                self.logger.debug(f"  {category}: {', '.join(tools)}")
        
        # Create research graph
        self.graph = create_research_graph(self.registry)
        self.logger.info("Research graph created successfully")
        
        self.logger.info("ResearchOrchestrator initialization complete")
    
    def research(
        self,
        query: str,
        custom_tools: Optional[List[BaseTool]] = None,
        max_loops: int = 3
    ) -> ResearchResult:
        """
        Execute a complete research workflow for the given query.
        
        This method orchestrates the entire research process:
        1. Registers any custom tools provided
        2. Initializes the research state
        3. Executes the LangGraph workflow
        4. Extracts and returns results
        
        Args:
            query: Research question to investigate
            custom_tools: Optional list of custom tool instances to register
            max_loops: Maximum number of research iterations (default: 3)
        
        Returns:
            ResearchResult containing report, sources, and execution log
        
        Raises:
            Exception: If graph execution fails catastrophically
        
        Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 11.4
        
        Example:
            >>> orchestrator = ResearchOrchestrator()
            >>> result = orchestrator.research(
            ...     query="What is quantum computing?",
            ...     max_loops=2
            ... )
            >>> print(f"Report length: {len(result.report)} characters")
            >>> print(f"Sources: {len(result.sources)}")
        """
        self.logger.info(f"Starting research for query: '{query}'")
        self.logger.info(f"Max loops: {max_loops}")
        
        try:
            # Register custom tools if provided
            if custom_tools:
                self.logger.info(f"Registering {len(custom_tools)} custom tools")
                for tool in custom_tools:
                    # Determine category based on tool type
                    category = "custom"
                    if hasattr(tool, '__class__'):
                        class_name = tool.__class__.__name__
                        if 'Search' in class_name:
                            category = "search"
                        elif 'Scraper' in class_name:
                            category = "scraper"
                        elif 'LLM' in class_name:
                            category = "llm"
                    
                    self.registry.register_tool(tool, category)
                    self.logger.debug(f"Registered custom tool: {tool.name} in category {category}")
            
            # Initialize state with all required fields
            initial_state = {
                "original_query": query,
                "research_plan": None,
                "gaps_identified": None,
                "retrieved_documents": [],
                "research_loop_count": 0,
                "final_report": None,
                "tool_execution_log": [],
                "max_loops": max_loops
            }
            
            self.logger.debug("Initial state created")
            self.logger.info("Invoking research graph...")
            
            # Execute the graph
            final_state = self.graph.invoke(initial_state)
            
            self.logger.info("Graph execution completed")
            
            # Extract results from final state
            final_report = final_state.get("final_report", "No report generated")
            retrieved_documents = final_state.get("retrieved_documents", [])
            tool_execution_log = final_state.get("tool_execution_log", [])
            
            # Log summary
            self.logger.info(f"Research complete:")
            self.logger.info(f"  - Report length: {len(final_report)} characters")
            self.logger.info(f"  - Sources retrieved: {len(retrieved_documents)}")
            self.logger.info(f"  - Tool calls made: {len(tool_execution_log)}")
            self.logger.info(f"  - Research loops: {final_state.get('research_loop_count', 0)}")
            
            # Count successful vs failed tool calls
            successful_calls = sum(1 for log in tool_execution_log if log.get("success"))
            failed_calls = len(tool_execution_log) - successful_calls
            self.logger.info(f"  - Successful tool calls: {successful_calls}")
            self.logger.info(f"  - Failed tool calls: {failed_calls}")
            
            # Create and return ResearchResult
            result = ResearchResult(
                report=final_report,
                sources=retrieved_documents,
                execution_log=tool_execution_log
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Research execution failed: {e}", exc_info=True)
            
            # Return partial results if available
            self.logger.warning("Returning error result due to execution failure")
            
            return ResearchResult(
                report=f"# Research Failed\n\nAn error occurred during research execution:\n\n{str(e)}\n\nPlease check the logs for more details.",
                sources=[],
                execution_log=[]
            )
