"""Supervisor orchestrator agent for routing claims to specialists."""

import os
from dotenv import load_dotenv
from agno.agent import Agent
from src.models import RoutingDecision

load_dotenv()


def create_supervisor_agent() -> Agent:
    """Create and configure the Supervisor Agent."""
    
    def route_claim(claim: str) -> str:
        """Route a claim to the appropriate specialist agent."""
        # This is a placeholder - in production, this would use NLP/classification
        claim_lower = claim.lower()
        
        # Simple keyword-based routing
        political_keywords = ["senator", "congress", "vote", "bill", "legislation", "government", "politician"]
        scientific_keywords = ["vaccine", "study", "research", "medical", "disease", "treatment", "scientific"]
        
        if any(keyword in claim_lower for keyword in political_keywords):
            decision = RoutingDecision(
                claim=claim,
                target_agent="PoliticalAgent",
                reasoning="Claim contains political keywords related to government, legislation, or voting records.",
                confidence=0.9
            )
        elif any(keyword in claim_lower for keyword in scientific_keywords):
            decision = RoutingDecision(
                claim=claim,
                target_agent="ScientificAgent",
                reasoning="Claim contains scientific/medical keywords related to research, health, or studies.",
                confidence=0.9
            )
        else:
            decision = RoutingDecision(
                claim=claim,
                target_agent="PoliticalAgent",  # Default fallback
                reasoning="Unable to clearly classify claim. Defaulting to Political Agent for general analysis.",
                confidence=0.5
            )
        
        return decision.model_dump_json(indent=2)
    
    agent = Agent(
        name="Supervisor",
        instructions="""You are the Supervisor Agent for a fact-checking system.

Your job is to route claims to the appropriate specialist agent.

When you receive a claim, you MUST:
1. Call the route_claim tool with the exact claim text
2. Return ONLY the tool's output - do not add any commentary

Example:
User: "Senator voted on bill"
You: <call route_claim tool>""",
        model="openai:gpt-4o-mini",
        tools=[route_claim],
        markdown=False,
    )
    
    return agent


def route_claim_direct(claim: str) -> RoutingDecision:
    """Direct routing function without agent wrapper."""
    claim_lower = claim.lower()
    
    # Simple keyword-based routing
    political_keywords = ["senator", "congress", "vote", "bill", "legislation", "government", "politician"]
    scientific_keywords = ["vaccine", "study", "research", "medical", "disease", "treatment", "scientific"]
    
    if any(keyword in claim_lower for keyword in political_keywords):
        return RoutingDecision(
            claim=claim,
            target_agent="PoliticalAgent",
            reasoning="Claim contains political keywords related to government, legislation, or voting records.",
            confidence=0.9
        )
    elif any(keyword in claim_lower for keyword in scientific_keywords):
        return RoutingDecision(
            claim=claim,
            target_agent="ScientificAgent",
            reasoning="Claim contains scientific/medical keywords related to research, health, or studies.",
            confidence=0.9
        )
    else:
        return RoutingDecision(
            claim=claim,
            target_agent="PoliticalAgent",  # Default fallback
            reasoning="Unable to clearly classify claim. Defaulting to Political Agent for general analysis.",
            confidence=0.5
        )


if __name__ == "__main__":
    # Test the agent
    agent = create_supervisor_agent()
    
    # Test political claim
    print("=== Testing Political Claim ===")
    response = agent.run("Senator Smith voted yes on the infrastructure bill")
    print(response.content)
    
    print("\n=== Testing Scientific Claim ===")
    response = agent.run("COVID-19 vaccines reduce hospitalization rates")
    print(response.content)
