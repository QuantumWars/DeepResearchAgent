"""Cryptocurrency tools using CoinGecko API."""

from typing import Optional, List
from langchain_core.tools import tool
import httpx

from research_agent.utils.logger import get_logger
from research_agent.utils.config import get_config

logger = get_logger(__name__)


@tool
async def get_crypto_data(
    symbol: str,
    vs_currency: str = "usd",
    include_market_data: bool = True
) -> dict:
    """
    Get cryptocurrency price and market data using CoinGecko API.
    
    This tool retrieves current price, market cap, volume, and other market data
    for any cryptocurrency.
    
    Args:
        symbol: Cryptocurrency symbol or ID (e.g., "bitcoin", "ethereum", "btc", "eth")
        vs_currency: Currency to compare against (default: "usd")
        include_market_data: Include detailed market data (default: True)
        
    Returns:
        Dictionary containing:
        - id: Cryptocurrency ID
        - symbol: Cryptocurrency symbol
        - name: Cryptocurrency name
        - current_price: Current price in vs_currency
        - market_data: Market cap, volume, price changes, etc.
        - error: Error message if request failed
        
    Examples:
        >>> result = await get_crypto_data("bitcoin")
        >>> result = await get_crypto_data("eth", vs_currency="eur")
        >>> result = await get_crypto_data("solana", include_market_data=True)
    """
    logger.info(
        f"Fetching crypto data",
        extra={"context": {
            "symbol": symbol,
            "vs_currency": vs_currency
        }}
    )
    
    try:
        # CoinGecko free API doesn't require API key for basic usage
        # If API key is configured, we'll use it for higher rate limits
        config = get_config()
        api_key = config.coingecko_api_key
        
        # Normalize symbol to lowercase
        symbol = symbol.lower()
        vs_currency = vs_currency.lower()
        
        # Map common symbols to CoinGecko IDs
        symbol_map = {
            "btc": "bitcoin",
            "eth": "ethereum",
            "usdt": "tether",
            "bnb": "binancecoin",
            "sol": "solana",
            "xrp": "ripple",
            "usdc": "usd-coin",
            "ada": "cardano",
            "doge": "dogecoin",
            "trx": "tron",
            "avax": "avalanche-2",
            "dot": "polkadot",
            "matic": "matic-network",
            "link": "chainlink",
            "atom": "cosmos"
        }
        
        # Convert symbol to ID if it's a known abbreviation
        crypto_id = symbol_map.get(symbol, symbol)
        
        # Build headers
        headers = {}
        if api_key:
            headers["x-cg-demo-api-key"] = api_key
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get coin data
            url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}"
            params = {
                "localization": "false",
                "tickers": "false",
                "community_data": "false",
                "developer_data": "false",
                "sparkline": "false"
            }
            
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Extract basic info
            result = {
                "id": data["id"],
                "symbol": data["symbol"].upper(),
                "name": data["name"],
                "current_price": data["market_data"]["current_price"].get(vs_currency),
                "vs_currency": vs_currency.upper()
            }
            
            # Add market data if requested
            if include_market_data:
                market_data = data["market_data"]
                result["market_data"] = {
                    "market_cap": market_data["market_cap"].get(vs_currency),
                    "market_cap_rank": market_data.get("market_cap_rank"),
                    "total_volume": market_data["total_volume"].get(vs_currency),
                    "high_24h": market_data["high_24h"].get(vs_currency),
                    "low_24h": market_data["low_24h"].get(vs_currency),
                    "price_change_24h": market_data.get("price_change_24h"),
                    "price_change_percentage_24h": market_data.get("price_change_percentage_24h"),
                    "price_change_percentage_7d": market_data.get("price_change_percentage_7d"),
                    "price_change_percentage_30d": market_data.get("price_change_percentage_30d"),
                    "circulating_supply": market_data.get("circulating_supply"),
                    "total_supply": market_data.get("total_supply"),
                    "max_supply": market_data.get("max_supply"),
                    "ath": market_data["ath"].get(vs_currency),
                    "ath_date": market_data["ath_date"].get(vs_currency),
                    "atl": market_data["atl"].get(vs_currency),
                    "atl_date": market_data["atl_date"].get(vs_currency)
                }
            
            # Add additional info
            if "description" in data and data["description"].get("en"):
                # Truncate description to first 500 chars
                description = data["description"]["en"]
                result["description"] = description[:500] + "..." if len(description) > 500 else description
            
            if "links" in data:
                result["links"] = {
                    "homepage": data["links"].get("homepage", [None])[0],
                    "blockchain_site": [site for site in data["links"].get("blockchain_site", []) if site][:3],
                    "official_forum_url": data["links"].get("official_forum_url", [None])[0]
                }
            
            logger.info(
                f"Crypto data retrieved successfully",
                extra={"context": {
                    "symbol": result["symbol"],
                    "name": result["name"],
                    "price": result["current_price"]
                }}
            )
            
            return result
            
    except httpx.HTTPStatusError as e:
        error_msg = f"CoinGecko API error: {e.response.status_code}"
        if e.response.status_code == 404:
            error_msg = f"Cryptocurrency '{symbol}' not found"
        elif e.response.status_code == 429:
            error_msg = "Rate limit exceeded. Try again later or configure API key."
        
        logger.error(
            f"Crypto data request failed: {error_msg}",
            extra={"context": {"symbol": symbol, "error": error_msg}}
        )
        return {"error": error_msg}
        
    except httpx.RequestError as e:
        logger.error(
            f"Crypto data request failed: {e}",
            exc_info=True,
            extra={"context": {"symbol": symbol, "error": str(e)}}
        )
        return {"error": f"Request failed: {str(e)}"}
        
    except Exception as e:
        logger.error(
            f"Crypto data retrieval failed: {e}",
            exc_info=True,
            extra={"context": {"symbol": symbol, "error": str(e)}}
        )
        return {"error": f"Failed to get crypto data: {str(e)}"}


@tool
async def get_crypto_market_overview(
    vs_currency: str = "usd",
    top_n: int = 10
) -> dict:
    """
    Get overview of top cryptocurrencies by market cap.
    
    This tool retrieves a list of top cryptocurrencies with their current prices
    and market data, useful for getting a market overview.
    
    Args:
        vs_currency: Currency to compare against (default: "usd")
        top_n: Number of top cryptocurrencies to retrieve (1-250, default: 10)
        
    Returns:
        Dictionary containing:
        - cryptocurrencies: List of top cryptocurrencies with market data
        - vs_currency: Currency used for comparison
        - total_market_cap: Total market cap of all cryptocurrencies
        - error: Error message if request failed
        
    Examples:
        >>> result = await get_crypto_market_overview()
        >>> result = await get_crypto_market_overview(vs_currency="eur", top_n=20)
    """
    logger.info(
        f"Fetching crypto market overview",
        extra={"context": {
            "vs_currency": vs_currency,
            "top_n": top_n
        }}
    )
    
    try:
        config = get_config()
        api_key = config.coingecko_api_key
        
        # Validate top_n
        top_n = max(1, min(top_n, 250))
        vs_currency = vs_currency.lower()
        
        # Build headers
        headers = {}
        if api_key:
            headers["x-cg-demo-api-key"] = api_key
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get market data
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                "vs_currency": vs_currency,
                "order": "market_cap_desc",
                "per_page": top_n,
                "page": 1,
                "sparkline": "false"
            }
            
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Parse cryptocurrency data
            cryptocurrencies = []
            for coin in data:
                cryptocurrencies.append({
                    "rank": coin["market_cap_rank"],
                    "id": coin["id"],
                    "symbol": coin["symbol"].upper(),
                    "name": coin["name"],
                    "current_price": coin["current_price"],
                    "market_cap": coin["market_cap"],
                    "total_volume": coin["total_volume"],
                    "price_change_percentage_24h": coin.get("price_change_percentage_24h"),
                    "circulating_supply": coin.get("circulating_supply"),
                    "total_supply": coin.get("total_supply")
                })
            
            # Get global market data
            global_url = "https://api.coingecko.com/api/v3/global"
            global_response = await client.get(global_url, headers=headers)
            global_data = global_response.json()
            
            result = {
                "cryptocurrencies": cryptocurrencies,
                "vs_currency": vs_currency.upper(),
                "count": len(cryptocurrencies),
                "global_data": {
                    "total_market_cap": global_data["data"]["total_market_cap"].get(vs_currency),
                    "total_volume": global_data["data"]["total_volume"].get(vs_currency),
                    "market_cap_percentage": global_data["data"]["market_cap_percentage"],
                    "active_cryptocurrencies": global_data["data"]["active_cryptocurrencies"]
                }
            }
            
            logger.info(
                f"Crypto market overview retrieved successfully",
                extra={"context": {
                    "count": len(cryptocurrencies),
                    "vs_currency": vs_currency
                }}
            )
            
            return result
            
    except httpx.HTTPStatusError as e:
        error_msg = f"CoinGecko API error: {e.response.status_code}"
        if e.response.status_code == 429:
            error_msg = "Rate limit exceeded. Try again later or configure API key."
        
        logger.error(
            f"Crypto market overview request failed: {error_msg}",
            extra={"context": {"error": error_msg}}
        )
        return {"error": error_msg}
        
    except Exception as e:
        logger.error(
            f"Crypto market overview failed: {e}",
            exc_info=True,
            extra={"context": {"error": str(e)}}
        )
        return {"error": f"Failed to get market overview: {str(e)}"}
