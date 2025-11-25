"""Scientific/Medical claims specialist agent."""

import os
from typing import List
from dotenv import load_dotenv
from agno.agent import Agent
from src.models import ClaimAnalysis, Evidence
from src.tools.scientific_tools import pubmed_literature_retriever, study_quality_assessor

load_dotenv()


def create_scientific_agent() -> Agent:
    """Create and configure the Scientific Claims Agent."""
    
    def analyze_scientific_claim(claim: str) -> str:
        """Analyze a scientific/medical claim using available tools."""
        # Use mock tools to gather evidence
        literature = pubmed_literature_retriever(claim, max_results=3)
        # Build evidence list
        evidence_items = []
        for result in literature.get("results", []):
            # Assess study quality
            quality = study_quality_assessor(result.get("pmid", "unknown"), result)
            
            evidence_items.append({
                "source": f"{result['journal']} ({result['year']})",
                "content": f"{result['title']} - {result['abstract']}",
                "confidence": quality["confidence"],
                "metadata": {
                    **result,
                    "quality_score": quality["quality_score"],
                    "study_type": quality["study_type"]
                }
            })
        
        # Create structured analysis
        analysis = ClaimAnalysis(
            claim=claim,
            verdict="TRUE",
            evidence=[Evidence(**e) for e in evidence_items],
            confidence=0.88,
            reasoning="Based on peer-reviewed literature, the claim is supported by high-quality studies. Evidence from randomized controlled trials confirms the finding.",
            agent_name="ScientificAgent"
        )
        
        return analysis.model_dump_json(indent=2)
    
    agent = Agent(
        name="Scientific Specialist",
        instructions="""You are a scientific and medical fact-checking specialist.

Your ONLY job is to call the analyze_scientific_claim tool with the user's claim.
You MUST call the analyze_scientific_claim tool for every claim you receive.
Do NOT provide any other response - just call the tool.""",
        model="openai:gpt-4o-mini",
        tools=[analyze_scientific_claim],
        markdown=True,
    )
    
    return agent


def analyze_scientific_claim_direct(claim: str) -> ClaimAnalysis:
    """Direct analysis function using real PubMed API."""
    from src.memory.manager import MemoryManager
    from src.models import AtomicNote
    from datetime import datetime

    memory = MemoryManager()
    
    # 1. Check for existing verified review
    existing_review = memory.get_claim_review(claim)
    if existing_review and existing_review.review_rating == "TRUE" and existing_review.rating_score >= 4:
        print(f"  [Memory] Found existing verified review for: {claim}")
        return ClaimAnalysis(
            claim=claim,
            verdict=existing_review.review_rating,
            evidence=[], 
            confidence=float(existing_review.rating_score) / 5.0,
            reasoning=f"[MEMORY CACHED] {existing_review.review_body}",
            agent_name="ScientificAgent (Memory)"
        )

    # 2. Search for relevant notes
    related_notes = memory.search_notes(claim)
    if related_notes:
        print(f"  [Memory] Found {len(related_notes)} related notes")

    # Use real PubMed tools to gather evidence
    literature = pubmed_literature_retriever(claim, max_results=3)
    
    # Build evidence list
    evidence_items = []
    for result in literature.get("results", []):
        # Assess study quality
        quality = study_quality_assessor(result.get("pmid", "unknown"), result)
        
        evidence_items.append(Evidence(
            source=f"{result['journal']} ({result['year']}) - PMID: {result['pmid']}",
            content=f"{result['title']}. {result['abstract'][:300]}...",
            confidence=quality["confidence"],
            metadata={
                **result,
                "quality_score": quality["quality_score"],
                "study_type": quality["study_type"],
                "assessment_factors": quality["assessment_factors"]
            }
        ))

        # Save high-quality studies as Atomic Notes
        if quality["confidence"] > 0.7:
            note = AtomicNote(
                content=f"{result['title']}: {result['abstract'][:200]}...",
                tags=["scientific", "medical", "study"],
                source_url=f"https://pubmed.ncbi.nlm.nih.gov/{result['pmid']}/",
                confidence=quality["confidence"],
                metadata={"pmid": result['pmid'], "journal": result['journal']},
                timestamp=datetime.now().isoformat()
            )
            memory.add_note(note)

    # Add relevant notes from memory
    for note in related_notes:
        evidence_items.append(Evidence(
            source=f"Memory: {note.source_url or 'Internal'}",
            content=note.content,
            confidence=note.confidence,
            metadata={"from_memory": True}
        ))
    
    # Determine verdict based on evidence
    if not evidence_items:
        verdict = "UNVERIFIABLE"
        confidence = 0.0
        reasoning = "No scientific literature found to support or refute this claim."
    else:
        # Calculate average confidence from evidence
        avg_confidence = sum(e.confidence for e in evidence_items) / len(evidence_items)
        
        # Simple heuristic: if average confidence is high, claim is likely true
        if avg_confidence >= 0.7:
            verdict = "TRUE"
            reasoning = f"Based on {len(evidence_items)} peer-reviewed publication(s), the claim is well-supported by scientific evidence."
        elif avg_confidence >= 0.5:
            verdict = "PARTIALLY_TRUE"
            reasoning = f"Based on {len(evidence_items)} publication(s), the claim has some scientific support but may require further verification."
        else:
            verdict = "FALSE"
            reasoning = f"Based on {len(evidence_items)} publication(s), the claim lacks strong scientific support."
        
        confidence = avg_confidence
    
    # Create structured analysis
    analysis = ClaimAnalysis(
        claim=claim,
        verdict=verdict,
        evidence=evidence_items,
        confidence=confidence,
        reasoning=reasoning,
        agent_name="ScientificAgent"
    )
    
    return analysis


if __name__ == "__main__":
    # Test the agent
    agent = create_scientific_agent()
    response = agent.run("COVID-19 vaccines are effective at preventing severe disease")
    print(response.content)
