#!/usr/bin/env python3
"""Test agent integration with all tools."""

import asyncio
import sys
from langchain_openai import ChatOpenAI

from research_agent.agent.research_agent import DeepResearchAgent
from research_agent.clients.tool_registry import get_tool_registry
from research_agent.utils.config import get_config


async def main():
    """Test agent with tools."""
    print("=" * 70)
    print("AGENT TOOL INTEGRATION TEST")
    print("=" * 70)
    
    # Get config
    config = get_config()
    print(f"\nSearch Provider: {config.search_provider}")
    print(f"Enabled Tools: {config.enabled_tools_list}")
    
    # Check registry before agent creation
    registry = get_tool_registry()
    print(f"\nTools in registry: {len(registry.list_tools())}")
    print(f"Enabled tools: {len(registry.list_enabled_tools())}")
    
    # Create LLM
    print("\nInitializing LLM...")
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=config.openai_api_key
    )
    
    # Create agent
    print("Creating DeepResearchAgent...")
    agent = DeepResearchAgent(
        llm=llm,
        search_provider=config.search_provider
    )
    
    # Check agent tools
    print(f"\nAgent has {len(agent.tools)} tools available")
    print("Tool names:")
    for tool in agent.tools:
        tool_name = tool.name if hasattr(tool, 'name') else str(tool)
        print(f"  - {tool_name}")
    
    # Verify core tools are present (check actual tool names, not registry names)
    tool_names = [tool.name if hasattr(tool, 'name') else str(tool) for tool in agent.tools]
    
    # Map registry names to actual tool function names
    expected_tool_names = {
        "web_search": "web_search",
        "code_executor": "execute_python_code", 
        "memory_search": "search_memories"
    }
    
    missing_tools = []
    for registry_name, tool_name in expected_tool_names.items():
        if tool_name not in tool_names:
            missing_tools.append(f"{registry_name} ({tool_name})")
    
    if missing_tools:
        print(f"\n❌ Missing core tools: {missing_tools}")
        return 1
    else:
        print(f"\n✅ All core tools are available to the agent")
    
    # Test a simple research query
    print("\n" + "-" * 70)
    print("TESTING SIMPLE RESEARCH")
    print("-" * 70)
    
    query = "What is Python?"
    print(f"\nQuery: {query}")
    print("Executing research (this may take a minute)...\n")
    
    try:
        result = await agent.research(query=query, user_id="test_user")
        
        print(f"\n✅ Research completed successfully!")
        print(f"   Execution time: {result.execution_time:.2f}s")
        print(f"   Sources found: {len(result.sources)}")
        print(f"   Charts generated: {len(result.charts)}")
        print(f"   Tool calls made: {len(result.tool_results)}")
        
        if result.tool_results:
            print(f"\n   Tools used:")
            tools_used = set()
            for tr in result.tool_results:
                if isinstance(tr, dict) and 'tool' in tr:
                    tools_used.add(tr['tool'])
            for tool in sorted(tools_used):
                print(f"     - {tool}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Research failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
