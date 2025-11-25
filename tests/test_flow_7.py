"""Test Flow 7: End-to-End System Integration

This test verifies the complete fact-checking system with real APIs:
- Supervisor routing
- Political Agent with Tavily
- Scientific Agent with PubMed
- Evidence Synthesis
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents.supervisor import route_claim_direct
from src.agents.political import analyze_political_claim_direct
from src.agents.scientific import analyze_scientific_claim_direct
from src.agents.synthesis import synthesize_evidence_direct


def test_end_to_end_political():
    """Test end-to-end system with a political claim."""
    print("=" * 60)
    print("TEST 1: End-to-End Political Claim")
    print("=" * 60)
    
    claim = "The Infrastructure Investment and Jobs Act passed in 2021"
    
    print(f"\nClaim: {claim}")
    
    try:
        # Step 1: Route
        print("\n[1] Routing claim...")
        routing = route_claim_direct(claim)
        print(f"    → Routed to: {routing.target_agent}")
        assert routing.target_agent == "PoliticalAgent", "Should route to Political Agent"
        
        # Step 2: Analyze
        print("\n[2] Analyzing with Political Agent...")
        analysis = analyze_political_claim_direct(claim)
        print(f"    → Verdict: {analysis.verdict}")
        print(f"    → Confidence: {analysis.confidence:.2f}")
        print(f"    → Evidence: {len(analysis.evidence)} sources")
        
        # Step 3: Synthesize
        print("\n[3] Synthesizing evidence...")
        final_verdict = synthesize_evidence_direct(claim, [analysis])
        print(f"    → Final Verdict: {final_verdict.verdict}")
        print(f"    → Overall Confidence: {final_verdict.confidence:.2f}")
        
        # Verify
        assert final_verdict.claim == claim
        assert len(final_verdict.agent_analyses) == 1
        assert final_verdict.verdict == analysis.verdict
        
        print("\n✓ PASS: End-to-end political claim processing successful")
        return True
        
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_end_to_end_scientific():
    """Test end-to-end system with a scientific claim."""
    print("\n" + "=" * 60)
    print("TEST 2: End-to-End Scientific Claim")
    print("=" * 60)
    
    claim = "COVID-19 vaccines reduce hospitalization rates"
    
    print(f"\nClaim: {claim}")
    
    try:
        # Step 1: Route
        print("\n[1] Routing claim...")
        routing = route_claim_direct(claim)
        print(f"    → Routed to: {routing.target_agent}")
        assert routing.target_agent == "ScientificAgent", "Should route to Scientific Agent"
        
        # Step 2: Analyze
        print("\n[2] Analyzing with Scientific Agent...")
        analysis = analyze_scientific_claim_direct(claim)
        print(f"    → Verdict: {analysis.verdict}")
        print(f"    → Confidence: {analysis.confidence:.2f}")
        print(f"    → Evidence: {len(analysis.evidence)} papers")
        
        # Step 3: Synthesize
        print("\n[3] Synthesizing evidence...")
        final_verdict = synthesize_evidence_direct(claim, [analysis])
        print(f"    → Final Verdict: {final_verdict.verdict}")
        print(f"    → Overall Confidence: {final_verdict.confidence:.2f}")
        
        # Verify
        assert final_verdict.claim == claim
        assert len(final_verdict.agent_analyses) == 1
        assert final_verdict.verdict == analysis.verdict
        
        print("\n✓ PASS: End-to-end scientific claim processing successful")
        return True
        
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_agent_synthesis():
    """Test synthesis with both political and scientific analyses."""
    print("\n" + "=" * 60)
    print("TEST 3: Multi-Agent Evidence Synthesis")
    print("=" * 60)
    
    claim = "Government funding for vaccine research"
    
    print(f"\nClaim: {claim}")
    
    try:
        # Get analyses from both agents
        print("\n[1] Analyzing with both agents...")
        political_analysis = analyze_political_claim_direct(claim)
        scientific_analysis = analyze_scientific_claim_direct(claim)
        
        print(f"    → Political: {political_analysis.verdict} ({political_analysis.confidence:.2f})")
        print(f"    → Scientific: {scientific_analysis.verdict} ({scientific_analysis.confidence:.2f})")
        
        # Synthesize
        print("\n[2] Synthesizing evidence from both agents...")
        final_verdict = synthesize_evidence_direct(
            claim, 
            [political_analysis, scientific_analysis]
        )
        print(f"    → Final Verdict: {final_verdict.verdict}")
        print(f"    → Overall Confidence: {final_verdict.confidence:.2f}")
        print(f"    → Total Evidence: {len(final_verdict.supporting_evidence)} pieces")
        
        # Verify
        assert len(final_verdict.agent_analyses) == 2
        assert len(final_verdict.supporting_evidence) > 0
        
        print("\n✓ PASS: Multi-agent synthesis successful")
        return True
        
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Flow 7 tests."""
    print("\n" + "=" * 60)
    print("FLOW 7 VERIFICATION: End-to-End System")
    print("=" * 60)
    
    # Check API keys
    if not os.getenv("TAVILY_API_KEY"):
        print("\n⚠ WARNING: TAVILY_API_KEY not set")
        return 1
    if not os.getenv("PUBMED_EMAIL"):
        print("\n⚠ WARNING: PUBMED_EMAIL not set")
    
    results = []
    
    # Test 1: Political claim end-to-end
    results.append(test_end_to_end_political())
    
    # Test 2: Scientific claim end-to-end
    results.append(test_end_to_end_scientific())
    
    # Test 3: Multi-agent synthesis
    results.append(test_multi_agent_synthesis())
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED - Flow 7 Complete!")
        print("\n🎉 ENTIRE SYSTEM VERIFIED - All Flows (1-7) Complete!")
        return 0
    else:
        print(f"\n✗ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
