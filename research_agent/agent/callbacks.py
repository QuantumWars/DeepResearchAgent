"""Streaming callback handlers for real-time research progress updates."""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.outputs import LLMResult
from research_agent.utils.logger import get_logger

logger = get_logger(__name__)


class ResearchStreamingCallback(AsyncCallbackHandler):
    """
    LangChain callback handler for streaming research progress events.
    
    Emits events for:
    - Tool execution start/end
    - Agent actions and decisions
    - LLM calls
    - Errors and warnings
    
    All events include timestamps for tracking execution flow.
    """
    
    def __init__(self, event_queue: asyncio.Queue):
        """
        Initialize the streaming callback handler.
        
        Args:
            event_queue: Async queue for emitting events to consumers
        """
        super().__init__()
        self.event_queue = event_queue
        logger.debug("ResearchStreamingCallback initialized")
    
    async def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any
    ) -> None:
        """
        Called when a tool starts executing.
        
        Emits a tool_start event with tool name, input, and timestamp.
        
        Args:
            serialized: Serialized tool information
            input_str: Input string passed to the tool
            **kwargs: Additional keyword arguments
        """
        tool_name = serialized.get("name", "unknown")
        
        event = {
            "type": "tool_start",
            "tool": tool_name,
            "input": input_str,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.debug(f"Tool started: {tool_name}")
        
        try:
            await self.event_queue.put(event)
        except Exception as e:
            logger.error(f"Failed to emit tool_start event: {e}")
    
    async def on_tool_end(
        self,
        output: str,
        **kwargs: Any
    ) -> None:
        """
        Called when a tool finishes executing.
        
        Emits a tool_end event with output (truncated) and timestamp.
        
        Args:
            output: Output string from the tool
            **kwargs: Additional keyword arguments
        """
        # Truncate output for streaming (first 500 chars)
        truncated_output = output[:500] if output else ""
        if len(output) > 500:
            truncated_output += "... (truncated)"
        
        event = {
            "type": "tool_end",
            "output": truncated_output,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.debug(f"Tool completed with output length: {len(output)}")
        
        try:
            await self.event_queue.put(event)
        except Exception as e:
            logger.error(f"Failed to emit tool_end event: {e}")
    
    async def on_tool_error(
        self,
        error: BaseException,
        **kwargs: Any
    ) -> None:
        """
        Called when a tool encounters an error.
        
        Emits a tool_error event with error message and timestamp.
        
        Args:
            error: The exception that occurred
            **kwargs: Additional keyword arguments
        """
        event = {
            "type": "tool_error",
            "error": str(error),
            "error_type": type(error).__name__,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.error(f"Tool error: {error}")
        
        try:
            await self.event_queue.put(event)
        except Exception as e:
            logger.error(f"Failed to emit tool_error event: {e}")
    
    async def on_agent_action(
        self,
        action: AgentAction,
        **kwargs: Any
    ) -> None:
        """
        Called when the agent takes an action (decides to use a tool).
        
        Emits an agent_action event with tool selection, input, and reasoning.
        
        Args:
            action: The agent action containing tool and input
            **kwargs: Additional keyword arguments
        """
        # Truncate log for streaming (first 200 chars)
        truncated_log = action.log[:200] if action.log else ""
        if action.log and len(action.log) > 200:
            truncated_log += "... (truncated)"
        
        event = {
            "type": "agent_action",
            "tool": action.tool,
            "tool_input": action.tool_input,
            "log": truncated_log,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.debug(f"Agent action: using tool '{action.tool}'")
        
        try:
            await self.event_queue.put(event)
        except Exception as e:
            logger.error(f"Failed to emit agent_action event: {e}")
    
    async def on_agent_finish(
        self,
        finish: AgentFinish,
        **kwargs: Any
    ) -> None:
        """
        Called when the agent finishes execution.
        
        Emits an agent_finish event with final output and timestamp.
        
        Args:
            finish: The agent finish object with return values
            **kwargs: Additional keyword arguments
        """
        event = {
            "type": "agent_finish",
            "output": str(finish.return_values),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info("Agent execution finished")
        
        try:
            await self.event_queue.put(event)
        except Exception as e:
            logger.error(f"Failed to emit agent_finish event: {e}")
    
    async def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: list[str],
        **kwargs: Any
    ) -> None:
        """
        Called when an LLM starts generating.
        
        Emits an llm_start event with model info and timestamp.
        
        Args:
            serialized: Serialized LLM information
            prompts: List of prompts being sent to the LLM
            **kwargs: Additional keyword arguments
        """
        model_name = serialized.get("name", "unknown")
        
        event = {
            "type": "llm_start",
            "model": model_name,
            "prompt_count": len(prompts),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.debug(f"LLM started: {model_name}")
        
        try:
            await self.event_queue.put(event)
        except Exception as e:
            logger.error(f"Failed to emit llm_start event: {e}")
    
    async def on_llm_end(
        self,
        response: LLMResult,
        **kwargs: Any
    ) -> None:
        """
        Called when an LLM finishes generating.
        
        Emits an llm_end event with generation info and timestamp.
        
        Args:
            response: The LLM result
            **kwargs: Additional keyword arguments
        """
        event = {
            "type": "llm_end",
            "generations": len(response.generations),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.debug("LLM generation completed")
        
        try:
            await self.event_queue.put(event)
        except Exception as e:
            logger.error(f"Failed to emit llm_end event: {e}")
    
    async def on_llm_error(
        self,
        error: BaseException,
        **kwargs: Any
    ) -> None:
        """
        Called when an LLM encounters an error.
        
        Emits an llm_error event with error details and timestamp.
        
        Args:
            error: The exception that occurred
            **kwargs: Additional keyword arguments
        """
        event = {
            "type": "llm_error",
            "error": str(error),
            "error_type": type(error).__name__,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.error(f"LLM error: {error}")
        
        try:
            await self.event_queue.put(event)
        except Exception as e:
            logger.error(f"Failed to emit llm_error event: {e}")
    
    async def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """
        Called when a chain starts executing.
        
        Emits a chain_start event with chain info and timestamp.
        
        Args:
            serialized: Serialized chain information
            inputs: Input dictionary for the chain
            **kwargs: Additional keyword arguments
        """
        chain_name = serialized.get("name", "unknown")
        
        event = {
            "type": "chain_start",
            "chain": chain_name,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.debug(f"Chain started: {chain_name}")
        
        try:
            await self.event_queue.put(event)
        except Exception as e:
            logger.error(f"Failed to emit chain_start event: {e}")
    
    async def on_chain_end(
        self,
        outputs: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """
        Called when a chain finishes executing.
        
        Emits a chain_end event with timestamp.
        
        Args:
            outputs: Output dictionary from the chain
            **kwargs: Additional keyword arguments
        """
        event = {
            "type": "chain_end",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.debug("Chain execution completed")
        
        try:
            await self.event_queue.put(event)
        except Exception as e:
            logger.error(f"Failed to emit chain_end event: {e}")
    
    async def on_chain_error(
        self,
        error: BaseException,
        **kwargs: Any
    ) -> None:
        """
        Called when a chain encounters an error.
        
        Emits a chain_error event with error details and timestamp.
        
        Args:
            error: The exception that occurred
            **kwargs: Additional keyword arguments
        """
        event = {
            "type": "chain_error",
            "error": str(error),
            "error_type": type(error).__name__,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.error(f"Chain error: {error}")
        
        try:
            await self.event_queue.put(event)
        except Exception as e:
            logger.error(f"Failed to emit chain_error event: {e}")


class NoOpStreamingCallback(AsyncCallbackHandler):
    """
    No-operation callback handler for non-streaming use cases.
    
    This handler does nothing and can be used when streaming is not needed,
    avoiding the overhead of event queue management.
    """
    
    async def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any
    ) -> None:
        """No-op implementation."""
        pass
    
    async def on_tool_end(
        self,
        output: str,
        **kwargs: Any
    ) -> None:
        """No-op implementation."""
        pass
    
    async def on_agent_action(
        self,
        action: AgentAction,
        **kwargs: Any
    ) -> None:
        """No-op implementation."""
        pass
