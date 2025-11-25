"""Supermemory client for storing and retrieving research context."""

import httpx
from typing import List, Optional, Dict, Any
from research_agent.utils.models import ResearchResult, Memory
from research_agent.utils.logger import get_logger
from research_agent.utils.config import get_config


logger = get_logger(__name__)


class SupermemoryClient:
    """Client for interacting with Supermemory API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize Supermemory client.
        
        Args:
            api_key: Supermemory API key (defaults to config)
            base_url: Supermemory API base URL (defaults to config)
        """
        config = get_config()
        self.api_key = api_key or config.supermemory_api_key
        self.base_url = base_url or config.supermemory_base_url
        
        if not self.api_key:
            logger.warning("Supermemory API key not configured, memory features will be disabled")
            self._client = None
        else:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20
                )
            )
            logger.info(
                "Supermemory client initialized",
                extra={"context": {"base_url": self.base_url}}
            )
    
    async def store_research(
        self,
        user_id: str,
        session_id: str,
        research_result: ResearchResult
    ) -> None:
        """
        Store research results in Supermemory.
        
        Each source is stored as a separate memory with metadata and tags
        for user isolation and session tracking.
        
        Args:
            user_id: User identifier for memory isolation
            session_id: Research session identifier
            research_result: Complete research result to store
            
        Raises:
            Exception: If storage fails (logged but not raised)
        """
        if not self._client:
            logger.warning("Supermemory client not configured, skipping storage")
            return
        
        if not research_result.sources:
            logger.info(
                "No sources to store",
                extra={"context": {
                    "user_id": user_id,
                    "session_id": session_id
                }}
            )
            return
        
        logger.info(
            f"Storing {len(research_result.sources)} sources in Supermemory",
            extra={"context": {
                "user_id": user_id,
                "session_id": session_id,
                "sources_count": len(research_result.sources),
                "query": research_result.query
            }}
        )
        
        try:
            # Prepare memories from sources
            memories = []
            for source in research_result.sources:
                memory = {
                    "content": source.content,
                    "metadata": {
                        "title": source.title,
                        "url": source.url,
                        "published_date": source.published_date,
                        "author": source.author,
                        "session_id": session_id,
                        "query": research_result.query
                    },
                    "container_tags": [user_id, f"session:{session_id}"]
                }
                memories.append(memory)
            
            # Store memories in batch
            response = await self._client.post(
                "/memories/batch",
                json={"memories": memories}
            )
            response.raise_for_status()
            
            logger.info(
                f"Successfully stored {len(memories)} memories",
                extra={"context": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "memories_count": len(memories)
                }}
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error storing research in Supermemory: {e.response.status_code}",
                exc_info=True,
                extra={"context": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "status_code": e.response.status_code,
                    "response": e.response.text
                }}
            )
        except Exception as e:
            logger.error(
                f"Failed to store research in Supermemory: {str(e)}",
                exc_info=True,
                extra={"context": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "error": str(e)
                }}
            )
    
    async def search(
        self,
        query: str,
        container_tags: List[str],
        limit: int = 10
    ) -> List[Memory]:
        """
        Search memories in Supermemory.
        
        Args:
            query: Search query
            container_tags: Tags to filter memories (e.g., [user_id, "session:xyz"])
            limit: Maximum number of memories to return (default 10)
            
        Returns:
            List of Memory objects matching the query
        """
        if not self._client:
            logger.warning("Supermemory client not configured, returning empty results")
            return []
        
        logger.info(
            f"Searching memories",
            extra={"context": {
                "query": query,
                "container_tags": container_tags,
                "limit": limit
            }}
        )
        
        try:
            response = await self._client.post(
                "/search/memories",
                json={
                    "q": query,
                    "container_tags": container_tags,
                    "limit": limit
                }
            )
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            # Convert to Memory objects
            memories = []
            for result in results:
                try:
                    memory = Memory(
                        id=result.get("id", ""),
                        content=result.get("content", ""),
                        metadata=result.get("metadata", {}),
                        score=result.get("score", 0.0)
                    )
                    memories.append(memory)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse memory result: {str(e)}",
                        extra={"context": {"result": result}}
                    )
                    continue
            
            logger.info(
                f"Found {len(memories)} memories",
                extra={"context": {
                    "query": query,
                    "memories_count": len(memories)
                }}
            )
            
            return memories
            
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error searching Supermemory: {e.response.status_code}",
                exc_info=True,
                extra={"context": {
                    "query": query,
                    "status_code": e.response.status_code,
                    "response": e.response.text
                }}
            )
            return []
        except Exception as e:
            logger.error(
                f"Failed to search Supermemory: {str(e)}",
                exc_info=True,
                extra={"context": {
                    "query": query,
                    "error": str(e)
                }}
            )
            return []
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            logger.debug("Supermemory client closed")


# Global client instance
_client: Optional[SupermemoryClient] = None


def get_supermemory_client() -> SupermemoryClient:
    """Get or create the global Supermemory client instance."""
    global _client
    if _client is None:
        _client = SupermemoryClient()
    return _client


def reset_supermemory_client() -> None:
    """Reset the global Supermemory client (useful for testing)."""
    global _client
    if _client:
        # Note: In production, you should await close() properly
        _client = None
