import asyncio
import json
import os
from dotenv import load_dotenv
from src.agents.orchestrator import OrchestratorAgent

# Unset any dummy environment variables
if os.getenv('OPENAI_API_KEY') == 'dummy':
    del os.environ['OPENAI_API_KEY']

# Load environment variables from src/.env
load_dotenv('src/.env')

async def main():
    # Check API key status
    openai_key = os.getenv("OPENAI_API_KEY")
    exa_key = os.getenv("EXA_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    print("=" * 60)
    print("API Key Status")
    print("=" * 60)
    print(f"OpenAI: {'✓ Configured' if openai_key and not openai_key.startswith('your_') else '✗ Missing'}")
    print(f"Exa:    {'✓ Configured' if exa_key and not exa_key.startswith('your_') else '✗ Missing'}")
    print(f"Tavily: {'✓ Configured' if tavily_key and not tavily_key.startswith('your_') else '✗ Missing'}")
    print("=" * 60)
    
    if not openai_key or openai_key.startswith('your_'):
        print("\n⚠️  Missing API Keys!")
        print("See setup_instructions.md for how to get and configure API keys.\n")
    
    orchestrator = OrchestratorAgent()
    
    claim = "The 2020 US election had the highest voter turnout in history."
    
    print(f"Verifying claim: {claim}")
    result = await orchestrator.verify_claim(claim)
    
    print("\nVerification Result:")
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())
