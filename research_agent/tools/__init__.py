"""Tools module for agent capabilities.

This module imports all available tools and registers them with the
global tool registry. Tools are registered with their default enabled/disabled
state based on their importance and API key requirements.
"""

from research_agent.clients.tool_registry import get_tool_registry
from research_agent.utils.logger import get_logger

# Import all tools
from .web_search import web_search
from .code_executor import execute_python_code
from .memory_search import search_memories
from .x_search import x_search
from .youtube_search import youtube_search
from .reddit_search import reddit_search
from .academic_search import academic_search
from .currency_converter import convert_currency
from .datetime_tool import datetime_operations
from .weather_tool import get_weather
from .flight_tracker import track_flight
from .stock_chart import get_stock_data
from .crypto_tools import get_crypto_data, get_crypto_market_overview
from .map_tools import geocode_location, reverse_geocode, calculate_distance

logger = get_logger(__name__)

__all__ = [
    "web_search",
    "execute_python_code",
    "search_memories",
    "x_search",
    "youtube_search",
    "reddit_search",
    "academic_search",
    "convert_currency",
    "datetime_operations",
    "get_weather",
    "track_flight",
    "get_stock_data",
    "get_crypto_data",
    "get_crypto_market_overview",
    "geocode_location",
    "reverse_geocode",
    "calculate_distance"
]


def _register_all_tools():
    """Register all tools with the global tool registry.
    
    Tools are registered with default enabled state. The actual enabled/disabled
    state will be controlled by the ENABLED_TOOLS configuration at runtime.
    
    Core tools (web_search, code_executor, memory_search) are enabled by default.
    Specialized tools are registered but will only be enabled if listed in ENABLED_TOOLS.
    """
    registry = get_tool_registry()
    
    # Core tools - enabled by default
    registry.register(
        "web_search",
        web_search,
        enabled=True,
        metadata={
            "description": "Search the web for information",
            "category": "search",
            "requires_api_key": True
        }
    )
    
    registry.register(
        "code_executor",
        execute_python_code,
        enabled=True,
        metadata={
            "description": "Execute Python code for data analysis and visualization",
            "category": "execution",
            "requires_api_key": False
        }
    )
    
    registry.register(
        "memory_search",
        search_memories,
        enabled=True,
        metadata={
            "description": "Search stored research memories",
            "category": "search",
            "requires_api_key": True
        }
    )
    
    # Specialized search tools - enabled by default but require specific API keys
    registry.register(
        "x_search",
        x_search,
        enabled=True,
        metadata={
            "description": "Search X/Twitter posts using xAI Grok",
            "category": "search",
            "requires_api_key": True,
            "api_key": "XAI_API_KEY"
        }
    )
    
    registry.register(
        "youtube_search",
        youtube_search,
        enabled=True,
        metadata={
            "description": "Search YouTube videos and extract transcripts",
            "category": "search",
            "requires_api_key": True,
            "api_key": "EXA_API_KEY"
        }
    )
    
    registry.register(
        "reddit_search",
        reddit_search,
        enabled=True,
        metadata={
            "description": "Search Reddit content",
            "category": "search",
            "requires_api_key": True,
            "api_key": "TAVILY_API_KEY"
        }
    )
    
    registry.register(
        "academic_search",
        academic_search,
        enabled=True,
        metadata={
            "description": "Search academic papers and research",
            "category": "search",
            "requires_api_key": True,
            "api_key": "EXA_API_KEY"
        }
    )
    
    # Utility tools - enabled by default, some require API keys
    registry.register(
        "convert_currency",
        convert_currency,
        enabled=True,
        metadata={
            "description": "Convert between currencies",
            "category": "utility",
            "requires_api_key": False
        }
    )
    
    registry.register(
        "datetime_operations",
        datetime_operations,
        enabled=True,
        metadata={
            "description": "Perform date and time operations",
            "category": "utility",
            "requires_api_key": False
        }
    )
    
    registry.register(
        "get_weather",
        get_weather,
        enabled=True,
        metadata={
            "description": "Get weather data for locations",
            "category": "utility",
            "requires_api_key": True,
            "api_key": "OPENWEATHER_API_KEY"
        }
    )
    
    registry.register(
        "track_flight",
        track_flight,
        enabled=True,
        metadata={
            "description": "Track flight status and information",
            "category": "utility",
            "requires_api_key": True,
            "api_key": "AVIATIONSTACK_API_KEY"
        }
    )
    
    registry.register(
        "get_stock_data",
        get_stock_data,
        enabled=True,
        metadata={
            "description": "Get stock market data",
            "category": "utility",
            "requires_api_key": True,
            "api_key": "ALPHAVANTAGE_API_KEY"
        }
    )
    
    registry.register(
        "get_crypto_data",
        get_crypto_data,
        enabled=True,
        metadata={
            "description": "Get cryptocurrency data",
            "category": "utility",
            "requires_api_key": True,
            "api_key": "COINGECKO_API_KEY"
        }
    )
    
    registry.register(
        "get_crypto_market_overview",
        get_crypto_market_overview,
        enabled=True,
        metadata={
            "description": "Get cryptocurrency market overview",
            "category": "utility",
            "requires_api_key": True,
            "api_key": "COINGECKO_API_KEY"
        }
    )
    
    registry.register(
        "geocode_location",
        geocode_location,
        enabled=True,
        metadata={
            "description": "Convert address to coordinates",
            "category": "utility",
            "requires_api_key": True,
            "api_key": "GOOGLE_MAPS_API_KEY"
        }
    )
    
    registry.register(
        "reverse_geocode",
        reverse_geocode,
        enabled=True,
        metadata={
            "description": "Convert coordinates to address",
            "category": "utility",
            "requires_api_key": True,
            "api_key": "GOOGLE_MAPS_API_KEY"
        }
    )
    
    registry.register(
        "calculate_distance",
        calculate_distance,
        enabled=True,
        metadata={
            "description": "Calculate distance between locations",
            "category": "utility",
            "requires_api_key": True,
            "api_key": "GOOGLE_MAPS_API_KEY"
        }
    )
    
    logger.info(f"Registered {len(registry.list_tools())} tools in registry")


# Register all tools when module is imported
_register_all_tools()
