"""Unit tests for Academic search tool."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from research_agent.tools.academic_search import academic_search, _execute_academic_search
from research_agent.utils.models import AcademicResult


@pytest.fixture
def mock_exa_response():
    """Mock Exa API response with academic papers."""
    mock_paper1 = Mock()
    mock_paper1.url = "https://arxiv.org/abs/2301.12345"
    mock_paper1.title = "Deep Learning for Natural Language Processing [arXiv:2301.12345]"
    mock_paper1.summary = "Summary: This paper presents a novel approach to NLP using deep learning."
    mock_paper1.published_date = "2023-01-15"
    mock_paper1.author = "John Doe"
    
    mock_paper2 = Mock()
    mock_paper2.url = "https://arxiv.org/abs/2302.67890"
    mock_paper2.title = "Quantum Computing Applications"
    mock_paper2.summary = "Abstract of quantum computing research and applications."
    mock_paper2.published_date = "2023-02-20"
    mock_paper2.author = "Jane Smith"
    
    mock_response = Mock()
    mock_response.results = [mock_paper1, mock_paper2]
    
    return mock_response


@pytest.mark.asyncio
async def test_academic_search_single_query(mock_exa_response):
    """Test academic search with a single query."""
    with patch('research_agent.tools.academic_search.Exa') as mock_exa_class:
        # Setup mock
        mock_exa = Mock()
        mock_exa.search_and_contents = Mock(return_value=mock_exa_response)
        mock_exa_class.return_value = mock_exa
        
        # Execute search
        result = await academic_search(queries=["deep learning NLP"])
        
        # Verify results
        assert "searches" in result
        assert len(result["searches"]) == 1
        
        # Verify search result structure
        search = result["searches"][0]
        assert search["query"] == "deep learning NLP"
        assert "results" in search
        assert len(search["results"]) == 2


@pytest.mark.asyncio
async def test_academic_search_multi_query(mock_exa_response):
    """Test academic search with multiple queries executed in parallel."""
    with patch('research_agent.tools.academic_search.Exa') as mock_exa_class:
        # Setup mock
        mock_exa = Mock()
        mock_exa.search_and_contents = Mock(return_value=mock_exa_response)
        mock_exa_class.return_value = mock_exa
        
        # Execute search with multiple queries
        result = await academic_search(queries=["quantum computing", "machine learning", "AI ethics"])
        
        # Verify results
        assert len(result["searches"]) == 3
        assert mock_exa.search_and_contents.call_count == 3


@pytest.mark.asyncio
async def test_academic_search_title_cleaning(mock_exa_response):
    """Test that paper titles are cleaned (brackets removed)."""
    with patch('research_agent.tools.academic_search.Exa') as mock_exa_class:
        # Setup mock
        mock_exa = Mock()
        mock_exa.search_and_contents = Mock(return_value=mock_exa_response)
        mock_exa_class.return_value = mock_exa
        
        # Execute search
        result = await academic_search(queries=["test"])
        
        # Verify title cleaning
        search = result["searches"][0]
        results = search["results"]
        
        # First paper should have brackets removed
        assert "[arXiv:2301.12345]" not in results[0].title
        assert "Deep Learning for Natural Language Processing" in results[0].title


@pytest.mark.asyncio
async def test_academic_search_summary_cleaning(mock_exa_response):
    """Test that paper summaries are cleaned (Summary: prefix removed)."""
    with patch('research_agent.tools.academic_search.Exa') as mock_exa_class:
        # Setup mock
        mock_exa = Mock()
        mock_exa.search_and_contents = Mock(return_value=mock_exa_response)
        mock_exa_class.return_value = mock_exa
        
        # Execute search
        result = await academic_search(queries=["test"])
        
        # Verify summary cleaning
        search = result["searches"][0]
        results = search["results"]
        
        # First paper should have "Summary:" prefix removed
        assert not results[0].summary.startswith("Summary:")
        assert "This paper presents" in results[0].summary


@pytest.mark.asyncio
async def test_academic_search_deduplication():
    """Test paper deduplication by URL."""
    # Create mock response with duplicate papers
    mock_paper1 = Mock()
    mock_paper1.url = "https://arxiv.org/abs/2301.12345"
    mock_paper1.title = "Paper 1"
    mock_paper1.summary = "Summary 1"
    mock_paper1.published_date = "2023-01-15"
    mock_paper1.author = "Author 1"
    
    mock_paper2 = Mock()
    mock_paper2.url = "https://arxiv.org/abs/2301.12345"  # Duplicate URL
    mock_paper2.title = "Paper 1 (duplicate)"
    mock_paper2.summary = "Summary 1 duplicate"
    mock_paper2.published_date = "2023-01-15"
    mock_paper2.author = "Author 1"
    
    mock_paper3 = Mock()
    mock_paper3.url = "https://arxiv.org/abs/2302.67890"
    mock_paper3.title = "Paper 2"
    mock_paper3.summary = "Summary 2"
    mock_paper3.published_date = "2023-02-20"
    mock_paper3.author = "Author 2"
    
    mock_response = Mock()
    mock_response.results = [mock_paper1, mock_paper2, mock_paper3]
    
    with patch('research_agent.tools.academic_search.Exa') as mock_exa_class:
        # Setup mock
        mock_exa = Mock()
        mock_exa.search_and_contents = Mock(return_value=mock_response)
        mock_exa_class.return_value = mock_exa
        
        # Execute search
        result = await academic_search(queries=["test"])
        
        # Verify deduplication - should only have 2 unique papers
        search = result["searches"][0]
        assert len(search["results"]) == 2


@pytest.mark.asyncio
async def test_academic_search_skip_no_summary():
    """Test that papers without summaries are skipped."""
    # Create mock response with paper without summary
    mock_paper1 = Mock()
    mock_paper1.url = "https://arxiv.org/abs/2301.12345"
    mock_paper1.title = "Paper with summary"
    mock_paper1.summary = "This is a summary"
    mock_paper1.published_date = "2023-01-15"
    mock_paper1.author = "Author 1"
    
    mock_paper2 = Mock()
    mock_paper2.url = "https://arxiv.org/abs/2302.67890"
    mock_paper2.title = "Paper without summary"
    mock_paper2.summary = None  # No summary
    mock_paper2.published_date = "2023-02-20"
    mock_paper2.author = "Author 2"
    
    mock_response = Mock()
    mock_response.results = [mock_paper1, mock_paper2]
    
    with patch('research_agent.tools.academic_search.Exa') as mock_exa_class:
        # Setup mock
        mock_exa = Mock()
        mock_exa.search_and_contents = Mock(return_value=mock_response)
        mock_exa_class.return_value = mock_exa
        
        # Execute search
        result = await academic_search(queries=["test"])
        
        # Verify only paper with summary is included
        search = result["searches"][0]
        assert len(search["results"]) == 1
        assert search["results"][0].title == "Paper with summary"


@pytest.mark.asyncio
async def test_academic_search_max_results():
    """Test max_results parameter."""
    with patch('research_agent.tools.academic_search.Exa') as mock_exa_class:
        # Setup mock
        mock_exa = Mock()
        mock_exa.search_and_contents = Mock(return_value=Mock(results=[]))
        mock_exa_class.return_value = mock_exa
        
        # Execute search with custom max_results
        result = await academic_search(
            queries=["q1", "q2"],
            max_results=[10, 30]
        )
        
        # Verify max_results passed to API
        calls = mock_exa.search_and_contents.call_args_list
        assert calls[0][1]["num_results"] == 10
        assert calls[1][1]["num_results"] == 30


@pytest.mark.asyncio
async def test_academic_search_default_max_results():
    """Test default max_results (20 per query)."""
    with patch('research_agent.tools.academic_search.Exa') as mock_exa_class:
        # Setup mock
        mock_exa = Mock()
        mock_exa.search_and_contents = Mock(return_value=Mock(results=[]))
        mock_exa_class.return_value = mock_exa
        
        # Execute search with defaults
        result = await academic_search(queries=["test"])
        
        # Verify default max_results
        call_args = mock_exa.search_and_contents.call_args[1]
        assert call_args["num_results"] == 20


@pytest.mark.asyncio
async def test_academic_search_category_filter():
    """Test that search uses research paper category."""
    with patch('research_agent.tools.academic_search.Exa') as mock_exa_class:
        # Setup mock
        mock_exa = Mock()
        mock_exa.search_and_contents = Mock(return_value=Mock(results=[]))
        mock_exa_class.return_value = mock_exa
        
        # Execute search
        result = await academic_search(queries=["test"])
        
        # Verify category filter
        call_args = mock_exa.search_and_contents.call_args[1]
        assert call_args["category"] == "research paper"


@pytest.mark.asyncio
async def test_academic_search_summary_query():
    """Test that search requests abstract summaries."""
    with patch('research_agent.tools.academic_search.Exa') as mock_exa_class:
        # Setup mock
        mock_exa = Mock()
        mock_exa.search_and_contents = Mock(return_value=Mock(results=[]))
        mock_exa_class.return_value = mock_exa
        
        # Execute search
        result = await academic_search(queries=["test"])
        
        # Verify summary query
        call_args = mock_exa.search_and_contents.call_args[1]
        assert "summary" in call_args
        assert call_args["summary"]["query"] == "Abstract of the paper"


@pytest.mark.asyncio
async def test_academic_search_error_handling():
    """Test academic search handles API errors gracefully."""
    with patch('research_agent.tools.academic_search.Exa') as mock_exa_class:
        # Setup mock to raise error
        mock_exa = Mock()
        mock_exa.search_and_contents = Mock(side_effect=Exception("API Error"))
        mock_exa_class.return_value = mock_exa
        
        # Execute search
        result = await academic_search(queries=["test"])
        
        # Verify error handling - should return empty results
        assert result["searches"] == []


@pytest.mark.asyncio
async def test_academic_search_empty_queries():
    """Test academic search with empty queries list."""
    result = await academic_search(queries=[])
    
    # Verify empty result
    assert result["searches"] == []


@pytest.mark.asyncio
async def test_academic_search_query_limit():
    """Test academic search limits queries to maximum of 5."""
    with patch('research_agent.tools.academic_search.Exa') as mock_exa_class:
        # Setup mock
        mock_exa = Mock()
        mock_exa.search_and_contents = Mock(return_value=Mock(results=[]))
        mock_exa_class.return_value = mock_exa
        
        # Execute search with more than 5 queries
        result = await academic_search(queries=["q1", "q2", "q3", "q4", "q5", "q6", "q7"])
        
        # Verify only 5 queries executed
        assert len(result["searches"]) == 5
        assert mock_exa.search_and_contents.call_count == 5


@pytest.mark.asyncio
async def test_academic_search_missing_api_key():
    """Test academic search with missing API key."""
    with patch('research_agent.tools.academic_search.get_config') as mock_config, \
         patch('research_agent.tools.academic_search.Exa'):
        # Setup mock config with no API key
        config = Mock()
        config.exa_api_key = None
        mock_config.return_value = config
        
        # Execute search
        result = await academic_search(queries=["test"])
        
        # Verify error handling
        assert result["searches"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
