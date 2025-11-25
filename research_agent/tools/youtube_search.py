"""YouTube search tool for finding and extracting video content."""

import asyncio
from typing import Literal, List, Dict, Any, Tuple
from langchain.tools import tool

from research_agent.utils.config import get_config
from research_agent.utils.models import VideoResult
from research_agent.utils.logger import get_logger
from research_agent.utils.performance import process_in_batches
from research_agent.clients.youtube_client import (
    extract_video_id,
    fetch_video_transcript,
    generate_timestamps,
    calculate_date_range
)

logger = get_logger(__name__)


@tool
async def youtube_search(
    query: str,
    time_range: Literal['day', 'week', 'month', 'year', 'anytime'] = 'week'
) -> Dict[str, Any]:
    """
    Search YouTube videos and extract transcripts with timestamps.
    
    This tool searches YouTube using the Exa API with domain filtering,
    extracts video transcripts when available, and generates chapter
    timestamps for easy navigation.
    
    Args:
        query: Search query for finding videos
        time_range: Time range filter - 'day', 'week', 'month', 'year', or 'anytime' (default: 'week')
    
    Returns:
        Dictionary containing:
        - results: List of VideoResult objects with transcripts and timestamps
        - query: The search query used
        - time_range: The time range filter applied
        - total_videos: Number of videos found
    
    Example:
        >>> result = await youtube_search("Python tutorial", time_range="week")
        >>> print(f"Found {result['total_videos']} videos")
        >>> for video in result['results']:
        ...     print(f"{video.title}: {video.url}")
    """
    try:
        from exa_py import Exa
        
        config = get_config()
        
        # Validate Exa API key
        if not config.exa_api_key:
            logger.error("Exa API key not configured")
            return {
                "results": [],
                "query": query,
                "time_range": time_range,
                "total_videos": 0,
                "error": "Exa API key not configured"
            }
        
        exa = Exa(api_key=config.exa_api_key)
        
        # Calculate date range for filtering
        start_date, end_date = calculate_date_range(time_range)
        
        logger.info(
            f"Searching YouTube videos",
            extra={"context": {
                "query": query,
                "time_range": time_range,
                "start_date": start_date,
                "end_date": end_date
            }}
        )
        
        # Build search parameters
        search_params = {
            "type": "auto",
            "num_results": 5,
            "include_domains": ["youtube.com", "youtu.be", "m.youtube.com"]
        }
        
        # Add date range if not 'anytime'
        if start_date:
            search_params["start_published_date"] = start_date
        if end_date:
            search_params["end_published_date"] = end_date
        
        # Execute search
        response = exa.search_and_contents(query, **search_params)
        
        if not response.results:
            logger.info(f"No YouTube videos found for query: {query}")
            return {
                "results": [],
                "query": query,
                "time_range": time_range,
                "total_videos": 0
            }
        
        # Deduplicate and prepare video items for batch processing
        video_items = []
        seen_video_ids = set()
        
        for result in response.results:
            # Extract video ID
            video_id = extract_video_id(result.url)
            
            if not video_id:
                logger.debug(f"Could not extract video ID from URL: {result.url}")
                continue
            
            # Skip duplicates
            if video_id in seen_video_ids:
                logger.debug(f"Skipping duplicate video: {video_id}")
                continue
            
            seen_video_ids.add(video_id)
            video_items.append((video_id, result))
        
        # Process videos in batches with rate limiting
        batch_results = await process_in_batches(
            items=video_items,
            processor_func=lambda item: _process_video(item[0], item[1]),
            batch_size=5,
            delay_between_batches=0.5
        )
        
        # Filter successful results
        videos = []
        for video_result in batch_results:
            if isinstance(video_result, VideoResult):
                videos.append(video_result)
            elif isinstance(video_result, Exception):
                logger.warning(f"Error processing video: {video_result}")
        
        logger.info(
            f"YouTube search completed",
            extra={"context": {
                "query": query,
                "total_videos": len(videos),
                "time_range": time_range
            }}
        )
        
        return {
            "results": [video.model_dump() for video in videos],
            "query": query,
            "time_range": time_range,
            "total_videos": len(videos)
        }
        
    except Exception as e:
        logger.error(
            f"YouTube search failed: {str(e)}",
            exc_info=True,
            extra={"context": {"query": query, "error": str(e)}}
        )
        return {
            "results": [],
            "query": query,
            "time_range": time_range,
            "total_videos": 0,
            "error": str(e)
        }


async def _process_video(video_id: str, search_result: Any) -> VideoResult:
    """
    Process a single video: fetch transcript and generate timestamps.
    
    Args:
        video_id: YouTube video ID
        search_result: Exa search result object
        
    Returns:
        VideoResult object with all metadata
    """
    try:
        # Fetch transcript and generate timestamps concurrently
        transcript_task = fetch_video_transcript(video_id)
        timestamps_task = generate_timestamps(video_id, target_count=30)
        
        captions, timestamps = await asyncio.gather(
            transcript_task,
            timestamps_task,
            return_exceptions=True
        )
        
        # Handle exceptions from gather
        if isinstance(captions, Exception):
            logger.debug(f"Transcript fetch failed for {video_id}: {captions}")
            captions = None
        
        if isinstance(timestamps, Exception):
            logger.debug(f"Timestamp generation failed for {video_id}: {timestamps}")
            timestamps = None
        
        # Build thumbnail URL
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        
        # Create VideoResult
        video = VideoResult(
            video_id=video_id,
            url=search_result.url,
            title=search_result.title if hasattr(search_result, 'title') else None,
            thumbnail_url=thumbnail_url,
            captions=captions,
            timestamps=timestamps,
            published_date=search_result.published_date if hasattr(search_result, 'published_date') else None
        )
        
        logger.debug(
            f"Processed video {video_id}",
            extra={"context": {
                "video_id": video_id,
                "has_captions": captions is not None,
                "has_timestamps": timestamps is not None
            }}
        )
        
        return video
        
    except Exception as e:
        logger.error(f"Error processing video {video_id}: {e}", exc_info=True)
        raise
