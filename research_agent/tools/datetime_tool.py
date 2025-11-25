"""DateTime operations tool for timezone conversion, duration calculations, and formatting."""

from typing import Literal, Optional
from datetime import datetime, timedelta
from langchain_core.tools import tool
import pytz

from research_agent.utils.logger import get_logger

logger = get_logger(__name__)


@tool
async def datetime_operations(
    operation: Literal["convert_timezone", "calculate_duration", "format_date", "current_time"],
    datetime_str: Optional[str] = None,
    from_timezone: Optional[str] = None,
    to_timezone: Optional[str] = None,
    start_datetime: Optional[str] = None,
    end_datetime: Optional[str] = None,
    format_string: Optional[str] = None,
    timezone: Optional[str] = None
) -> dict:
    """
    Perform various datetime operations including timezone conversion, duration calculations, and formatting.
    
    This tool supports multiple datetime operations:
    - convert_timezone: Convert datetime from one timezone to another
    - calculate_duration: Calculate duration between two datetimes
    - format_date: Format a datetime string in a specific format
    - current_time: Get current time in a specific timezone
    
    Args:
        operation: Type of operation to perform
        datetime_str: DateTime string (ISO format recommended, e.g., "2024-01-15T10:30:00")
        from_timezone: Source timezone (e.g., "America/New_York", "UTC")
        to_timezone: Target timezone (e.g., "Europe/London", "Asia/Tokyo")
        start_datetime: Start datetime for duration calculation
        end_datetime: End datetime for duration calculation
        format_string: Python strftime format string (e.g., "%Y-%m-%d %H:%M:%S")
        timezone: Timezone for current_time operation
        
    Returns:
        Dictionary containing operation results or error message
        
    Examples:
        >>> # Convert timezone
        >>> result = await datetime_operations(
        ...     operation="convert_timezone",
        ...     datetime_str="2024-01-15T10:30:00",
        ...     from_timezone="America/New_York",
        ...     to_timezone="Europe/London"
        ... )
        
        >>> # Calculate duration
        >>> result = await datetime_operations(
        ...     operation="calculate_duration",
        ...     start_datetime="2024-01-15T10:00:00",
        ...     end_datetime="2024-01-15T14:30:00"
        ... )
        
        >>> # Format date
        >>> result = await datetime_operations(
        ...     operation="format_date",
        ...     datetime_str="2024-01-15T10:30:00",
        ...     format_string="%B %d, %Y at %I:%M %p"
        ... )
        
        >>> # Get current time
        >>> result = await datetime_operations(
        ...     operation="current_time",
        ...     timezone="Asia/Tokyo"
        ... )
    """
    logger.info(
        f"Performing datetime operation",
        extra={"context": {"operation": operation}}
    )
    
    try:
        if operation == "convert_timezone":
            return await _convert_timezone(datetime_str, from_timezone, to_timezone)
        elif operation == "calculate_duration":
            return await _calculate_duration(start_datetime, end_datetime)
        elif operation == "format_date":
            return await _format_date(datetime_str, format_string, timezone)
        elif operation == "current_time":
            return await _get_current_time(timezone)
        else:
            return {"error": f"Unknown operation: {operation}"}
            
    except Exception as e:
        logger.error(
            f"DateTime operation failed: {e}",
            exc_info=True,
            extra={"context": {"operation": operation, "error": str(e)}}
        )
        return {"error": f"Operation failed: {str(e)}"}


async def _convert_timezone(
    datetime_str: Optional[str],
    from_timezone: Optional[str],
    to_timezone: Optional[str]
) -> dict:
    """Convert datetime from one timezone to another."""
    if not datetime_str or not from_timezone or not to_timezone:
        return {"error": "datetime_str, from_timezone, and to_timezone are required"}
    
    try:
        # Parse datetime
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        
        # Get timezones
        from_tz = pytz.timezone(from_timezone)
        to_tz = pytz.timezone(to_timezone)
        
        # Localize to source timezone if naive
        if dt.tzinfo is None:
            dt = from_tz.localize(dt)
        else:
            dt = dt.astimezone(from_tz)
        
        # Convert to target timezone
        converted_dt = dt.astimezone(to_tz)
        
        logger.info(
            f"Timezone conversion successful",
            extra={"context": {
                "from": f"{datetime_str} ({from_timezone})",
                "to": f"{converted_dt.isoformat()} ({to_timezone})"
            }}
        )
        
        return {
            "operation": "convert_timezone",
            "original_datetime": datetime_str,
            "original_timezone": from_timezone,
            "converted_datetime": converted_dt.isoformat(),
            "converted_timezone": to_timezone,
            "formatted": converted_dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        }
        
    except pytz.exceptions.UnknownTimeZoneError as e:
        return {"error": f"Unknown timezone: {str(e)}"}
    except ValueError as e:
        return {"error": f"Invalid datetime format: {str(e)}"}


async def _calculate_duration(
    start_datetime: Optional[str],
    end_datetime: Optional[str]
) -> dict:
    """Calculate duration between two datetimes."""
    if not start_datetime or not end_datetime:
        return {"error": "start_datetime and end_datetime are required"}
    
    try:
        # Parse datetimes
        start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
        
        # Calculate duration
        duration = end_dt - start_dt
        
        # Break down duration
        total_seconds = int(duration.total_seconds())
        days = duration.days
        hours = total_seconds // 3600 % 24
        minutes = total_seconds // 60 % 60
        seconds = total_seconds % 60
        
        # Create human-readable string
        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds > 0 or not parts:
            parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
        
        human_readable = ", ".join(parts)
        
        logger.info(
            f"Duration calculation successful",
            extra={"context": {
                "start": start_datetime,
                "end": end_datetime,
                "duration": human_readable
            }}
        )
        
        return {
            "operation": "calculate_duration",
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "duration": {
                "days": days,
                "hours": hours,
                "minutes": minutes,
                "seconds": seconds,
                "total_seconds": total_seconds,
                "human_readable": human_readable
            }
        }
        
    except ValueError as e:
        return {"error": f"Invalid datetime format: {str(e)}"}


async def _format_date(
    datetime_str: Optional[str],
    format_string: Optional[str],
    timezone: Optional[str]
) -> dict:
    """Format a datetime string in a specific format."""
    if not datetime_str:
        return {"error": "datetime_str is required"}
    
    # Default format if not provided
    if not format_string:
        format_string = "%Y-%m-%d %H:%M:%S"
    
    try:
        # Parse datetime
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        
        # Apply timezone if provided
        if timezone:
            tz = pytz.timezone(timezone)
            if dt.tzinfo is None:
                dt = tz.localize(dt)
            else:
                dt = dt.astimezone(tz)
        
        # Format datetime
        formatted = dt.strftime(format_string)
        
        logger.info(
            f"Date formatting successful",
            extra={"context": {
                "original": datetime_str,
                "formatted": formatted,
                "format": format_string
            }}
        )
        
        return {
            "operation": "format_date",
            "original_datetime": datetime_str,
            "formatted_datetime": formatted,
            "format_string": format_string,
            "timezone": timezone
        }
        
    except ValueError as e:
        return {"error": f"Invalid datetime or format string: {str(e)}"}
    except pytz.exceptions.UnknownTimeZoneError as e:
        return {"error": f"Unknown timezone: {str(e)}"}


async def _get_current_time(timezone: Optional[str]) -> dict:
    """Get current time in a specific timezone."""
    try:
        # Get current time
        now = datetime.now(pytz.UTC)
        
        # Apply timezone if provided
        if timezone:
            tz = pytz.timezone(timezone)
            now = now.astimezone(tz)
            tz_name = timezone
        else:
            tz_name = "UTC"
        
        logger.info(
            f"Current time retrieved",
            extra={"context": {
                "timezone": tz_name,
                "time": now.isoformat()
            }}
        )
        
        return {
            "operation": "current_time",
            "timezone": tz_name,
            "datetime": now.isoformat(),
            "formatted": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "timestamp": int(now.timestamp())
        }
        
    except pytz.exceptions.UnknownTimeZoneError as e:
        return {"error": f"Unknown timezone: {str(e)}"}
