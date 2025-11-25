"""Retry utilities for API clients with exponential backoff and rate limiting."""

import asyncio
from typing import TypeVar, Callable, Optional, Any
from functools import wraps
import httpx

from research_agent.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0,
        exponential_base: float = 2.0,
        retry_on_timeout: bool = True,
        retry_on_connection_error: bool = True,
        retry_on_rate_limit: bool = True
    ):
        """Initialize retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_backoff: Initial backoff time in seconds
            max_backoff: Maximum backoff time in seconds
            exponential_base: Base for exponential backoff calculation
            retry_on_timeout: Whether to retry on timeout errors
            retry_on_connection_error: Whether to retry on connection errors
            retry_on_rate_limit: Whether to retry on rate limit (429) errors
        """
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.exponential_base = exponential_base
        self.retry_on_timeout = retry_on_timeout
        self.retry_on_connection_error = retry_on_connection_error
        self.retry_on_rate_limit = retry_on_rate_limit
    
    def calculate_backoff(self, attempt: int) -> float:
        """Calculate backoff time for given attempt number.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Backoff time in seconds
        """
        backoff = min(
            self.initial_backoff * (self.exponential_base ** attempt),
            self.max_backoff
        )
        return backoff


async def retry_async(
    func: Callable[..., T],
    *args,
    config: Optional[RetryConfig] = None,
    context: Optional[dict] = None,
    **kwargs
) -> T:
    """Execute an async function with retry logic.
    
    Args:
        func: Async function to execute
        *args: Positional arguments for the function
        config: Retry configuration (uses default if not provided)
        context: Additional context for logging
        **kwargs: Keyword arguments for the function
        
    Returns:
        Result from the function
        
    Raises:
        Exception: If all retries are exhausted
    """
    if config is None:
        config = RetryConfig()
    
    if context is None:
        context = {}
    
    last_exception = None
    
    for attempt in range(config.max_retries):
        try:
            result = await func(*args, **kwargs)
            
            if attempt > 0:
                logger.info(
                    f"Retry successful on attempt {attempt + 1}",
                    extra={"context": {**context, "attempt": attempt + 1}}
                )
            
            return result
            
        except httpx.TimeoutException as e:
            last_exception = e
            if not config.retry_on_timeout or attempt >= config.max_retries - 1:
                logger.error(
                    f"Timeout error, no more retries",
                    exc_info=True,
                    extra={"context": {**context, "attempt": attempt + 1, "error": str(e)}}
                )
                raise
            
            backoff = config.calculate_backoff(attempt)
            logger.warning(
                f"Timeout error on attempt {attempt + 1}, retrying in {backoff}s",
                extra={"context": {**context, "attempt": attempt + 1, "backoff": backoff}}
            )
            await asyncio.sleep(backoff)
            
        except httpx.ConnectError as e:
            last_exception = e
            if not config.retry_on_connection_error or attempt >= config.max_retries - 1:
                logger.error(
                    f"Connection error, no more retries",
                    exc_info=True,
                    extra={"context": {**context, "attempt": attempt + 1, "error": str(e)}}
                )
                raise
            
            backoff = config.calculate_backoff(attempt)
            logger.warning(
                f"Connection error on attempt {attempt + 1}, retrying in {backoff}s",
                extra={"context": {**context, "attempt": attempt + 1, "backoff": backoff}}
            )
            await asyncio.sleep(backoff)
            
        except httpx.HTTPStatusError as e:
            last_exception = e
            
            # Handle rate limiting (429)
            if e.response.status_code == 429:
                if not config.retry_on_rate_limit or attempt >= config.max_retries - 1:
                    logger.error(
                        f"Rate limit exceeded, no more retries",
                        extra={"context": {
                            **context,
                            "attempt": attempt + 1,
                            "status_code": e.response.status_code
                        }}
                    )
                    raise
                
                # Check for Retry-After header
                retry_after = e.response.headers.get("Retry-After")
                if retry_after:
                    try:
                        backoff = float(retry_after)
                    except ValueError:
                        backoff = config.calculate_backoff(attempt)
                else:
                    backoff = config.calculate_backoff(attempt)
                
                backoff = min(backoff, config.max_backoff)
                
                logger.warning(
                    f"Rate limited (429) on attempt {attempt + 1}, retrying in {backoff}s",
                    extra={"context": {
                        **context,
                        "attempt": attempt + 1,
                        "backoff": backoff,
                        "status_code": 429
                    }}
                )
                await asyncio.sleep(backoff)
            else:
                # Don't retry on other HTTP errors (4xx, 5xx)
                logger.error(
                    f"HTTP error {e.response.status_code}, not retrying",
                    extra={"context": {
                        **context,
                        "attempt": attempt + 1,
                        "status_code": e.response.status_code
                    }}
                )
                raise
                
        except httpx.RequestError as e:
            last_exception = e
            if attempt >= config.max_retries - 1:
                logger.error(
                    f"Request error, no more retries",
                    exc_info=True,
                    extra={"context": {**context, "attempt": attempt + 1, "error": str(e)}}
                )
                raise
            
            backoff = config.calculate_backoff(attempt)
            logger.warning(
                f"Request error on attempt {attempt + 1}, retrying in {backoff}s",
                extra={"context": {**context, "attempt": attempt + 1, "backoff": backoff}}
            )
            await asyncio.sleep(backoff)
    
    # If we get here, all retries were exhausted
    if last_exception:
        logger.error(
            f"All {config.max_retries} retry attempts exhausted",
            exc_info=last_exception,
            extra={"context": {**context, "max_retries": config.max_retries}}
        )
        raise last_exception
    
    raise Exception(f"Retry logic failed after {config.max_retries} attempts")


def with_retry(config: Optional[RetryConfig] = None):
    """Decorator to add retry logic to async functions.
    
    Args:
        config: Retry configuration (uses default if not provided)
        
    Returns:
        Decorated function with retry logic
        
    Example:
        @with_retry(RetryConfig(max_retries=5))
        async def fetch_data():
            # ... API call ...
            pass
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            context = {
                "function": func.__name__,
                "module": func.__module__
            }
            return await retry_async(func, *args, config=config, context=context, **kwargs)
        
        return wrapper
    
    return decorator
