"""Performance optimization utilities for the research agent.

This module provides utilities for optimizing performance including:
- Parallel query execution with concurrency control
- Caching for expensive operations
- Batch processing utilities
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import List, Callable, Any, TypeVar, Coroutine, Optional, Dict
from research_agent.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


# In-memory cache with TTL support
class CacheEntry:
    """Cache entry with expiration time."""
    
    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() > self.expires_at


class AsyncCache:
    """
    Simple async-safe in-memory cache with TTL support.
    
    This cache is used for expensive operations like video transcripts,
    exchange rates, and weather data. It provides automatic expiration
    and thread-safe access.
    """
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if it exists and hasn't expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired():
                    logger.debug(
                        f"Cache hit for key: {key[:50]}...",
                        extra={"context": {"cache_key": key}}
                    )
                    return entry.value
                else:
                    # Remove expired entry
                    logger.debug(
                        f"Cache expired for key: {key[:50]}...",
                        extra={"context": {"cache_key": key}}
                    )
                    del self._cache[key]
            
            logger.debug(
                f"Cache miss for key: {key[:50]}...",
                extra={"context": {"cache_key": key}}
            )
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int):
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
        """
        async with self._lock:
            self._cache[key] = CacheEntry(value, ttl_seconds)
            logger.debug(
                f"Cache set for key: {key[:50]}... (TTL: {ttl_seconds}s)",
                extra={"context": {
                    "cache_key": key,
                    "ttl_seconds": ttl_seconds
                }}
            )
    
    async def clear(self):
        """Clear all cache entries."""
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(
                f"Cache cleared ({count} entries removed)",
                extra={"context": {"entries_cleared": count}}
            )
    
    async def cleanup_expired(self):
        """Remove all expired entries from cache."""
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(
                    f"Cleaned up {len(expired_keys)} expired cache entries",
                    extra={"context": {"expired_count": len(expired_keys)}}
                )


# Global cache instance
_global_cache = AsyncCache()


def get_cache() -> AsyncCache:
    """Get the global cache instance."""
    return _global_cache


def cache_key(*args, **kwargs) -> str:
    """
    Generate a cache key from function arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Hash string to use as cache key
    """
    # Create a deterministic string representation
    key_data = {
        'args': args,
        'kwargs': kwargs
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    
    # Hash it for a shorter key
    return hashlib.md5(key_str.encode()).hexdigest()


def cached(ttl_seconds: int):
    """
    Decorator for caching async function results.
    
    Args:
        ttl_seconds: Time to live in seconds
        
    Examples:
        >>> @cached(ttl_seconds=3600)
        ... async def expensive_operation(param: str) -> dict:
        ...     # Expensive computation
        ...     return {"result": param}
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cache = get_cache()
            cached_value = await cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache.set(key, result, ttl_seconds)
            
            return result
        
        return wrapper
    
    return decorator


async def execute_multi_query_tool(
    queries: List[str],
    executor_func: Callable[[str], Coroutine[Any, Any, T]],
    max_concurrent: int = 5
) -> List[T]:
    """
    Execute multiple queries in parallel with concurrency control.
    
    This generic helper executes multiple queries concurrently while limiting
    the number of simultaneous requests to avoid overwhelming APIs. It uses
    asyncio.gather with exception handling to ensure individual query failures
    don't stop other queries from executing.
    
    Args:
        queries: List of query strings to execute
        executor_func: Async function that executes a single query
        max_concurrent: Maximum number of concurrent requests (default: 5)
        
    Returns:
        List of results from executor_func, in the same order as queries.
        Failed queries will have their exceptions in the list.
        
    Examples:
        >>> async def search_query(query: str) -> dict:
        ...     # Execute search
        ...     return {"query": query, "results": [...]}
        >>> 
        >>> queries = ["AI", "ML", "DL"]
        >>> results = await execute_multi_query_tool(queries, search_query)
    """
    if not queries:
        logger.warning("No queries provided to execute_multi_query_tool")
        return []
    
    logger.info(
        f"Executing {len(queries)} queries in parallel with max {max_concurrent} concurrent",
        extra={"context": {
            "query_count": len(queries),
            "max_concurrent": max_concurrent
        }}
    )
    
    # Create semaphore for concurrency control
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def bounded_executor(query: str, index: int) -> T:
        """Execute query with semaphore-based concurrency control."""
        async with semaphore:
            logger.debug(
                f"Executing query {index + 1}/{len(queries)}: {query[:50]}...",
                extra={"context": {
                    "query_index": index,
                    "query": query
                }}
            )
            try:
                result = await executor_func(query)
                logger.debug(
                    f"Query {index + 1}/{len(queries)} completed successfully",
                    extra={"context": {"query_index": index}}
                )
                return result
            except Exception as e:
                logger.error(
                    f"Query {index + 1}/{len(queries)} failed: {str(e)}",
                    exc_info=True,
                    extra={"context": {
                        "query_index": index,
                        "query": query,
                        "error": str(e)
                    }}
                )
                raise
    
    # Create tasks for all queries
    tasks = [bounded_executor(query, i) for i, query in enumerate(queries)]
    
    # Execute all tasks and gather results (including exceptions)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Log summary
    successful = sum(1 for r in results if not isinstance(r, Exception))
    failed = len(results) - successful
    
    logger.info(
        f"Multi-query execution completed",
        extra={"context": {
            "total_queries": len(queries),
            "successful": successful,
            "failed": failed
        }}
    )
    
    return results



async def process_in_batches(
    items: List[Any],
    processor_func: Callable[[Any], Coroutine[Any, Any, T]],
    batch_size: int = 5,
    delay_between_batches: float = 0.5
) -> List[T]:
    """
    Process items in batches with delays to respect rate limits.
    
    This utility processes a list of items in batches, executing each batch
    concurrently while adding delays between batches to avoid overwhelming
    APIs with rate limits.
    
    Args:
        items: List of items to process
        processor_func: Async function that processes a single item
        batch_size: Number of items to process per batch (default: 5)
        delay_between_batches: Delay in seconds between batches (default: 0.5)
        
    Returns:
        List of results from processor_func, in the same order as items.
        Failed items will have their exceptions in the list.
        
    Examples:
        >>> async def process_video(video_id: str) -> dict:
        ...     # Process video
        ...     return {"id": video_id, "data": ...}
        >>> 
        >>> video_ids = ["id1", "id2", "id3", "id4", "id5", "id6"]
        >>> results = await process_in_batches(video_ids, process_video, batch_size=3)
    """
    if not items:
        logger.warning("No items provided to process_in_batches")
        return []
    
    logger.info(
        f"Processing {len(items)} items in batches",
        extra={"context": {
            "total_items": len(items),
            "batch_size": batch_size,
            "delay_between_batches": delay_between_batches
        }}
    )
    
    all_results = []
    total_batches = (len(items) + batch_size - 1) // batch_size
    
    for batch_num, i in enumerate(range(0, len(items), batch_size), 1):
        batch = items[i:i + batch_size]
        
        logger.debug(
            f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)",
            extra={"context": {
                "batch_num": batch_num,
                "total_batches": total_batches,
                "batch_size": len(batch)
            }}
        )
        
        # Process batch concurrently
        tasks = [processor_func(item) for item in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successes and failures
        successful = sum(1 for r in batch_results if not isinstance(r, Exception))
        failed = len(batch_results) - successful
        
        logger.debug(
            f"Batch {batch_num}/{total_batches} completed",
            extra={"context": {
                "batch_num": batch_num,
                "successful": successful,
                "failed": failed
            }}
        )
        
        all_results.extend(batch_results)
        
        # Add delay between batches (except after the last batch)
        if i + batch_size < len(items):
            logger.debug(
                f"Waiting {delay_between_batches}s before next batch",
                extra={"context": {"delay": delay_between_batches}}
            )
            await asyncio.sleep(delay_between_batches)
    
    # Log final summary
    total_successful = sum(1 for r in all_results if not isinstance(r, Exception))
    total_failed = len(all_results) - total_successful
    
    logger.info(
        f"Batch processing completed",
        extra={"context": {
            "total_items": len(items),
            "total_batches": total_batches,
            "successful": total_successful,
            "failed": total_failed
        }}
    )
    
    return all_results
