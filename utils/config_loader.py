"""Configuration loader with environment variable substitution.

This module provides utilities for loading and validating YAML configuration files
with support for environment variable substitution using the 'env:VAR_NAME' pattern.

Requirements: 3.1, 3.4
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """
    Raised when configuration is invalid or missing.
    
    This exception is raised when:
    - Configuration file is not found
    - YAML syntax is invalid
    - Required configuration sections are missing
    - Required fields within sections are missing
    """
    pass


def load_config(config_path: str = "config/tool_config.yaml") -> Dict[str, Any]:
    """
    Load and parse YAML configuration file with environment variable substitution.
    
    This function:
    1. Loads the YAML configuration file
    2. Substitutes environment variables (env:VAR_NAME pattern)
    3. Validates required configuration sections
    4. Returns the parsed configuration dictionary
    
    Args:
        config_path: Path to the YAML configuration file (default: config/tool_config.yaml)
        
    Returns:
        Dictionary containing parsed configuration with environment variables substituted
        
    Raises:
        ConfigurationError: If config file is missing, malformed, or invalid
        
    Examples:
        >>> config = load_config("config/tool_config.yaml")
        >>> api_key = config["search_tools"]["tavily"]["api_key"]
        >>> # api_key will contain the actual value from TAVILY_API_KEY env var
        
        >>> config = load_config("custom_config.yaml")
        >>> max_loops = config["workflow"]["max_loops"]
    
    Requirements: 3.1, 3.4
    """
    config_file = Path(config_path)
    
    # Handle missing configuration file
    if not config_file.exists():
        logger.error(f"Configuration file not found: {config_path}")
        raise ConfigurationError(
            f"Configuration file not found: {config_path}. "
            f"Please create a configuration file or use the default path."
        )
    
    # Load YAML file
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML configuration: {e}")
        raise ConfigurationError(
            f"Malformed YAML configuration in {config_path}: {e}"
        )
    except Exception as e:
        logger.error(f"Failed to read configuration file: {e}")
        raise ConfigurationError(
            f"Failed to read configuration file {config_path}: {e}"
        )
    
    if config is None:
        logger.error(f"Configuration file is empty: {config_path}")
        raise ConfigurationError(f"Configuration file is empty: {config_path}")
    
    # Substitute environment variables
    config = _substitute_env_vars(config)
    
    # Validate required fields
    _validate_config(config)
    
    logger.info(f"Successfully loaded configuration from {config_path}")
    return config


def _substitute_env_vars(config: Any) -> Any:
    """
    Recursively substitute environment variables in configuration.
    
    Traverses the configuration structure (dicts, lists, strings) and replaces
    any string matching the pattern 'env:VAR_NAME' with the value of the
    environment variable VAR_NAME.
    
    Supports the pattern: env:VAR_NAME
    Example: api_key: env:TAVILY_API_KEY
    
    Args:
        config: Configuration dictionary, list, string, or other value
        
    Returns:
        Configuration with environment variables substituted. If an environment
        variable is not found, it is replaced with None and a warning is logged.
    
    Examples:
        >>> os.environ['MY_KEY'] = 'secret123'
        >>> _substitute_env_vars({'key': 'env:MY_KEY'})
        {'key': 'secret123'}
        
        >>> _substitute_env_vars(['env:VAR1', 'env:VAR2'])
        [value1, value2]  # where value1 and value2 are from environment
    
    Requirements: 3.4
    """
    if isinstance(config, dict):
        return {key: _substitute_env_vars(value) for key, value in config.items()}
    elif isinstance(config, list):
        return [_substitute_env_vars(item) for item in config]
    elif isinstance(config, str):
        # Check for env:VAR_NAME pattern
        env_pattern = r'^env:([A-Z_][A-Z0-9_]*)$'
        match = re.match(env_pattern, config)
        if match:
            env_var = match.group(1)
            value = os.getenv(env_var)
            if value is None:
                logger.warning(
                    f"Environment variable {env_var} not found, using None"
                )
            return value
        return config
    else:
        return config


def _validate_config(config: Dict[str, Any]) -> None:
    """
    Validate that required configuration fields are present.
    
    Checks for:
    - Required top-level sections (search_tools, scraper_tools, llm_tools)
    - Fallback chains in search_tools and scraper_tools
    - Model routing in llm_tools (fast, balanced, powerful)
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ConfigurationError: If required fields are missing or invalid
    
    Requirements: 3.1, 3.2, 3.3
    """
    required_sections = ["search_tools", "scraper_tools", "llm_tools"]
    
    for section in required_sections:
        if section not in config:
            logger.error(f"Missing required configuration section: {section}")
            raise ConfigurationError(
                f"Configuration missing required section: {section}"
            )
    
    # Validate search_tools section
    if "fallback_chain" not in config["search_tools"]:
        logger.error("Missing fallback_chain in search_tools section")
        raise ConfigurationError(
            "search_tools section must include 'fallback_chain'"
        )
    
    # Validate scraper_tools section
    if "fallback_chain" not in config["scraper_tools"]:
        logger.error("Missing fallback_chain in scraper_tools section")
        raise ConfigurationError(
            "scraper_tools section must include 'fallback_chain'"
        )
    
    # Validate llm_tools section
    if "routing" not in config["llm_tools"]:
        logger.error("Missing routing in llm_tools section")
        raise ConfigurationError(
            "llm_tools section must include 'routing' with fast/balanced/powerful models"
        )
    
    routing = config["llm_tools"]["routing"]
    required_model_types = ["fast", "balanced", "powerful"]
    for model_type in required_model_types:
        if model_type not in routing:
            logger.error(f"Missing {model_type} model in llm_tools routing")
            raise ConfigurationError(
                f"llm_tools routing must include '{model_type}' model"
            )
    
    logger.debug("Configuration validation passed")


def get_tool_config(
    config: Dict[str, Any],
    category: str,
    tool_name: str
) -> Optional[Dict[str, Any]]:
    """
    Get configuration for a specific tool.
    
    Retrieves the configuration dictionary for a specific tool within a category.
    
    Args:
        config: Full configuration dictionary loaded from YAML
        category: Tool category (e.g., 'search_tools', 'scraper_tools', 'llm_tools')
        tool_name: Name of the tool (e.g., 'tavily', 'trafilatura')
        
    Returns:
        Tool configuration dictionary containing enabled, priority, api_key, and
        extra_params fields, or None if the category or tool is not found
    
    Examples:
        >>> config = load_config()
        >>> tavily_config = get_tool_config(config, 'search_tools', 'tavily')
        >>> tavily_config['priority']
        10
        
        >>> missing = get_tool_config(config, 'search_tools', 'nonexistent')
        >>> missing is None
        True
    """
    if category not in config:
        return None
    
    if tool_name not in config[category]:
        return None
    
    return config[category][tool_name]
