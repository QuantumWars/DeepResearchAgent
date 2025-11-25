"""Map and geocoding tools using OpenStreetMap Nominatim API."""

from typing import Optional, Literal
from langchain_core.tools import tool
import httpx
from urllib.parse import quote

from research_agent.utils.logger import get_logger
from research_agent.utils.config import get_config

logger = get_logger(__name__)


@tool
async def geocode_location(
    address: str,
    limit: int = 1
) -> dict:
    """
    Geocode an address to coordinates (latitude, longitude) using OpenStreetMap Nominatim.
    
    This tool converts a human-readable address into geographic coordinates.
    Uses the free OpenStreetMap Nominatim API (no API key required).
    
    Args:
        address: Address to geocode (e.g., "1600 Amphitheatre Parkway, Mountain View, CA")
        limit: Maximum number of results to return (default: 1, max: 10)
        
    Returns:
        Dictionary containing:
        - query: Original address query
        - results: List of geocoding results with coordinates and details
        - error: Error message if request failed
        
    Examples:
        >>> result = await geocode_location("Eiffel Tower, Paris")
        >>> result = await geocode_location("Times Square, New York", limit=3)
    """
    logger.info(
        f"Geocoding address",
        extra={"context": {"address": address}}
    )
    
    try:
        # Validate limit
        limit = max(1, min(limit, 10))
        
        # Use OpenStreetMap Nominatim (free, no API key required)
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": address,
            "format": "json",
            "limit": limit,
            "addressdetails": 1
        }
        
        # Nominatim requires a User-Agent header
        headers = {
            "User-Agent": "ResearchAgent/1.0"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return {
                    "query": address,
                    "results": [],
                    "error": f"No results found for address: {address}"
                }
            
            # Parse results
            results = []
            for item in data:
                result = {
                    "display_name": item["display_name"],
                    "latitude": float(item["lat"]),
                    "longitude": float(item["lon"]),
                    "type": item.get("type"),
                    "importance": item.get("importance"),
                    "address": {}
                }
                
                # Parse address components
                if "address" in item:
                    addr = item["address"]
                    result["address"] = {
                        "house_number": addr.get("house_number"),
                        "road": addr.get("road"),
                        "city": addr.get("city") or addr.get("town") or addr.get("village"),
                        "state": addr.get("state"),
                        "postcode": addr.get("postcode"),
                        "country": addr.get("country"),
                        "country_code": addr.get("country_code", "").upper()
                    }
                
                # Add bounding box if available
                if "boundingbox" in item:
                    bbox = item["boundingbox"]
                    result["bounding_box"] = {
                        "south": float(bbox[0]),
                        "north": float(bbox[1]),
                        "west": float(bbox[2]),
                        "east": float(bbox[3])
                    }
                
                results.append(result)
            
            logger.info(
                f"Geocoding successful",
                extra={"context": {
                    "address": address,
                    "results_count": len(results)
                }}
            )
            
            return {
                "query": address,
                "results": results,
                "count": len(results)
            }
            
    except httpx.HTTPStatusError as e:
        error_msg = f"Geocoding API error: {e.response.status_code}"
        if e.response.status_code == 429:
            error_msg = "Rate limit exceeded. Please wait before making more requests."
        
        logger.error(
            f"Geocoding request failed: {error_msg}",
            extra={"context": {"address": address, "error": error_msg}}
        )
        return {"query": address, "results": [], "error": error_msg}
        
    except httpx.RequestError as e:
        logger.error(
            f"Geocoding request failed: {e}",
            exc_info=True,
            extra={"context": {"address": address, "error": str(e)}}
        )
        return {"query": address, "results": [], "error": f"Request failed: {str(e)}"}
        
    except Exception as e:
        logger.error(
            f"Geocoding failed: {e}",
            exc_info=True,
            extra={"context": {"address": address, "error": str(e)}}
        )
        return {"query": address, "results": [], "error": f"Failed to geocode: {str(e)}"}


@tool
async def reverse_geocode(
    latitude: float,
    longitude: float,
    zoom: int = 18
) -> dict:
    """
    Reverse geocode coordinates to an address using OpenStreetMap Nominatim.
    
    This tool converts geographic coordinates (latitude, longitude) into a
    human-readable address. Uses the free OpenStreetMap Nominatim API.
    
    Args:
        latitude: Latitude coordinate (-90 to 90)
        longitude: Longitude coordinate (-180 to 180)
        zoom: Detail level (3=country, 10=city, 18=building, default: 18)
        
    Returns:
        Dictionary containing:
        - coordinates: Input coordinates
        - address: Reverse geocoded address
        - error: Error message if request failed
        
    Examples:
        >>> result = await reverse_geocode(48.8584, 2.2945)  # Eiffel Tower
        >>> result = await reverse_geocode(40.7580, -73.9855, zoom=10)  # Times Square
    """
    logger.info(
        f"Reverse geocoding coordinates",
        extra={"context": {
            "latitude": latitude,
            "longitude": longitude
        }}
    )
    
    try:
        # Validate coordinates
        if not (-90 <= latitude <= 90):
            return {"error": "Latitude must be between -90 and 90"}
        if not (-180 <= longitude <= 180):
            return {"error": "Longitude must be between -180 and 180"}
        
        # Validate zoom
        zoom = max(0, min(zoom, 18))
        
        # Use OpenStreetMap Nominatim
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": latitude,
            "lon": longitude,
            "format": "json",
            "zoom": zoom,
            "addressdetails": 1
        }
        
        headers = {
            "User-Agent": "ResearchAgent/1.0"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                return {
                    "coordinates": {"latitude": latitude, "longitude": longitude},
                    "error": data["error"]
                }
            
            # Parse result
            result = {
                "coordinates": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "display_name": data["display_name"],
                "type": data.get("type"),
                "importance": data.get("importance"),
                "address": {}
            }
            
            # Parse address components
            if "address" in data:
                addr = data["address"]
                result["address"] = {
                    "house_number": addr.get("house_number"),
                    "road": addr.get("road"),
                    "suburb": addr.get("suburb"),
                    "city": addr.get("city") or addr.get("town") or addr.get("village"),
                    "county": addr.get("county"),
                    "state": addr.get("state"),
                    "postcode": addr.get("postcode"),
                    "country": addr.get("country"),
                    "country_code": addr.get("country_code", "").upper()
                }
            
            # Add bounding box if available
            if "boundingbox" in data:
                bbox = data["boundingbox"]
                result["bounding_box"] = {
                    "south": float(bbox[0]),
                    "north": float(bbox[1]),
                    "west": float(bbox[2]),
                    "east": float(bbox[3])
                }
            
            logger.info(
                f"Reverse geocoding successful",
                extra={"context": {
                    "coordinates": f"{latitude},{longitude}",
                    "address": result["display_name"]
                }}
            )
            
            return result
            
    except httpx.HTTPStatusError as e:
        error_msg = f"Reverse geocoding API error: {e.response.status_code}"
        if e.response.status_code == 429:
            error_msg = "Rate limit exceeded. Please wait before making more requests."
        
        logger.error(
            f"Reverse geocoding request failed: {error_msg}",
            extra={"context": {
                "coordinates": f"{latitude},{longitude}",
                "error": error_msg
            }}
        )
        return {
            "coordinates": {"latitude": latitude, "longitude": longitude},
            "error": error_msg
        }
        
    except httpx.RequestError as e:
        logger.error(
            f"Reverse geocoding request failed: {e}",
            exc_info=True,
            extra={"context": {
                "coordinates": f"{latitude},{longitude}",
                "error": str(e)
            }}
        )
        return {
            "coordinates": {"latitude": latitude, "longitude": longitude},
            "error": f"Request failed: {str(e)}"
        }
        
    except Exception as e:
        logger.error(
            f"Reverse geocoding failed: {e}",
            exc_info=True,
            extra={"context": {
                "coordinates": f"{latitude},{longitude}",
                "error": str(e)
            }}
        )
        return {
            "coordinates": {"latitude": latitude, "longitude": longitude},
            "error": f"Failed to reverse geocode: {str(e)}"
        }


@tool
async def calculate_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    unit: Literal["km", "miles", "meters"] = "km"
) -> dict:
    """
    Calculate the distance between two geographic coordinates using the Haversine formula.
    
    This tool calculates the great-circle distance between two points on Earth.
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
        unit: Distance unit - "km", "miles", or "meters" (default: "km")
        
    Returns:
        Dictionary containing:
        - point1: First coordinate
        - point2: Second coordinate
        - distance: Calculated distance
        - unit: Distance unit
        - error: Error message if calculation failed
        
    Examples:
        >>> result = await calculate_distance(48.8584, 2.2945, 40.7580, -73.9855)  # Paris to NYC
        >>> result = await calculate_distance(51.5074, -0.1278, 48.8566, 2.3522, unit="miles")  # London to Paris
    """
    logger.info(
        f"Calculating distance",
        extra={"context": {
            "point1": f"{lat1},{lon1}",
            "point2": f"{lat2},{lon2}",
            "unit": unit
        }}
    )
    
    try:
        # Validate coordinates
        if not (-90 <= lat1 <= 90) or not (-90 <= lat2 <= 90):
            return {"error": "Latitude must be between -90 and 90"}
        if not (-180 <= lon1 <= 180) or not (-180 <= lon2 <= 180):
            return {"error": "Longitude must be between -180 and 180"}
        
        # Haversine formula
        import math
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        earth_radius_km = 6371.0
        
        # Calculate distance in kilometers
        distance_km = earth_radius_km * c
        
        # Convert to requested unit
        if unit == "miles":
            distance = distance_km * 0.621371
        elif unit == "meters":
            distance = distance_km * 1000
        else:  # km
            distance = distance_km
        
        result = {
            "point1": {"latitude": lat1, "longitude": lon1},
            "point2": {"latitude": lat2, "longitude": lon2},
            "distance": round(distance, 2),
            "unit": unit
        }
        
        logger.info(
            f"Distance calculation successful",
            extra={"context": {
                "distance": f"{result['distance']} {unit}"
            }}
        )
        
        return result
        
    except Exception as e:
        logger.error(
            f"Distance calculation failed: {e}",
            exc_info=True,
            extra={"context": {"error": str(e)}}
        )
        return {"error": f"Failed to calculate distance: {str(e)}"}
