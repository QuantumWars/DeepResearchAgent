#!/usr/bin/env python3
"""Verification script for tool integration (Task 7).

This script verifies that:
1. All tools are properly registered in the tool registry
2. The configuration system correctly manages enabled tools
3. The DeepResearchAgent properly initializes with filtered tools
"""

import os
import sys

# Set minimal required env vars for testing
os.environ['OPENAI_API_KEY'] = 'test-key'
os.environ['EXA_API_KEY'] = 'test-key'

from research_agent.clients.tool_registry import get_tool_registry
from research_agent.utils.config import get_config, reset_config
from research_agent.utils.logger import get_logger

logger = get_logger(__name__)


def verify_tool_registration():
    """Verify that all tools are registered in the registry."""
    print("=" * 70)
    print("VERIFICATION 1: Tool Registration")
    print("=" * 70)
    
    # Import tools module to trigger registration
    import research_agent.tools
    
    registry = get_tool_registry()
    
    expected_tools = [
        'web_search',
        'code_executor',
        'memory_search',
        'x_search',
        'youtube_search',
        'reddit_search',
        'academic_search',
        'convert_currency',
        'datetime_operations',
        'get_weather',
        'track_flight',
        'get_stock_data',
        'get_crypto_data',
        'get_crypto_market_overview',
        'geocode_location',
        'reverse_geocode',
        'calculate_distance'
    ]
    
    registered_tools = registry.list_tools()
    
    print(f"Expected tools: {len(expected_tools)}")
    print(f"Registered tools: {len(registered_tools)}")
    print()
    
    # Check all expected tools are registered
    missing_tools = set(expected_tools) - set(registered_tools)
    extra_tools = set(registered_tools) - set(expected_tools)
    
    if missing_tools:
        print(f"❌ FAILED: Missing tools: {missing_tools}")
        return False
    
    if extra_tools:
        print(f"⚠️  WARNING: Extra tools registered: {extra_tools}")
    
    print(f"✅ PASSED: All {len(expected_tools)} tools registered successfully")
    print()
    print("Registered tools:")
    for tool in sorted(registered_tools):
        metadata = registry.get_metadata(tool)
        category = metadata.get('category', 'unknown') if metadata else 'unknown'
        print(f"  - {tool:30s} [{category}]")
    
    return True


def verify_config_system():
    """Verify that the configuration system manages enabled tools."""
    print("\n" + "=" * 70)
    print("VERIFICATION 2: Configuration System")
    print("=" * 70)
    
    # Reset config to pick up env vars
    reset_config()
    config = get_config()
    
    print(f"Default enabled tools: {config.enabled_tools_list}")
    print()
    
    # Test with custom enabled tools
    os.environ['ENABLED_TOOLS'] = 'web_search,x_search,youtube_search'
    reset_config()
    config = get_config()
    
    print(f"Custom enabled tools: {config.enabled_tools_list}")
    expected = ['web_search', 'x_search', 'youtube_search']
    
    if config.enabled_tools_list == expected:
        print(f"✅ PASSED: Configuration correctly parses ENABLED_TOOLS")
    else:
        print(f"❌ FAILED: Expected {expected}, got {config.enabled_tools_list}")
        return False
    
    # Reset to default
    os.environ['ENABLED_TOOLS'] = 'web_search,code_executor,memory_search'
    reset_config()
    
    return True


def verify_tool_filtering():
    """Verify that tools are filtered based on configuration."""
    print("\n" + "=" * 70)
    print("VERIFICATION 3: Tool Filtering")
    print("=" * 70)
    
    import research_agent.tools
    from research_agent.clients.tool_registry import get_tool_registry, reset_tool_registry
    
    # Reset registry
    reset_tool_registry()
    
    # Re-import to re-register
    import importlib
    importlib.reload(research_agent.tools)
    
    registry = get_tool_registry()
    reset_config()
    config = get_config()
    
    print(f"Config enabled tools: {config.enabled_tools_list}")
    print(f"Registry before filtering: {len(registry.list_enabled_tools())} enabled")
    print()
    
    # Apply filtering (what the agent does)
    registry.set_enabled_tools(config.enabled_tools_list)
    
    enabled_tools = registry.list_enabled_tools()
    print(f"Registry after filtering: {len(enabled_tools)} enabled")
    print(f"Enabled tools: {sorted(enabled_tools)}")
    print()
    
    if set(enabled_tools) == set(config.enabled_tools_list):
        print(f"✅ PASSED: Tool filtering works correctly")
        return True
    else:
        print(f"❌ FAILED: Filtering mismatch")
        print(f"  Expected: {sorted(config.enabled_tools_list)}")
        print(f"  Got: {sorted(enabled_tools)}")
        return False


def verify_agent_integration():
    """Verify that DeepResearchAgent properly uses the tool registry."""
    print("\n" + "=" * 70)
    print("VERIFICATION 4: Agent Integration")
    print("=" * 70)
    
    try:
        from langchain_openai import ChatOpenAI
        from research_agent.agent.research_agent import DeepResearchAgent
        from research_agent.clients.tool_registry import reset_tool_registry
        
        # Reset and re-register tools
        reset_tool_registry()
        import importlib
        import research_agent.tools
        importlib.reload(research_agent.tools)
        
        # Create a mock LLM
        llm = ChatOpenAI(model="gpt-4", api_key="test-key")
        
        # Create agent
        agent = DeepResearchAgent(llm=llm)
        
        print(f"Agent initialized with {len(agent.tools)} tools")
        print(f"Tool names: {sorted([tool.name for tool in agent.tools])}")
        print()
        
        # Verify tools match config
        reset_config()
        config = get_config()
        expected_count = len(config.enabled_tools_list)
        actual_count = len(agent.tools)
        
        print(f"Expected tool count: {expected_count}")
        print(f"Actual tool count: {actual_count}")
        print()
        
        if expected_count == actual_count:
            print(f"✅ PASSED: Agent uses correct number of tools from registry")
            print(f"   Agent successfully initialized with {actual_count} tools")
            return True
        else:
            print(f"❌ FAILED: Tool count mismatch")
            print(f"  Expected: {expected_count}")
            print(f"  Got: {actual_count}")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Agent initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verifications."""
    print("\n" + "=" * 70)
    print("TOOL INTEGRATION VERIFICATION (Task 7)")
    print("=" * 70)
    print()
    
    results = []
    
    # Run verifications
    results.append(("Tool Registration", verify_tool_registration()))
    results.append(("Configuration System", verify_config_system()))
    results.append(("Tool Filtering", verify_tool_filtering()))
    results.append(("Agent Integration", verify_agent_integration()))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")
    
    all_passed = all(passed for _, passed in results)
    
    print()
    if all_passed:
        print("🎉 All verifications passed! Task 7 implementation is complete.")
        return 0
    else:
        print("⚠️  Some verifications failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
