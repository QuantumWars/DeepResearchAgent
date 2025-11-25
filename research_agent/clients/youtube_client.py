"""YouTube client utilities for video ID extraction and transcript fetching."""

import re
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

from research_agent.utils.logger import get_logger
from research_agent.utils.performance import cached

logger = get_logger(__name__)


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from various URL formats.
    
    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://m.youtube.com/watch?v=VIDEO_ID
    - https://youtube.com/watch?v=VIDEO_ID
    
    Args:
        url: YouTube URL
        
    Returns:
        Video ID if found, None otherwise
    """
    try:
        # Parse the URL
        parsed = urlparse(url)
        
        # Handle youtu.be short URLs
        if parsed.netloc in ('youtu.be', 'www.youtu.be'):
            # Video ID is in the path
            video_id = parsed.path.lstrip('/')
            # Remove any query parameters or fragments
            video_id = video_id.split('?')[0].split('#')[0]
            if video_id:
                return video_id
        
        # Handle youtube.com URLs
        if 'youtube.com' in parsed.netloc or 'youtube' in parsed.netloc:
            # Check for /watch?v= format
            if parsed.path == '/watch' or parsed.path.startswith('/watch'):
                query_params = parse_qs(parsed.query)
                if 'v' in query_params:
                    return query_params['v'][0]
            
            # Check for /embed/ format
            if '/embed/' in parsed.path:
                video_id = parsed.path.split('/embed/')[1]
                video_id = video_id.split('?')[0].split('#')[0]
                if video_id:
                    return video_id
            
            # Check for /v/ format
            if '/v/' in parsed.path:
                video_id = parsed.path.split('/v/')[1]
                video_id = video_id.split('?')[0].split('#')[0]
                if video_id:
                    return video_id
        
        logger.debug(f"Could not extract video ID from URL: {url}")
        return None
        
    except Exception as e:
        logger.warning(f"Error extracting video ID from {url}: {e}")
        return None


@cached(ttl_seconds=3600)  # Cache for 1 hour
async def fetch_video_transcript(video_id: str) -> Optional[str]:
    """
    Fetch video transcript using youtube-transcript-api.
    
    Transcripts are cached for 1 hour to avoid repeated API calls
    for the same video.
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        Full transcript text if available, None otherwise
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # Get transcript (tries multiple languages)
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Combine all transcript entries into single text
        transcript_text = "\n".join([entry['text'] for entry in transcript_list])
        
        logger.debug(f"Successfully fetched transcript for video {video_id}")
        return transcript_text
        
    except Exception as e:
        logger.debug(f"Could not fetch transcript for video {video_id}: {e}")
        return None


async def generate_timestamps(video_id: str, target_count: int = 30) -> Optional[List[str]]:
    """
    Generate chapter timestamps from video captions.
    
    Creates evenly distributed timestamps throughout the video with
    associated caption text.
    
    Args:
        video_id: YouTube video ID
        target_count: Target number of timestamps (default 30)
        
    Returns:
        List of timestamp strings in format "MM:SS - Caption text" or None if unavailable
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # Get transcript with timing information
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        if not transcript_list:
            return None
        
        # Calculate total video duration
        last_entry = transcript_list[-1]
        total_duration = last_entry['start'] + last_entry.get('duration', 0)
        
        # Calculate interval between timestamps (minimum 10 seconds)
        interval = max(10, total_duration / target_count)
        
        timestamps = []
        for i in range(target_count):
            target_time = i * interval
            
            # Find the closest caption entry to this time
            closest_entry = min(
                transcript_list,
                key=lambda x: abs(x['start'] - target_time)
            )
            
            # Format timestamp
            time_str = format_timestamp(closest_entry['start'])
            
            # Truncate caption text to 50 characters
            caption_text = closest_entry['text'][:50]
            if len(closest_entry['text']) > 50:
                caption_text += "..."
            
            timestamps.append(f"{time_str} - {caption_text}")
            
            # Stop if we've exceeded video duration
            if target_time >= total_duration:
                break
        
        logger.debug(f"Generated {len(timestamps)} timestamps for video {video_id}")
        return timestamps
        
    except Exception as e:
        logger.debug(f"Could not generate timestamps for video {video_id}: {e}")
        return None


def format_timestamp(seconds: float) -> str:
    """
    Format seconds into MM:SS or HH:MM:SS timestamp.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted timestamp string
    """
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def calculate_date_range(time_range: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Calculate start and end dates based on time range filter.
    
    Args:
        time_range: One of 'day', 'week', 'month', 'year', 'anytime'
        
    Returns:
        Tuple of (start_date, end_date) in ISO format, or (None, None) for 'anytime'
    """
    if time_range == 'anytime':
        return None, None
    
    end_date = datetime.now()
    
    if time_range == 'day':
        start_date = end_date - timedelta(days=1)
    elif time_range == 'week':
        start_date = end_date - timedelta(weeks=1)
    elif time_range == 'month':
        start_date = end_date - timedelta(days=30)
    elif time_range == 'year':
        start_date = end_date - timedelta(days=365)
    else:
        # Default to week if unknown
        start_date = end_date - timedelta(weeks=1)
    
    # Format as ISO date strings
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
