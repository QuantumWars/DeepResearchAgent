"""Test Flow 4: Evidence Synthesis

This test verifies that the Evidence Synthesis Coordinator correctly aggregates
evidence from multiple specialist agents into a final verdict.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents.synthesis import synthesize_evidence_direct
from src.agents.political import analyze_political_claim_direct
from src.agents.scientific import analyze_scientific_claim_direct
from src.models import FinalVerdict


def test_evidence_synthesis():
    """Test that Evidence Synthesis Coordinator aggregates multiple analyses."""
    print("=" * 60)
    print("TEST 1: Evidence Synthesis")
    print("=" * 60)
    
    claim = "Test claim for synthesis"
    
    print(f"\nClaim: {claim}")
    print("\nGathering evidence from specialist agents...")
    
    try:
        # Get analyses from different agents
        political_analysis = analyze_political_claim_direct(claim)
        scientific_analysis = analyze_scientific_claim_direct(claim)
        
        print(f"  Political Agent: {political_analysis.verdict} (confidence: {political_analysis.confidence})")
        print(f"  Scientific Agent: {scientific_analysis.verdict} (confidence: {scientific_analysis.confidence})")
        
        print("\nSynthesizing evidence...")
        
        # Synthesize
        final_verdict = synthesize_evidence_direct(claim, [political_analysis, scientific_analysis])
        
        print(f"\n✓ Successfully synthesized evidence:")
        print(f"  Final Verdict: {final_verdict.verdict}")
        print(f"  Overall Confidence: {final_verdict.confidence:.2f}")
        print(f"  Total Evidence: {len(final_verdict.supporting_evidence)} pieces")
        print(f"  Agent Analyses: {len(final_verdict.agent_analyses)}")
        
        # Verify structure
        assert final_verdict.claim == claim, "Claim mismatch"
        assert len(final_verdict.agent_analyses) == 2, "Should have 2 agent analyses"
        assert len(final_verdict.supporting_evidence) > 0, "Should have evidence"
        assert 0 <= final_verdict.confidence <= 1, "Invalid confidence score"
        assert final_verdict.summary, "Should have summary"
        
        print("\n✓ PASS: Evidence Synthesis Coordinator returned valid final verdict")
        return True
        
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_single_agent_synthesis():
    """Test synthesis with only one agent."""
    print("\n" + "=" * 60)
    print("TEST 2: Single Agent Synthesis")
    print("=" * 60)
    
    claim = "Single agent test claim"
    
    print(f"\nClaim: {claim}")
    
    try:
        # Get analysis from one agent
        political_analysis = analyze_political_claim_direct(claim)
        
        # Synthesize
        final_verdict = synthesize_evidence_direct(claim, [political_analysis])
        
        print(f"\n✓ Successfully synthesized with single agent:")
        print(f"  Final Verdict: {final_verdict.verdict}")
        print(f"  Confidence: {final_verdict.confidence:.2f}")
        
        assert final_verdict.verdict == political_analysis.verdict, "Verdict should match single agent"
        assert final_verdict.confidence == political_analysis.confidence, "Confidence should match"
        
        print("\n✓ PASS: Single agent synthesis works correctly")
        return True
        
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Flow 4 tests."""
    print("\n" + "=" * 60)
    print("FLOW 4 VERIFICATION: Evidence Synthesis")
    print("=" * 60)
    
    results = []
    
    # Test 1: Multi-agent synthesis
    results.append(test_evidence_synthesis())
    
    # Test 2: Single agent synthesis
    results.append(test_single_agent_synthesis())
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED - Flow 4 Complete!")
        return 0
    else:
        print(f"\n✗ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
