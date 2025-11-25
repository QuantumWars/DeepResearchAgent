"""Main entry point for the Agentic Fact-Checking System.

This demonstrates the end-to-end workflow using Agno agents.
"""

import sys
import json
from src.agents.supervisor import create_supervisor_agent
from src.agents.political import analyze_political_claim_direct
from src.agents.scientific import analyze_scientific_claim_direct
from src.agents.synthesis import synthesize_evidence_direct
from src.models import RoutingDecision


def fact_check(claim: str) -> dict:
    """
    Fact-check a claim using the multi-agent system.
    
    Args:
        claim: The claim to fact-check
        
    Returns:
        Dictionary with routing decision, analyses, and final verdict
    """
    print(f"\n{'='*60}")
    print(f"FACT-CHECKING: {claim}")
    print(f"{'='*60}\n")
    
    # Step 1: Route the claim using Supervisor Agent
    print("Step 1: Routing claim using Supervisor Agent...")
    supervisor = create_supervisor_agent()
    routing_response = supervisor.run(claim)
    
    # Parse the routing decision from agent response
    try:
        # Try to parse the content directly as JSON
        routing_data = json.loads(routing_response.content)
        
        # Check if this is a tool call structure (Agno format)
        if "recipient_name" in routing_data and "parameters" in routing_data:
            # This is a tool call - we need to actually execute it
            # For now, fall back to direct routing
            raise ValueError("Tool call structure detected, using fallback")
        
        routing = RoutingDecision(**routing_data)
    except (json.JSONDecodeError, ValueError, Exception) as e:
        # Fallback to direct routing
        from src.agents.supervisor import route_claim_direct
        routing = route_claim_direct(claim)
    
    print(f"  → Routed to: {routing.target_agent}")
    print(f"  → Reasoning: {routing.reasoning}")
    print(f"  → Confidence: {routing.confidence}\n")
    
    # Step 2: Get specialist analysis
    print("Step 2: Analyzing claim with specialist agent(s)...")
    analyses = []
    
    if routing.target_agent == "PoliticalAgent":
        analysis = analyze_political_claim_direct(claim)
        analyses.append(analysis)
        print(f"  → Political Agent: {analysis.verdict} (confidence: {analysis.confidence})")
    elif routing.target_agent == "ScientificAgent":
        analysis = analyze_scientific_claim_direct(claim)
        analyses.append(analysis)
        print(f"  → Scientific Agent: {analysis.verdict} (confidence: {analysis.confidence})")
    
    # Step 3: Synthesize evidence
    print("\nStep 3: Synthesizing evidence...")
    final_verdict = synthesize_evidence_direct(claim, analyses)
    print(f"  → Final Verdict: {final_verdict.verdict}")
    print(f"  → Overall Confidence: {final_verdict.confidence:.2f}")
    print(f"  → Total Evidence: {len(final_verdict.supporting_evidence)} piece(s)\n")
    
    # Print summary
    print("="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(final_verdict.summary)
    
    return {
        "routing": routing,
        "analyses": analyses,
        "final_verdict": final_verdict
    }


def main():
    """Run example fact-checks."""
    # Example 1: Political claim
    fact_check("Senator Smith voted yes on the infrastructure bill in 2024")
    
    print("\n" + "="*80 + "\n")
    
    # Example 2: Scientific claim
    fact_check("COVID-19 vaccines are effective at preventing severe disease")


if __name__ == "__main__":
    main()
