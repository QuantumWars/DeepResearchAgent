"""Unit tests for YouTube search tool."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from research_agent.tools.youtube_search import youtube_search, _process_video
from research_agent.utils.models import VideoResult


@pytest.fixture
def mock_exa_response():
    """Mock Exa API response with YouTube videos."""
    mock_result1 = Mock()
    mock_result1.url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    mock_result1.title = "Test Video 1"
    mock_result1.published_date = "2024-01-15"
    
    mock_result2 = Mock()
    mock_result2.url = "https://youtu.be/abc123def"
    mock_result2.title = "Test Video 2"
    mock_result2.published_date = "2024-01-10"
    
    mock_response = Mock()
    mock_response.results = [mock_result1, mock_result2]
    
    return mock_response


@pytest.fixture
def mock_transcript():
    """Mock video transcript."""
    return [
        {"text": "Welcome to this tutorial", "start": 0.0, "duration": 2.5},
        {"text": "Today we'll learn about Python", "start": 2.5, "duration": 3.0},
        {"text": "Let's get started", "start": 5.5, "duration": 2.0}
    ]


@pytest.mark.asyncio
async def test_youtube_search_basic(mock_exa_response):
    """Test basic YouTube search functionality."""
    with patch('research_agent.tools.youtube_search.Exa') as mock_exa_class, \
         patch('research_agent.tools.youtube_search.fetch_video_transcript', new_callable=AsyncMock) as mock_transcript, \
         patch('research_agent.tools.youtube_search.generate_timestamps', new_callable=AsyncMock) as mock_timestamps:
        
        # Setup mocks
        mock_exa = Mock()
        mock_exa.search_and_contents = Mock(return_value=mock_exa_response)
        mock_exa_class.return_value = mock_exa
        
        mock_transcript.return_value = "Test transcript content"
        mock_timestamps.return_value = ["0:00 - Intro", "1:30 - Main content"]
        
        # Execute search
        result = await youtube_search(query="Python tutorial", time_range="week")
        
        # Verify results
        assert "results" in result
        assert "query" in result
        assert "time_range" in result
        assert "total_videos" in result
        
        assert result["query"] == "Python tutorial"
        assert result["time_range"] == "week"
        assert result["total_videos"] == 2
        assert len(result["results"]) == 2


@pytest.mark.asyncio
async def test_youtube_search_time_ranges(mock_exa_response):
    """Test YouTube search with different time ranges."""
    time_ranges = ['day', 'week', 'month', 'year', 'anytime']
    
    for time_range in time_ranges:
        with patch('research_agent.tools.youtube_search.Exa') as mock_exa_class, \
             patch('research_agent.tools.youtube_search.fetch_video_transcript', new_callable=AsyncMock) as mock_transcript, \
             patch('research_agent.tools.youtube_search.generate_timestamps', new_callable=AsyncMock) as mock_timestamps:
            
            # Setup mocks
            mock_exa = Mock()
            mock_exa.search_and_contents = Mock(return_value=mock_exa_response)
            mock_exa_class.return_value = mock_exa
            
            mock_transcript.return_value = "Test transcript"
            mock_timestamps.return_value = []
            
            # Execute search
            result = await youtube_search(query="test", time_range=time_range)
            
            # Verify time range
            assert result["time_range"] == time_range
            
            # Verify Exa was called with appropriate date filters
            call_args = mock_exa.search_and_contents.call_args
            if time_range != 'anytime':
                assert "start_published_date" in call_args[1]


@pytest.mark.asyncio
async def test_youtube_search_transcript_extraction(mock_exa_response):
    """Test transcript extraction for videos."""
    with patch('research_agent.tools.youtube_search.Exa') as mock_exa_class, \
         patch('research_agent.tools.youtube_search.fetch_video_transcript', new_callable=AsyncMock) as mock_transcript, \
         patch('research_agent.tools.youtube_search.generate_timestamps', new_callable=AsyncMock) as mock_timestamps:
        
        # Setup mocks
        mock_exa = Mock()
        mock_exa.search_and_contents = Mock(return_value=mock_exa_response)
        mock_exa_class.return_value = mock_exa
        
        expected_transcript = "This is the full video transcript"
        mock_transcript.return_value = expected_transcript
        mock_timestamps.return_value = []
        
        # Execute search
        result = await youtube_search(query="test")
        
        # Verify transcript extraction was called
        assert mock_transcript.call_count == 2  # Once per video
        
        # Verify transcripts in results
        for video in result["results"]:
            assert video["captions"] == expected_transcript


@pytest.mark.asyncio
async def test_youtube_search_timestamp_generation(mock_exa_response):
    """Test timestamp generation for videos."""
    with patch('research_agent.tools.youtube_search.Exa') as mock_exa_class, \
         patch('research_agent.tools.youtube_search.fetch_video_transcript', new_callable=AsyncMock) as mock_transcript, \
         patch('research_agent.tools.youtube_search.generate_timestamps', new_callable=AsyncMock) as mock_timestamps:
        
        # Setup mocks
        mock_exa = Mock()
        mock_exa.search_and_contents = Mock(return_value=mock_exa_response)
        mock_exa_class.return_value = mock_exa
        
        mock_transcript.return_value = "Transcript"
        expected_timestamps = [
            "0:00 - Introduction",
            "1:30 - Main topic",
            "5:00 - Conclusion"
        ]
        mock_timestamps.return_value = expected_timestamps
        
        # Execute search
        result = await youtube_search(query="test")
        
        # Verify timestamp generation was called with target_count=30
        assert mock_timestamps.call_count == 2
        call_args = mock_timestamps.call_args_list[0]
        assert call_args[1]["target_count"] == 30
        
        # Verify timestamps in results
        for video in result["results"]:
            assert video["timestamps"] == expected_timestamps


@pytest.mark.asyncio
async def test_youtube_search_deduplication():
    """Test video deduplication by video ID."""
    # Create mock response with duplicate videos
    mock_result1 = Mock()
    mock_result1.url = "https://www.youtube.com/watch?v=abc123"
    mock_result1.title = "Video 1"
    mock_result1.published_date = "2024-01-15"
    
    mock_result2 = Mock()
    mock_result2.url = "https://youtu.be/abc123"  # Same video, different URL format
    mock_result2.title = "Video 1 (duplicate)"
    mock_result2.published_date = "2024-01-15"
    
    mock_result3 = Mock()
    mock_result3.url = "https://www.youtube.com/watch?v=xyz789"
    mock_result3.title = "Video 2"
    mock_result3.published_date = "2024-01-10"
    
    mock_response = Mock()
    mock_response.results = [mock_result1, mock_result2, mock_result3]
    
    with patch('research_agent.tools.youtube_search.Exa') as mock_exa_class, \
         patch('research_agent.tools.youtube_search.fetch_video_transcript', new_callable=AsyncMock) as mock_transcript, \
         patch('research_agent.tools.youtube_search.generate_timestamps', new_callable=AsyncMock) as mock_timestamps:
        
        # Setup mocks
        mock_exa = Mock()
        mock_exa.search_and_contents = Mock(return_value=mock_response)
        mock_exa_class.return_value = mock_exa
        
        mock_transcript.return_value = "Transcript"
        mock_timestamps.return_value = []
        
        # Execute search
        result = await youtube_search(query="test")
        
        # Verify deduplication - should only have 2 unique videos
        assert result["total_videos"] == 2
        assert len(result["results"]) == 2


@pytest.mark.asyncio
async def test_youtube_search_batch_processing(mock_exa_response):
    """Test batch processing of videos."""
    with patch('research_agent.tools.youtube_search.Exa') as mock_exa_class, \
         patch('research_agent.tools.youtube_search.process_in_batches', new_callable=AsyncMock) as mock_batch, \
         patch('research_agent.tools.youtube_search.fetch_video_transcript', new_callable=AsyncMock) as mock_transcript, \
         patch('research_agent.tools.youtube_search.generate_timestamps', new_callable=AsyncMock) as mock_timestamps:
        
        # Setup mocks
        mock_exa = Mock()
        mock_exa.search_and_contents = Mock(return_value=mock_exa_response)
        mock_exa_class.return_value = mock_exa
        
        # Mock batch processing to return VideoResult objects
        mock_video1 = VideoResult(
            video_id="dQw4w9WgXcQ",
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            title="Test Video 1",
            thumbnail_url="https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
            captions="Test transcript",
            timestamps=[],
            published_date="2024-01-15"
        )
        mock_video2 = VideoResult(
            video_id="abc123def",
            url="https://youtu.be/abc123def",
            title="Test Video 2",
            thumbnail_url="https://img.youtube.com/vi/abc123def/hqdefault.jpg",
            captions="Test transcript",
            timestamps=[],
            published_date="2024-01-10"
        )
        mock_batch.return_value = [mock_video1, mock_video2]
        
        # Execute search
        result = await youtube_search(query="test")
        
        # Verify batch processing was called
        assert mock_batch.called
        call_args = mock_batch.call_args[1]
        assert call_args["batch_size"] == 5
        assert call_args["delay_between_batches"] == 0.5


@pytest.mark.asyncio
async def test_youtube_search_error_handling():
    """Test YouTube search handles errors gracefully."""
    with patch('research_agent.tools.youtube_search.Exa') as mock_exa_class:
        # Setup mock to raise error
        mock_exa = Mock()
        mock_exa.search_and_contents = Mock(side_effect=Exception("API Error"))
        mock_exa_class.return_value = mock_exa
        
        # Execute search
        result = await youtube_search(query="test")
        
        # Verify error handling
        assert result["results"] == []
        assert result["total_videos"] == 0
        assert "error" in result


@pytest.mark.asyncio
async def test_youtube_search_no_results():
    """Test YouTube search with no results."""
    mock_response = Mock()
    mock_response.results = []
    
    with patch('research_agent.tools.youtube_search.Exa') as mock_exa_class:
        # Setup mock
        mock_exa = Mock()
        mock_exa.search_and_contents = Mock(return_value=mock_response)
        mock_exa_class.return_value = mock_exa
        
        # Execute search
        result = await youtube_search(query="nonexistent query")
        
        # Verify empty results
        assert result["results"] == []
        assert result["total_videos"] == 0


@pytest.mark.asyncio
async def test_youtube_search_missing_api_key():
    """Test YouTube search with missing API key."""
    with patch('research_agent.tools.youtube_search.get_config') as mock_config:
        # Setup mock config with no API key
        config = Mock()
        config.exa_api_key = None
        mock_config.return_value = config
        
        # Execute search
        result = await youtube_search(query="test")
        
        # Verify error handling
        assert result["results"] == []
        assert "error" in result
        assert "API key not configured" in result["error"]


@pytest.mark.asyncio
async def test_youtube_search_invalid_video_url():
    """Test YouTube search handles invalid video URLs."""
    # Create mock response with invalid URL
    mock_result = Mock()
    mock_result.url = "https://example.com/not-a-youtube-url"
    mock_result.title = "Invalid Video"
    
    mock_response = Mock()
    mock_response.results = [mock_result]
    
    with patch('research_agent.tools.youtube_search.Exa') as mock_exa_class, \
         patch('research_agent.tools.youtube_search.fetch_video_transcript', new_callable=AsyncMock) as mock_transcript, \
         patch('research_agent.tools.youtube_search.generate_timestamps', new_callable=AsyncMock) as mock_timestamps:
        
        # Setup mocks
        mock_exa = Mock()
        mock_exa.search_and_contents = Mock(return_value=mock_response)
        mock_exa_class.return_value = mock_exa
        
        # Execute search
        result = await youtube_search(query="test")
        
        # Verify invalid URLs are skipped
        assert result["total_videos"] == 0
        assert len(result["results"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
