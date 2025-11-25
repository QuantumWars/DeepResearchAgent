"""Unit tests for utility tools (currency, datetime, weather, flight, stock, crypto, map)."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import pytz

# Currency converter tests
from research_agent.tools.currency_converter import convert_currency, _get_exchange_rates


@pytest.mark.asyncio
async def test_convert_currency_basic():
    """Test basic currency conversion."""
    mock_rates = {
        "base": "USD",
        "date": "2024-01-15",
        "rates": {
            "EUR": 0.85,
            "GBP": 0.73,
            "JPY": 110.0
        }
    }
    
    with patch('research_agent.tools.currency_converter._get_exchange_rates', return_value=mock_rates):
        result = await convert_currency(100, "USD", "EUR")
        
        assert result["original_amount"] == 100
        assert result["from_currency"] == "USD"
        assert result["to_currency"] == "EUR"
        assert result["converted_amount"] == 85.0
        assert result["exchange_rate"] == 0.85


@pytest.mark.asyncio
async def test_convert_currency_same_currency():
    """Test conversion with same source and target currency."""
    result = await convert_currency(100, "USD", "USD")
    
    assert result["converted_amount"] == 100
    assert result["exchange_rate"] == 1.0


@pytest.mark.asyncio
async def test_convert_currency_negative_amount():
    """Test currency conversion with negative amount."""
    result = await convert_currency(-50, "USD", "EUR")
    
    assert "error" in result
    assert "positive" in result["error"].lower()


@pytest.mark.asyncio
async def test_convert_currency_case_insensitive():
    """Test currency codes are case-insensitive."""
    mock_rates = {
        "base": "USD",
        "rates": {"EUR": 0.85}
    }
    
    with patch('research_agent.tools.currency_converter._get_exchange_rates', return_value=mock_rates):
        result = await convert_currency(100, "usd", "eur")
        
        assert result["from_currency"] == "USD"
        assert result["to_currency"] == "EUR"


@pytest.mark.asyncio
async def test_convert_currency_unsupported_currency():
    """Test conversion with unsupported currency."""
    mock_rates = {
        "base": "USD",
        "rates": {"EUR": 0.85}
    }
    
    with patch('research_agent.tools.currency_converter._get_exchange_rates', return_value=mock_rates):
        result = await convert_currency(100, "USD", "XYZ")
        
        assert "error" in result
        assert "not supported" in result["error"]


@pytest.mark.asyncio
async def test_convert_currency_api_failure():
    """Test currency conversion handles API failures."""
    with patch('research_agent.tools.currency_converter._get_exchange_rates', return_value=None):
        result = await convert_currency(100, "USD", "EUR")
        
        assert "error" in result
        assert "Failed to fetch" in result["error"]


# DateTime tool tests
from research_agent.tools.datetime_tool import datetime_operations


@pytest.mark.asyncio
async def test_datetime_convert_timezone():
    """Test timezone conversion."""
    result = await datetime_operations(
        operation="convert_timezone",
        datetime_str="2024-01-15T10:30:00",
        from_timezone="America/New_York",
        to_timezone="Europe/London"
    )
    
    assert result["operation"] == "convert_timezone"
    assert result["original_datetime"] == "2024-01-15T10:30:00"
    assert result["original_timezone"] == "America/New_York"
    assert result["converted_timezone"] == "Europe/London"
    assert "converted_datetime" in result


@pytest.mark.asyncio
async def test_datetime_calculate_duration():
    """Test duration calculation."""
    result = await datetime_operations(
        operation="calculate_duration",
        start_datetime="2024-01-15T10:00:00",
        end_datetime="2024-01-15T14:30:00"
    )
    
    assert result["operation"] == "calculate_duration"
    assert result["duration"]["hours"] == 4
    assert result["duration"]["minutes"] == 30
    assert result["duration"]["total_seconds"] == 16200


@pytest.mark.asyncio
async def test_datetime_format_date():
    """Test date formatting."""
    result = await datetime_operations(
        operation="format_date",
        datetime_str="2024-01-15T10:30:00",
        format_string="%B %d, %Y at %I:%M %p"
    )
    
    assert result["operation"] == "format_date"
    assert "January 15, 2024" in result["formatted_datetime"]


@pytest.mark.asyncio
async def test_datetime_current_time():
    """Test getting current time."""
    result = await datetime_operations(
        operation="current_time",
        timezone="America/New_York"
    )
    
    assert result["operation"] == "current_time"
    assert result["timezone"] == "America/New_York"
    assert "datetime" in result
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_datetime_invalid_timezone():
    """Test datetime operations with invalid timezone."""
    result = await datetime_operations(
        operation="convert_timezone",
        datetime_str="2024-01-15T10:30:00",
        from_timezone="Invalid/Timezone",
        to_timezone="Europe/London"
    )
    
    assert "error" in result
    assert "timezone" in result["error"].lower()


@pytest.mark.asyncio
async def test_datetime_invalid_format():
    """Test datetime operations with invalid datetime format."""
    result = await datetime_operations(
        operation="convert_timezone",
        datetime_str="not-a-date",
        from_timezone="America/New_York",
        to_timezone="Europe/London"
    )
    
    assert "error" in result


# Weather tool tests
from research_agent.tools.weather_tool import get_weather


@pytest.mark.asyncio
async def test_get_weather_basic():
    """Test basic weather retrieval."""
    mock_current = {
        "name": "London",
        "sys": {"country": "GB", "sunrise": 1705305600, "sunset": 1705339200},
        "coord": {"lat": 51.5074, "lon": -0.1278},
        "main": {
            "temp": 15.5,
            "feels_like": 14.2,
            "temp_min": 13.0,
            "temp_max": 17.0,
            "pressure": 1013,
            "humidity": 72
        },
        "weather": [{"main": "Clouds", "description": "scattered clouds"}],
        "wind": {"speed": 5.5, "deg": 180},
        "clouds": {"all": 40},
        "visibility": 10000
    }
    
    with patch('research_agent.tools.weather_tool.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_current
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        
        with patch('research_agent.tools.weather_tool.get_config') as mock_config:
            config = Mock()
            config.openweather_api_key = "test_key"
            mock_config.return_value = config
            
            result = await get_weather("London")
            
            assert "location" in result
            assert result["location"]["name"] == "London"
            assert "current" in result
            assert result["current"]["temperature"] == 15.5
            assert result["current"]["conditions"] == "Clouds"


@pytest.mark.asyncio
async def test_get_weather_missing_api_key():
    """Test weather tool with missing API key."""
    with patch('research_agent.tools.weather_tool.get_config') as mock_config:
        config = Mock()
        config.openweather_api_key = None
        mock_config.return_value = config
        
        result = await get_weather("London")
        
        assert "error" in result
        assert "API key not configured" in result["error"]


@pytest.mark.asyncio
async def test_get_weather_location_not_found():
    """Test weather tool with invalid location."""
    with patch('research_agent.tools.weather_tool.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404")
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        
        with patch('research_agent.tools.weather_tool.get_config') as mock_config:
            config = Mock()
            config.openweather_api_key = "test_key"
            mock_config.return_value = config
            
            result = await get_weather("InvalidCity123")
            
            assert "error" in result


# Flight tracker tests
from research_agent.tools.flight_tracker import track_flight


@pytest.mark.asyncio
async def test_track_flight_basic():
    """Test basic flight tracking."""
    mock_flight_data = {
        "data": [{
            "flight": {"iata": "AA100", "icao": "AAL100"},
            "flight_date": "2024-01-15",
            "flight_status": "active",
            "departure": {
                "airport": "JFK",
                "timezone": "America/New_York",
                "scheduled": "2024-01-15T10:00:00",
                "actual": "2024-01-15T10:15:00",
                "terminal": "8",
                "gate": "B12"
            },
            "arrival": {
                "airport": "LAX",
                "timezone": "America/Los_Angeles",
                "scheduled": "2024-01-15T13:30:00",
                "estimated": "2024-01-15T13:45:00",
                "terminal": "4",
                "gate": "42A"
            },
            "airline": {"name": "American Airlines"}
        }]
    }
    
    with patch('research_agent.tools.flight_tracker.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_flight_data
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        
        with patch('research_agent.tools.flight_tracker.get_config') as mock_config:
            config = Mock()
            config.aviationstack_api_key = "test_key"
            mock_config.return_value = config
            
            result = await track_flight("AA100")
            
            assert "flight_number" in result
            assert result["status"] == "active"
            assert "departure" in result
            assert "arrival" in result


# Stock chart tests
from research_agent.tools.stock_chart import get_stock_data


@pytest.mark.asyncio
async def test_get_stock_data_basic():
    """Test basic stock data retrieval."""
    with patch('research_agent.tools.stock_chart.yf.Ticker') as mock_ticker_class:
        mock_ticker = Mock()
        mock_hist = Mock()
        mock_hist.to_dict.return_value = {
            "Open": {0: 150.0},
            "High": {0: 155.0},
            "Low": {0: 148.0},
            "Close": {0: 153.0},
            "Volume": {0: 1000000}
        }
        mock_ticker.history.return_value = mock_hist
        mock_ticker.info = {
            "symbol": "AAPL",
            "longName": "Apple Inc.",
            "currentPrice": 153.0,
            "marketCap": 2500000000000
        }
        mock_ticker_class.return_value = mock_ticker
        
        result = await get_stock_data("AAPL", period="1d", interval="1h")
        
        assert result["symbol"] == "AAPL"
        assert "data" in result
        assert "info" in result


# Crypto tools tests
from research_agent.tools.crypto_tools import get_crypto_data, get_crypto_market_overview


@pytest.mark.asyncio
async def test_get_crypto_data_basic():
    """Test basic crypto data retrieval."""
    mock_crypto_data = {
        "bitcoin": {
            "usd": 45000.0,
            "usd_market_cap": 880000000000,
            "usd_24h_vol": 25000000000,
            "usd_24h_change": 2.5
        }
    }
    
    with patch('research_agent.tools.crypto_tools.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_crypto_data
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        
        result = await get_crypto_data("bitcoin", vs_currency="usd")
        
        assert result["symbol"] == "bitcoin"
        assert result["price"] == 45000.0
        assert result["market_cap"] == 880000000000


# Map tools tests
from research_agent.tools.map_tools import geocode_location, reverse_geocode, calculate_distance


@pytest.mark.asyncio
async def test_geocode_location_basic():
    """Test basic geocoding."""
    mock_geocode_data = {
        "results": [{
            "formatted_address": "1600 Amphitheatre Parkway, Mountain View, CA 94043, USA",
            "geometry": {
                "location": {"lat": 37.4224764, "lng": -122.0842499}
            },
            "place_id": "ChIJ2eUgeAK6j4ARbn5u_wAGqWA"
        }],
        "status": "OK"
    }
    
    with patch('research_agent.tools.map_tools.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_geocode_data
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        
        with patch('research_agent.tools.map_tools.get_config') as mock_config:
            config = Mock()
            config.google_maps_api_key = "test_key"
            mock_config.return_value = config
            
            result = await geocode_location("1600 Amphitheatre Parkway, Mountain View, CA")
            
            assert result["address"] == "1600 Amphitheatre Parkway, Mountain View, CA 94043, USA"
            assert result["latitude"] == 37.4224764
            assert result["longitude"] == -122.0842499


@pytest.mark.asyncio
async def test_reverse_geocode_basic():
    """Test basic reverse geocoding."""
    mock_reverse_data = {
        "results": [{
            "formatted_address": "1600 Amphitheatre Parkway, Mountain View, CA 94043, USA"
        }],
        "status": "OK"
    }
    
    with patch('research_agent.tools.map_tools.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_reverse_data
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        
        with patch('research_agent.tools.map_tools.get_config') as mock_config:
            config = Mock()
            config.google_maps_api_key = "test_key"
            mock_config.return_value = config
            
            result = await reverse_geocode(37.4224764, -122.0842499)
            
            assert result["address"] == "1600 Amphitheatre Parkway, Mountain View, CA 94043, USA"


@pytest.mark.asyncio
async def test_calculate_distance_basic():
    """Test distance calculation between two points."""
    result = await calculate_distance(
        lat1=40.7128,
        lon1=-74.0060,
        lat2=34.0522,
        lon2=-118.2437
    )
    
    assert "distance_km" in result
    assert "distance_miles" in result
    assert result["distance_km"] > 0
    assert result["distance_miles"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
