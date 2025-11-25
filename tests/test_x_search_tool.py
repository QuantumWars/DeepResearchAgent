"""Unit tests for X (Twitter) search tool."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from research_agent.tools.x_search import x_search, _execute_x_search
from research_agent.utils.models import XPost, XSearchResult


@pytest.fixture
def mock_xai_response():
    """Mock XAI API response."""
    return {
        "choices": [{
            "message": {
                "content": "Test content about AI and machine learning"
            }
        }],
        "citations": [
            {"text": "Citation 1", "url": "https://x.com/post1"},
            {"text": "Citation 2", "url": "https://x.com/post2"}
        ],
        "sources": [
            {
                "type": "x",
                "text": "This is a test post about AI",
                "link": "https://x.com/user1/status/123",
                "favorites": 150,
                "views": 5000,
                "author": "@testuser1"
            },
            {
                "type": "x",
                "text": "Another post about machine learning",
                "link": "https://x.com/user2/status/456",
                "favorites": 200,
                "views": 8000,
                "author": "@testuser2"
            }
        ]
    }


@pytest.mark.asyncio
async def test_x_search_single_query(mock_xai_response):
    """Test X search with a single query."""
    with patch('research_agent.tools.x_search.XAIClient') as mock_client_class:
        # Setup mock
        mock_client = AsyncMock()
        mock_client.search_with_grok = AsyncMock(return_value=mock_xai_response)
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Execute search
        result = await x_search(queries=["AI news"])
        
        # Verify results
        assert "searches" in result
        assert "date_range" in result
        assert "handles" in result
        assert len(result["searches"]) == 1
        
        # Verify search result structure
        search = result["searches"][0]
        assert search.content == "Test content about AI and machine learning"
        assert len(search.citations) == 2
        assert len(search.sources) == 2
        assert search.query == "AI news"


@pytest.mark.asyncio
async def test_x_search_multi_query(mock_xai_response):
    """Test X search with multiple queries executed in parallel."""
    with patch('research_agent.tools.x_search.XAIClient') as mock_client_class:
        # Setup mock
        mock_client = AsyncMock()
        mock_client.search_with_grok = AsyncMock(return_value=mock_xai_response)
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Execute search with multiple queries
        result = await x_search(queries=["AI news", "machine learning", "deep learning"])
        
        # Verify results
        assert len(result["searches"]) == 3
        assert mock_client.search_with_grok.call_count == 3


@pytest.mark.asyncio
async def test_x_search_date_range_handling():
    """Test X search with custom date range."""
    with patch('research_agent.tools.x_search.XAIClient') as mock_client_class:
        # Setup mock
        mock_client = AsyncMock()
        mock_client.search_with_grok = AsyncMock(return_value={
            "choices": [{"message": {"content": "Test"}}],
            "citations": [],
            "sources": []
        })
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Execute search with custom date range
        start_date = "2024-01-01"
        end_date = "2024-01-15"
        result = await x_search(
            queries=["test"],
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify date range in result
        assert result["date_range"] == f"{start_date} to {end_date}"
        
        # Verify date range passed to API
        call_args = mock_client.search_with_grok.call_args
        assert call_args[1]["start_date"] == start_date
        assert call_args[1]["end_date"] == end_date


@pytest.mark.asyncio
async def test_x_search_default_date_range():
    """Test X search uses default 15-day date range."""
    with patch('research_agent.tools.x_search.XAIClient') as mock_client_class:
        # Setup mock
        mock_client = AsyncMock()
        mock_client.search_with_grok = AsyncMock(return_value={
            "choices": [{"message": {"content": "Test"}}],
            "citations": [],
            "sources": []
        })
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Execute search without date range
        result = await x_search(queries=["test"])
        
        # Verify default date range (15 days)
        expected_start = (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d')
        expected_end = datetime.now().strftime('%Y-%m-%d')
        assert result["date_range"] == f"{expected_start} to {expected_end}"


@pytest.mark.asyncio
async def test_x_search_handle_filtering():
    """Test X search with handle filtering."""
    with patch('research_agent.tools.x_search.XAIClient') as mock_client_class:
        # Setup mock
        mock_client = AsyncMock()
        mock_client.search_with_grok = AsyncMock(return_value={
            "choices": [{"message": {"content": "Test"}}],
            "citations": [],
            "sources": []
        })
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Execute search with handle filtering
        include_handles = ["@elonmusk", "@sama"]
        exclude_handles = ["@spammer"]
        result = await x_search(
            queries=["AI"],
            include_x_handles=include_handles,
            exclude_x_handles=exclude_handles
        )
        
        # Verify handles in result
        assert set(result["handles"]) == set(include_handles + exclude_handles)
        
        # Verify handles passed to API
        call_args = mock_client.search_with_grok.call_args
        assert call_args[1]["include_x_handles"] == include_handles
        assert call_args[1]["exclude_x_handles"] == exclude_handles


@pytest.mark.asyncio
async def test_x_search_engagement_filtering():
    """Test X search with engagement metrics filtering."""
    with patch('research_agent.tools.x_search.XAIClient') as mock_client_class:
        # Setup mock
        mock_client = AsyncMock()
        mock_client.search_with_grok = AsyncMock(return_value={
            "choices": [{"message": {"content": "Test"}}],
            "citations": [],
            "sources": []
        })
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Execute search with engagement filtering
        result = await x_search(
            queries=["viral posts"],
            post_favorites_count=1000,
            post_view_count=50000
        )
        
        # Verify engagement filters passed to API
        call_args = mock_client.search_with_grok.call_args
        assert call_args[1]["post_favorites_count"] == 1000
        assert call_args[1]["post_view_count"] == 50000


@pytest.mark.asyncio
async def test_x_search_error_handling():
    """Test X search handles API errors gracefully."""
    with patch('research_agent.tools.x_search.XAIClient') as mock_client_class:
        # Setup mock to raise error
        mock_client = AsyncMock()
        mock_client.search_with_grok = AsyncMock(side_effect=Exception("API Error"))
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Execute search
        result = await x_search(queries=["test"])
        
        # Verify error handling - should return empty results
        assert result["searches"] == []
        assert "date_range" in result
        assert "handles" in result


@pytest.mark.asyncio
async def test_x_search_empty_queries():
    """Test X search with empty queries list."""
    result = await x_search(queries=[])
    
    # Verify empty result
    assert result["searches"] == []
    assert result["date_range"] == ""
    assert result["handles"] == []


@pytest.mark.asyncio
async def test_x_search_query_limit():
    """Test X search limits queries to maximum of 5."""
    with patch('research_agent.tools.x_search.XAIClient') as mock_client_class:
        # Setup mock
        mock_client = AsyncMock()
        mock_client.search_with_grok = AsyncMock(return_value={
            "choices": [{"message": {"content": "Test"}}],
            "citations": [],
            "sources": []
        })
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Execute search with more than 5 queries
        result = await x_search(queries=["q1", "q2", "q3", "q4", "q5", "q6", "q7"])
        
        # Verify only 5 queries executed
        assert len(result["searches"]) == 5
        assert mock_client.search_with_grok.call_count == 5


@pytest.mark.asyncio
async def test_x_search_handle_limit():
    """Test X search limits handles to maximum of 10."""
    with patch('research_agent.tools.x_search.XAIClient') as mock_client_class:
        # Setup mock
        mock_client = AsyncMock()
        mock_client.search_with_grok = AsyncMock(return_value={
            "choices": [{"message": {"content": "Test"}}],
            "citations": [],
            "sources": []
        })
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Execute search with more than 10 handles
        many_handles = [f"@user{i}" for i in range(15)]
        result = await x_search(
            queries=["test"],
            include_x_handles=many_handles
        )
        
        # Verify handles limited to 10
        call_args = mock_client.search_with_grok.call_args
        assert len(call_args[1]["include_x_handles"]) == 10


@pytest.mark.asyncio
async def test_x_search_max_results_per_query():
    """Test X search with custom max_results per query."""
    with patch('research_agent.tools.x_search.XAIClient') as mock_client_class:
        # Setup mock
        mock_client = AsyncMock()
        mock_client.search_with_grok = AsyncMock(return_value={
            "choices": [{"message": {"content": "Test"}}],
            "citations": [],
            "sources": []
        })
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Execute search with custom max_results
        result = await x_search(
            queries=["q1", "q2"],
            max_results=[10, 20]
        )
        
        # Verify max_results passed correctly
        calls = mock_client.search_with_grok.call_args_list
        assert calls[0][1]["max_results"] == 10
        assert calls[1][1]["max_results"] == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
