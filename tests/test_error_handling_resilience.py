"""Test error handling and resilience features."""

import asyncio
import httpx
from research_agent.utils.retry import RetryConfig, retry_async, with_retry
from research_agent.utils.error_handling import (
    safe_tool_execution,
    validate_api_key,
    create_error_response
)
from research_agent.clients.client_manager import get_client_manager


async def test_retry_logic():
    """Test retry logic with exponential backoff."""
    print("\n=== Testing Retry Logic ===")
    
    # Test successful retry after failures
    attempt_count = 0
    
    async def flaky_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise httpx.RequestError("Simulated failure")
        return {"success": True, "attempts": attempt_count}
    
    config = RetryConfig(max_retries=5, initial_backoff=0.1)
    result = await retry_async(flaky_function, config=config)
    
    print(f"✓ Retry succeeded after {result['attempts']} attempts")
    assert result['success'] is True
    assert result['attempts'] == 3


async def test_retry_decorator():
    """Test retry decorator."""
    print("\n=== Testing Retry Decorator ===")
    
    call_count = 0
    
    @with_retry(RetryConfig(max_retries=3, initial_backoff=0.1))
    async def decorated_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise httpx.RequestError("Simulated failure")
        return {"success": True}
    
    result = await decorated_function()
    print(f"✓ Decorated function succeeded after {call_count} calls")
    assert result['success'] is True


async def test_rate_limit_handling():
    """Test rate limit handling with Retry-After."""
    print("\n=== Testing Rate Limit Handling ===")
    
    attempt_count = 0
    
    async def rate_limited_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            # Simulate 429 rate limit error
            response = httpx.Response(
                status_code=429,
                headers={"Retry-After": "0.1"},
                request=httpx.Request("GET", "http://test.com")
            )
            raise httpx.HTTPStatusError(
                "Rate limited",
                request=response.request,
                response=response
            )
        return {"success": True}
    
    config = RetryConfig(max_retries=3, initial_backoff=0.1)
    result = await retry_async(rate_limited_function, config=config)
    
    print(f"✓ Rate limit retry succeeded after {attempt_count} attempts")
    assert result['success'] is True


async def test_error_handling_decorator():
    """Test safe tool execution decorator."""
    print("\n=== Testing Error Handling Decorator ===")
    
    @safe_tool_execution()
    async def tool_with_error():
        raise ValueError("Simulated error")
    
    result = await tool_with_error()
    print(f"✓ Error caught and returned: {result.get('error', '')[:50]}")
    assert 'error' in result
    assert 'Invalid input' in result['error']


async def test_api_key_validation():
    """Test API key validation."""
    print("\n=== Testing API Key Validation ===")
    
    try:
        validate_api_key(None, "TestService")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✓ API key validation works: {str(e)[:50]}")
        assert "TestService" in str(e)


async def test_error_response_creation():
    """Test error response creation."""
    print("\n=== Testing Error Response Creation ===")
    
    response = create_error_response(
        "Test error",
        query="test query",
        results=[]
    )
    
    print(f"✓ Error response created: {response}")
    assert response['error'] == "Test error"
    assert response['query'] == "test query"
    assert response['results'] == []


async def test_client_manager():
    """Test API client manager."""
    print("\n=== Testing API Client Manager ===")
    
    manager = get_client_manager()
    
    # Get a generic client
    client1 = manager.get_generic_client("test_client")
    print(f"✓ Created client: test_client")
    
    # Get the same client again (should reuse)
    client2 = manager.get_generic_client("test_client")
    assert client1 is client2
    print(f"✓ Client reuse works")
    
    # Get stats
    stats = manager.get_stats()
    print(f"✓ Manager stats: {stats}")
    assert stats['total_clients'] >= 1
    assert 'test_client' in stats['client_names']
    
    # Close specific client
    await manager.close_client("test_client")
    print(f"✓ Closed specific client")
    
    # Verify it's removed
    stats = manager.get_stats()
    assert 'test_client' not in stats['client_names']
    
    # Close all remaining clients
    await manager.close_all()
    print(f"✓ Closed all clients")


async def test_client_manager_context():
    """Test client manager context manager."""
    print("\n=== Testing Client Manager Context ===")
    
    from research_agent.clients.client_manager import managed_client_context
    
    async with managed_client_context() as manager:
        client = manager.get_generic_client("context_test")
        print(f"✓ Created client in context")
        assert client is not None
    
    # Verify clients are closed after context
    stats = manager.get_stats()
    print(f"✓ Context cleanup complete, clients: {stats['total_clients']}")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Error Handling and Resilience Features")
    print("=" * 60)
    
    try:
        await test_retry_logic()
        await test_retry_decorator()
        await test_rate_limit_handling()
        await test_error_handling_decorator()
        await test_api_key_validation()
        await test_error_response_creation()
        await test_client_manager()
        await test_client_manager_context()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
