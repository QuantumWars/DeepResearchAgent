"""Deep Research Agent for autonomous multi-step research execution."""

import asyncio
import time
import uuid
from typing import Optional, List, Dict, Any
from langchain_core.language_models import BaseChatModel
from langchain_core.callbacks import AsyncCallbackHandler
from langgraph.prebuilt import create_react_agent

from research_agent.agent.planner import ResearchPlanner
from research_agent.agent.callbacks import ResearchStreamingCallback, NoOpStreamingCallback
from research_agent.clients.tool_registry import get_tool_registry
from research_agent.memory.supermemory_client import SupermemoryClient, get_supermemory_client
from research_agent.utils.models import ResearchResult, ResearchPlan, SearchResult
from research_agent.utils.logger import get_logger
from research_agent.utils.config import get_config
from research_agent.utils.content_processor import deduplicate_results, truncate_content

# Import tools module to trigger tool registration
import research_agent.tools  # noqa: F401


logger = get_logger(__name__)


class DeepResearchAgent:
    """
    Main orchestrator for autonomous deep research.
    
    Coordinates research planning, tool execution, result aggregation,
    and memory storage. Uses LangChain's AgentExecutor for autonomous
    tool selection and execution.
    """
    
    def __init__(
        self,
        llm: BaseChatModel,
        search_provider: Optional[str] = None,
        memory_client: Optional[SupermemoryClient] = None,
        stream_handler: Optional[AsyncCallbackHandler] = None
    ):
        """
        Initialize the Deep Research Agent.
        
        Args:
            llm: Language model for planning and tool selection
            search_provider: Search provider to use (defaults to config)
            memory_client: Supermemory client for context storage (defaults to global)
            stream_handler: Callback handler for streaming progress (defaults to no-op)
        """
        self.llm = llm
        self.config = get_config()
        
        # Override search provider if specified
        if search_provider:
            self.config.search_provider = search_provider
        
        # Initialize components
        self.planner = ResearchPlanner(llm)
        self.memory_client = memory_client or get_supermemory_client()
        self.stream_handler = stream_handler or NoOpStreamingCallback()
        
        # Get tools from registry and filter by enabled_tools config
        self.tool_registry = get_tool_registry()
        self._initialize_tools()
        
        logger.info(
            "DeepResearchAgent initialized",
            extra={"context": {
                "search_provider": self.config.search_provider,
                "max_tool_calls": self.config.max_tool_calls,
                "tools": [tool.name for tool in self.tools]
            }}
        )
    
    def _initialize_tools(self) -> None:
        """
        Initialize tools from registry based on enabled_tools configuration.
        
        Gets all enabled tools from the registry and filters them based on
        the enabled_tools list in the configuration.
        """
        # Get enabled tools list from config
        enabled_tool_names = self.config.enabled_tools_list
        
        # Set enabled tools in registry based on config
        self.tool_registry.set_enabled_tools(enabled_tool_names)
        
        # Get the filtered list of enabled tools
        self.tools = self.tool_registry.get_enabled_tools()
        
        logger.info(
            f"Initialized {len(self.tools)} tools from registry",
            extra={"context": {
                "enabled_tools": enabled_tool_names,
                "tool_count": len(self.tools)
            }}
        )
    
    async def research(
        self,
        query: str,
        user_id: Optional[str] = None
    ) -> ResearchResult:
        """
        Execute autonomous research on a query.
        
        Main entry point for research execution. Follows these steps:
        1. Generate research plan using LLM
        2. Create agent executor with tools
        3. Execute research autonomously
        4. Aggregate and deduplicate results
        5. Store in Supermemory
        
        Args:
            query: Research query to investigate
            user_id: Optional user identifier for memory isolation
            
        Returns:
            ResearchResult with text, sources, charts, and metadata
        """
        start_time = time.time()
        session_id = str(uuid.uuid4())
        
        logger.info(
            f"Starting research",
            extra={"context": {
                "query": query,
                "user_id": user_id,
                "session_id": session_id
            }}
        )
        
        try:
            # Step 1: Create research plan
            logger.info("Creating research plan")
            plan = await self._create_research_plan(query)
            
            logger.info(
                f"Research plan created",
                extra={"context": {
                    "topics": len(plan.topics),
                    "total_tasks": plan.total_tasks
                }}
            )
            
            # Step 2: Execute autonomous research
            logger.info("Starting autonomous research execution")
            result = await self._execute_research(
                query=query,
                plan=plan,
                user_id=user_id,
                session_id=session_id
            )
            
            # Calculate execution time
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            logger.info(
                f"Research completed successfully",
                extra={"context": {
                    "query": query,
                    "execution_time": execution_time,
                    "sources_count": len(result.sources),
                    "charts_count": len(result.charts)
                }}
            )
            
            # Step 3: Store in Supermemory if user_id provided
            if user_id and result.sources:
                logger.info("Storing research results in Supermemory")
                await self._store_research_results(
                    user_id=user_id,
                    session_id=session_id,
                    research_result=result
                )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Research failed: {str(e)}",
                exc_info=True,
                extra={"context": {
                    "query": query,
                    "error": str(e),
                    "execution_time": execution_time
                }}
            )
            
            # Return partial results if available
            return ResearchResult(
                query=query,
                plan=plan if 'plan' in locals() else None,
                text=f"Research failed: {str(e)}",
                sources=[],
                charts=[],
                tool_results=[],
                execution_time=execution_time
            )
    
    async def _create_research_plan(self, query: str) -> ResearchPlan:
        """
        Generate a structured research plan for the query.
        
        Args:
            query: Research query
            
        Returns:
            ResearchPlan with topics and tasks
        """
        try:
            plan = await self.planner.create_plan(query)
            return plan
        except Exception as e:
            logger.error(
                f"Failed to create research plan: {str(e)}",
                exc_info=True
            )
            raise
    
    def _create_agent_executor(
        self,
        plan: ResearchPlan
    ):
        """
        Create LangGraph agent executor with tools and configuration.
        
        Uses tools from the registry that have been filtered based on
        the enabled_tools configuration.
        
        Args:
            plan: Research plan to guide execution
            
        Returns:
            Configured LangGraph agent
        """
        # Format plan for system message
        plan_text = self._format_plan_for_prompt(plan)
        
        # Build tool descriptions dynamically based on available tools
        tool_names = [tool.name for tool in self.tools]
        tool_list = ", ".join(tool_names)
        
        # Create system message with research plan
        system_message = f"""You are a research assistant conducting autonomous research. You have access to the following tools: {tool_list}.

Research Plan:
{plan_text}

Your task is to execute this research plan systematically. Use the available tools to gather information:
- Use web search tools to find relevant information
- Use code execution if data analysis or visualization is needed
- Use memory search to check for relevant past research
- Use specialized search tools (X, YouTube, Reddit, Academic) for platform-specific content
- Use utility tools (weather, currency, datetime, etc.) for supplementary data

Guidelines:
- Focus primarily on search tools for information gathering
- Use code execution sparingly for data analysis or charts
- Be thorough but efficient - aim to complete research within {self.config.max_tool_calls} tool calls
- Gather diverse sources from different domains
- Extract key insights and findings from each source
- When you have gathered sufficient information, provide a comprehensive final answer"""
        
        # Create ReAct agent using LangGraph with registered tools
        agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=system_message
        )
        
        logger.debug(
            "Agent executor created",
            extra={"context": {
                "max_tool_calls": self.config.max_tool_calls,
                "tools": tool_names
            }}
        )
        
        return agent
    
    def _format_plan_for_prompt(self, plan: ResearchPlan) -> str:
        """
        Format research plan as text for the agent prompt.
        
        Args:
            plan: Research plan to format
            
        Returns:
            Formatted plan text
        """
        lines = []
        for i, topic in enumerate(plan.topics, 1):
            lines.append(f"{i}. {topic.title}")
            for j, task in enumerate(topic.tasks, 1):
                lines.append(f"   {i}.{j}. {task}")
        
        return "\n".join(lines)
    
    async def _execute_research(
        self,
        query: str,
        plan: ResearchPlan,
        user_id: Optional[str],
        session_id: str
    ) -> ResearchResult:
        """
        Execute autonomous research using the agent executor.
        
        Subtask 9.1: Implement autonomous research execution
        - Execute agent with research plan as initial prompt
        - Let agent autonomously select and call tools
        - Collect all tool results and sources
        - Aggregate and deduplicate sources by URL
        - Limit source content to 3000 characters in final results
        - Return ResearchResult with text, sources, charts, tool_results
        
        Args:
            query: Research query
            plan: Research plan
            user_id: Optional user identifier
            session_id: Research session identifier
            
        Returns:
            ResearchResult with aggregated findings
        """
        logger.info("Executing autonomous research")
        
        # Create agent
        agent = self._create_agent_executor(plan)
        
        # Prepare agent input
        agent_input = {
            "messages": [("user", f"Conduct research on: {query}")]
        }
        
        # Configure recursion limit (max tool calls)
        config = {
            "recursion_limit": self.config.max_tool_calls,
            "callbacks": [self.stream_handler]
        }
        
        # Execute agent
        try:
            logger.debug("Invoking agent")
            
            # Collect all messages from agent execution
            messages = []
            async for chunk in agent.astream(agent_input, config=config):
                messages.append(chunk)
            
            logger.info(
                "Agent execution completed",
                extra={"context": {
                    "message_chunks": len(messages)
                }}
            )
            
        except Exception as e:
            logger.error(
                f"Agent execution failed: {str(e)}",
                exc_info=True
            )
            # Return minimal result on failure
            return ResearchResult(
                query=query,
                plan=plan,
                text=f"Agent execution failed: {str(e)}",
                sources=[],
                charts=[],
                tool_results=[],
                execution_time=0.0
            )
        
        # Extract and aggregate results from messages
        sources: List[SearchResult] = []
        charts: List[Dict[str, Any]] = []
        tool_results: List[Dict[str, Any]] = []
        final_answer = ""
        
        # Process messages to extract tool calls and results
        for chunk in messages:
            # Check for agent messages
            if "agent" in chunk:
                agent_messages = chunk["agent"].get("messages", [])
                for msg in agent_messages:
                    # Extract final answer from AI messages
                    if hasattr(msg, "content") and msg.content:
                        final_answer = msg.content
            
            # Check for tool messages
            if "tools" in chunk:
                tool_messages = chunk["tools"].get("messages", [])
                for msg in tool_messages:
                    if hasattr(msg, "name") and hasattr(msg, "content"):
                        tool_name = msg.name
                        tool_content = msg.content
                        
                        # Record tool result
                        tool_results.append({
                            "tool": tool_name,
                            "output": str(tool_content)[:500]  # Truncate for storage
                        })
                        
                        # Extract sources from web_search results
                        if tool_name == "web_search" and isinstance(tool_content, list):
                            for item in tool_content:
                                if isinstance(item, SearchResult):
                                    sources.append(item)
                        
                        # Extract charts from code execution results
                        if tool_name == "execute_python_code":
                            if hasattr(tool_content, 'charts') and tool_content.charts:
                                charts.extend(tool_content.charts)
        
        logger.info(
            f"Collected results from agent execution",
            extra={"context": {
                "sources": len(sources),
                "charts": len(charts),
                "tool_results": len(tool_results)
            }}
        )
        
        # Deduplicate sources by URL
        deduplicated_sources = deduplicate_results(sources, by_url=True, by_domain=False)
        
        logger.info(
            f"Deduplicated sources: {len(sources)} -> {len(deduplicated_sources)}",
            extra={"context": {
                "before": len(sources),
                "after": len(deduplicated_sources)
            }}
        )
        
        # Limit source content to 3000 characters
        for source in deduplicated_sources:
            if source.content:
                source.content = truncate_content(
                    source.content,
                    max_length=self.config.content_max_chars
                )
        
        # Use final answer or default message
        if not final_answer:
            final_answer = "Research completed. See sources for details."
        
        # Create research result
        research_result = ResearchResult(
            query=query,
            plan=plan,
            text=final_answer,
            sources=deduplicated_sources,
            charts=charts,
            tool_results=tool_results,
            execution_time=0.0  # Will be set by caller
        )
        
        return research_result
    
    async def _store_research_results(
        self,
        user_id: str,
        session_id: str,
        research_result: ResearchResult
    ) -> None:
        """
        Store research results in Supermemory.
        
        Subtask 9.2: Add memory storage after research
        - After research completes, store results in Supermemory
        - Tag with user_id and session_id
        - Store each source as a separate memory
        - Include metadata (title, URL, published_date, session_id)
        - Handle storage errors gracefully
        
        Args:
            user_id: User identifier
            session_id: Research session identifier
            research_result: Complete research result to store
        """
        logger.info(
            "Storing research results in Supermemory",
            extra={"context": {
                "user_id": user_id,
                "session_id": session_id,
                "sources_count": len(research_result.sources)
            }}
        )
        
        try:
            await self.memory_client.store_research(
                user_id=user_id,
                session_id=session_id,
                research_result=research_result
            )
            
            logger.info(
                "Successfully stored research results",
                extra={"context": {
                    "user_id": user_id,
                    "session_id": session_id
                }}
            )
            
        except Exception as e:
            # Log error but don't fail the research
            logger.error(
                f"Failed to store research results: {str(e)}",
                exc_info=True,
                extra={"context": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "error": str(e)
                }}
            )
