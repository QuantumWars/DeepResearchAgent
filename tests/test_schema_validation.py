"""Schema validation tests for Pydantic models."""

import pytest
from pydantic import ValidationError
from research_agent.utils.models import (
    XPost,
    XSearchResult,
    VideoResult,
    RedditResult,
    AcademicResult,
    SearchResult,
    ResearchTask,
    ResearchPlan,
    CodeExecutionResult,
    ResearchResult,
    Memory
)


# XPost model tests
def test_xpost_valid():
    """Test XPost with valid data."""
    post = XPost(
        text="This is a test post",
        link="https://x.com/user/status/123",
        favorites=100,
        views=5000,
        author="@testuser"
    )
    
    assert post.text == "This is a test post"
    assert post.favorites == 100
    assert post.views == 5000


def test_xpost_invalid_link():
    """Test XPost with invalid link format."""
    with pytest.raises(ValidationError) as exc_info:
        XPost(
            text="Test post",
            link="not-a-url",
            favorites=100
        )
    
    assert "Link must be a valid URL" in str(exc_info.value)


def test_xpost_negative_metrics():
    """Test XPost with negative engagement metrics."""
    with pytest.raises(ValidationError):
        XPost(
            text="Test post",
            link="https://x.com/post",
            favorites=-10
        )


def test_xpost_minimal():
    """Test XPost with minimal required fields."""
    post = XPost(
        text="Minimal post",
        link="https://x.com/post"
    )
    
    assert post.text == "Minimal post"
    assert post.favorites is None
    assert post.views is None


# XSearchResult model tests
def test_xsearch_result_valid():
    """Test XSearchResult with valid data."""
    result = XSearchResult(
        content="Search results content",
        citations=[{"text": "Citation 1", "url": "https://example.com"}],
        sources=[
            XPost(text="Post 1", link="https://x.com/post1"),
            XPost(text="Post 2", link="https://x.com/post2")
        ],
        query="test query",
        date_range="2024-01-01 to 2024-01-15",
        handles=["@user1", "@user2"]
    )
    
    assert result.query == "test query"
    assert len(result.sources) == 2
    assert len(result.handles) == 2


def test_xsearch_result_handle_validation():
    """Test XSearchResult handle validation and normalization."""
    result = XSearchResult(
        content="Content",
        query="test",
        date_range="2024-01-01 to 2024-01-15",
        handles=["user1", "@user2", "@user_3"]
    )
    
    # All handles should be normalized with @ prefix
    assert all(h.startswith('@') for h in result.handles)
    assert "@user1" in result.handles
    assert "@user2" in result.handles
    assert "@user_3" in result.handles


def test_xsearch_result_invalid_handle():
    """Test XSearchResult with invalid handle format."""
    with pytest.raises(ValidationError) as exc_info:
        XSearchResult(
            content="Content",
            query="test",
            date_range="2024-01-01 to 2024-01-15",
            handles=["@user-with-dash"]  # Dashes not allowed
        )
    
    assert "Invalid X handle format" in str(exc_info.value)


def test_xsearch_result_invalid_date_range():
    """Test XSearchResult with invalid date range format."""
    with pytest.raises(ValidationError) as exc_info:
        XSearchResult(
            content="Content",
            query="test",
            date_range="2024-01-01",  # Missing " to " separator
            handles=[]
        )
    
    assert "Date range must be in format" in str(exc_info.value)


# VideoResult model tests
def test_video_result_valid():
    """Test VideoResult with valid data."""
    video = VideoResult(
        video_id="dQw4w9WgXcQ",
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title="Test Video",
        thumbnail_url="https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
        captions="Video transcript here",
        timestamps=["0:00 - Intro", "1:30 - Main content"],
        published_date="2024-01-15"
    )
    
    assert video.video_id == "dQw4w9WgXcQ"
    assert "youtube.com" in video.url


def test_video_result_invalid_video_id():
    """Test VideoResult with invalid video ID."""
    with pytest.raises(ValidationError) as exc_info:
        VideoResult(
            video_id="ab",  # Too short
            url="https://www.youtube.com/watch?v=ab"
        )
    
    assert "Invalid video ID" in str(exc_info.value)


def test_video_result_invalid_url():
    """Test VideoResult with non-YouTube URL."""
    with pytest.raises(ValidationError) as exc_info:
        VideoResult(
            video_id="dQw4w9WgXcQ",
            url="https://example.com/video"
        )
    
    assert "must be a YouTube URL" in str(exc_info.value)


def test_video_result_minimal():
    """Test VideoResult with minimal required fields."""
    video = VideoResult(
        video_id="test12345",
        url="https://youtu.be/test12345"
    )
    
    assert video.video_id == "test12345"
    assert video.title is None
    assert video.captions is None


# RedditResult model tests
def test_reddit_result_valid():
    """Test RedditResult with valid data."""
    result = RedditResult(
        url="https://www.reddit.com/r/python/comments/abc123/title/",
        title="Great Python Tutorial",
        content="This is the post content",
        score=0.95,
        published_date="2024-01-15",
        subreddit="python",
        is_reddit_post=True
    )
    
    assert result.subreddit == "python"
    assert result.is_reddit_post is True


def test_reddit_result_subreddit_normalization():
    """Test RedditResult subreddit name normalization."""
    result = RedditResult(
        url="https://www.reddit.com/r/learnprogramming/",
        title="Title",
        subreddit="r/learnprogramming"  # Should remove r/ prefix
    )
    
    assert result.subreddit == "learnprogramming"


def test_reddit_result_invalid_url():
    """Test RedditResult with non-Reddit URL."""
    with pytest.raises(ValidationError) as exc_info:
        RedditResult(
            url="https://example.com/post",
            title="Title",
            subreddit="test"
        )
    
    assert "must be a Reddit URL" in str(exc_info.value)


def test_reddit_result_unknown_subreddit():
    """Test RedditResult with unknown subreddit."""
    result = RedditResult(
        url="https://www.reddit.com/",
        title="Title",
        subreddit="unknown"
    )
    
    assert result.subreddit == "unknown"


# AcademicResult model tests
def test_academic_result_valid():
    """Test AcademicResult with valid data."""
    result = AcademicResult(
        title="Deep Learning for NLP",
        url="https://arxiv.org/abs/2301.12345",
        summary="This paper presents a novel approach to NLP.",
        published_date="2023-01-15",
        author="John Doe"
    )
    
    assert result.title == "Deep Learning for NLP"
    assert result.author == "John Doe"


def test_academic_result_title_cleaning():
    """Test AcademicResult title cleaning."""
    result = AcademicResult(
        title="Deep Learning [PDF] for NLP [arXiv:2301.12345]",
        url="https://arxiv.org/abs/2301.12345",
        summary="Summary"
    )
    
    # Brackets should be removed
    assert "[PDF]" not in result.title
    assert "[arXiv:2301.12345]" not in result.title
    # Note: cleaning may affect spacing, just verify brackets are gone
    assert "Deep Learning" in result.title
    assert "NLP" in result.title


def test_academic_result_summary_cleaning():
    """Test AcademicResult summary cleaning."""
    result = AcademicResult(
        title="Title",
        url="https://arxiv.org/abs/2301.12345",
        summary="Summary: This is the abstract of the paper."
    )
    
    # "Summary:" prefix should be removed
    assert not result.summary.startswith("Summary:")
    assert result.summary.startswith("This is the abstract")


def test_academic_result_abstract_prefix_cleaning():
    """Test AcademicResult removes Abstract: prefix."""
    result = AcademicResult(
        title="Title",
        url="https://arxiv.org/abs/2301.12345",
        summary="Abstract: This paper discusses quantum computing."
    )
    
    assert not result.summary.startswith("Abstract:")
    assert result.summary.startswith("This paper discusses")


def test_academic_result_invalid_url():
    """Test AcademicResult with invalid URL."""
    with pytest.raises(ValidationError) as exc_info:
        AcademicResult(
            title="Title",
            url="not-a-url",
            summary="Summary"
        )
    
    assert "URL must start with" in str(exc_info.value)


# SearchResult model tests
def test_search_result_valid():
    """Test SearchResult with valid data."""
    result = SearchResult(
        title="Test Article",
        url="https://example.com/article",
        content="Article content here",
        published_date="2024-01-15",
        author="Jane Doe"
    )
    
    assert result.title == "Test Article"
    assert result.author == "Jane Doe"


def test_search_result_minimal():
    """Test SearchResult with minimal fields."""
    result = SearchResult(
        title="Title",
        url="https://example.com"
    )
    
    assert result.content == ""
    assert result.author is None


# ResearchTask model tests
def test_research_task_valid():
    """Test ResearchTask with valid data."""
    task = ResearchTask(
        title="Understanding Quantum Computing Basics",
        tasks=[
            "Research quantum bits and superposition",
            "Study quantum gates and circuits",
            "Explore quantum algorithms"
        ]
    )
    
    assert len(task.tasks) == 3
    assert len(task.title) >= 10


def test_research_task_title_too_short():
    """Test ResearchTask with title too short."""
    with pytest.raises(ValidationError):
        ResearchTask(
            title="Short",  # Less than 10 characters
            tasks=["Task 1", "Task 2", "Task 3"]
        )


def test_research_task_too_few_tasks():
    """Test ResearchTask with too few tasks."""
    with pytest.raises(ValidationError):
        ResearchTask(
            title="Valid Title Here",
            tasks=["Task 1", "Task 2"]  # Less than 3 tasks
        )


# ResearchPlan model tests
def test_research_plan_valid():
    """Test ResearchPlan with valid data."""
    plan = ResearchPlan(
        topics=[
            ResearchTask(
                title="Topic 1: Quantum Computing",
                tasks=["Task 1", "Task 2", "Task 3"]
            ),
            ResearchTask(
                title="Topic 2: Machine Learning",
                tasks=["Task 1", "Task 2", "Task 3", "Task 4"]
            )
        ]
    )
    
    assert len(plan.topics) == 2
    assert plan.total_tasks == 7


def test_research_plan_too_many_tasks():
    """Test ResearchPlan with too many total tasks."""
    # Create a plan with 16 tasks (exceeds limit of 15)
    # Each topic has max 5 tasks, so we need 4 topics with 4 tasks each = 16 total
    with pytest.raises(ValidationError) as exc_info:
        ResearchPlan(
            topics=[
                ResearchTask(
                    title="Topic 1: Very Long Topic",
                    tasks=["Task 1", "Task 2", "Task 3", "Task 4"]
                ),
                ResearchTask(
                    title="Topic 2: Another Long Topic",
                    tasks=["Task 1", "Task 2", "Task 3", "Task 4"]
                ),
                ResearchTask(
                    title="Topic 3: Yet Another Topic",
                    tasks=["Task 1", "Task 2", "Task 3", "Task 4"]
                ),
                ResearchTask(
                    title="Topic 4: Fourth Topic Here",
                    tasks=["Task 1", "Task 2", "Task 3", "Task 4"]
                )
            ]
        )
    
    assert "cannot exceed 15" in str(exc_info.value)


# CodeExecutionResult model tests
def test_code_execution_result_valid():
    """Test CodeExecutionResult with valid data."""
    result = CodeExecutionResult(
        output="Hello, World!",
        error=None,
        charts=[{"type": "line", "data": [1, 2, 3]}]
    )
    
    assert result.output == "Hello, World!"
    assert result.error is None
    assert len(result.charts) == 1


def test_code_execution_result_with_error():
    """Test CodeExecutionResult with error."""
    result = CodeExecutionResult(
        output="",
        error="NameError: name 'x' is not defined"
    )
    
    assert result.error is not None
    assert "NameError" in result.error


# ResearchResult model tests
def test_research_result_valid():
    """Test ResearchResult with valid data."""
    result = ResearchResult(
        query="What is quantum computing?",
        text="Quantum computing is...",
        sources=[
            SearchResult(title="Source 1", url="https://example.com/1"),
            SearchResult(title="Source 2", url="https://example.com/2")
        ],
        execution_time=5.5
    )
    
    assert result.query == "What is quantum computing?"
    assert len(result.sources) == 2
    assert result.execution_time == 5.5


def test_research_result_negative_execution_time():
    """Test ResearchResult with negative execution time."""
    with pytest.raises(ValidationError):
        ResearchResult(
            query="Test query",
            execution_time=-1.0
        )


# Memory model tests
def test_memory_valid():
    """Test Memory with valid data."""
    memory = Memory(
        id="mem_123",
        content="This is stored content",
        metadata={"source": "web", "date": "2024-01-15"},
        score=0.85
    )
    
    assert memory.id == "mem_123"
    assert memory.score == 0.85


def test_memory_invalid_score():
    """Test Memory with invalid score."""
    with pytest.raises(ValidationError):
        Memory(
            id="mem_123",
            content="Content",
            score=1.5  # Score must be between 0 and 1
        )


# Input validation consistency tests
def test_url_validation_consistency():
    """Test that URL validation is consistent across models."""
    invalid_url = "not-a-url"
    
    # SearchResult doesn't validate URL format, just length
    # So we test with models that do validate
    
    with pytest.raises(ValidationError):
        AcademicResult(title="Title", url=invalid_url, summary="Summary")
    
    with pytest.raises(ValidationError):
        XPost(text="Text", link=invalid_url)
    
    with pytest.raises(ValidationError):
        RedditResult(title="Title", url=invalid_url, subreddit="test")


def test_output_format_consistency():
    """Test that similar models have consistent output formats."""
    # Create instances of different result types
    search_result = SearchResult(title="Title", url="https://example.com")
    academic_result = AcademicResult(title="Title", url="https://example.com", summary="Summary")
    reddit_result = RedditResult(title="Title", url="https://reddit.com/r/test", subreddit="test")
    
    # All should have title and url fields
    assert hasattr(search_result, 'title')
    assert hasattr(search_result, 'url')
    assert hasattr(academic_result, 'title')
    assert hasattr(academic_result, 'url')
    assert hasattr(reddit_result, 'title')
    assert hasattr(reddit_result, 'url')


def test_field_length_limits():
    """Test that field length limits are enforced."""
    # Test title length limit
    with pytest.raises(ValidationError):
        SearchResult(
            title="x" * 501,  # Exceeds max_length=500
            url="https://example.com"
        )
    
    # Test content length limit
    with pytest.raises(ValidationError):
        XPost(
            text="x" * 5001,  # Exceeds max_length=5000
            link="https://x.com/post"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
