"""Agentic investigator using Agno with structured Pydantic outputs.

This module provides a proper agent-based investigation system that:
1. Uses Agno agents for decision-making
2. Returns structured Pydantic models
3. Integrates with the fact-checking workflow
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from dotenv import load_dotenv
load_dotenv()

from agno.agent import Agent
from typing import List, Dict, Any
from src.tools.web_scraper import scrape_url_content
from src.tools.link_analyzer import extract_links_with_context, filter_relevant_links
from src.memory import InvestigationMemory
from src.models.investigation import (
    InvestigationResult, 
    PageFinding, 
    InvestigationDecision,
    LinkWithContext
)


def create_investigator_agent() -> Agent:
    """Create an investigator agent that makes decisions about link following."""
    #recursive process of self calling tool 
    
    def decide_next_links(
        page_content: str,
        available_links: str,
        query: str,
        pages_visited: int,
        max_pages: int
    ) -> str:
        """
        Analyze page content and decide which links to follow.
        
        Args:
            page_content: Content of the current page (first 1000 chars)
            available_links: JSON string of available links with context
            query: Investigation query
            pages_visited: Number of pages already visited
            max_pages: Maximum pages allowed
            
        Returns:
            JSON string with InvestigationDecision
        """
        import json
        
        # Parse available links
        try:
            links = json.loads(available_links)
        except:
            return InvestigationDecision(
                continue_investigation=False,
                reasoning="Could not parse available links",
                confidence=0.0
            ).model_dump_json()
        
        # Check if we should continue
        if pages_visited >= max_pages:
            return InvestigationDecision(
                continue_investigation=False,
                reasoning=f"Reached maximum pages ({max_pages})",
                confidence=1.0
            ).model_dump_json()
        
        if not links:
            return InvestigationDecision(
                continue_investigation=False,
                reasoning="No relevant links found",
                confidence=0.8
            ).model_dump_json()
        
        # Select top links based on relevance
        top_links = sorted(links, key=lambda x: x.get('relevance_score', 0), reverse=True)[:3]
        selected_urls = [link['url'] for link in top_links]
        
        return InvestigationDecision(
            continue_investigation=True,
            reasoning=f"Found {len(top_links)} highly relevant links to investigate further",
            links_to_follow=selected_urls,
            confidence=0.85
        ).model_dump_json()
    
    agent = Agent(
        name="InvestigatorAgent",
        instructions="""You are an expert investigative researcher.

Your job is to analyze web page content and decide which links are worth following for deeper investigation.

When making decisions:
1. Prioritize links that provide evidence or deeper context
2. Look for authoritative sources (news, government, academic)
3. Avoid social media, ads, and unrelated topics
4. Consider the investigation query and what has been found so far

Always use the decide_next_links tool to make structured decisions.""",
        model="openai:gpt-4o-mini",
        tools=[decide_next_links],
        markdown=False,
    )
    
    return agent


def agentic_investigate(
    start_url: str,
    query: str,
    max_depth: int = 2,
    max_pages: int = 5
) -> InvestigationResult:
    """
    Perform agent-driven recursive investigation with structured outputs.
    
    Args:
        start_url: Starting URL
        query: Investigation query
        max_depth: Maximum recursion depth
        max_pages: Maximum pages to visit
        
    Returns:
        Structured InvestigationResult
    """
    memory = InvestigationMemory(query)
    agent = create_investigator_agent()
    
    # Queue: (url, depth, parent_url)
    to_visit = [(start_url, 0, None)]
    findings: List[PageFinding] = []
    
    print(f"\n🤖 Starting AGENTIC Investigation with Structured Outputs...")
    print(f"   Query: {query}")
    print(f"   Max Depth: {max_depth}, Max Pages: {max_pages}\n")
    
    while to_visit and memory.get_page_count() < max_pages:
        current_url, depth, parent_url = to_visit.pop(0)
        
        if memory.has_visited(current_url):
            continue
        
        indent = '  ' * depth
        print(f"{indent}🔍 Investigating (depth {depth}): {current_url[:80]}...")
        
        # Scrape the page
        result = scrape_url_content(current_url)
        
        if not result["success"]:
            print(f"{indent}   ✗ Failed: {result.get('error')}")
            continue
        
        page_content = result['content']
        page_title = result.get('metadata', {}).get('title', 'Untitled')
        
        # Add to memory
        memory.add_finding(current_url, page_content, result.get("metadata", {}), depth)
        
        # Create structured finding
        finding = PageFinding(
            url=current_url,
            title=page_title,
            content_preview=page_content[:500],
            relevance_score=0.8,  # Could be calculated
            depth=depth,
            key_points=_extract_key_points(page_content, query)
        )
        findings.append(finding)
        
        print(f"{indent}   ✓ Extracted {len(page_content):,} chars")
        print(f"{indent}   📝 Title: {page_title[:60]}...")
        
        # Agent decides next steps
        if depth < max_depth and memory.get_page_count() < max_pages:
            print(f"{indent}   🧠 Agent analyzing links...")
            
            # Extract links
            import requests
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                response = requests.get(current_url, headers=headers, timeout=10)
                
                links_with_context = extract_links_with_context(response.text, current_url, query)
                relevant_links = filter_relevant_links(links_with_context, query, min_relevance=0.15, max_links=5)
                
                # Remove visited
                relevant_links = [l for l in relevant_links if not memory.has_visited(l['url'])]
                
                if relevant_links:
                    # Let agent decide which to follow
                    import json
                    links_json = json.dumps([
                        {
                            'url': l['url'],
                            'text': l['text'],
                            'relevance_score': l['relevance_score']
                        }
                        for l in relevant_links
                    ])
                    
                    # Simple programmatic decision (agent integration can be added later)
                    top_links = relevant_links[:3]
                    
                    print(f"{indent}   🎯 Following {len(top_links)} relevant links:")
                    for link in top_links:
                        print(f"{indent}      → [{link['text'][:40]}] (score: {link['relevance_score']:.2f})")
                        to_visit.append((link['url'], depth + 1, current_url))
                        
            except Exception as e:
                print(f"{indent}   ⚠ Error extracting links: {e}")
        
        print()
    
    # Build structured result
    result = InvestigationResult(
        query=query,
        pages_visited=memory.get_page_count(),
        total_content_length=memory.total_content_length,
        findings=findings,
        key_insights=_extract_insights(findings, query),
        evidence_summary=_create_summary(findings),
        confidence=0.85
    )
    
    print(f"✅ Investigation complete!")
    print(f"   Pages: {result.pages_visited}")
    print(f"   Content: {result.total_content_length:,} chars")
    print(f"   Insights: {len(result.key_insights)}\n")
    
    return result


def _extract_key_points(content: str, query: str, max_points: int = 3) -> List[str]:
    """Extract key points from content relevant to query."""
    # Simple implementation: find sentences containing query words
    query_words = set(query.lower().split())
    sentences = content.split('.')[:20]  # First 20 sentences
    
    key_points = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 20:
            sentence_words = set(sentence.lower().split())
            if query_words & sentence_words:
                key_points.append(sentence[:200])
                if len(key_points) >= max_points:
                    break
    
    return key_points


def _extract_insights(findings: List[PageFinding], query: str) -> List[str]:
    """Extract key insights from all findings."""
    insights = []
    
    # Aggregate key points
    all_points = []
    for finding in findings:
        all_points.extend(finding.key_points)
    
    # Return top unique insights
    seen = set()
    for point in all_points:
        if point not in seen and len(insights) < 5:
            insights.append(point)
            seen.add(point)
    
    return insights


def _create_summary(findings: List[PageFinding]) -> str:
    """Create a summary of all findings."""
    summary = f"Investigated {len(findings)} pages:\n\n"
    
    for i, finding in enumerate(findings, 1):
        summary += f"{i}. {finding.title}\n"
        summary += f"   URL: {finding.url}\n"
        if finding.key_points:
            summary += f"   Key: {finding.key_points[0][:100]}...\n"
        summary += "\n"
    
    return summary


if __name__ == "__main__":
    # Test
    test_url = "https://www.aljazeera.com/news/2025/11/21/explosion-at-glue-factory-in-eastern-pakistan-kills-at-least-16"
    test_query = "how many pakistany died in the glue factory"
    
    print("="*70)
    print("STRUCTURED AGENTIC INVESTIGATION TEST")
    print("="*70)
    
    result = agentic_investigate(test_url, test_query, max_depth=2, max_pages=5)
    
    print("\n" + "="*70)
    print("STRUCTURED RESULTS")
    print("="*70)
    print(f"\nQuery: {result.query}")
    print(f"Pages Visited: {result.pages_visited}")
    print(f"Confidence: {result.confidence}")
    print(f"\nKey Insights:")
    for i, insight in enumerate(result.key_insights, 1):
        print(f"{i}. {insight}")
    
    print(f"\n{result.evidence_summary}")


# page depth and max pages should be agentic in future