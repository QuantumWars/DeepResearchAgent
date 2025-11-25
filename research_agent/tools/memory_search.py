"""Memory search tool for retrieving past research from Supermemory."""

from typing import List
from langchain_core.tools import tool

from research_agent.utils.models import Memory
from research_agent.utils.logger import get_logger
from research_agent.memory.supermemory_client import get_supermemory_client


logger = get_logger(__name__)


@tool
async def search_memories(
    query: str,
    user_id: str,
    limit: int = 10
) -> List[Memory]:
    """
    Search past research stored in Supermemory.
    
    This tool retrieves relevant memories from previous research sessions,
    allowing the agent to build on past work and avoid redundant searches.
    Memories are isolated by user_id to ensure data privacy.
    
    Args:
        query: Search query to find relevant memories
        user_id: User identifier for memory isolation (required)
        limit: Maximum number of memories to return (default 10, max 50)
        
    Returns:
        List of Memory objects with content, metadata, and relevance scores.
        Memories are sorted by relevance score (highest first).
        
    Examples:
        >>> memories = await search_memories("quantum computing", user_id="user123")
        >>> memories = await search_memories("AI research", user_id="user123", limit=5)
    """
    logger.info(
        f"Searching memories",
        extra={"context": {
            "query": query,
            "user_id": user_id,
            "limit": limit
        }}
    )
    
    try:
        # Validate inputs
        if not user_id or not user_id.strip():
            logger.error(
                "user_id is required for memory search",
                extra={"context": {"query": query}}
            )
            return []
        
        # Limit to reasonable maximum
        limit = min(limit, 50)
        
        # Get Supermemory client
        client = get_supermemory_client()
        
        # Search with user_id as container tag for isolation
        container_tags = [user_id]
        
        logger.debug(
            f"Executing memory search",
            extra={"context": {
                "query": query,
                "container_tags": container_tags,
                "limit": limit
            }}
        )
        
        memories = await client.search(
            query=query,
            container_tags=container_tags,
            limit=limit
        )
        
        logger.info(
            f"Memory search completed",
            extra={"context": {
                "query": query,
                "user_id": user_id,
                "memories_found": len(memories)
            }}
        )
        
        return memories
        
    except Exception as e:
        logger.error(
            f"Memory search failed for query '{query}': {str(e)}",
            exc_info=True,
            extra={"context": {
                "query": query,
                "user_id": user_id,
                "error": str(e)
            }}
        )
        # Return empty results instead of raising to allow agent to continue
        return []
