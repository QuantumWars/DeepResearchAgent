"""Test Flow 5: Political Agent with Real Tavily Search

This test verifies that the Political Agent correctly analyzes political claims
using the real Tavily web search API.

NOTE: This test requires TAVILY_API_KEY to be set in your .env file.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents.political import analyze_political_claim_direct
from src.models import ClaimAnalysis


def test_political_agent_real_api():
    """Test that Political Agent analyzes a claim using real Tavily API."""
    print("=" * 60)
    print("TEST 1: Political Agent with Real Tavily Search")
    print("=" * 60)
    
    claim = "The Infrastructure Investment and Jobs Act passed in 2021"
    
    print(f"\nClaim: {claim}")
    print("\nAnalyzing with real Tavily web search...")
    
    try:
        analysis = analyze_political_claim_direct(claim)
        
        print(f"\n✓ Successfully got analysis:")
        print(f"  Verdict: {analysis.verdict}")
        print(f"  Confidence: {analysis.confidence:.2f}")
        print(f"  Evidence count: {len(analysis.evidence)}")
        print(f"  Agent: {analysis.agent_name}")
        
        # Print evidence details
        print(f"\n  Evidence:")
        for i, evidence in enumerate(analysis.evidence, 1):
            print(f"    {i}. {evidence.source[:80]}...")
            print(f"       Confidence: {evidence.confidence:.2f}")
            print(f"       Credibility: {evidence.metadata.get('credibility_score', 'N/A'):.2f}")
            print(f"       Type: {evidence.metadata.get('source_type', 'N/A')}")
        
        # Verify it has the expected structure
        assert analysis.claim == claim, "Claim mismatch"
        assert analysis.agent_name == "PoliticalAgent", "Wrong agent name"
        assert 0 <= analysis.confidence <= 1, "Invalid confidence score"
        
        print("\n✓ PASS: Political Agent returned valid analysis with real Tavily data")
        return True
        
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_political_agent_voting_record():
    """Test Political Agent with a voting record claim."""
    print("\n" + "=" * 60)
    print("TEST 2: Political Agent with Voting Record Claim")
    print("=" * 60)
    
    claim = "American Rescue Plan Act passed in March 2021"
    
    print(f"\nClaim: {claim}")
    print("\nAnalyzing...")
    
    try:
        analysis = analyze_political_claim_direct(claim)
        
        print(f"\n✓ Successfully analyzed claim:")
        print(f"  Verdict: {analysis.verdict}")
        print(f"  Confidence: {analysis.confidence:.2f}")
        print(f"  Evidence count: {len(analysis.evidence)}")
        
        # Just verify it returns valid data
        assert analysis.agent_name == "PoliticalAgent", "Wrong agent"
        assert 0 <= analysis.confidence <= 1, "Invalid confidence"
        
        print("\n✓ PASS: Correctly analyzed voting record claim")
        return True
        
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Flow 5 tests."""
    print("\n" + "=" * 60)
    print("FLOW 5 VERIFICATION: Political Agent with Real Tools")
    print("=" * 60)
    
    # Check if Tavily API key is set
    if not os.getenv("TAVILY_API_KEY"):
        print("\n⚠ WARNING: TAVILY_API_KEY not set in .env file")
        print("Please set your Tavily API key to run these tests.")
        print("Get a free API key at: https://tavily.com/")
        return 1
    
    results = []
    
    # Test 1: Real API analysis
    results.append(test_political_agent_real_api())
    
    # Test 2: Voting record
    results.append(test_political_agent_voting_record())
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED - Flow 5 Complete!")
        return 0
    else:
        print(f"\n✗ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
