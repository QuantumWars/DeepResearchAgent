import asyncio
import json
import os
from src.agents.orchestrator import OrchestratorAgent

async def main():
    # Check for API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not found. Agents may fail.")
    
    orchestrator = OrchestratorAgent()
    
    claim = "The 2020 US election had the highest voter turnout in history."
    
    print(f"Verifying claim: {claim}")
    result = await orchestrator.verify_claim(claim)
    
    print("\nVerification Result:")
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())
