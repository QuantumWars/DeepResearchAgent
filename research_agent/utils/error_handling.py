"""Error handling utilities for tools and API clients."""

from typing import TypeVar, Callable, Any, Dict, Optional
from functools import wraps
import httpx

from research_agent.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


def safe_tool_execution(default_return: Optional[Dict[str, Any]] = None):
    """Decorator to wrap tool execution with comprehensive error handling.
    
    This decorator ensures that tools never raise exceptions to the agent,
    instead returning error information in the result dictionary.
    
    Args:
        default_return: Default return value on error (if None, returns {"error": ...})
        
    Returns:
        Decorated function that catches all exceptions
        
    Example:
        @tool
        @safe_tool_execution()
        async def my_tool(param: str) -> dict:
            # Tool implementation
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Dict[str, Any]:
            tool_name = func.__name__
            
            try:
                result = await func(*args, **kwargs)
                return result
                
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP error {e.response.status_code}"
                
                # Provide more specific error messages
                if e.response.status_code == 400:
                    error_msg = "Bad request - check input parameters"
                elif e.response.status_code == 401:
                    error_msg = "Authentication failed - check API key"
                elif e.response.status_code == 403:
                    error_msg = "Access forbidden - check API permissions"
                elif e.response.status_code == 404:
                    error_msg = "Resource not found"
                elif e.response.status_code == 429:
                    error_msg = "Rate limit exceeded - try again later"
                elif e.response.status_code >= 500:
                    error_msg = f"Server error ({e.response.status_code}) - try again later"
                
                logger.error(
                    f"HTTP error in {tool_name}: {error_msg}",
                    exc_info=True,
                    extra={"context": {
                        "tool": tool_name,
                        "status_code": e.response.status_code,
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    }}
                )
                
                if default_return:
                    return {**default_return, "error": error_msg}
                return {"error": error_msg}
                
            except httpx.TimeoutException as e:
                error_msg = "Request timed out - try again later"
                logger.error(
                    f"Timeout in {tool_name}",
                    exc_info=True,
                    extra={"context": {
                        "tool": tool_name,
                        "error": str(e),
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    }}
                )
                
                if default_return:
                    return {**default_return, "error": error_msg}
                return {"error": error_msg}
                
            except httpx.ConnectError as e:
                error_msg = "Connection failed - check network connectivity"
                logger.error(
                    f"Connection error in {tool_name}",
                    exc_info=True,
                    extra={"context": {
                        "tool": tool_name,
                        "error": str(e),
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    }}
                )
                
                if default_return:
                    return {**default_return, "error": error_msg}
                return {"error": error_msg}
                
            except httpx.RequestError as e:
                error_msg = f"Request failed: {str(e)}"
                logger.error(
                    f"Request error in {tool_name}",
                    exc_info=True,
                    extra={"context": {
                        "tool": tool_name,
                        "error": str(e),
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    }}
                )
                
                if default_return:
                    return {**default_return, "error": error_msg}
                return {"error": error_msg}
                
            except ValueError as e:
                error_msg = f"Invalid input: {str(e)}"
                logger.error(
                    f"Validation error in {tool_name}",
                    exc_info=True,
                    extra={"context": {
                        "tool": tool_name,
                        "error": str(e),
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    }}
                )
                
                if default_return:
                    return {**default_return, "error": error_msg}
                return {"error": error_msg}
                
            except KeyError as e:
                error_msg = f"Missing required data: {str(e)}"
                logger.error(
                    f"Key error in {tool_name}",
                    exc_info=True,
                    extra={"context": {
                        "tool": tool_name,
                        "error": str(e),
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    }}
                )
                
                if default_return:
                    return {**default_return, "error": error_msg}
                return {"error": error_msg}
                
            except ImportError as e:
                error_msg = f"Missing dependency: {str(e)}"
                logger.error(
                    f"Import error in {tool_name}",
                    exc_info=True,
                    extra={"context": {
                        "tool": tool_name,
                        "error": str(e),
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    }}
                )
                
                if default_return:
                    return {**default_return, "error": error_msg}
                return {"error": error_msg}
                
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(
                    f"Unexpected error in {tool_name}",
                    exc_info=True,
                    extra={"context": {
                        "tool": tool_name,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    }}
                )
                
                if default_return:
                    return {**default_return, "error": error_msg}
                return {"error": error_msg}
        
        return wrapper
    
    return decorator


def validate_api_key(api_key: Optional[str], service_name: str) -> None:
    """Validate that an API key is present.
    
    Args:
        api_key: API key to validate
        service_name: Name of the service (for error message)
        
    Raises:
        ValueError: If API key is missing or empty
    """
    if not api_key or not api_key.strip():
        raise ValueError(
            f"{service_name} API key not configured. "
            f"Set the appropriate environment variable."
        )


def handle_api_response_error(response: httpx.Response, service_name: str) -> None:
    """Handle API response errors with detailed logging.
    
    Args:
        response: HTTP response object
        service_name: Name of the service (for logging)
        
    Raises:
        httpx.HTTPStatusError: If response has error status
    """
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        # Try to extract error message from response
        error_detail = ""
        try:
            error_data = response.json()
            if isinstance(error_data, dict):
                error_detail = error_data.get("error", error_data.get("message", ""))
        except Exception:
            error_detail = response.text[:200]
        
        logger.error(
            f"{service_name} API error",
            extra={"context": {
                "service": service_name,
                "status_code": response.status_code,
                "error_detail": error_detail,
                "url": str(response.url)
            }}
        )
        raise


def create_error_response(
    error_message: str,
    **additional_fields
) -> Dict[str, Any]:
    """Create a standardized error response dictionary.
    
    Args:
        error_message: Error message to include
        **additional_fields: Additional fields to include in response
        
    Returns:
        Dictionary with error field and any additional fields
    """
    return {
        "error": error_message,
        **additional_fields
    }


def log_tool_execution(
    tool_name: str,
    operation: str,
    success: bool,
    **context
) -> None:
    """Log tool execution with consistent format.
    
    Args:
        tool_name: Name of the tool
        operation: Operation being performed
        success: Whether operation was successful
        **context: Additional context to log
    """
    log_level = "info" if success else "error"
    message = f"{tool_name}: {operation} {'succeeded' if success else 'failed'}"
    
    log_context = {
        "tool": tool_name,
        "operation": operation,
        "success": success,
        **context
    }
    
    if log_level == "info":
        logger.info(message, extra={"context": log_context})
    else:
        logger.error(message, extra={"context": log_context})
