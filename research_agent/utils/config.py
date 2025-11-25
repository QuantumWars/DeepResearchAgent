"""Configuration management for the research agent."""

import os
from typing import Optional, Literal, List, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Configuration loaded from environment variables."""
    
    # LLM Configuration
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    
    # Search Provider API Keys
    exa_api_key: Optional[str] = Field(default=None, alias="EXA_API_KEY")
    tavily_api_key: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")
    firecrawl_api_key: Optional[str] = Field(default=None, alias="FIRECRAWL_API_KEY")
    parallel_api_key: Optional[str] = Field(default=None, alias="PARALLEL_API_KEY")
    
    # New Tool API Keys
    xai_api_key: Optional[str] = Field(default=None, alias="XAI_API_KEY")
    openweather_api_key: Optional[str] = Field(default=None, alias="OPENWEATHER_API_KEY")
    aviationstack_api_key: Optional[str] = Field(default=None, alias="AVIATIONSTACK_API_KEY")
    alphavantage_api_key: Optional[str] = Field(default=None, alias="ALPHAVANTAGE_API_KEY")
    coingecko_api_key: Optional[str] = Field(default=None, alias="COINGECKO_API_KEY")
    google_maps_api_key: Optional[str] = Field(default=None, alias="GOOGLE_MAPS_API_KEY")
    
    # Memory Configuration
    supermemory_api_key: Optional[str] = Field(default=None, alias="SUPERMEMORY_API_KEY")
    supermemory_base_url: str = Field(
        default="https://api.supermemory.ai",
        alias="SUPERMEMORY_BASE_URL"
    )
    
    # Code Execution
    daytona_api_key: Optional[str] = Field(default=None, alias="DAYTONA_API_KEY")
    
    # Application Configuration
    search_provider: Literal["exa", "tavily", "firecrawl", "parallel"] = Field(
        default="exa",
        alias="SEARCH_PROVIDER"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        alias="LOG_LEVEL"
    )
    max_research_tasks: int = Field(default=15, alias="MAX_RESEARCH_TASKS", ge=1, le=20)
    max_search_results: int = Field(default=8, alias="MAX_SEARCH_RESULTS", ge=1, le=20)
    max_tool_calls: int = Field(default=15, alias="MAX_TOOL_CALLS", ge=1, le=30)
    content_max_chars: int = Field(default=3000, alias="CONTENT_MAX_CHARS", ge=100, le=10000)
    
    # Tool Configuration
    enabled_tools: str = Field(
        default="web_search,code_executor,memory_search",
        alias="ENABLED_TOOLS"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def enabled_tools_list(self) -> List[str]:
        """Get enabled_tools as a list.
        
        Returns:
            List of enabled tool names
        """
        if isinstance(self.enabled_tools, str):
            return [tool.strip() for tool in self.enabled_tools.split(",") if tool.strip()]
        return self.enabled_tools
    
    @field_validator("search_provider")
    @classmethod
    def validate_search_provider_key(cls, v: str, info) -> str:
        """Validate that the API key for the selected search provider exists."""
        # Note: This validation happens after all fields are set
        # We'll do runtime validation in validate_config method
        return v
    
    def validate_config(self) -> None:
        """Validate configuration at startup.
        
        Validates that required API keys are present based on:
        - LLM provider selection
        - Search provider selection
        - Enabled tools configuration
        """
        errors = []
        
        # Validate LLM API key
        if not self.openai_api_key and not self.anthropic_api_key:
            errors.append("At least one LLM API key (OPENAI_API_KEY or ANTHROPIC_API_KEY) is required")
        
        # Validate search provider API key
        provider_key_map = {
            "exa": self.exa_api_key,
            "tavily": self.tavily_api_key,
            "firecrawl": self.firecrawl_api_key,
            "parallel": self.parallel_api_key,
        }
        
        if not provider_key_map.get(self.search_provider):
            errors.append(
                f"API key for search provider '{self.search_provider}' is required. "
                f"Set {self.search_provider.upper()}_API_KEY environment variable."
            )
        
        # Validate API keys for enabled tools
        enabled_tools = self.enabled_tools_list
        tool_key_requirements = {
            "x_search": ("XAI_API_KEY", self.xai_api_key),
            "youtube_search": ("EXA_API_KEY", self.exa_api_key),  # Uses Exa
            "reddit_search": ("TAVILY_API_KEY", self.tavily_api_key),  # Uses Tavily
            "academic_search": ("EXA_API_KEY", self.exa_api_key),  # Uses Exa
            "get_weather": ("OPENWEATHER_API_KEY", self.openweather_api_key),
            "track_flight": ("AVIATIONSTACK_API_KEY", self.aviationstack_api_key),
            "get_stock_data": ("ALPHAVANTAGE_API_KEY", self.alphavantage_api_key),
            "get_crypto_data": ("COINGECKO_API_KEY", self.coingecko_api_key),
            "get_crypto_market_overview": ("COINGECKO_API_KEY", self.coingecko_api_key),
            "geocode_location": ("GOOGLE_MAPS_API_KEY", self.google_maps_api_key),
            "reverse_geocode": ("GOOGLE_MAPS_API_KEY", self.google_maps_api_key),
            "calculate_distance": ("GOOGLE_MAPS_API_KEY", self.google_maps_api_key),
        }
        
        for tool_name in enabled_tools:
            if tool_name in tool_key_requirements:
                key_name, key_value = tool_key_requirements[tool_name]
                if not key_value:
                    errors.append(
                        f"Tool '{tool_name}' is enabled but {key_name} is not set. "
                        f"Either set {key_name} or remove '{tool_name}' from ENABLED_TOOLS."
                    )
        
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
    
    @property
    def llm_provider(self) -> Literal["openai", "anthropic"]:
        """Determine which LLM provider to use based on available API keys."""
        if self.openai_api_key:
            return "openai"
        elif self.anthropic_api_key:
            return "anthropic"
        else:
            raise ValueError("No LLM API key configured")


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
        _config.validate_config()
    return _config


def reset_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global _config
    _config = None
