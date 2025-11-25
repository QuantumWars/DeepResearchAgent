"""Political claims specialist agent."""

import os
from typing import List
from dotenv import load_dotenv
from src.models import ClaimAnalysis, Evidence
from src.tools.political_tools import political_web_search, assess_political_source

load_dotenv()


def analyze_political_claim_direct(claim: str) -> ClaimAnalysis:
    """Direct analysis function using real Tavily web search and deep scraping."""
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
            evidence=[], # Could reconstruct evidence from review body if needed
            confidence=float(existing_review.rating_score) / 5.0,
            reasoning=f"[MEMORY CACHED] {existing_review.review_body}",
            agent_name="PoliticalAgent (Memory)"
        )

    # 2. Search for relevant notes to augment context
    related_notes = memory.search_notes(claim)
    if related_notes:
        print(f"  [Memory] Found {len(related_notes)} related notes")

    # Use real Tavily web search to gather evidence
    search_results = political_web_search(claim, max_results=5)
    
    # Build evidence list
    evidence_items = []
    
    # Deep scrape the top 2 results for better context
    from src.tools.web_scraper import scrape_url_content
    
    for i, result in enumerate(search_results.get("results", [])):
        content = result.get("content", "")
        url = result.get("url", "")
        
        # If it's a top result, try to scrape full content for "reading between lines"
        if i < 2 and url:
            print(f"  ...Deep scraping: {url}")
            scraped = scrape_url_content(url)
            if scraped["success"] and len(scraped["content"]) > len(content):
                content = scraped["content"][:2000]  # Limit to 2000 chars to avoid context overflow
                print(f"     ✓ Extracted {len(scraped['content'])} chars")
        
        # Assess source credibility
        assessment = assess_political_source(url, content)
        
        evidence_items.append(Evidence(
            source=f"{result['title']} - {url}",
            content=content,
            confidence=assessment["confidence"],
            metadata={
                **result,
                "credibility_score": assessment["credibility_score"],
                "source_type": assessment["source_type"],
                "assessment_factors": assessment["assessment_factors"]
            }
        ))

        # Save high-confidence evidence as Atomic Notes
        if assessment["confidence"] > 0.7:
            note = AtomicNote(
                content=f"{result['title']}: {content[:200]}...",
                tags=["political", "fact-check"],
                source_url=url,
                confidence=assessment["confidence"],
                metadata={"claim": claim},
                timestamp=datetime.now().isoformat()
            )
            memory.add_note(note)
    
    # Add relevant notes from memory as evidence if they add value
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
        reasoning = "No reliable sources found to verify this political claim."
    else:
        # Calculate average confidence from evidence
        avg_confidence = sum(e.confidence for e in evidence_items) / len(evidence_items)
        
        # Check for official government sources
        has_official = any(
            e.metadata.get("source_type") == "official_government" 
            for e in evidence_items
        )
        
        if has_official and avg_confidence >= 0.7:
            verdict = "TRUE"
            reasoning = f"Based on {len(evidence_items)} source(s) including official government records, the claim is verified."
        elif avg_confidence >= 0.6:
            verdict = "PARTIALLY_TRUE"
            reasoning = f"Based on {len(evidence_items)} source(s), the claim has some support but may lack complete verification."
        elif avg_confidence >= 0.4:
            verdict = "UNVERIFIABLE"
            reasoning = f"Based on {len(evidence_items)} source(s), there is insufficient evidence to verify this claim."
        else:
            verdict = "FALSE"
            reasoning = f"Based on {len(evidence_items)} source(s), the claim appears to be false or misleading."
        
        confidence = avg_confidence
    
    # Create structured analysis
    analysis = ClaimAnalysis(
        claim=claim,
        verdict=verdict,
        evidence=evidence_items,
        confidence=confidence,
        reasoning=reasoning,
        agent_name="PoliticalAgent"
    )
    
    return analysis


if __name__ == "__main__":
    # Test the direct analysis function
    result = analyze_political_claim_direct("Senator Smith voted yes on the infrastructure bill in 2024")
    print(result.model_dump_json(indent=2))
