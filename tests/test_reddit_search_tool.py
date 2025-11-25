"""Unit tests for Reddit search tool."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from research_agent.tools.reddit_search import reddit_search, _execute_reddit_search, _extract_subreddit, _time_range_to_days
from research_agent.utils.models import RedditResult


@pytest.fixture
def mock_tavily_response():
    """Mock Tavily API response with Reddit results."""
    return {
        "results": [
            {
                "url": "https://www.reddit.com/r/python/comments/abc123/great_python_tutorial/",
                "title": "Great Python Tutorial",
                "content": "This is an excellent tutorial for learning Python basics.",
                "score": 0.95,
                "published_date": "2024-01-15"
            },
            {
                "url": "https://www.reddit.com/r/learnprogramming/comments/def456/help_with_loops/",
                "title": "Help with loops",
                "content": "I'm having trouble understanding for loops in Python.",
                "score": 0.87,
                "published_date": "2024-01-14"
            },
            {
                "url": "https://www.reddit.com/r/programming/",
                "title": "Programming Subreddit",
                "content": "General programming discussions",
                "score": 0.75,
                "published_date": "2024-01-10"
            }
        ]
    }


@pytest.mark.asyncio
async def test_reddit_search_single_query(mock_tavily_response):
    """Test Reddit search with a single query."""
    with patch('research_agent.tools.reddit_search.TavilyClient') as mock_tavily_class:
        # Setup mock
        mock_tavily = Mock()
        mock_tavily.search = Mock(return_value=mock_tavily_response)
        mock_tavily_class.return_value = mock_tavily
        
        # Execute search
        result = await reddit_search(queries=["Python tutorial"])
        
        # Verify results
        assert "searches" in result
        assert len(result["searches"]) == 1
        
        # Verify search result structure
        search = result["searches"][0]
        assert search["query"] == "Python tutorial"
        assert "results" in search
        assert "time_range" in search
        assert len(search["results"]) == 3


@pytest.mark.asyncio
async def test_reddit_search_multi_query(mock_tavily_response):
    """Test Reddit search with multiple queries executed in parallel."""
    with patch('research_agent.tools.reddit_search.TavilyClient') as mock_tavily_class:
        # Setup mock
        mock_tavily = Mock()
        mock_tavily.search = Mock(return_value=mock_tavily_response)
        mock_tavily_class.return_value = mock_tavily
        
        # Execute search with multiple queries
        result = await reddit_search(queries=["Python", "JavaScript", "Rust"])
        
        # Verify results
        assert len(result["searches"]) == 3
        assert mock_tavily.search.call_count == 3


@pytest.mark.asyncio
async def test_reddit_search_subreddit_extraction(mock_tavily_response):
    """Test subreddit extraction from URLs."""
    with patch('research_agent.tools.reddit_search.TavilyClient') as mock_tavily_class:
        # Setup mock
        mock_tavily = Mock()
        mock_tavily.search = Mock(return_value=mock_tavily_response)
        mock_tavily_class.return_value = mock_tavily
        
        # Execute search
        result = await reddit_search(queries=["test"])
        
        # Verify subreddit extraction
        search = result["searches"][0]
        results = search["results"]
        
        assert results[0].subreddit == "python"
        assert results[1].subreddit == "learnprogramming"
        assert results[2].subreddit == "programming"


@pytest.mark.asyncio
async def test_reddit_search_post_detection():
    """Test detection of Reddit posts vs subreddit pages."""
    with patch('research_agent.tools.reddit_search.TavilyClient') as mock_tavily_class:
        # Setup mock
        mock_tavily = Mock()
        mock_tavily.search = Mock(return_value={
            "results": [
                {
                    "url": "https://www.reddit.com/r/python/comments/abc123/post/",
                    "title": "Post",
                    "content": "Content",
                    "score": 0.9
                },
                {
                    "url": "https://www.reddit.com/r/python/",
                    "title": "Subreddit",
                    "content": "Content",
                    "score": 0.8
                }
            ]
        })
        mock_tavily_class.return_value = mock_tavily
        
        # Execute search
        result = await reddit_search(queries=["test"])
        
        # Verify post detection
        search = result["searches"][0]
        results = search["results"]
        
        assert results[0].is_reddit_post is True  # Has /comments/ in URL
        assert results[1].is_reddit_post is False  # No /comments/ in URL


@pytest.mark.asyncio
async def test_reddit_search_time_range_filtering():
    """Test time range filtering."""
    with patch('research_agent.tools.reddit_search.TavilyClient') as mock_tavily_class:
        # Setup mock
        mock_tavily = Mock()
        mock_tavily.search = Mock(return_value={"results": []})
        mock_tavily_class.return_value = mock_tavily
        
        # Execute search with different time ranges
        time_ranges = ['day', 'week', 'month', 'year']
        result = await reddit_search(
            queries=["q1", "q2", "q3", "q4"],
            time_range=time_ranges
        )
        
        # Verify time ranges passed to API
        calls = mock_tavily.search.call_args_list
        assert calls[0][1]["days"] == 1  # day
        assert calls[1][1]["days"] == 7  # week
        assert calls[2][1]["days"] == 30  # month
        assert calls[3][1]["days"] == 365  # year


@pytest.mark.asyncio
async def test_reddit_search_max_results():
    """Test max_results parameter."""
    with patch('research_agent.tools.reddit_search.TavilyClient') as mock_tavily_class:
        # Setup mock
        mock_tavily = Mock()
        mock_tavily.search = Mock(return_value={"results": []})
        mock_tavily_class.return_value = mock_tavily
        
        # Execute search with custom max_results
        result = await reddit_search(
            queries=["q1", "q2"],
            max_results=[10, 30]
        )
        
        # Verify max_results passed to API (Tavily requests more to account for filtering)
        calls = mock_tavily.search.call_args_list
        assert calls[0][1]["max_results"] >= 10
        assert calls[1][1]["max_results"] >= 30


@pytest.mark.asyncio
async def test_reddit_search_default_parameters():
    """Test default parameters (max_results=20, time_range='week')."""
    with patch('research_agent.tools.reddit_search.TavilyClient') as mock_tavily_class:
        # Setup mock
        mock_tavily = Mock()
        mock_tavily.search = Mock(return_value={"results": []})
        mock_tavily_class.return_value = mock_tavily
        
        # Execute search with defaults
        result = await reddit_search(queries=["test"])
        
        # Verify defaults
        search = result["searches"][0]
        assert search["time_range"] == "week"
        
        # Verify API call
        call_args = mock_tavily.search.call_args[1]
        assert call_args["days"] == 7  # week


@pytest.mark.asyncio
async def test_reddit_search_error_handling():
    """Test Reddit search handles API errors gracefully."""
    with patch('research_agent.tools.reddit_search.TavilyClient') as mock_tavily_class:
        # Setup mock to raise error
        mock_tavily = Mock()
        mock_tavily.search = Mock(side_effect=Exception("API Error"))
        mock_tavily_class.return_value = mock_tavily
        
        # Execute search
        result = await reddit_search(queries=["test"])
        
        # Verify error handling - should return empty results
        assert result["searches"] == []


@pytest.mark.asyncio
async def test_reddit_search_empty_queries():
    """Test Reddit search with empty queries list."""
    result = await reddit_search(queries=[])
    
    # Verify empty result
    assert result["searches"] == []


@pytest.mark.asyncio
async def test_reddit_search_query_limit():
    """Test Reddit search limits queries to maximum of 5."""
    with patch('research_agent.tools.reddit_search.TavilyClient') as mock_tavily_class:
        # Setup mock
        mock_tavily = Mock()
        mock_tavily.search = Mock(return_value={"results": []})
        mock_tavily_class.return_value = mock_tavily
        
        # Execute search with more than 5 queries
        result = await reddit_search(queries=["q1", "q2", "q3", "q4", "q5", "q6", "q7"])
        
        # Verify only 5 queries executed
        assert len(result["searches"]) == 5
        assert mock_tavily.search.call_count == 5


def test_extract_subreddit():
    """Test subreddit extraction utility function."""
    # Test various URL formats
    assert _extract_subreddit("https://www.reddit.com/r/python/comments/abc/") == "python"
    assert _extract_subreddit("https://reddit.com/r/learnprogramming/") == "learnprogramming"
    assert _extract_subreddit("https://www.reddit.com/r/AskReddit/comments/xyz/title/") == "AskReddit"
    assert _extract_subreddit("https://www.reddit.com/") == "unknown"
    assert _extract_subreddit("https://example.com/") == "unknown"


def test_time_range_to_days():
    """Test time range to days conversion."""
    assert _time_range_to_days("day") == 1
    assert _time_range_to_days("week") == 7
    assert _time_range_to_days("month") == 30
    assert _time_range_to_days("year") == 365
    assert _time_range_to_days("invalid") is None


@pytest.mark.asyncio
async def test_reddit_search_missing_api_key():
    """Test Reddit search with missing API key."""
    with patch('research_agent.tools.reddit_search.get_config') as mock_config, \
         patch('research_agent.tools.reddit_search.TavilyClient'):
        # Setup mock config with no API key
        config = Mock()
        config.tavily_api_key = None
        mock_config.return_value = config
        
        # Execute search
        result = await reddit_search(queries=["test"])
        
        # Verify error handling
        assert result["searches"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
