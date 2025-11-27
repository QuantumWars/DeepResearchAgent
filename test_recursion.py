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

async def test_recursion():
    """Test recursion with claims designed to trigger deeper investigation"""
    
    orchestrator = OrchestratorAgent()
    
    # Claims designed to have low initial confidence
    claims = [
        "The moon landing was faked in 1969.",  # Controversial, should have contradicting sources
        "Drinking 8 glasses of water daily is scientifically proven.",  # Common myth with nuanced truth
    ]
    
    for claim in claims:
        print("\n" + "="*70)
        print(f"TESTING: {claim}")
        print("="*70)
        
        result = await orchestrator.verify_claim(claim, max_depth=2)
        
        print("\n" + "-"*70)
        print("RESULTS")
        print("-"*70)
        print(f"Verdict: {result['verdict']['status']}")
        print(f"Confidence: {result['verdict']['confidence']:.2%}")
        print(f"Sub-claims: {len(result['sub_claims'])}")
        print(f"Evidence: {len(result['key_evidence'])}")
        print(f"Time: {result['investigation_metadata']['time_elapsed']:.2f}s")
        print("="*70)
        
        # Small delay between tests
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(test_recursion())
