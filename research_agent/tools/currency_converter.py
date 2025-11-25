"""Currency converter tool using exchangerate-api."""

from typing import Optional
from datetime import datetime
from langchain_core.tools import tool
import httpx

from research_agent.utils.logger import get_logger
from research_agent.utils.config import get_config
from research_agent.utils.performance import cached

logger = get_logger(__name__)


@cached(ttl_seconds=3600)  # Cache for 1 hour
async def _get_exchange_rates(base_currency: str = "USD") -> Optional[dict]:
    """
    Fetch exchange rates from exchangerate-api with caching.
    
    Exchange rates are cached for 1 hour to reduce API calls and improve performance.
    
    Args:
        base_currency: Base currency code (default: USD)
        
    Returns:
        Dictionary of exchange rates or None on failure
    """
    # Fetch fresh rates
    try:
        # Using free exchangerate-api.com service (no API key required for basic usage)
        url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Fetched exchange rates for {base_currency}")
            return data
            
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch exchange rates: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching exchange rates: {e}", exc_info=True)
        return None


@tool
async def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str
) -> dict:
    """
    Convert currency from one type to another using current exchange rates.
    
    This tool converts amounts between different currencies using live exchange rates.
    Rates are cached for 1 hour to improve performance and reduce API calls.
    
    Args:
        amount: Amount to convert (must be positive)
        from_currency: Source currency code (e.g., "USD", "EUR", "GBP")
        to_currency: Target currency code (e.g., "USD", "EUR", "GBP")
        
    Returns:
        Dictionary containing:
        - original_amount: Input amount
        - from_currency: Source currency
        - to_currency: Target currency
        - converted_amount: Converted amount
        - exchange_rate: Exchange rate used
        - timestamp: When the rate was fetched
        - error: Error message if conversion failed
        
    Examples:
        >>> result = await convert_currency(100, "USD", "EUR")
        >>> result = await convert_currency(50.5, "GBP", "JPY")
    """
    logger.info(
        f"Converting currency",
        extra={"context": {
            "amount": amount,
            "from": from_currency,
            "to": to_currency
        }}
    )
    
    try:
        # Validate inputs
        if amount <= 0:
            return {
                "original_amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "converted_amount": None,
                "exchange_rate": None,
                "error": "Amount must be positive"
            }
        
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # If same currency, no conversion needed
        if from_currency == to_currency:
            return {
                "original_amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "converted_amount": amount,
                "exchange_rate": 1.0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Get exchange rates
        rates_data = await _get_exchange_rates(from_currency)
        
        if not rates_data or "rates" not in rates_data:
            return {
                "original_amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "converted_amount": None,
                "exchange_rate": None,
                "error": "Failed to fetch exchange rates"
            }
        
        # Get the exchange rate
        rates = rates_data["rates"]
        if to_currency not in rates:
            return {
                "original_amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "converted_amount": None,
                "exchange_rate": None,
                "error": f"Currency {to_currency} not supported"
            }
        
        exchange_rate = rates[to_currency]
        converted_amount = round(amount * exchange_rate, 2)
        
        logger.info(
            f"Currency conversion successful",
            extra={"context": {
                "from": f"{amount} {from_currency}",
                "to": f"{converted_amount} {to_currency}",
                "rate": exchange_rate
            }}
        )
        
        return {
            "original_amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "converted_amount": converted_amount,
            "exchange_rate": exchange_rate,
            "timestamp": rates_data.get("date", datetime.now().isoformat())
        }
        
    except Exception as e:
        logger.error(
            f"Currency conversion failed: {e}",
            exc_info=True,
            extra={"context": {
                "amount": amount,
                "from": from_currency,
                "to": to_currency,
                "error": str(e)
            }}
        )
        return {
            "original_amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "converted_amount": None,
            "exchange_rate": None,
            "error": f"Conversion failed: {str(e)}"
        }
