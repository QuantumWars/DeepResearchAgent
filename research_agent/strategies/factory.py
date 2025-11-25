"""Factory for creating search strategy instances based on configuration."""

from typing import Literal, Optional
from research_agent.utils.config import Config
from research_agent.utils.logger import get_logger
from .base import SearchStrategy
from .exa_strategy import ExaSearchStrategy
from .tavily_strategy import TavilySearchStrategy
from .firecrawl_strategy import FirecrawlSearchStrategy
from .parallel_strategy import ParallelSearchStrategy


logger = get_logger(__name__)


def create_search_strategy(
    provider: Optional[Literal["exa", "tavily", "firecrawl", "parallel"]] = None,
    config: Optional[Config] = None
) -> SearchStrategy:
    """
    Create a search strategy instance based on the provider name.
    
    Args:
        provider: Search provider name (exa, tavily, firecrawl, parallel)
                 If None, uses the provider from config
        config: Configuration object. If None, loads from environment
        
    Returns:
        SearchStrategy instance for the specified provider
        
    Raises:
        ValueError: If provider is invalid or API key is missing
        
    Example:
        >>> strategy = create_search_strategy("exa")
        >>> results = await strategy.search("quantum computing")
    """
    # Load config if not provided
    if config is None:
        from research_agent.utils.config import get_config
        config = get_config()
    
    # Use provider from config if not specified
    if provider is None:
        provider = config.search_provider
    
    logger.info(
        f"Creating search strategy",
        extra={"context": {"provider": provider}}
    )
    
    # Create strategy based on provider
    if provider == "exa":
        if not config.exa_api_key:
            raise ValueError("EXA_API_KEY is required for Exa search strategy")
        return ExaSearchStrategy(api_key=config.exa_api_key)
    
    elif provider == "tavily":
        if not config.tavily_api_key:
            raise ValueError("TAVILY_API_KEY is required for Tavily search strategy")
        return TavilySearchStrategy(api_key=config.tavily_api_key)
    
    elif provider == "firecrawl":
        if not config.firecrawl_api_key:
            raise ValueError("FIRECRAWL_API_KEY is required for Firecrawl search strategy")
        return FirecrawlSearchStrategy(api_key=config.firecrawl_api_key)
    
    elif provider == "parallel":
        if not config.parallel_api_key:
            raise ValueError("PARALLEL_API_KEY is required for Parallel AI search strategy")
        # Optionally pass Firecrawl API key for image search
        return ParallelSearchStrategy(
            api_key=config.parallel_api_key,
            firecrawl_api_key=config.firecrawl_api_key
        )
    
    else:
        raise ValueError(
            f"Invalid search provider: {provider}. "
            f"Must be one of: exa, tavily, firecrawl, parallel"
        )


def create_fallback_strategy(
    primary_provider: str,
    config: Optional[Config] = None
) -> SearchStrategy:
    """
    Create a fallback search strategy for content retrieval.
    
    The fallback strategy is used when the primary strategy fails to retrieve content.
    By default, Firecrawl is used as the fallback for all providers.
    
    Args:
        primary_provider: Primary search provider name
        config: Configuration object. If None, loads from environment
        
    Returns:
        SearchStrategy instance to use as fallback
        
    Raises:
        ValueError: If fallback API key is missing
        
    Example:
        >>> primary = create_search_strategy("exa")
        >>> fallback = create_fallback_strategy("exa")
        >>> enriched = await enrich_with_content(results, primary, fallback)
    """
    # Load config if not provided
    if config is None:
        from research_agent.utils.config import get_config
        config = get_config()
    
    logger.info(
        f"Creating fallback strategy",
        extra={"context": {"primary_provider": primary_provider}}
    )
    
    # Use Firecrawl as the default fallback for all providers
    # (Firecrawl has good content extraction capabilities)
    if primary_provider != "firecrawl":
        if config.firecrawl_api_key:
            return FirecrawlSearchStrategy(api_key=config.firecrawl_api_key)
    
    # If primary is Firecrawl or Firecrawl is not available, try Exa
    if config.exa_api_key:
        return ExaSearchStrategy(api_key=config.exa_api_key)
    
    # If Exa is not available, try Parallel AI
    if config.parallel_api_key:
        return ParallelSearchStrategy(
            api_key=config.parallel_api_key,
            firecrawl_api_key=None
        )
    
    # If no fallback is available, raise an error
    raise ValueError(
        "No fallback strategy available. At least one of FIRECRAWL_API_KEY, "
        "EXA_API_KEY, or PARALLEL_API_KEY must be configured."
    )


def get_search_strategy(config: Optional[Config] = None) -> SearchStrategy:
    """
    Get the configured search strategy instance.
    
    This is a convenience function that creates a strategy based on the
    configuration's search_provider setting.
    
    Args:
        config: Configuration object. If None, loads from environment
        
    Returns:
        SearchStrategy instance
        
    Example:
        >>> strategy = get_search_strategy()
        >>> results = await strategy.search("quantum computing")
    """
    return create_search_strategy(provider=None, config=config)
