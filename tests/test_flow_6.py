"""Test Flow 6: Scientific Agent with Real PubMed Tools

This test verifies that the Scientific Agent correctly analyzes scientific claims
using the real PubMed API.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents.scientific import analyze_scientific_claim_direct
from src.models import ClaimAnalysis


def test_scientific_agent_real_api():
    """Test that Scientific Agent analyzes a claim using real PubMed API."""
    print("=" * 60)
    print("TEST 1: Scientific Agent with Real PubMed API")
    print("=" * 60)
    
    claim = "COVID-19 vaccines reduce hospitalization rates"
    
    print(f"\nClaim: {claim}")
    print("\nAnalyzing with real PubMed API...")
    
    try:
        analysis = analyze_scientific_claim_direct(claim)
        
        print(f"\n✓ Successfully got analysis:")
        print(f"  Verdict: {analysis.verdict}")
        print(f"  Confidence: {analysis.confidence:.2f}")
        print(f"  Evidence count: {len(analysis.evidence)}")
        print(f"  Agent: {analysis.agent_name}")
        
        # Print evidence details
        print(f"\n  Evidence:")
        for i, evidence in enumerate(analysis.evidence, 1):
            print(f"    {i}. {evidence.source}")
            print(f"       Confidence: {evidence.confidence:.2f}")
            print(f"       Quality: {evidence.metadata.get('quality_score', 'N/A'):.2f}")
            print(f"       Type: {evidence.metadata.get('study_type', 'N/A')}")
        
        # Verify it has the expected structure
        assert analysis.claim == claim, "Claim mismatch"
        assert analysis.agent_name == "ScientificAgent", "Wrong agent name"
        assert len(analysis.evidence) > 0, "No evidence provided"
        assert 0 <= analysis.confidence <= 1, "Invalid confidence score"
        
        print("\n✓ PASS: Scientific Agent returned valid analysis with real PubMed data")
        return True
        
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scientific_agent_vitamin_claim():
    """Test Scientific Agent with a vitamin supplementation claim."""
    print("\n" + "=" * 60)
    print("TEST 2: Scientific Agent with Vitamin D Claim")
    print("=" * 60)
    
    claim = "Vitamin D supplementation prevents respiratory infections"
    
    print(f"\nClaim: {claim}")
    print("\nAnalyzing...")
    
    try:
        analysis = analyze_scientific_claim_direct(claim)
        
        print(f"\n✓ Successfully analyzed claim:")
        print(f"  Verdict: {analysis.verdict}")
        print(f"  Confidence: {analysis.confidence:.2f}")
        print(f"  Evidence count: {len(analysis.evidence)}")
        
        # Just verify it returns valid data
        assert analysis.agent_name == "ScientificAgent", "Wrong agent"
        assert 0 <= analysis.confidence <= 1, "Invalid confidence"
        
        print("\n✓ PASS: Correctly analyzed vitamin claim")
        return True
        
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Flow 6 tests."""
    print("\n" + "=" * 60)
    print("FLOW 6 VERIFICATION: Scientific Agent with Real Tools")
    print("=" * 60)
    
    results = []
    
    # Test 1: Real API analysis
    results.append(test_scientific_agent_real_api())
    
    # Test 2: Vitamin claim
    results.append(test_scientific_agent_vitamin_claim())
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED - Flow 6 Complete!")
        return 0
    else:
        print(f"\n✗ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
