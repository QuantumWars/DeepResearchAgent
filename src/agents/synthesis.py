"""Evidence Synthesis Coordinator Agent.

This agent aggregates evidence from multiple specialist agents and produces
a final synthesized verdict.
"""

import os
from typing import List
from dotenv import load_dotenv
from agno.agent import Agent
from src.models import ClaimAnalysis, FinalVerdict, Evidence

load_dotenv()


def synthesize_evidence_direct(claim: str, agent_analyses: List[ClaimAnalysis]) -> FinalVerdict:
    """
    Synthesize evidence from multiple agent analyses into a final verdict.
    
    Args:
        claim: The original claim being fact-checked
        agent_analyses: List of analyses from specialist agents
        
    Returns:
        FinalVerdict with aggregated evidence and confidence
    """
    if not agent_analyses:
        return FinalVerdict(
            claim=claim,
            verdict="UNVERIFIABLE",
            confidence=0.0,
            supporting_evidence=[],
            agent_analyses=[],
            summary="No evidence available to verify this claim."
        )
    
    # Aggregate all evidence
    all_evidence = []
    for analysis in agent_analyses:
        all_evidence.extend(analysis.evidence)
    
    # Calculate weighted confidence (average of agent confidences)
    total_confidence = sum(a.confidence for a in agent_analyses) / len(agent_analyses)
    
    # Determine final verdict based on consensus
    verdicts = [a.verdict for a in agent_analyses]
    
    # Simple majority voting
    verdict_counts = {}
    for v in verdicts:
        verdict_counts[v] = verdict_counts.get(v, 0) + 1
    
    final_verdict = max(verdict_counts, key=verdict_counts.get)
    
    # Build summary
    agent_summaries = []
    for analysis in agent_analyses:
        agent_summaries.append(
            f"- {analysis.agent_name}: {analysis.verdict} (confidence: {analysis.confidence:.2f})"
        )
    
    summary = f"""Final Verdict: {final_verdict}

Based on analysis from {len(agent_analyses)} specialist agent(s):
{chr(10).join(agent_summaries)}

Overall Confidence: {total_confidence:.2f}

The claim has been evaluated using {len(all_evidence)} piece(s) of evidence from multiple sources.
"""
    
    # Save final verdict to memory as ClaimReview
    from src.memory.manager import MemoryManager
    from src.models import ClaimReview
    from datetime import datetime
    
    memory = MemoryManager()
    
    # Map confidence to 1-5 score
    rating_score = int(total_confidence * 5)
    if rating_score < 1: rating_score = 1
    
    review = ClaimReview(
        claim_reviewed=claim,
        item_reviewed="User Query",
        review_rating=final_verdict,
        rating_score=rating_score,
        review_body=summary,
        author="SynthesisAgent",
        date_published=datetime.now().isoformat()
    )
    memory.save_claim_review(review)
    print(f"  [Memory] Saved final verdict for: {claim}")

    return FinalVerdict(
        claim=claim,
        verdict=final_verdict,
        confidence=total_confidence,
        supporting_evidence=all_evidence,
        agent_analyses=agent_analyses,
        summary=summary
    )


def create_synthesis_agent() -> Agent:
    """Create and configure the Evidence Synthesis Coordinator Agent."""
    
    def synthesize_evidence(analyses_json: str) -> str:
        """Tool to synthesize evidence from multiple analyses."""
        import json
        
        # Parse the analyses
        analyses_data = json.loads(analyses_json)
        claim = analyses_data.get("claim", "")
        analyses_list = analyses_data.get("analyses", [])
        
        # Convert to ClaimAnalysis objects
        agent_analyses = [ClaimAnalysis(**a) for a in analyses_list]
        
        # Synthesize
        verdict = synthesize_evidence_direct(claim, agent_analyses)
        
        return verdict.model_dump_json(indent=2)
    
    agent = Agent(
        name="Evidence Synthesis Coordinator",
        instructions="""You are the Evidence Synthesis Coordinator.

Your ONLY job is to call the synthesize_evidence tool with the provided analyses.
You MUST call the synthesize_evidence tool.
Do NOT provide any other response - just call the tool.""",
        model="openai:gpt-4o-mini",
        tools=[synthesize_evidence],
        markdown=True,
    )
    
    return agent


if __name__ == "__main__":
    # Test the synthesis
    from src.agents.political import analyze_political_claim_direct
    from src.agents.scientific import analyze_scientific_claim_direct
    
    claim = "Test claim"
    
    # Get analyses from different agents
    political_analysis = analyze_political_claim_direct(claim)
    scientific_analysis = analyze_scientific_claim_direct(claim)
    
    # Synthesize
    final_verdict = synthesize_evidence_direct(claim, [political_analysis, scientific_analysis])
    
    print(final_verdict.model_dump_json(indent=2))
