"""Integration tests for tool integration system."""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
from langchain_openai import ChatOpenAI

# Set minimal required env vars for testing
os.environ['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', 'test-key')
os.environ['EXA_API_KEY'] = os.environ.get('EXA_API_KEY', 'test-key')

from research_agent.clients.tool_registry import get_tool_registry, reset_tool_registry
from research_agent.utils.config import get_config, reset_config
from research_agent.agent.research_agent import DeepResearchAgent


@pytest.fixture
def reset_environment():
    """Reset tool registry and config before each test."""
    reset_tool_registry()
    reset_config()
    yield
    reset_tool_registry()
    reset_config()


def test_tool_registry_initialization(reset_environment):
    """Test that tool registry initializes with all tools."""
    # Import tools to trigger registration
    import research_agent.tools
    
    registry = get_tool_registry()
    registered_tools = registry.list_tools()
    
    # Verify core tools are registered
    assert "web_search" in registered_tools
    assert "code_executor" in registered_tools
    assert "memory_search" in registered_tools
    
    # Verify new search tools are registered
    assert "x_search" in registered_tools
    assert "youtube_search" in registered_tools
    assert "reddit_search" in registered_tools
    assert "academic_search" in registered_tools
    
    # Verify utility tools are registered
    assert "convert_currency" in registered_tools
    assert "datetime_operations" in registered_tools
    assert "get_weather" in registered_tools


def test_tool_registry_enable_disable(reset_environment):
    """Test enabling and disabling tools in registry."""
    import research_agent.tools
    
    registry = get_tool_registry()
    
    # Initially all tools should be enabled
    enabled_tools = registry.list_enabled_tools()
    assert len(enabled_tools) > 0
    
    # Disable a tool
    registry.disable_tool("x_search")
    enabled_tools = registry.list_enabled_tools()
    assert "x_search" not in enabled_tools
    
    # Re-enable the tool
    registry.enable_tool("x_search")
    enabled_tools = registry.list_enabled_tools()
    assert "x_search" in enabled_tools


def test_tool_registry_selective_enabling(reset_environment):
    """Test selective tool enabling via configuration."""
    import research_agent.tools
    
    registry = get_tool_registry()
    
    # Set specific tools to enable
    enabled_list = ["web_search", "x_search", "youtube_search"]
    registry.set_enabled_tools(enabled_list)
    
    enabled_tools = registry.list_enabled_tools()
    
    # Verify only specified tools are enabled
    assert set(enabled_tools) == set(enabled_list)
    assert "reddit_search" not in enabled_tools
    assert "academic_search" not in enabled_tools


def test_tool_registry_metadata(reset_environment):
    """Test tool metadata retrieval."""
    import research_agent.tools
    
    registry = get_tool_registry()
    
    # Get metadata for a tool
    metadata = registry.get_metadata("x_search")
    
    assert metadata is not None
    assert "category" in metadata
    assert metadata["category"] == "search"


def test_config_enabled_tools_parsing(reset_environment):
    """Test configuration parsing of enabled tools."""
    # Set environment variable
    os.environ['ENABLED_TOOLS'] = 'web_search,x_search,youtube_search'
    
    reset_config()
    config = get_config()
    
    # Verify parsing
    assert config.enabled_tools_list == ['web_search', 'x_search', 'youtube_search']


def test_config_default_enabled_tools(reset_environment):
    """Test default enabled tools configuration."""
    # Clear environment variable
    if 'ENABLED_TOOLS' in os.environ:
        del os.environ['ENABLED_TOOLS']
    
    reset_config()
    config = get_config()
    
    # Verify defaults include core tools
    assert 'web_search' in config.enabled_tools_list
    assert 'code_executor' in config.enabled_tools_list
    assert 'memory_search' in config.enabled_tools_list


@pytest.mark.asyncio
async def test_agent_uses_tool_registry(reset_environment):
    """Test that DeepResearchAgent uses tools from registry."""
    import research_agent.tools
    
    # Reset and configure
    reset_tool_registry()
    reset_config()
    
    # Set specific enabled tools
    os.environ['ENABLED_TOOLS'] = 'web_search,code_executor,memory_search'
    reset_config()
    
    # Re-import to re-register
    import importlib
    importlib.reload(research_agent.tools)
    
    registry = get_tool_registry()
    config = get_config()
    registry.set_enabled_tools(config.enabled_tools_list)
    
    # Create mock LLM
    llm = ChatOpenAI(model="gpt-4", api_key="test-key")
    
    # Create agent
    agent = DeepResearchAgent(llm=llm)
    
    # Verify agent has correct number of tools
    assert len(agent.tools) == 3
    
    # Verify tool names match enabled tools
    tool_names = [tool.name for tool in agent.tools]
    assert set(tool_names) == set(config.enabled_tools_list)


@pytest.mark.asyncio
async def test_agent_with_all_tools_enabled(reset_environment):
    """Test agent initialization with all tools enabled."""
    import research_agent.tools
    
    # Reset and configure
    reset_tool_registry()
    reset_config()
    
    # Enable all tools
    os.environ['ENABLED_TOOLS'] = 'web_search,code_executor,memory_search,x_search,youtube_search,reddit_search,academic_search'
    reset_config()
    
    # Re-import to re-register
    import importlib
    importlib.reload(research_agent.tools)
    
    registry = get_tool_registry()
    config = get_config()
    registry.set_enabled_tools(config.enabled_tools_list)
    
    # Create mock LLM
    llm = ChatOpenAI(model="gpt-4", api_key="test-key")
    
    # Create agent
    agent = DeepResearchAgent(llm=llm)
    
    # Verify agent has all enabled tools
    assert len(agent.tools) == 7


@pytest.mark.asyncio
async def test_error_handling_across_tools(reset_environment):
    """Test that errors in one tool don't affect others."""
    from research_agent.tools.x_search import x_search
    from research_agent.tools.youtube_search import youtube_search
    
    # Mock X search to fail
    with patch('research_agent.tools.x_search.XAIClient') as mock_xai:
        mock_client = AsyncMock()
        mock_client.search_with_grok = AsyncMock(side_effect=Exception("API Error"))
        mock_client.close = AsyncMock()
        mock_xai.return_value = mock_client
        
        # X search should handle error gracefully
        x_result = await x_search(queries=["test"])
        assert x_result["searches"] == []
        assert "date_range" in x_result
    
    # YouTube search should still work
    with patch('research_agent.tools.youtube_search.Exa') as mock_exa:
        mock_exa_instance = Mock()
        mock_response = Mock()
        mock_response.results = []
        mock_exa_instance.search_and_contents = Mock(return_value=mock_response)
        mock_exa.return_value = mock_exa_instance
        
        yt_result = await youtube_search(query="test")
        assert "results" in yt_result
        assert yt_result["total_videos"] == 0


@pytest.mark.asyncio
async def test_tool_registry_get_tool_function(reset_environment):
    """Test retrieving tool function from registry."""
    import research_agent.tools
    
    registry = get_tool_registry()
    
    # Get a tool function
    tool_func = registry.get_tool("web_search")
    
    assert tool_func is not None
    assert callable(tool_func)


@pytest.mark.asyncio
async def test_tool_categories(reset_environment):
    """Test that tools are properly categorized."""
    import research_agent.tools
    
    registry = get_tool_registry()
    
    # Get tools by category
    search_tools = registry.get_tools_by_category("search")
    utility_tools = registry.get_tools_by_category("utility")
    
    # Verify search tools
    assert "web_search" in search_tools
    assert "x_search" in search_tools
    assert "youtube_search" in search_tools
    assert "reddit_search" in search_tools
    assert "academic_search" in search_tools
    
    # Verify utility tools
    assert "convert_currency" in utility_tools
    assert "datetime_operations" in utility_tools
    assert "get_weather" in utility_tools


@pytest.mark.asyncio
async def test_parallel_tool_execution(reset_environment):
    """Test that multiple tools can execute in parallel."""
    from research_agent.tools.x_search import x_search
    from research_agent.tools.reddit_search import reddit_search
    
    with patch('research_agent.tools.x_search.XAIClient') as mock_xai, \
         patch('research_agent.tools.reddit_search.TavilyClient') as mock_tavily:
        
        # Setup mocks
        mock_xai_client = AsyncMock()
        mock_xai_client.search_with_grok = AsyncMock(return_value={
            "choices": [{"message": {"content": "Test"}}],
            "citations": [],
            "sources": []
        })
        mock_xai_client.close = AsyncMock()
        mock_xai.return_value = mock_xai_client
        
        mock_tavily_client = Mock()
        mock_tavily_client.search = Mock(return_value={"results": []})
        mock_tavily.return_value = mock_tavily_client
        
        # Execute tools in parallel
        results = await asyncio.gather(
            x_search(queries=["test1"]),
            reddit_search(queries=["test2"])
        )
        
        # Verify both completed
        assert len(results) == 2
        assert "searches" in results[0]
        assert "searches" in results[1]


@pytest.mark.asyncio
async def test_tool_input_validation(reset_environment):
    """Test that tools validate inputs properly."""
    from research_agent.tools.x_search import x_search
    from research_agent.tools.youtube_search import youtube_search
    
    # Test empty queries
    x_result = await x_search(queries=[])
    assert x_result["searches"] == []
    
    # Test too many queries (should limit to 5)
    with patch('research_agent.tools.x_search.XAIClient') as mock_xai:
        mock_client = AsyncMock()
        mock_client.search_with_grok = AsyncMock(return_value={
            "choices": [{"message": {"content": "Test"}}],
            "citations": [],
            "sources": []
        })
        mock_client.close = AsyncMock()
        mock_xai.return_value = mock_client
        
        x_result = await x_search(queries=["q1", "q2", "q3", "q4", "q5", "q6", "q7"])
        assert len(x_result["searches"]) == 5


@pytest.mark.asyncio
async def test_tool_output_consistency(reset_environment):
    """Test that tools return consistent output formats."""
    from research_agent.tools.x_search import x_search
    from research_agent.tools.reddit_search import reddit_search
    from research_agent.tools.academic_search import academic_search
    
    with patch('research_agent.tools.x_search.XAIClient') as mock_xai, \
         patch('research_agent.tools.reddit_search.TavilyClient') as mock_tavily, \
         patch('research_agent.tools.academic_search.Exa') as mock_exa:
        
        # Setup mocks
        mock_xai_client = AsyncMock()
        mock_xai_client.search_with_grok = AsyncMock(return_value={
            "choices": [{"message": {"content": "Test"}}],
            "citations": [],
            "sources": []
        })
        mock_xai_client.close = AsyncMock()
        mock_xai.return_value = mock_xai_client
        
        mock_tavily_client = Mock()
        mock_tavily_client.search = Mock(return_value={"results": []})
        mock_tavily.return_value = mock_tavily_client
        
        mock_exa_instance = Mock()
        mock_exa_instance.search_and_contents = Mock(return_value=Mock(results=[]))
        mock_exa.return_value = mock_exa_instance
        
        # Execute tools
        x_result = await x_search(queries=["test"])
        reddit_result = await reddit_search(queries=["test"])
        academic_result = await academic_search(queries=["test"])
        
        # Verify all have "searches" key
        assert "searches" in x_result
        assert "searches" in reddit_result
        assert "searches" in academic_result
        
        # Verify all return lists
        assert isinstance(x_result["searches"], list)
        assert isinstance(reddit_result["searches"], list)
        assert isinstance(academic_result["searches"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
