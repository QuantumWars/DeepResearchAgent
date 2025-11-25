"""Utility modules for the research agent."""

from .models import (
    SearchCategory,
    SearchResult,
    ResearchTask,
    ResearchPlan,
    CodeExecutionResult,
    ResearchResult,
    Memory,
)
from .content_processor import (
    extract_domain,
    clean_title,
    truncate_content,
    generate_favicon_url,
    deduplicate_by_url,
    deduplicate_by_domain,
    deduplicate_results,
)
from .retry import (
    RetryConfig,
    retry_async,
    with_retry,
)
from .error_handling import (
    safe_tool_execution,
    validate_api_key,
    handle_api_response_error,
    create_error_response,
    log_tool_execution,
)
from .performance import (
    execute_multi_query_tool,
    get_cache,
    cached,
    process_in_batches,
    AsyncCache,
)

__all__ = [
    # Models
    "SearchCategory",
    "SearchResult",
    "ResearchTask",
    "ResearchPlan",
    "CodeExecutionResult",
    "ResearchResult",
    "Memory",
    # Content Processing
    "extract_domain",
    "clean_title",
    "truncate_content",
    "generate_favicon_url",
    "deduplicate_by_url",
    "deduplicate_by_domain",
    "deduplicate_results",
    # Retry Logic
    "RetryConfig",
    "retry_async",
    "with_retry",
    # Error Handling
    "safe_tool_execution",
    "validate_api_key",
    "handle_api_response_error",
    "create_error_response",
    "log_tool_execution",
    # Performance Optimization
    "execute_multi_query_tool",
    "get_cache",
    "cached",
    "process_in_batches",
    "AsyncCache",
]
