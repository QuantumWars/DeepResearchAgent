"""Quick test to verify DeepResearchAgent can be instantiated."""

import asyncio
from langchain_openai import ChatOpenAI
from research_agent.agent import DeepResearchAgent
from research_agent.utils.config import get_config


async def test_instantiation():
    """Test that DeepResearchAgent can be instantiated."""
    try:
        # Get config
        config = get_config()
        print(f"✓ Config loaded successfully")
        print(f"  - Search provider: {config.search_provider}")
        print(f"  - Max tool calls: {config.max_tool_calls}")
        
        # Create LLM
        if config.openai_api_key:
            llm = ChatOpenAI(
                model="gpt-4",
                temperature=0.7,
                api_key=config.openai_api_key
            )
            print(f"✓ LLM initialized (OpenAI)")
        else:
            print("✗ No OpenAI API key found")
            return
        
        # Create agent
        agent = DeepResearchAgent(llm=llm)
        print(f"✓ DeepResearchAgent instantiated successfully")
        print(f"  - Tools: {[tool.name for tool in agent.tools]}")
        print(f"  - Planner: {agent.planner.__class__.__name__}")
        print(f"  - Memory client: {agent.memory_client.__class__.__name__}")
        
        print("\n✓ All components initialized successfully!")
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_instantiation())
