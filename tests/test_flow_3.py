"""Test Flow 3: Scientific Agent Implementation

This test verifies that the Scientific Agent correctly analyzes scientific claims
and returns structured evidence using mock tools.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents.scientific import analyze_scientific_claim_direct
from src.models import ClaimAnalysis


def test_scientific_agent_analysis():
    """Test that Scientific Agent analyzes a claim and returns structured evidence."""
    print("=" * 60)
    print("TEST 1: Scientific Agent Analysis")
    print("=" * 60)
    
    claim = "COVID-19 vaccines are effective at preventing severe disease"
    
    print(f"\nClaim: {claim}")
    print("\nAnalyzing...")
    
    try:
        analysis = analyze_scientific_claim_direct(claim)
        
        print(f"\n✓ Successfully got analysis:")
        print(f"  Verdict: {analysis.verdict}")
        print(f"  Confidence: {analysis.confidence}")
        print(f"  Evidence count: {len(analysis.evidence)}")
        print(f"  Agent: {analysis.agent_name}")
        
        # Verify it has the expected structure
        assert analysis.claim == claim, "Claim mismatch"
        assert analysis.agent_name == "ScientificAgent", "Wrong agent name"
        assert len(analysis.evidence) > 0, "No evidence provided"
        assert analysis.confidence > 0, "Invalid confidence score"
        
        print("\n✓ PASS: Scientific Agent returned valid structured analysis")
        return True
        
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Flow 3 tests."""
    print("\n" + "=" * 60)
    print("FLOW 3 VERIFICATION: Scientific Agent")
    print("=" * 60)
    
    results = []
    
    # Test 1: Scientific agent analysis
    results.append(test_scientific_agent_analysis())
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED - Flow 3 Complete!")
        return 0
    else:
        print(f"\n✗ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
