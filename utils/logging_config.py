"""Structured logging configuration for the Deep Research Framework.

This module provides a centralized logging setup with consistent formatting
across all components of the framework.
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: Optional[str] = None,
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up and configure a logger with structured formatting.
    
    Creates a logger with consistent formatting across the framework:
    [timestamp] [level] [component] message
    
    Args:
        name: Logger name (typically __name__ of the calling module).
              If None, returns the root logger.
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Default is INFO.
        log_file: Optional file path to write logs to. If None, logs only
                  to console.
    
    Returns:
        Configured logger instance
    
    Examples:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Starting research workflow")
        [2024-11-14 10:30:15] [INFO] [core.orchestrator] Starting research workflow
        
        >>> logger = setup_logger(__name__, level=logging.DEBUG)
        >>> logger.debug("Detailed debug information")
        
        >>> logger = setup_logger(__name__, log_file="research.log")
        >>> logger.info("This will be written to file and console")
    
    Requirements: 11.5
    """
    # Get or create logger
    logger = logging.getLogger(name) if name else logging.getLogger()
    
    # Avoid adding duplicate handlers if logger already configured
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Create formatter with structured format
    # Format: [timestamp] [level] [component] message
    formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Failed to create file handler for {log_file}: {e}")
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    return logger


def set_log_level(logger: logging.Logger, level: int) -> None:
    """
    Change the log level of an existing logger and all its handlers.
    
    Args:
        logger: Logger instance to modify
        level: New logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Examples:
        >>> logger = setup_logger(__name__)
        >>> set_log_level(logger, logging.DEBUG)
    """
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger by name or create a new one with default settings.
    
    This is a convenience function that ensures consistent logger configuration
    across the framework.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
    
    Returns:
        Logger instance
    
    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.info("Using default logger configuration")
    """
    logger = logging.getLogger(name)
    
    # If logger has no handlers, set it up with defaults
    if not logger.handlers:
        return setup_logger(name)
    
    return logger
