"""Flight tracker tool using AviationStack API."""

from typing import Optional
from datetime import datetime
from langchain_core.tools import tool
import httpx

from research_agent.utils.logger import get_logger
from research_agent.utils.config import get_config

logger = get_logger(__name__)


@tool
async def track_flight(
    flight_number: str,
    date: Optional[str] = None
) -> dict:
    """
    Track flight status and information using AviationStack API.
    
    This tool retrieves real-time flight information including status, delays,
    departure/arrival times, gate information, and aircraft details.
    
    Args:
        flight_number: Flight number (e.g., "AA100", "BA456")
        date: Flight date in YYYY-MM-DD format (default: today)
        
    Returns:
        Dictionary containing:
        - flight: Flight identification information
        - status: Current flight status
        - departure: Departure information (airport, time, gate, terminal)
        - arrival: Arrival information (airport, time, gate, terminal)
        - aircraft: Aircraft information
        - airline: Airline information
        - error: Error message if request failed
        
    Examples:
        >>> result = await track_flight("AA100")
        >>> result = await track_flight("BA456", date="2024-01-15")
    """
    logger.info(
        f"Tracking flight",
        extra={"context": {
            "flight_number": flight_number,
            "date": date
        }}
    )
    
    try:
        config = get_config()
        api_key = config.aviationstack_api_key
        
        if not api_key:
            return {
                "error": "AviationStack API key not configured. Set AVIATIONSTACK_API_KEY environment variable."
            }
        
        # Use today's date if not provided
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Build API request
        url = "http://api.aviationstack.com/v1/flights"
        params = {
            "access_key": api_key,
            "flight_iata": flight_number.upper()
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if "error" in data:
                error_msg = data["error"].get("message", "Unknown API error")
                logger.error(
                    f"AviationStack API error: {error_msg}",
                    extra={"context": {"flight_number": flight_number}}
                )
                return {"error": f"API error: {error_msg}"}
            
            # Check if flight found
            if not data.get("data") or len(data["data"]) == 0:
                return {
                    "error": f"Flight {flight_number} not found. Check flight number and try again."
                }
            
            # Get the most recent flight (first in list)
            flight_data = data["data"][0]
            
            # Parse flight information
            result = {
                "flight": {
                    "number": flight_data["flight"]["iata"],
                    "icao": flight_data["flight"].get("icao"),
                    "date": flight_data["flight_date"]
                },
                "status": flight_data["flight_status"],
                "departure": {
                    "airport": flight_data["departure"]["airport"],
                    "iata": flight_data["departure"]["iata"],
                    "icao": flight_data["departure"].get("icao"),
                    "terminal": flight_data["departure"].get("terminal"),
                    "gate": flight_data["departure"].get("gate"),
                    "scheduled": flight_data["departure"]["scheduled"],
                    "estimated": flight_data["departure"].get("estimated"),
                    "actual": flight_data["departure"].get("actual"),
                    "delay": flight_data["departure"].get("delay"),
                    "timezone": flight_data["departure"].get("timezone")
                },
                "arrival": {
                    "airport": flight_data["arrival"]["airport"],
                    "iata": flight_data["arrival"]["iata"],
                    "icao": flight_data["arrival"].get("icao"),
                    "terminal": flight_data["arrival"].get("terminal"),
                    "gate": flight_data["arrival"].get("gate"),
                    "baggage": flight_data["arrival"].get("baggage"),
                    "scheduled": flight_data["arrival"]["scheduled"],
                    "estimated": flight_data["arrival"].get("estimated"),
                    "actual": flight_data["arrival"].get("actual"),
                    "delay": flight_data["arrival"].get("delay"),
                    "timezone": flight_data["arrival"].get("timezone")
                },
                "airline": {
                    "name": flight_data["airline"]["name"],
                    "iata": flight_data["airline"]["iata"],
                    "icao": flight_data["airline"].get("icao")
                }
            }
            
            # Add aircraft info if available
            if flight_data.get("aircraft"):
                result["aircraft"] = {
                    "registration": flight_data["aircraft"].get("registration"),
                    "iata": flight_data["aircraft"].get("iata"),
                    "icao": flight_data["aircraft"].get("icao")
                }
            
            # Add live tracking info if available
            if flight_data.get("live"):
                result["live"] = {
                    "updated": flight_data["live"].get("updated"),
                    "latitude": flight_data["live"].get("latitude"),
                    "longitude": flight_data["live"].get("longitude"),
                    "altitude": flight_data["live"].get("altitude"),
                    "direction": flight_data["live"].get("direction"),
                    "speed_horizontal": flight_data["live"].get("speed_horizontal"),
                    "speed_vertical": flight_data["live"].get("speed_vertical")
                }
            
            logger.info(
                f"Flight tracking successful",
                extra={"context": {
                    "flight": flight_number,
                    "status": result["status"],
                    "route": f"{result['departure']['iata']} -> {result['arrival']['iata']}"
                }}
            )
            
            return result
            
    except httpx.HTTPStatusError as e:
        error_msg = f"Flight API error: {e.response.status_code}"
        if e.response.status_code == 401:
            error_msg = "Invalid API key"
        elif e.response.status_code == 403:
            error_msg = "API access forbidden - check subscription plan"
        
        logger.error(
            f"Flight tracking request failed: {error_msg}",
            extra={"context": {"flight_number": flight_number, "error": error_msg}}
        )
        return {"error": error_msg}
        
    except httpx.RequestError as e:
        logger.error(
            f"Flight tracking request failed: {e}",
            exc_info=True,
            extra={"context": {"flight_number": flight_number, "error": str(e)}}
        )
        return {"error": f"Request failed: {str(e)}"}
        
    except Exception as e:
        logger.error(
            f"Flight tracking failed: {e}",
            exc_info=True,
            extra={"context": {"flight_number": flight_number, "error": str(e)}}
        )
        return {"error": f"Failed to track flight: {str(e)}"}
