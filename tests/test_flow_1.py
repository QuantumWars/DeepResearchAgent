"""Test Flow 1: Supervisor Routing

This test verifies that the Supervisor routing logic correctly routes claims
to the appropriate specialist agents.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents.supervisor import route_claim_direct
from src.models import RoutingDecision


def test_political_claim_routing():
    """Test that political claims are routed to PoliticalAgent."""
    print("=" * 60)
    print("TEST 1: Political Claim Routing")
    print("=" * 60)
    
    claim = "Senator Smith voted yes on the infrastructure bill in 2024"
    
    print(f"\nClaim: {claim}")
    print("\nRouting decision:")
    
    decision = route_claim_direct(claim)
    print(f"  Target Agent: {decision.target_agent}")
    print(f"  Reasoning: {decision.reasoning}")
    print(f"  Confidence: {decision.confidence}")
    
    if decision.target_agent == "PoliticalAgent":
        print("\n✓ PASS: Correctly routed to PoliticalAgent")
        return True
    else:
        print(f"\n✗ FAIL: Expected PoliticalAgent, got {decision.target_agent}")
        return False


def test_scientific_claim_routing():
    """Test that scientific claims are routed to ScientificAgent."""
    print("\n" + "=" * 60)
    print("TEST 2: Scientific Claim Routing")
    print("=" * 60)
    
    claim = "COVID-19 vaccines are effective at preventing severe disease"
    
    print(f"\nClaim: {claim}")
    print("\nRouting decision:")
    
    decision = route_claim_direct(claim)
    print(f"  Target Agent: {decision.target_agent}")
    print(f"  Reasoning: {decision.reasoning}")
    print(f"  Confidence: {decision.confidence}")
    
    if decision.target_agent == "ScientificAgent":
        print("\n✓ PASS: Correctly routed to ScientificAgent")
        return True
    else:
        print(f"\n✗ FAIL: Expected ScientificAgent, got {decision.target_agent}")
        return False


def main():
    """Run all Flow 1 tests."""
    print("\n" + "=" * 60)
    print("FLOW 1 VERIFICATION: Supervisor Routing")
    print("=" * 60)
    
    results = []
    
    # Test 1: Political routing
    results.append(test_political_claim_routing())
    
    # Test 2: Scientific routing
    results.append(test_scientific_claim_routing())
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED - Flow 1 Complete!")
        return 0
    else:
        print(f"\n✗ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
