"""Tool registry for managing and discovering research tools."""

from typing import Callable, Dict, List, Set, Optional
from research_agent.utils.logger import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """Central registry for all research tools.
    
    The ToolRegistry manages tool registration, discovery, and enablement.
    Tools can be registered with a name and enabled/disabled dynamically.
    """
    
    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, Callable] = {}
        self._enabled_tools: Set[str] = set()
        self._tool_metadata: Dict[str, Dict] = {}
    
    def register(
        self,
        name: str,
        tool: Callable,
        enabled: bool = True,
        metadata: Optional[Dict] = None
    ) -> None:
        """Register a tool in the registry.
        
        Args:
            name: Unique name for the tool
            tool: The tool function (should be decorated with @tool)
            enabled: Whether the tool is enabled by default
            metadata: Optional metadata about the tool (description, requirements, etc.)
        """
        if name in self._tools:
            logger.warning(f"Tool '{name}' is already registered. Overwriting.")
        
        self._tools[name] = tool
        if enabled:
            self._enabled_tools.add(name)
        
        if metadata:
            self._tool_metadata[name] = metadata
        
        logger.debug(f"Registered tool: {name} (enabled={enabled})")
    
    def get_enabled_tools(self) -> List[Callable]:
        """Get list of enabled tool functions.
        
        Returns:
            List of enabled tool callables
        """
        enabled = [
            self._tools[name]
            for name in self._enabled_tools
            if name in self._tools
        ]
        logger.debug(f"Retrieved {len(enabled)} enabled tools")
        return enabled
    
    def get_all_tools(self) -> Dict[str, Callable]:
        """Get all registered tools.
        
        Returns:
            Dictionary mapping tool names to callables
        """
        return self._tools.copy()
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """Get a specific tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool callable or None if not found
        """
        return self._tools.get(name)
    
    def enable_tool(self, name: str) -> bool:
        """Enable a tool.
        
        Args:
            name: Tool name to enable
            
        Returns:
            True if tool was enabled, False if tool doesn't exist
        """
        if name in self._tools:
            self._enabled_tools.add(name)
            logger.info(f"Enabled tool: {name}")
            return True
        else:
            logger.warning(f"Cannot enable tool '{name}': not registered")
            return False
    
    def disable_tool(self, name: str) -> bool:
        """Disable a tool.
        
        Args:
            name: Tool name to disable
            
        Returns:
            True if tool was disabled, False if tool doesn't exist
        """
        if name in self._tools:
            self._enabled_tools.discard(name)
            logger.info(f"Disabled tool: {name}")
            return True
        else:
            logger.warning(f"Cannot disable tool '{name}': not registered")
            return False
    
    def is_enabled(self, name: str) -> bool:
        """Check if a tool is enabled.
        
        Args:
            name: Tool name
            
        Returns:
            True if tool is enabled, False otherwise
        """
        return name in self._enabled_tools
    
    def list_tools(self) -> List[str]:
        """List all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())
    
    def list_enabled_tools(self) -> List[str]:
        """List enabled tool names.
        
        Returns:
            List of enabled tool names
        """
        return list(self._enabled_tools)
    
    def get_metadata(self, name: str) -> Optional[Dict]:
        """Get metadata for a tool.
        
        Args:
            name: Tool name
            
        Returns:
            Tool metadata or None if not found
        """
        return self._tool_metadata.get(name)
    
    def set_enabled_tools(self, tool_names: List[str]) -> None:
        """Set which tools should be enabled.
        
        Disables all tools and enables only those in the provided list.
        
        Args:
            tool_names: List of tool names to enable
        """
        self._enabled_tools.clear()
        for name in tool_names:
            if name in self._tools:
                self._enabled_tools.add(name)
                logger.debug(f"Enabled tool: {name}")
            else:
                logger.warning(f"Cannot enable tool '{name}': not registered")
        
        logger.info(f"Set enabled tools: {self.list_enabled_tools()}")
    
    def clear(self) -> None:
        """Clear all registered tools (useful for testing)."""
        self._tools.clear()
        self._enabled_tools.clear()
        self._tool_metadata.clear()
        logger.debug("Cleared tool registry")


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance.
    
    Returns:
        Global ToolRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        logger.debug("Created global tool registry")
    return _registry


def register_tool(
    name: str,
    enabled: bool = True,
    metadata: Optional[Dict] = None
):
    """Decorator to register a tool in the global registry.
    
    Args:
        name: Unique name for the tool
        enabled: Whether the tool is enabled by default
        metadata: Optional metadata about the tool
        
    Returns:
        Decorator function
        
    Example:
        @register_tool("my_tool", enabled=True)
        @tool
        def my_tool(query: str) -> str:
            return "result"
    """
    def decorator(func: Callable) -> Callable:
        registry = get_tool_registry()
        registry.register(name, func, enabled=enabled, metadata=metadata)
        return func
    return decorator


def reset_tool_registry() -> None:
    """Reset the global tool registry (useful for testing)."""
    global _registry
    if _registry is not None:
        _registry.clear()
    _registry = None
    logger.debug("Reset global tool registry")
