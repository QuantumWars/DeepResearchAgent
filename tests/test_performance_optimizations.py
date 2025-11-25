"""Test script for performance optimization utilities."""

import asyncio
import time
from research_agent.utils.performance import (
    execute_multi_query_tool,
    get_cache,
    cached,
    process_in_batches
)
from research_agent.utils.logger import get_logger

logger = get_logger(__name__)


async def test_multi_query_execution():
    """Test parallel query execution with concurrency control."""
    print("\n=== Testing Multi-Query Execution ===")
    
    async def mock_search(query: str) -> dict:
        """Mock search function that simulates API call."""
        await asyncio.sleep(0.1)  # Simulate API delay
        return {"query": query, "results": [f"result for {query}"]}
    
    queries = ["query1", "query2", "query3", "query4", "query5", "query6"]
    
    start_time = time.time()
    results = await execute_multi_query_tool(
        queries=queries,
        executor_func=mock_search,
        max_concurrent=3
    )
    elapsed = time.time() - start_time
    
    print(f"Processed {len(queries)} queries in {elapsed:.2f}s")
    print(f"Successful results: {sum(1 for r in results if not isinstance(r, Exception))}")
    print(f"Failed results: {sum(1 for r in results if isinstance(r, Exception))}")
    
    assert len(results) == len(queries), "Should return result for each query"
    assert all(not isinstance(r, Exception) for r in results), "All queries should succeed"
    print("✓ Multi-query execution test passed")


async def test_caching():
    """Test caching decorator."""
    print("\n=== Testing Caching ===")
    
    call_count = 0
    
    @cached(ttl_seconds=2)
    async def expensive_operation(param: str) -> dict:
        """Mock expensive operation."""
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.1)
        return {"param": param, "result": f"computed {param}"}
    
    # First call - should execute
    result1 = await expensive_operation("test")
    assert call_count == 1, "Should execute on first call"
    print(f"First call executed (call_count={call_count})")
    
    # Second call - should use cache
    result2 = await expensive_operation("test")
    assert call_count == 1, "Should use cache on second call"
    assert result1 == result2, "Cached result should match"
    print(f"Second call used cache (call_count={call_count})")
    
    # Different parameter - should execute
    result3 = await expensive_operation("different")
    assert call_count == 2, "Should execute for different parameter"
    print(f"Different parameter executed (call_count={call_count})")
    
    # Wait for cache to expire
    print("Waiting for cache to expire...")
    await asyncio.sleep(2.5)
    
    # Call again - should execute after expiration
    result4 = await expensive_operation("test")
    assert call_count == 3, "Should execute after cache expiration"
    print(f"After expiration executed (call_count={call_count})")
    
    print("✓ Caching test passed")


async def test_batch_processing():
    """Test batch processing with delays."""
    print("\n=== Testing Batch Processing ===")
    
    processed_items = []
    
    async def process_item(item: str) -> dict:
        """Mock item processor."""
        await asyncio.sleep(0.05)  # Simulate processing
        processed_items.append(item)
        return {"item": item, "processed": True}
    
    items = [f"item{i}" for i in range(12)]
    
    start_time = time.time()
    results = await process_in_batches(
        items=items,
        processor_func=process_item,
        batch_size=5,
        delay_between_batches=0.2
    )
    elapsed = time.time() - start_time
    
    print(f"Processed {len(items)} items in {elapsed:.2f}s")
    print(f"Successful results: {sum(1 for r in results if not isinstance(r, Exception))}")
    print(f"Batches: {(len(items) + 4) // 5}")
    
    assert len(results) == len(items), "Should return result for each item"
    assert all(not isinstance(r, Exception) for r in results), "All items should succeed"
    assert len(processed_items) == len(items), "All items should be processed"
    
    # Check that batching added delays (should take longer than processing all at once)
    min_expected_time = 0.2 * 2  # 2 delays between 3 batches
    assert elapsed >= min_expected_time, f"Should have delays between batches (expected >= {min_expected_time}s)"
    
    print("✓ Batch processing test passed")


async def test_cache_cleanup():
    """Test cache cleanup functionality."""
    print("\n=== Testing Cache Cleanup ===")
    
    cache = get_cache()
    
    # Add some entries
    await cache.set("key1", "value1", ttl_seconds=1)
    await cache.set("key2", "value2", ttl_seconds=10)
    
    # Check they exist
    value1 = await cache.get("key1")
    value2 = await cache.get("key2")
    assert value1 == "value1", "Should retrieve cached value"
    assert value2 == "value2", "Should retrieve cached value"
    print("Added 2 cache entries")
    
    # Wait for first entry to expire
    await asyncio.sleep(1.5)
    
    # Cleanup expired entries
    await cache.cleanup_expired()
    print("Cleaned up expired entries")
    
    # Check that expired entry is gone but valid one remains
    value1_after = await cache.get("key1")
    value2_after = await cache.get("key2")
    assert value1_after is None, "Expired entry should be removed"
    assert value2_after == "value2", "Valid entry should remain"
    print("✓ Cache cleanup test passed")
    
    # Clear all
    await cache.clear()
    print("Cleared all cache entries")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Performance Optimization Tests")
    print("=" * 60)
    
    try:
        await test_multi_query_execution()
        await test_caching()
        await test_batch_processing()
        await test_cache_cleanup()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
