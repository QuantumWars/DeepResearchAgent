"""Weather tool using OpenWeatherMap API."""

from typing import Optional
from langchain_core.tools import tool
import httpx

from research_agent.utils.logger import get_logger
from research_agent.utils.config import get_config
from research_agent.utils.performance import cached

logger = get_logger(__name__)


@cached(ttl_seconds=1800)  # Cache for 30 minutes
async def _fetch_weather_data(
    location: str,
    forecast_days: int,
    units: str,
    api_key: str
) -> dict:
    """
    Internal function to fetch weather data with caching.
    
    Weather data is cached for 30 minutes to reduce API calls.
    """
    try:
        # Validate inputs
        forecast_days = max(0, min(forecast_days, 5))
        if units not in ["metric", "imperial", "standard"]:
            units = "metric"
        
        # Determine if location is coordinates or name
        is_coords = False
        try:
            parts = location.split(',')
            if len(parts) == 2:
                float(parts[0])
                float(parts[1])
                is_coords = True
        except ValueError:
            pass
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get current weather
            if is_coords:
                lat, lon = location.split(',')
                current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units={units}"
            else:
                current_url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units={units}"
            
            current_response = await client.get(current_url)
            current_response.raise_for_status()
            current_data = current_response.json()
            
            # Parse current weather
            current_weather = {
                "temperature": current_data["main"]["temp"],
                "feels_like": current_data["main"]["feels_like"],
                "temp_min": current_data["main"]["temp_min"],
                "temp_max": current_data["main"]["temp_max"],
                "pressure": current_data["main"]["pressure"],
                "humidity": current_data["main"]["humidity"],
                "conditions": current_data["weather"][0]["main"],
                "description": current_data["weather"][0]["description"],
                "wind_speed": current_data["wind"]["speed"],
                "wind_direction": current_data["wind"].get("deg"),
                "clouds": current_data["clouds"]["all"],
                "visibility": current_data.get("visibility"),
                "sunrise": current_data["sys"]["sunrise"],
                "sunset": current_data["sys"]["sunset"]
            }
            
            location_info = {
                "name": current_data["name"],
                "country": current_data["sys"]["country"],
                "coordinates": {
                    "lat": current_data["coord"]["lat"],
                    "lon": current_data["coord"]["lon"]
                }
            }
            
            result = {
                "location": location_info,
                "current": current_weather,
                "units": units
            }
            
            # Get forecast if requested
            if forecast_days > 0:
                lat = current_data["coord"]["lat"]
                lon = current_data["coord"]["lon"]
                forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units={units}"
                
                forecast_response = await client.get(forecast_url)
                forecast_response.raise_for_status()
                forecast_data = forecast_response.json()
                
                # Parse forecast (group by day)
                daily_forecasts = []
                current_day = None
                day_data = []
                
                for item in forecast_data["list"][:forecast_days * 8]:  # 8 forecasts per day (3-hour intervals)
                    dt = item["dt_txt"].split()[0]
                    
                    if dt != current_day:
                        if day_data:
                            daily_forecasts.append(_aggregate_day_forecast(current_day, day_data))
                        current_day = dt
                        day_data = [item]
                    else:
                        day_data.append(item)
                
                if day_data:
                    daily_forecasts.append(_aggregate_day_forecast(current_day, day_data))
                
                result["forecast"] = daily_forecasts[:forecast_days]
            
            # Check for weather alerts (using One Call API if available)
            # Note: One Call API requires separate subscription, so we'll skip alerts for now
            result["alerts"] = []
            
            return result
            
    except httpx.HTTPStatusError as e:
        error_msg = f"Weather API error: {e.response.status_code}"
        if e.response.status_code == 404:
            error_msg = f"Location '{location}' not found"
        elif e.response.status_code == 401:
            error_msg = "Invalid API key"
        
        logger.error(
            f"Weather request failed: {error_msg}",
            extra={"context": {"location": location, "error": error_msg}}
        )
        return {"error": error_msg}
        
    except httpx.RequestError as e:
        logger.error(
            f"Weather request failed: {e}",
            exc_info=True,
            extra={"context": {"location": location, "error": str(e)}}
        )
        return {"error": f"Request failed: {str(e)}"}
        
    except Exception as e:
        logger.error(
            f"Weather tool failed: {e}",
            exc_info=True,
            extra={"context": {"location": location, "error": str(e)}}
        )
        raise


@tool
async def get_weather(
    location: str,
    forecast_days: int = 1,
    units: str = "metric"
) -> dict:
    """
    Get current weather and forecast for a location using OpenWeatherMap API.
    
    This tool retrieves weather information including temperature, conditions,
    humidity, wind speed, and alerts for a specified location. Weather data
    is cached for 30 minutes to improve performance.
    
    Args:
        location: Location name (city name, city,country, or coordinates "lat,lon")
        forecast_days: Number of forecast days (1-5, default: 1)
        units: Temperature units - "metric" (Celsius), "imperial" (Fahrenheit), or "standard" (Kelvin)
        
    Returns:
        Dictionary containing:
        - location: Location information
        - current: Current weather conditions
        - forecast: Weather forecast (if forecast_days > 0)
        - alerts: Weather alerts if any
        - error: Error message if request failed
        
    Examples:
        >>> result = await get_weather("London")
        >>> result = await get_weather("New York,US", forecast_days=3)
        >>> result = await get_weather("51.5074,-0.1278", units="imperial")
    """
    logger.info(
        f"Getting weather data",
        extra={"context": {
            "location": location,
            "forecast_days": forecast_days,
            "units": units
        }}
    )
    
    try:
        config = get_config()
        api_key = config.openweather_api_key
        
        if not api_key:
            return {
                "error": "OpenWeatherMap API key not configured. Set OPENWEATHER_API_KEY environment variable."
            }
        
        result = await _fetch_weather_data(location, forecast_days, units, api_key)
        
        logger.info(
            f"Weather data retrieved successfully",
            extra={"context": {
                "location": result.get("location", {}).get("name", location),
                "temperature": result.get("current", {}).get("temperature"),
                "conditions": result.get("current", {}).get("conditions")
            }}
        )
        
        return result
        
    except Exception as e:
        logger.error(
            f"Weather tool failed: {e}",
            exc_info=True,
            extra={"context": {"location": location, "error": str(e)}}
        )
        return {"error": f"Failed to get weather: {str(e)}"}


def _aggregate_day_forecast(date: str, forecasts: list) -> dict:
    """Aggregate 3-hour forecasts into daily summary."""
    temps = [f["main"]["temp"] for f in forecasts]
    conditions = [f["weather"][0]["main"] for f in forecasts]
    
    # Find most common condition
    condition_counts = {}
    for cond in conditions:
        condition_counts[cond] = condition_counts.get(cond, 0) + 1
    most_common_condition = max(condition_counts, key=condition_counts.get)
    
    return {
        "date": date,
        "temp_min": min(temps),
        "temp_max": max(temps),
        "temp_avg": sum(temps) / len(temps),
        "conditions": most_common_condition,
        "description": forecasts[0]["weather"][0]["description"],
        "humidity": sum(f["main"]["humidity"] for f in forecasts) / len(forecasts),
        "wind_speed": sum(f["wind"]["speed"] for f in forecasts) / len(forecasts),
        "precipitation_probability": max(f.get("pop", 0) for f in forecasts) * 100
    }
