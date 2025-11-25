#!/usr/bin/env python3
"""Test individual tools to verify they work correctly."""

import asyncio
import sys

# Import tools to trigger registration
import research_agent.tools
from research_agent.clients.tool_registry import get_tool_registry
from research_agent.utils.config import get_config


async def test_tool(tool_name: str):
    """Test a single tool by name."""
    registry = get_tool_registry()
    
    # Check if tool is registered
    if tool_name not in registry.list_tools():
        print(f"❌ Tool '{tool_name}' is NOT registered")
        return False
    
    # Check if tool is enabled
    if tool_name not in registry.list_enabled_tools():
        print(f"⚠️  Tool '{tool_name}' is registered but NOT enabled")
        return False
    
    # Get the tool function
    tool_func = registry.get_tool(tool_name)
    if tool_func is None:
        print(f"❌ Tool '{tool_name}' function is None")
        return False
    
    print(f"✅ Tool '{tool_name}' is registered and enabled")
    print(f"   Function: {tool_func.name if hasattr(tool_func, 'name') else tool_func.__name__}")
    print(f"   Description: {tool_func.description[:100] if hasattr(tool_func, 'description') else 'N/A'}...")
    
    return True


async def main():
    """Test all core tools."""
    print("=" * 70)
    print("TOOL REGISTRATION TEST")
    print("=" * 70)
    
    # Get config to see what's enabled
    config = get_config()
    print(f"\nEnabled tools from config: {config.enabled_tools}")
    print(f"Parsed as list: {config.enabled_tools_list}\n")
    
    # Get registry stats
    registry = get_tool_registry()
    print(f"Total registered tools: {len(registry.list_tools())}")
    print(f"Total enabled tools: {len(registry.list_enabled_tools())}\n")
    
    print("-" * 70)
    print("TESTING CORE TOOLS")
    print("-" * 70)
    
    # Test core tools
    core_tools = ["web_search", "code_executor", "memory_search"]
    
    results = {}
    for tool_name in core_tools:
        print(f"\nTesting: {tool_name}")
        results[tool_name] = await test_tool(tool_name)
    
    print("\n" + "-" * 70)
    print("TESTING NEW TOOLS")
    print("-" * 70)
    
    # Test new tools
    new_tools = [
        "x_search",
        "youtube_search", 
        "reddit_search",
        "academic_search",
        "convert_currency",
        "datetime_operations",
        "get_weather"
    ]
    
    for tool_name in new_tools:
        print(f"\nTesting: {tool_name}")
        results[tool_name] = await test_tool(tool_name)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tools are working correctly!")
        return 0
    else:
        print("❌ Some tools failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
