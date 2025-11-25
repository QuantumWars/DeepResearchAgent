

"""Memory management for the fact-checking system.

This module provides memory structures for agents to retain context
across recursive investigations and multi-step reasoning.
"""

from typing import Dict, Any, List, Set


class InvestigationMemory:
    """Stores the accumulated findings from a recursive investigation."""
    
    def __init__(self, query: str):
        self.query = query
        self.visited_urls: Set[str] = set()
        self.findings: List[Dict[str, Any]] = []
        self.total_content_length = 0
        
    def add_finding(self, url: str, content: str, metadata: Dict[str, Any], depth: int):
        """Add a finding to the investigation memory."""
        self.visited_urls.add(url)
        self.findings.append({
            "url": url,
            "content": content[:1000],  # Store first 1000 chars
            "full_length": len(content),
            "metadata": metadata,
            "depth": depth
        })
        self.total_content_length += len(content)
    
    def has_visited(self, url: str) -> bool:
        """Check if a URL has already been visited."""
        return url in self.visited_urls
    
    def get_summary(self) -> str:
        """Generate a summary of the investigation."""
        summary = f"Investigation Query: {self.query}\n"
        summary += f"Pages Visited: {len(self.visited_urls)}\n"
        summary += f"Total Content: {self.total_content_length} characters\n\n"
        summary += "Findings:\n"
        
        for i, finding in enumerate(self.findings, 1):
            summary += f"\n{i}. [{finding['metadata'].get('title', 'Untitled')}]({finding['url']})\n"
            summary += f"   Depth: {finding['depth']} | Length: {finding['full_length']} chars\n"
            summary += f"   Preview: {finding['content'][:200]}...\n"
        
        return summary
    
    def get_all_content(self) -> str:
        """Get all accumulated content as a single string."""
        return "\n\n---\n\n".join([
            f"Source: {f['url']}\n{f['content']}" 
            for f in self.findings
        ])
    
    def get_page_count(self) -> int:
        """Get the number of pages visited."""
        return len(self.visited_urls)


class AgentMemory:
    """Memory for individual agents to track their reasoning and findings."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.reasoning_steps: List[str] = []
        self.evidence_collected: List[Dict[str, Any]] = []
        self.intermediate_conclusions: List[str] = []
        
    def add_reasoning_step(self, step: str):
        """Add a reasoning step to memory."""
        self.reasoning_steps.append(step)
    
    def add_evidence(self, evidence: Dict[str, Any]):
        """Add evidence to memory."""
        self.evidence_collected.append(evidence)
    
    def add_conclusion(self, conclusion: str):
        """Add an intermediate conclusion."""
        self.intermediate_conclusions.append(conclusion)
    
    def get_context(self) -> str:
        """Get the full context as a string."""
        context = f"Agent: {self.agent_name}\n\n"
        
        if self.reasoning_steps:
            context += "Reasoning Steps:\n"
            for i, step in enumerate(self.reasoning_steps, 1):
                context += f"{i}. {step}\n"
            context += "\n"
        
        if self.evidence_collected:
            context += f"Evidence Collected: {len(self.evidence_collected)} items\n\n"
        
        if self.intermediate_conclusions:
            context += "Intermediate Conclusions:\n"
            for conclusion in self.intermediate_conclusions:
                context += f"- {conclusion}\n"
        
        return context
