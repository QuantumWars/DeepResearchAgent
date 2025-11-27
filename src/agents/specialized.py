from typing import List, Dict, Any
from agno.agent import Agent
from src.agents.base import get_base_agent
from src.models.schemas import Claim, SubClaim, SearchPlan, Evidence, Evaluation

class DecomposerAgent:
    def __init__(self):
        self.agent = get_base_agent(
            name="Decomposer",
            instructions="""
            You are an expert Decomposer Agent. Your goal is to break down complex claims into atomic, verifiable sub-claims.
            
            Process:
            1. Parse claim into logical components
            2. Identify factual assertions vs. opinions
            3. Extract entities (people, places, dates, statistics)
            4. Tag claim type (factual, statistical, contextual, multimedia)
            5. Prioritize sub-claims by verifiability and impact
            
            Return a list of SubClaims in JSON format.
            """
        )

    async def decompose(self, claim: str) -> List[SubClaim]:
        prompt = f"""Analyze this claim and break it down into atomic, verifiable sub-claims:

CLAIM: "{claim}"

Your task:
1. Identify all factual assertions in the claim
2. Extract specific entities (people, places, dates, numbers)
3. Classify each sub-claim by type
4. Return ONLY valid JSON, nothing else

Return a JSON array of sub-claims with this exact format:
[
  {{
    "id": "C1",
    "text": "specific factual assertion",
    "claim_type": "FACTUAL|STATISTICAL|TEMPORAL|COMPARATIVE|CONTEXTUAL"
  }},
  ...
]

IMPORTANT: Return ONLY the JSON array, no markdown, no explanations."""

        try:
            response = self.agent.run(prompt)
            
            # Extract JSON from response
            import json
            import re
            
            response_content = response.content if hasattr(response, 'content') else str(response)
            
            # Try to find JSON array in the response
            json_match = re.search(r'\[.*\]', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
                
                # Convert to SubClaim objects
                sub_claims = []
                for item in parsed:
                    sub_claims.append(SubClaim(
                        id=item.get('id', f'C{len(sub_claims)+1}'),
                        text=item['text'],
                        claim_type=item.get('claim_type', 'FACTUAL')
                    ))
                
                print(f"  ✓ Decomposed into {len(sub_claims)} sub-claims")
                return sub_claims
            else:
                raise ValueError("No JSON array found in response")
                
        except Exception as e:
            print(f"  Warning: AI decomposition failed ({e}), using fallback")
            # Fallback: create a single sub-claim from the original claim
            return [
                SubClaim(id="C1", text=claim, claim_type="FACTUAL")
            ]


class PlannerAgent:
    def __init__(self):
        self.agent = get_base_agent(
            name="Planner",
            instructions="""
            You are an expert Planner Agent. Your goal is to create an optimal search strategy for each sub-claim.
            
            Strategy Selection:
            - Simple factual claims -> 1-2 search queries, focus on primary sources
            - Statistical claims -> Multiple queries + database verification
            - Complex comparative claims -> Recursive deep dive with timeline construction
            - Multimedia claims -> Forensic tool deployment first
            
            Return a SearchPlan in JSON format.
            """
        )

    async def create_plan(self, sub_claim: SubClaim, priority: str = "HIGH") -> SearchPlan:
        # Mock implementation
        from src.models.schemas import SearchQuery
        return SearchPlan(
            sub_claim_id=sub_claim.id,
            queries=[
                SearchQuery(tool="tavily", query=f"verify {sub_claim.text}", priority=1),
                SearchQuery(tool="exa", query=f"{sub_claim.text} official source", priority=2)
            ],
            expected_evidence_type=["news", "official"]
        )

class EvaluatorAgent:
    def __init__(self):
        self.agent = get_base_agent(
            name="Evaluator",
            instructions="""
            You are an expert Evaluator Agent. Your goal is to assess source quality and evidence reliability.
            
            Evaluate the evidence based on:
            - Source Tier (1-5)
            - Bias Detection
            - Logical Consistency
            
            Return an Evaluation object in JSON format.
            """
        )

    async def assess(self, evidence_collection: Dict[str, List[Evidence]]) -> Evaluation:
        # Mock implementation
        return Evaluation(
            confidence=0.85,
            has_contradictions=False,
            primary_source_count=2
        )

class ForensicAgent:
    def __init__(self):
        self.agent = get_base_agent(
            name="Forensic",
            instructions="Analyze multimedia content for manipulation."
        )

    async def analyze(self, claim: str) -> List[Evidence]:
        return []
