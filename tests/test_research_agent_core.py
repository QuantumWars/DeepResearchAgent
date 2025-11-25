"""Test script to verify DeepResearchAgent core functionality."""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from research_agent.agent.research_agent import DeepResearchAgent
from research_agent.utils.config import get_config

# Load environment variables from research_agent/.env
env_path = Path(__file__).parent / "research_agent" / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"Loaded environment from: {env_path}")


async def test_agent_initialization():
    """Test that the agent can be initialized properly."""
    print("Testing DeepResearchAgent initialization...")
    
    try:
        # Get config
        config = get_config()
        print(f"✓ Configuration loaded successfully")
        print(f"  - Search provider: {config.search_provider}")
        print(f"  - Max tool calls: {config.max_tool_calls}")
        print(f"  - Max research tasks: {config.max_research_tasks}")
        
        # Initialize LLM
        if config.openai_api_key:
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                api_key=config.openai_api_key
            )
            print(f"✓ LLM initialized (OpenAI)")
        else:
            print("✗ No OpenAI API key found")
            return False
        
        # Initialize agent
        agent = DeepResearchAgent(
            llm=llm,
            search_provider=config.search_provider
        )
        print(f"✓ DeepResearchAgent initialized successfully")
        
        # Verify components
        assert agent.planner is not None, "Planner not initialized"
        print(f"✓ Research planner initialized")
        
        assert agent.memory_client is not None, "Memory client not initialized"
        print(f"✓ Memory client initialized")
        
        assert len(agent.tools) == 3, f"Expected 3 tools, got {len(agent.tools)}"
        print(f"✓ Tools initialized: {[tool.name for tool in agent.tools]}")
        
        print("\n✅ All initialization tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Initialization test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_research_plan_creation():
    """Test that the agent can create a research plan."""
    print("\nTesting research plan creation...")
    
    try:
        # Get config
        config = get_config()
        
        # Initialize LLM
        if config.openai_api_key:
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                api_key=config.openai_api_key
            )
        else:
            print("✗ No OpenAI API key found")
            return False
        
        # Initialize agent
        agent = DeepResearchAgent(llm=llm)
        
        # Create a simple research plan
        print("Creating research plan for: 'What is quantum computing?'")
        plan = await agent._create_research_plan("What is quantum computing?")
        
        print(f"✓ Research plan created successfully")
        print(f"  - Topics: {len(plan.topics)}")
        print(f"  - Total tasks: {plan.total_tasks}")
        
        # Verify plan structure
        assert 1 <= len(plan.topics) <= 5, f"Invalid topic count: {len(plan.topics)}"
        assert plan.total_tasks <= 15, f"Too many tasks: {plan.total_tasks}"
        
        # Print plan details
        for i, topic in enumerate(plan.topics, 1):
            print(f"\n  Topic {i}: {topic.title}")
            for j, task in enumerate(topic.tasks, 1):
                print(f"    {i}.{j}. {task}")
        
        print("\n✅ Research plan creation test passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Research plan creation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_executor_creation():
    """Test that the agent executor can be created."""
    print("\nTesting agent executor creation...")
    
    try:
        # Get config
        config = get_config()
        
        # Initialize LLM
        if config.openai_api_key:
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                api_key=config.openai_api_key
            )
        else:
            print("✗ No OpenAI API key found")
            return False
        
        # Initialize agent
        agent = DeepResearchAgent(llm=llm)
        
        # Create a simple research plan
        plan = await agent._create_research_plan("Test query")
        
        # Create agent executor
        executor = agent._create_agent_executor(plan)
        
        print(f"✓ Agent executor created successfully")
        print(f"  - Type: {type(executor).__name__}")
        
        # Verify executor is created (LangGraph agent)
        assert executor is not None
        
        print("\n✅ Agent executor creation test passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Agent executor creation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("DeepResearchAgent Core Functionality Tests")
    print("=" * 60)
    
    results = []
    
    # Test 1: Initialization
    results.append(await test_agent_initialization())
    
    # Test 2: Research plan creation
    results.append(await test_research_plan_creation())
    
    # Test 3: Agent executor creation
    results.append(await test_agent_executor_creation())
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
