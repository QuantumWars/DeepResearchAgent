"""API Client Manager for connection pooling and lifecycle management."""

from typing import Dict, Optional, Any
import httpx
from contextlib import asynccontextmanager

from research_agent.utils.logger import get_logger
from research_agent.utils.config import get_config

logger = get_logger(__name__)


class APIClientManager:
    """Centralized manager for HTTP clients with connection pooling.
    
    This class manages HTTP client instances with connection pooling to improve
    performance and resource utilization. It ensures proper cleanup of connections
    and provides a consistent interface for all API clients.
    """
    
    def __init__(self):
        """Initialize the API client manager."""
        self._clients: Dict[str, httpx.AsyncClient] = {}
        self._config = get_config()
        logger.debug("Initialized APIClientManager")
    
    def get_client(
        self,
        name: str,
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        **kwargs
    ) -> httpx.AsyncClient:
        """Get or create an HTTP client with connection pooling.
        
        Args:
            name: Unique name for this client (e.g., "xai", "exa", "tavily")
            base_url: Base URL for the API (optional)
            headers: Default headers to include in all requests
            timeout: Request timeout in seconds
            max_connections: Maximum number of connections in the pool
            max_keepalive_connections: Maximum number of keepalive connections
            **kwargs: Additional arguments to pass to httpx.AsyncClient
            
        Returns:
            httpx.AsyncClient instance with connection pooling configured
        """
        if name in self._clients:
            logger.debug(f"Reusing existing client: {name}")
            return self._clients[name]
        
        # Create new client with connection pooling
        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            keepalive_expiry=30.0  # Keep connections alive for 30 seconds
        )
        
        timeout_config = httpx.Timeout(
            timeout=timeout,
            connect=10.0,  # Connection timeout
            read=timeout,  # Read timeout
            write=timeout,  # Write timeout
            pool=5.0  # Pool timeout
        )
        
        client_kwargs = {
            "limits": limits,
            "timeout": timeout_config,
            "follow_redirects": True,
            **kwargs
        }
        
        # Enable HTTP/2 if available (requires h2 package)
        try:
            import h2
            client_kwargs["http2"] = True
        except ImportError:
            logger.debug("HTTP/2 support not available (h2 package not installed)")
            client_kwargs["http2"] = False
        
        if base_url:
            client_kwargs["base_url"] = base_url
        
        if headers:
            client_kwargs["headers"] = headers
        
        client = httpx.AsyncClient(**client_kwargs)
        self._clients[name] = client
        
        logger.info(
            f"Created new HTTP client: {name}",
            extra={"context": {
                "name": name,
                "base_url": base_url,
                "max_connections": max_connections,
                "max_keepalive": max_keepalive_connections,
                "timeout": timeout
            }}
        )
        
        return client
    
    def get_xai_client(self) -> httpx.AsyncClient:
        """Get HTTP client for xAI API.
        
        Returns:
            Configured httpx.AsyncClient for xAI
        """
        api_key = self._config.xai_api_key
        if not api_key:
            raise ValueError("XAI_API_KEY is required")
        
        return self.get_client(
            name="xai",
            base_url="https://api.x.ai/v1",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=60.0,
            max_connections=10,
            max_keepalive_connections=5
        )
    
    def get_exa_client(self) -> httpx.AsyncClient:
        """Get HTTP client for Exa API.
        
        Returns:
            Configured httpx.AsyncClient for Exa
        """
        api_key = self._config.exa_api_key
        if not api_key:
            raise ValueError("EXA_API_KEY is required")
        
        return self.get_client(
            name="exa",
            base_url="https://api.exa.ai",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0,
            max_connections=20,
            max_keepalive_connections=10
        )
    
    def get_tavily_client(self) -> httpx.AsyncClient:
        """Get HTTP client for Tavily API.
        
        Returns:
            Configured httpx.AsyncClient for Tavily
        """
        api_key = self._config.tavily_api_key
        if not api_key:
            raise ValueError("TAVILY_API_KEY is required")
        
        return self.get_client(
            name="tavily",
            base_url="https://api.tavily.com",
            headers={
                "Content-Type": "application/json"
            },
            timeout=30.0,
            max_connections=20,
            max_keepalive_connections=10
        )
    
    def get_openweather_client(self) -> httpx.AsyncClient:
        """Get HTTP client for OpenWeatherMap API.
        
        Returns:
            Configured httpx.AsyncClient for OpenWeatherMap
        """
        return self.get_client(
            name="openweather",
            base_url="https://api.openweathermap.org",
            timeout=10.0,
            max_connections=10,
            max_keepalive_connections=5
        )
    
    def get_aviationstack_client(self) -> httpx.AsyncClient:
        """Get HTTP client for AviationStack API.
        
        Returns:
            Configured httpx.AsyncClient for AviationStack
        """
        return self.get_client(
            name="aviationstack",
            base_url="http://api.aviationstack.com",
            timeout=10.0,
            max_connections=5,
            max_keepalive_connections=3
        )
    
    def get_coingecko_client(self) -> httpx.AsyncClient:
        """Get HTTP client for CoinGecko API.
        
        Returns:
            Configured httpx.AsyncClient for CoinGecko
        """
        headers = {}
        if self._config.coingecko_api_key:
            headers["x-cg-demo-api-key"] = self._config.coingecko_api_key
        
        return self.get_client(
            name="coingecko",
            base_url="https://api.coingecko.com/api/v3",
            headers=headers if headers else None,
            timeout=10.0,
            max_connections=10,
            max_keepalive_connections=5
        )
    
    def get_nominatim_client(self) -> httpx.AsyncClient:
        """Get HTTP client for OpenStreetMap Nominatim API.
        
        Returns:
            Configured httpx.AsyncClient for Nominatim
        """
        return self.get_client(
            name="nominatim",
            base_url="https://nominatim.openstreetmap.org",
            headers={
                "User-Agent": "ResearchAgent/1.0"
            },
            timeout=10.0,
            max_connections=5,
            max_keepalive_connections=3
        )
    
    def get_generic_client(self, name: str = "generic") -> httpx.AsyncClient:
        """Get a generic HTTP client for general purpose use.
        
        Args:
            name: Name for this client instance
            
        Returns:
            Configured httpx.AsyncClient
        """
        return self.get_client(
            name=name,
            timeout=30.0,
            max_connections=50,
            max_keepalive_connections=20
        )
    
    async def close_client(self, name: str) -> None:
        """Close a specific HTTP client.
        
        Args:
            name: Name of the client to close
        """
        if name in self._clients:
            await self._clients[name].aclose()
            del self._clients[name]
            logger.info(f"Closed HTTP client: {name}")
    
    async def close_all(self) -> None:
        """Close all HTTP clients and cleanup resources.
        
        This should be called during application shutdown to ensure
        all connections are properly closed.
        """
        logger.info(f"Closing {len(self._clients)} HTTP clients")
        
        for name, client in list(self._clients.items()):
            try:
                await client.aclose()
                logger.debug(f"Closed client: {name}")
            except Exception as e:
                logger.error(
                    f"Error closing client {name}: {e}",
                    exc_info=True
                )
        
        self._clients.clear()
        logger.info("All HTTP clients closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_all()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about managed clients.
        
        Returns:
            Dictionary with client statistics
        """
        return {
            "total_clients": len(self._clients),
            "client_names": list(self._clients.keys())
        }


# Global singleton instance
_client_manager: Optional[APIClientManager] = None


def get_client_manager() -> APIClientManager:
    """Get the global API client manager instance.
    
    Returns:
        APIClientManager singleton instance
    """
    global _client_manager
    if _client_manager is None:
        _client_manager = APIClientManager()
    return _client_manager


@asynccontextmanager
async def managed_client_context():
    """Context manager for API client lifecycle.
    
    Usage:
        async with managed_client_context():
            manager = get_client_manager()
            client = manager.get_client("my_api")
            # ... use client ...
        # Clients are automatically closed on exit
    """
    manager = get_client_manager()
    try:
        yield manager
    finally:
        await manager.close_all()
