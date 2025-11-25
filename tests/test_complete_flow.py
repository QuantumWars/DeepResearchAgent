#!/usr/bin/env python3
"""
Complete flow test for tool integration.

This script tests:
1. Individual tool registration
2. Agent integration with tools
3. Complete research flow
"""

import asyncio
import sys
from langchain_openai import ChatOpenAI

# Import tools to trigger registration
import research_agent.tools
from research_agent.agent.research_agent import DeepResearchAgent
from research_agent.clients.tool_registry import get_tool_registry
from research_agent.utils.config import get_config


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(title.center(70))
    print("=" * 70 + "\n")


async def test_tool_registration():
    """Test that all tools are properly registered."""
    print_section("STEP 1: TOOL REGISTRATION")
    
    registry = get_tool_registry()
    
    print(f"Total tools registered: {len(registry.list_tools())}")
    print(f"Total tools enabled: {len(registry.list_enabled_tools())}")
    
    # Check core tools
    core_tools = ["web_search", "code_executor", "memory_search"]
    print(f"\nCore tools:")
    for tool_name in core_tools:
        status = "✅" if tool_name in registry.list_tools() else "❌"
        enabled = "enabled" if tool_name in registry.list_enabled_tools() else "disabled"
        print(f"  {status} {tool_name} ({enabled})")
    
    # Check new tools
    new_tools = ["x_search", "youtube_search", "reddit_search", "academic_search"]
    print(f"\nNew search tools:")
    for tool_name in new_tools:
        status = "✅" if tool_name in registry.list_tools() else "❌"
        enabled = "enabled" if tool_name in registry.list_enabled_tools() else "disabled"
        print(f"  {status} {tool_name} ({enabled})")
    
    # Check utility tools
    utility_tools = ["convert_currency", "datetime_operations", "get_weather"]
    print(f"\nUtility tools:")
    for tool_name in utility_tools:
        status = "✅" if tool_name in registry.list_tools() else "❌"
        enabled = "enabled" if tool_name in registry.list_enabled_tools() else "disabled"
        print(f"  {status} {tool_name} ({enabled})")
    
    all_registered = all(
        tool in registry.list_tools() 
        for tool in core_tools + new_tools + utility_tools
    )
    
    if all_registered:
        print(f"\n✅ All tools are properly registered")
        return True
    else:
        print(f"\n❌ Some tools are missing")
        return False


async def test_agent_integration():
    """Test that agent properly integrates with tools."""
    print_section("STEP 2: AGENT INTEGRATION")
    
    config = get_config()
    print(f"Configuration:")
    print(f"  Search Provider: {config.search_provider}")
    print(f"  Enabled Tools: {config.enabled_tools_list}")
    print(f"  Max Tool Calls: {config.max_tool_calls}")
    
    # Create LLM
    print(f"\nInitializing LLM...")
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=config.openai_api_key
    )
    
    # Create agent
    print(f"Creating DeepResearchAgent...")
    agent = DeepResearchAgent(
        llm=llm,
        search_provider=config.search_provider
    )
    
    print(f"\nAgent initialized successfully")
    print(f"  Tools available: {len(agent.tools)}")
    print(f"  Tool names:")
    for tool in agent.tools:
        tool_name = tool.name if hasattr(tool, 'name') else str(tool)
        print(f"    - {tool_name}")
    
    # Verify expected tools are present
    tool_names = [tool.name if hasattr(tool, 'name') else str(tool) for tool in agent.tools]
    expected = ["web_search", "execute_python_code", "search_memories"]
    
    all_present = all(tool in tool_names for tool in expected)
    
    if all_present:
        print(f"\n✅ Agent has all expected tools")
        return agent
    else:
        print(f"\n❌ Agent is missing some tools")
        return None


async def test_research_flow(agent):
    """Test complete research flow."""
    print_section("STEP 3: RESEARCH FLOW")
    
    query = "What is artificial intelligence?"
    print(f"Query: {query}")
    print(f"Executing research...\n")
    
    try:
        result = await agent.research(query=query, user_id="test_user")
        
        print(f"✅ Research completed successfully!")
        print(f"\nResults:")
        print(f"  Execution time: {result.execution_time:.2f}s")
        print(f"  Sources found: {len(result.sources)}")
        print(f"  Charts generated: {len(result.charts)}")
        print(f"  Tool calls made: {len(result.tool_results)}")
        
        if result.tool_results:
            tools_used = set()
            for tr in result.tool_results:
                if isinstance(tr, dict) and 'tool' in tr:
                    tools_used.add(tr['tool'])
            
            if tools_used:
                print(f"\n  Tools used during research:")
                for tool in sorted(tools_used):
                    print(f"    - {tool}")
        
        if result.sources:
            print(f"\n  Sample sources:")
            for i, source in enumerate(result.sources[:3], 1):
                print(f"    {i}. {source.title}")
                print(f"       {source.url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Research failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run complete flow test."""
    print_section("TOOL INTEGRATION - COMPLETE FLOW TEST")
    
    print("This test verifies:")
    print("  1. All tools are properly registered")
    print("  2. Agent integrates correctly with tools")
    print("  3. Complete research flow works end-to-end")
    
    # Step 1: Test tool registration
    registration_ok = await test_tool_registration()
    if not registration_ok:
        print("\n❌ FAILED: Tool registration issues")
        return 1
    
    # Step 2: Test agent integration
    agent = await test_agent_integration()
    if agent is None:
        print("\n❌ FAILED: Agent integration issues")
        return 1
    
    # Step 3: Test research flow
    research_ok = await test_research_flow(agent)
    if not research_ok:
        print("\n❌ FAILED: Research flow issues")
        return 1
    
    # Final summary
    print_section("TEST SUMMARY")
    print("✅ All tests passed!")
    print("\nVerified:")
    print("  ✅ Tool registration working")
    print("  ✅ Agent integration working")
    print("  ✅ Research flow working")
    print("\nConclusion:")
    print("  The tool integration is complete and functional.")
    print("  All tools are properly registered and accessible to the agent.")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
