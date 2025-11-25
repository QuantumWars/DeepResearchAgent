"""Structured logging infrastructure for the research agent."""

import logging
import sys
from typing import Any, Callable, Optional
from functools import wraps
from datetime import datetime
import json


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra context if available
        if hasattr(record, "context"):
            log_data["context"] = record.context
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName", "relativeCreated",
                "thread", "threadName", "exc_info", "exc_text", "stack_info",
                "context"
            ]:
                log_data[key] = value
        
        return json.dumps(log_data)


class SimpleFormatter(logging.Formatter):
    """Simple human-readable formatter for development."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as simple text."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        message = record.getMessage()
        
        # Add context if available
        context_str = ""
        if hasattr(record, "context"):
            context_items = [f"{k}={v}" for k, v in record.context.items()]
            context_str = f" [{', '.join(context_items)}]"
        
        log_line = f"{timestamp} | {record.levelname:8} | {record.name:30} | {message}{context_str}"
        
        # Add exception if present
        if record.exc_info:
            log_line += "\n" + self.formatException(record.exc_info)
        
        return log_line


def setup_logging(
    level: str = "INFO",
    structured: bool = False,
    logger_name: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        structured: If True, use JSON structured logging
        logger_name: Name of the logger to configure (None for root logger)
    
    Returns:
        Configured logger instance
    """
    # Get or create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))
    
    # Set formatter
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = SimpleFormatter()
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Prevent propagation to root logger if this is a named logger
    if logger_name:
        logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_function_call(logger: Optional[logging.Logger] = None):
    """
    Decorator to log function entry and exit.
    
    Args:
        logger: Logger instance to use (if None, creates one from function module)
    
    Example:
        @log_function_call()
        def my_function(arg1, arg2):
            return arg1 + arg2
    """
    def decorator(func: Callable) -> Callable:
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = func.__qualname__
            logger.debug(
                f"Entering {func_name}",
                extra={"context": {"args": str(args)[:100], "kwargs": str(kwargs)[:100]}}
            )
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Exiting {func_name}")
                return result
            except Exception as e:
                logger.error(
                    f"Exception in {func_name}: {str(e)}",
                    exc_info=True,
                    extra={"context": {"function": func_name}}
                )
                raise
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = func.__qualname__
            logger.debug(
                f"Entering {func_name}",
                extra={"context": {"args": str(args)[:100], "kwargs": str(kwargs)[:100]}}
            )
            try:
                result = await func(*args, **kwargs)
                logger.debug(f"Exiting {func_name}")
                return result
            except Exception as e:
                logger.error(
                    f"Exception in {func_name}: {str(e)}",
                    exc_info=True,
                    extra={"context": {"function": func_name}}
                )
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_with_context(logger: logging.Logger, level: str, message: str, **context):
    """
    Log a message with additional context.
    
    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error)
        message: Log message
        **context: Additional context key-value pairs
    """
    log_func = getattr(logger, level.lower())
    log_func(message, extra={"context": context})
