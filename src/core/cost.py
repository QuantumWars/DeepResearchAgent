from typing import List
from src.models.schemas import SearchQuery

class CostOptimizer:
    """
    Minimize API costs while maximizing information quality
    """
    def __init__(self):
        self.tool_costs = {
            'exa': 0.01,       # per search
            'tavily': 0.005,   # per search
            'perplexity': 0.02,# per query
            'official_api': 0.0 # usually free
        }
        self.budget_per_claim = 0.50  # $0.50 max per claim

    def optimize_search_plan(self, search_plan: List[SearchQuery], priority: str) -> List[SearchQuery]:
        """
        Optimize search execution for cost-effectiveness
        """
        # Always start with free official APIs
        prioritized_plan = []

        # Tier 1: Free official sources
        official_searches = [
            s for s in search_plan
            if s.tool == 'official_api'
        ]
        prioritized_plan.extend(official_searches)

        # Tier 2: Cost-effective broad searches
        if priority in ["MEDIUM", "HIGH"]:
            tavily_searches = [
                s for s in search_plan
                if s.tool == 'tavily'
            ]
            prioritized_plan.extend(tavily_searches[:2])  # Limit to 2

        # Tier 3: Precision searches for high-priority claims
        if priority == "HIGH":
            exa_searches = [
                s for s in search_plan
                if s.tool == 'exa'
            ]
            prioritized_plan.extend(exa_searches[:3])  # Limit to 3

        # Calculate projected cost
        projected_cost = sum(
            self.tool_costs.get(s.tool, 0)
            for s in prioritized_plan
        )

        # If over budget, trim low-priority searches (simplified logic)
        if projected_cost > self.budget_per_claim:
             # Simple trimming for now
             while projected_cost > self.budget_per_claim and prioritized_plan:
                 removed = prioritized_plan.pop()
                 projected_cost -= self.tool_costs.get(removed.tool, 0)

        return prioritized_plan
