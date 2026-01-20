"""Tool registry system for managing pluggable tools."""

import logging
import importlib
import inspect
import os
from pathlib import Path
from typing import Dict, List, Optional, Type, Any, Union

from registry.base_tool import (
    BaseSearchTool,
    BaseScraperTool,
    BaseLLMTool,
    BaseCustomTool
)
from utils.config_loader import load_config, get_tool_config

logger = logging.getLogger(__name__)


# Type alias for any base tool type
BaseTool = Union[BaseSearchTool, BaseScraperTool, BaseLLMTool, BaseCustomTool]


class ToolRegistry:
    """
    Central registry for tool discovery, registration, and retrieval.
    
    The registry manages tools across different categories (search, scraper, llm, custom)
    and provides fallback chain support for resilient tool execution.
    
    Attributes:
        _tools: Dictionary mapping category -> tool_name -> tool_instance
        _fallback_chains: Dictionary mapping category -> ordered list of tool names
        _config: Configuration dictionary loaded from YAML
    
    Example:
        >>> registry = ToolRegistry.from_config("config/tool_config.yaml")
        >>> search_tool = registry.get_tool("search")
        >>> results = search_tool.search("quantum computing")
    """
    
    def __init__(self):
        """Initialize empty tool registry."""
        self._tools: Dict[str, Dict[str, BaseTool]] = {
            "search": {},
            "scraper": {},
            "llm": {},
            "custom": {}
        }
        self._fallback_chains: Dict[str, List[str]] = {
            "search": [],
            "scraper": [],
            "llm": [],
            "custom": []
        }
        self._config: Dict[str, Any] = {}
        logger.debug("Initialized empty ToolRegistry")
    
    def register_tool(
        self,
        tool_instance: BaseTool,
        category: str,
        priority: Optional[int] = None
    ) -> None:
        """
        Register a tool instance in the registry.
        
        Args:
            tool_instance: Instance of a tool implementing a base tool interface
            category: Tool category ('search', 'scraper', 'llm', 'custom')
            priority: Optional priority override (higher = tried first)
        
        Raises:
            ValueError: If category is invalid or tool lacks required attributes
        
        Example:
            >>> tool = TavilySearch(api_key="...")
            >>> registry.register_tool(tool, "search", priority=10)
        """
        if category not in self._tools:
            raise ValueError(
                f"Invalid category '{category}'. "
                f"Must be one of: {list(self._tools.keys())}"
            )
        
        # Validate tool has required attributes
        if not hasattr(tool_instance, 'name'):
            raise ValueError(
                f"Tool instance must have 'name' attribute"
            )
        
        tool_name = tool_instance.name
        
        # Override priority if provided
        if priority is not None and hasattr(tool_instance, 'priority'):
            tool_instance.priority = priority
        
        # Register the tool
        self._tools[category][tool_name] = tool_instance
        
        logger.info(
            f"Registered tool '{tool_name}' in category '{category}' "
            f"with priority {getattr(tool_instance, 'priority', 'N/A')}"
        )
        
        # Update fallback chain
        # Use priority if available, otherwise use 0 as default
        tool_priority = getattr(tool_instance, 'priority', 0)
        if priority is not None:
            tool_priority = priority
        self._update_fallback_chain(category, tool_name, tool_priority)
    
    def _update_fallback_chain(
        self,
        category: str,
        tool_name: str,
        priority: int
    ) -> None:
        """
        Update fallback chain for a category based on tool priority.
        
        Args:
            category: Tool category
            tool_name: Name of the tool
            priority: Tool priority (higher = tried first)
        """
        chain = self._fallback_chains[category]
        
        # Remove tool if already in chain
        if tool_name in chain:
            chain.remove(tool_name)
        
        # Insert tool in priority order (highest priority first)
        inserted = False
        for i, existing_tool_name in enumerate(chain):
            existing_tool = self._tools[category].get(existing_tool_name)
            if existing_tool and hasattr(existing_tool, 'priority'):
                if priority > existing_tool.priority:
                    chain.insert(i, tool_name)
                    inserted = True
                    break
        
        if not inserted:
            chain.append(tool_name)
        
        logger.debug(
            f"Updated fallback chain for '{category}': {chain}"
        )
    
    def get_tool(
        self,
        category: str,
        name: Optional[str] = None
    ) -> Optional[BaseTool]:
        """
        Retrieve a tool by category and optional name.
        
        If name is not provided, returns the highest priority enabled tool
        in the category.
        
        Args:
            category: Tool category ('search', 'scraper', 'llm', 'custom')
            name: Optional specific tool name
        
        Returns:
            Tool instance or None if not found
        
        Example:
            >>> # Get highest priority search tool
            >>> search_tool = registry.get_tool("search")
            >>> 
            >>> # Get specific tool by name
            >>> tavily = registry.get_tool("search", "tavily")
        """
        if category not in self._tools:
            logger.warning(f"Invalid category '{category}'")
            return None
        
        # If specific name requested, return that tool
        if name:
            tool = self._tools[category].get(name)
            if tool:
                logger.debug(f"Retrieved tool '{name}' from category '{category}'")
            else:
                logger.warning(
                    f"Tool '{name}' not found in category '{category}'"
                )
            return tool
        
        # Otherwise, return highest priority tool from fallback chain
        chain = self._fallback_chains[category]
        if not chain:
            logger.warning(
                f"No tools registered in category '{category}'"
            )
            return None
        
        # Find first tool in chain that actually exists
        for tool_name in chain:
            tool = self._tools[category].get(tool_name)
            if tool:
                logger.debug(
                    f"Retrieved highest priority tool '{tool_name}' "
                    f"from category '{category}'"
                )
                return tool
        
        # No tools in chain exist
        logger.warning(
            f"No registered tools found in fallback chain for '{category}'"
        )
        return None
    
    def get_tool_chain(self, category: str) -> List[BaseTool]:
        """
        Get ordered list of tools for fallback chain.
        
        Returns tools in priority order (highest first). Nodes can iterate
        through this chain, trying each tool until one succeeds.
        
        Args:
            category: Tool category ('search', 'scraper', 'llm', 'custom')
        
        Returns:
            List of tool instances in priority order
        
        Example:
            >>> search_chain = registry.get_tool_chain("search")
            >>> for tool in search_chain:
            ...     results = tool.search(query)
            ...     if results:
            ...         break
        """
        if category not in self._tools:
            logger.warning(f"Invalid category '{category}'")
            return []
        
        chain = self._fallback_chains[category]
        tools = []
        
        for tool_name in chain:
            tool = self._tools[category].get(tool_name)
            if tool:
                tools.append(tool)
        
        logger.debug(
            f"Retrieved fallback chain for '{category}' "
            f"with {len(tools)} tools: {[t.name for t in tools]}"
        )
        
        return tools
    
    @classmethod
    def from_config(cls, config_path: str = "config/tool_config.yaml") -> "ToolRegistry":
        """
        Factory method to create and initialize registry from configuration.
        
        Loads configuration, discovers tools, and initializes the registry
        with all configured tools.
        
        Args:
            config_path: Path to YAML configuration file
        
        Returns:
            Initialized ToolRegistry instance
        
        Raises:
            ConfigurationError: If configuration is invalid
        
        Example:
            >>> registry = ToolRegistry.from_config("config/tool_config.yaml")
            >>> # Registry is now populated with all configured tools
        """
        registry = cls()
        
        # Load configuration
        config = load_config(config_path)
        registry._config = config
        
        logger.info(f"Initializing ToolRegistry from config: {config_path}")
        
        # Initialize fallback chains from config
        if "search_tools" in config and "fallback_chain" in config["search_tools"]:
            registry._fallback_chains["search"] = config["search_tools"]["fallback_chain"].copy()
            logger.debug(f"Set search fallback chain: {registry._fallback_chains['search']}")
        
        if "scraper_tools" in config and "fallback_chain" in config["scraper_tools"]:
            registry._fallback_chains["scraper"] = config["scraper_tools"]["fallback_chain"].copy()
            logger.debug(f"Set scraper fallback chain: {registry._fallback_chains['scraper']}")
        
        # Note: LLM tools don't use fallback chains, they use model routing
        # Custom tools can be added dynamically
        
        logger.info("ToolRegistry initialized from configuration")
        
        return registry
    
    def discover_tools(self, tools_directory: str = "tools") -> int:
        """
        Discover and register tools from directory.
        
        Recursively scans the tools directory, imports Python modules,
        inspects classes for base tool inheritance, and automatically
        registers discovered tools.
        
        Args:
            tools_directory: Root directory to scan for tools
        
        Returns:
            Number of tools discovered and registered
        
        Example:
            >>> registry = ToolRegistry.from_config()
            >>> count = registry.discover_tools("tools")
            >>> print(f"Discovered {count} tools")
        """
        tools_path = Path(tools_directory)
        
        if not tools_path.exists():
            logger.warning(f"Tools directory not found: {tools_directory}")
            return 0
        
        discovered_count = 0
        logger.info(f"Scanning for tools in: {tools_directory}")
        
        # Map base classes to categories
        base_class_to_category = {
            BaseSearchTool: "search",
            BaseScraperTool: "scraper",
            BaseLLMTool: "llm",
            BaseCustomTool: "custom"
        }
        
        # Recursively find all Python files
        for py_file in tools_path.rglob("*.py"):
            # Skip __init__.py and __pycache__
            if py_file.name.startswith("__"):
                continue
            
            # Convert file path to module path
            # Make paths absolute to handle relative tool directories
            abs_py_file = py_file.resolve()
            abs_cwd = Path.cwd().resolve()
            
            try:
                relative_path = abs_py_file.relative_to(abs_cwd)
            except ValueError:
                # If file is not relative to cwd, skip it
                logger.warning(f"Skipping file outside workspace: {py_file}")
                continue
            
            module_path = str(relative_path.with_suffix("")).replace(os.sep, ".")
            
            try:
                # Import the module
                module = importlib.import_module(module_path)
                logger.debug(f"Imported module: {module_path}")
                
                # Inspect all classes in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Skip imported base classes
                    if obj.__module__ != module.__name__:
                        continue
                    
                    # Check if class inherits from any base tool class
                    for base_class, category in base_class_to_category.items():
                        if issubclass(obj, base_class) and obj != base_class:
                            # Found a tool class, try to instantiate it
                            discovered_count += self._instantiate_and_register_tool(
                                obj, category, module_path
                            )
                            break
            
            except Exception as e:
                logger.warning(
                    f"Failed to import or inspect module {module_path}: {e}"
                )
                continue
        
        logger.info(f"Tool discovery complete. Registered {discovered_count} tools")
        return discovered_count
    
    def _instantiate_and_register_tool(
        self,
        tool_class: Type[BaseTool],
        category: str,
        module_path: str
    ) -> int:
        """
        Instantiate a tool class and register it.
        
        Args:
            tool_class: Tool class to instantiate
            category: Tool category
            module_path: Module path for logging
        
        Returns:
            1 if successfully registered, 0 otherwise
        """
        try:
            # Get tool name from class
            tool_name = getattr(tool_class, 'name', tool_class.__name__.lower())
            
            # Get tool configuration
            config_section = f"{category}_tools" if category != "custom" else "custom_tools"
            tool_config = get_tool_config(self._config, config_section, tool_name)
            
            # Check if tool is enabled in config
            if tool_config and not tool_config.get("enabled", True):
                logger.debug(
                    f"Skipping disabled tool: {tool_name} ({tool_class.__name__})"
                )
                return 0
            
            # Extract initialization parameters from config
            init_params = {}
            
            # Special handling for LLM tools (need routing config)
            if category == "llm" and tool_name == "litellm":
                llm_config = self._config.get("llm_tools", {})
                init_params["routing"] = llm_config.get("routing", {})
                if "extra_params" in llm_config:
                    init_params["extra_params"] = llm_config["extra_params"]
                if "api_keys" in llm_config:
                    init_params["api_keys"] = llm_config["api_keys"]
            elif tool_config:
                # Add API key if present
                if "api_key" in tool_config:
                    init_params["api_key"] = tool_config["api_key"]
                
                # Add extra params if present
                if "extra_params" in tool_config:
                    init_params["extra_params"] = tool_config["extra_params"]
            
            # Try to instantiate the tool
            # First try with config params, then without
            try:
                tool_instance = tool_class(**init_params)
            except TypeError as te:
                # If initialization fails, try without params
                logger.warning(f"Failed to instantiate {tool_name} with params, trying without: {te}")
                try:
                    tool_instance = tool_class()
                except Exception as e2:
                    logger.error(f"Failed to instantiate {tool_name} without params: {e2}")
                    return 0
            
            # Get priority from config or class attribute
            priority = None
            if tool_config and "priority" in tool_config:
                priority = tool_config["priority"]
            elif hasattr(tool_instance, 'priority'):
                priority = tool_instance.priority
            
            # Register the tool
            self.register_tool(tool_instance, category, priority)
            
            logger.info(
                f"Discovered and registered tool: {tool_name} "
                f"({tool_class.__name__}) from {module_path}"
            )
            
            return 1
        
        except Exception as e:
            logger.error(
                f"Failed to instantiate tool {tool_class.__name__} "
                f"from {module_path}: {e}"
            )
            return 0
    
    def get_registered_tools(self, category: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get list of registered tool names by category.
        
        Args:
            category: Optional category filter
        
        Returns:
            Dictionary mapping category to list of tool names
        
        Example:
            >>> tools = registry.get_registered_tools()
            >>> print(tools)
            {'search': ['tavily', 'serper'], 'scraper': ['trafilatura'], ...}
        """
        if category:
            if category not in self._tools:
                return {}
            return {category: list(self._tools[category].keys())}
        
        return {
            cat: list(tools.keys())
            for cat, tools in self._tools.items()
        }
    
    def __repr__(self) -> str:
        """String representation of registry."""
        tool_counts = {
            cat: len(tools)
            for cat, tools in self._tools.items()
        }
        return f"ToolRegistry(tools={tool_counts})"

