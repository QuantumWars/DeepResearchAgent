"""Stock chart tool using yfinance library."""

from typing import Literal, Optional
from datetime import datetime, timedelta
from langchain_core.tools import tool
import yfinance as yf

from research_agent.utils.logger import get_logger

logger = get_logger(__name__)


@tool
async def get_stock_data(
    symbol: str,
    period: Literal["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"] = "1d",
    interval: Literal["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"] = "1h"
) -> dict:
    """
    Get stock market data including price history and basic indicators using yfinance.
    
    This tool retrieves historical stock data, current price, and basic market information
    for any publicly traded stock symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., "AAPL", "GOOGL", "TSLA")
        period: Time period for historical data
                Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        interval: Data interval/granularity
                  Valid intervals: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
                  Note: Intraday data (< 1d) is limited to last 60 days
        
    Returns:
        Dictionary containing:
        - symbol: Stock ticker symbol
        - info: Company and stock information
        - current_price: Latest price
        - price_history: Historical price data
        - statistics: Basic price statistics
        - error: Error message if request failed
        
    Examples:
        >>> result = await get_stock_data("AAPL")
        >>> result = await get_stock_data("GOOGL", period="1mo", interval="1d")
        >>> result = await get_stock_data("TSLA", period="5d", interval="15m")
    """
    logger.info(
        f"Fetching stock data",
        extra={"context": {
            "symbol": symbol,
            "period": period,
            "interval": interval
        }}
    )
    
    try:
        # Create ticker object
        ticker = yf.Ticker(symbol.upper())
        
        # Get stock info
        try:
            info = ticker.info
            if not info or "symbol" not in info:
                return {"error": f"Stock symbol '{symbol}' not found"}
        except Exception as e:
            logger.warning(f"Could not fetch stock info: {e}")
            info = {}
        
        # Get historical data
        try:
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                return {"error": f"No data available for {symbol} with period={period}, interval={interval}"}
            
            # Convert to list of dictionaries
            price_history = []
            for idx, row in hist.iterrows():
                price_history.append({
                    "date": idx.isoformat(),
                    "open": round(float(row["Open"]), 2),
                    "high": round(float(row["High"]), 2),
                    "low": round(float(row["Low"]), 2),
                    "close": round(float(row["Close"]), 2),
                    "volume": int(row["Volume"])
                })
            
            # Calculate statistics
            closes = [p["close"] for p in price_history]
            current_price = closes[-1]
            period_start_price = closes[0]
            price_change = current_price - period_start_price
            price_change_percent = (price_change / period_start_price) * 100
            
            statistics = {
                "current_price": current_price,
                "period_start_price": period_start_price,
                "period_high": max(closes),
                "period_low": min(closes),
                "price_change": round(price_change, 2),
                "price_change_percent": round(price_change_percent, 2),
                "average_price": round(sum(closes) / len(closes), 2),
                "total_volume": sum(p["volume"] for p in price_history)
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch historical data: {e}", exc_info=True)
            return {"error": f"Failed to fetch historical data: {str(e)}"}
        
        # Build result
        result = {
            "symbol": symbol.upper(),
            "period": period,
            "interval": interval,
            "current_price": statistics["current_price"],
            "statistics": statistics,
            "price_history": price_history,
            "data_points": len(price_history)
        }
        
        # Add company info if available
        if info:
            result["info"] = {
                "name": info.get("longName", info.get("shortName", symbol)),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "market_cap": info.get("marketCap"),
                "currency": info.get("currency", "USD"),
                "exchange": info.get("exchange"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "pe_ratio": info.get("trailingPE"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta")
            }
        
        logger.info(
            f"Stock data retrieved successfully",
            extra={"context": {
                "symbol": symbol,
                "current_price": current_price,
                "data_points": len(price_history)
            }}
        )
        
        return result
        
    except Exception as e:
        logger.error(
            f"Stock data retrieval failed: {e}",
            exc_info=True,
            extra={"context": {"symbol": symbol, "error": str(e)}}
        )
        return {"error": f"Failed to get stock data: {str(e)}"}
