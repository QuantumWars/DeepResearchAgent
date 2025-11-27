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

async def test_claims():
    """Test the fact-checker with different types of claims"""
    
    orchestrator = OrchestratorAgent()
    
    # Different types of claims to test
    test_claims = [
        {
            "type": "STATISTICAL",
            "claim": "The 2020 US election had the highest voter turnout in history.",
            "description": "Statistical claim requiring numerical verification"
        },
        {
            "type": "FACTUAL",
            "claim": "The Eiffel Tower was completed in 1889.",
            "description": "Simple factual claim with specific date"
        },
        {
            "type": "COMPARATIVE",
            "claim": "Electric cars produce zero emissions.",
            "description": "Comparative/contextual claim requiring nuanced analysis"
        }
    ]
    
    print("="*70)
    print("FACT-CHECKER TEST SUITE")
    print("Testing AI-powered claim decomposition across different claim types")
    print("="*70)
    
    for idx, test in enumerate(test_claims, 1):
        print(f"\n{'='*70}")
        print(f"TEST {idx}: {test['type']} Claim")
        print(f"{'='*70}")
        print(f"Claim: {test['claim']}")
        print(f"Description: {test['description']}")
        print(f"{'-'*70}\n")
        
        try:
            result = await orchestrator.verify_claim(test['claim'])
            
            # Display results
            print(f"\n{'='*70}")
            print(f"RESULTS FOR TEST {idx}")
            print(f"{'='*70}")
            print(f"Verdict: {result['verdict']['status']}")
            print(f"Confidence: {result['verdict']['confidence']:.2%}")
            print(f"\nSub-claims identified ({len(result['sub_claims'])}):")
            for i, sc in enumerate(result['sub_claims'], 1):
                print(f"  {i}. [{sc['claim_type']}] {sc['text']}")
            
            print(f"\nTop Evidence Sources:")
            for i, evidence in enumerate(result['key_evidence'][:3], 1):
                tier_label = {1: "Official", 2: "Expert", 3: "News", 4: "Other"}
                print(f"  {i}. [Tier {evidence['source_tier']} - {tier_label.get(evidence['source_tier'], 'Unknown')}]")
                print(f"     {evidence['source']}")
                print(f"     {evidence['url']}")
            
            print(f"\nInvestigation Stats:")
            print(f"  • Time: {result['investigation_metadata']['time_elapsed']:.2f}s")
            print(f"  • Evidence: {len(result['key_evidence'])} sources")
            
            # Save individual report
            filename = f"test_report_{idx}_{test['type'].lower()}.json"
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"  • Report saved: {filename}")
            
        except Exception as e:
            print(f"\n✗ Test {idx} failed: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n{'='*70}\n")
        
        # Small delay between tests to avoid rate limits
        if idx < len(test_claims):
            print("Waiting 3 seconds before next test...\n")
            await asyncio.sleep(3)
    
    print("\n" + "="*70)
    print("TEST SUITE COMPLETE")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_claims())
