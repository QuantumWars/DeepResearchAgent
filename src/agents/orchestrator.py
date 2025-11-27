import asyncio
import time
from typing import Dict, Any, List
from src.agents.specialized import DecomposerAgent, PlannerAgent, EvaluatorAgent, ForensicAgent
from src.tools.search_tools_real import SearchToolsReal
from src.core.confidence import ConfidenceScorer
from src.core.timeline import TimelineConstructor
from src.core.contradiction import ContradictionResolver
from src.core.cost import CostOptimizer
from src.models.schemas import Claim, InvestigationResult, Evidence, Verdict, Evaluation, SubClaim


class OrchestratorAgent:
    def __init__(self):
        self.decomposer = DecomposerAgent()
        self.planner = PlannerAgent()
        self.evaluator = EvaluatorAgent()
        self.forensic = ForensicAgent()
        
        self.search_tools = SearchToolsReal()
        self.confidence_scorer = ConfidenceScorer()
        self.timeline_builder = TimelineConstructor()
        self.contradiction_resolver = ContradictionResolver()
        self.cost_optimizer = CostOptimizer()

    async def verify_claim(
        self, 
        claim_text: str, 
        priority: str = "HIGH", 
        current_depth: int = 0,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Recursively verify a claim with adaptive depth.
        
        Args:
            claim_text: The claim to verify
            priority: Investigation priority (HIGH/MEDIUM/LOW)
            current_depth: Current recursion depth (0 = initial call)
            max_depth: Maximum recursion depth allowed
        """
        depth_prefix = "  " * current_depth
        print(f"{depth_prefix}Starting verification (depth {current_depth}): {claim_text[:60]}...")
        start_time = time.time()
        
        # Initialize investigation state
        claim = Claim(original_text=claim_text)
        evidence_collection: Dict[str, List[Evidence]] = {}
        
        # STAGE 1: Decompose claim
        print("\n[Stage 1/7] Decomposing claim...")
        sub_claims = await self.decomposer.decompose(claim_text)
        
        # STAGE 2-3: Plan and execute searches
        print("\n[Stage 2-3/7] Planning and executing searches...")
        for sub_claim in sub_claims:
            search_plan = await self.planner.create_plan(sub_claim, priority)
            optimized_plan = self.cost_optimizer.optimize_search_plan(search_plan.queries, priority)
            
            # Execute searches with real APIs
            evidence_list = []
            for query in optimized_plan:
                try:
                    # Call the appropriate search tool based on query.tool
                    if query.tool == "tavily":
                        result = self.search_tools.tavily_search(query.query, max_results=3)
                    elif query.tool == "exa":
                        result = self.search_tools.exa_search(query.query, num_results=3)
                    elif query.tool == "official_api":
                        result = self.search_tools.official_api_search(
                            source=query.api_source or "unknown",
                            endpoint=query.endpoint or "search",
                            params=query.params
                        )
                    else:
                        result = "[]"
                    
                    # Parse the JSON result and convert to Evidence objects
                    import json
                    if result.startswith("[MOCK]") or result.startswith("[ERROR]"):
                        # Fallback to mock data if API failed
                        evidence_list.append(Evidence(
                            source=f"Mock Source ({query.tool})",
                            source_tier=3,
                            excerpt=result[:200],
                            relevance="Medium",
                            verdict="UNCERTAIN",
                            confidence=0.5
                        ))
                    else:
                        search_results = json.loads(result)
                        for item in search_results[:2]:  # Limit to 2 results per query
                            # Determine source tier based on domain
                            tier = self._determine_source_tier(item.get('url', ''))
                            
                            evidence_list.append(Evidence(
                                source=item.get('title', 'Unknown Source'),
                                source_tier=tier,
                                url=item.get('url'),
                                published=item.get('published_date'),
                                excerpt=item.get('content', item.get('text', ''))[:500],
                                relevance="High",
                                verdict="UNCERTAIN",  # Will be determined by evaluator
                                confidence=item.get('score', 0.8)
                            ))
                except Exception as e:
                    print(f"  Warning: Search failed for {query.query}: {e}")
                    evidence_list.append(Evidence(
                        source=f"Error Source",
                        source_tier=5,
                        excerpt=f"Search failed: {str(e)}",
                        relevance="Low",
                        verdict="UNCERTAIN",
                        confidence=0.1
                    ))
            evidence_collection[sub_claim.id] = evidence_list

        # STAGE 4: Evaluate evidence
        depth_prefix = "  " * current_depth
        print(f"\n{depth_prefix}[Stage 4/7] Evaluating evidence...")
        evaluation = await self.evaluator.assess(evidence_collection)
        
        # Calculate preliminary confidence
        all_evidence = [e for ev_list in evidence_collection.values() for e in ev_list]
        preliminary_confidence = self.confidence_scorer.calculate_confidence(all_evidence, claim)
        
        # RECURSION DECISION POINT
        should_recurse = self._should_recurse(
            evaluation, 
            preliminary_confidence, 
            current_depth, 
            max_depth
        )
        
        if should_recurse:
            print(f"\n{depth_prefix}[🔄 RECURSION TRIGGERED]")
            print(f"{depth_prefix}  Confidence: {preliminary_confidence:.2%} (threshold: 0.70)")
            print(f"{depth_prefix}  Depth: {current_depth}/{max_depth}")
            print(f"{depth_prefix}  Reason: ", end="")
            
            if preliminary_confidence < 0.70:
                print("Low confidence - need more evidence")
            elif evaluation.has_contradictions:
                print("Contradictions detected - need resolution")
            elif evaluation.critical_gaps:
                print("Critical knowledge gaps found")
            else:
                print("Other investigation needs")
            
            # Identify what needs deeper investigation
            deeper_claims = self._identify_knowledge_gaps(
                evaluation, 
                sub_claims, 
                all_evidence
            )
            
            print(f"{depth_prefix}  Investigating {len(deeper_claims)} additional claims...")
            
            # Recursive investigations
            recursive_evidence = []
            for idx, deeper_claim in enumerate(deeper_claims[:2], 1):  # Limit to 2 per level
                print(f"\n{depth_prefix}  [{idx}/{len(deeper_claims[:2])}] Deeper investigation:")
                sub_result = await self.verify_claim(
                    deeper_claim,
                    priority=priority,
                    current_depth=current_depth + 1,
                    max_depth=max_depth
                )
                
                # Extract evidence from recursive result
                if 'key_evidence' in sub_result:
                    recursive_evidence.extend(sub_result['key_evidence'][:3])
            
            # Merge recursive evidence
            if recursive_evidence:
                print(f"\n{depth_prefix}  ✓ Added {len(recursive_evidence)} sources from deeper investigation")
                for rec_ev in recursive_evidence:
                    # Convert dict back to Evidence object
                    evidence_obj = Evidence(**rec_ev)
                    all_evidence.append(evidence_obj)
                
                # Re-evaluate with new evidence
                preliminary_confidence = self.confidence_scorer.calculate_confidence(all_evidence, claim)
                print(f"{depth_prefix}  Updated confidence: {preliminary_confidence:.2%}")
        

        # STAGE 5: Forensic analysis
        print("\n[Stage 5/7] Skipping forensics (no multimedia)")
        
        # STAGE 6: Synthesize
        print("\n[Stage 6/7] Synthesizing evidence...")
        all_evidence = [e for ev_list in evidence_collection.values() for e in ev_list]
        timeline = await self.timeline_builder.build(all_evidence)
        
        if evaluation.has_contradictions:
            resolutions = await self.contradiction_resolver.resolve(evaluation.contradictions)
            
        final_confidence = self.confidence_scorer.calculate_confidence(all_evidence, claim)
        
        verdict = Verdict(
            status="PARTIALLY_TRUE", # Logic to determine this would be more complex
            confidence=final_confidence,
            summary="The claim is partially true based on the evidence."
        )
        
        # STAGE 7: Format report
        print("\n[Stage 7/7] Formatting report...")
        
        result = InvestigationResult(
            claim=claim,
            verdict=verdict,
            sub_claims=sub_claims,
            timeline=timeline,
            key_evidence=all_evidence[:5],
            investigation_metadata={
                "time_elapsed": time.time() - start_time
            }
        )
        
        return result.model_dump()
    
    def _determine_source_tier(self, url: str) -> int:
        """Determine source tier based on domain quality"""
        if not url:
            return 4
        
        url_lower = url.lower()
        
        # Tier 1: Official/Government/Academic
        tier_1_domains = ['.gov', '.edu', 'census.gov', 'federalregister.gov', 
                          'whitehouse.gov', 'congress.gov']
        if any(domain in url_lower for domain in tier_1_domains):
            return 1
        
        # Tier 2: Established fact-checkers and research
        tier_2_domains = ['factcheck.org', 'politifact', 'snopes', 'fullfact',
                          'reuters.com/fact-check', 'apnews.com']
        if any(domain in url_lower for domain in tier_2_domains):
            return 2
        
        # Tier 3: Major news organizations
        tier_3_domains = ['nytimes.com', 'washingtonpost.com', 'bbc.com', 'reuters.com',
                          'apnews.com', 'wsj.com', 'theguardian.com', 'npr.org']
        if any(domain in url_lower for domain in tier_3_domains):
            return 3
        
        # Tier 4: Other sources
        return 4
    
    def _should_recurse(
        self,
        evaluation: Evaluation,
        confidence: float,
        current_depth: int,
        max_depth: int
    ) -> bool:
        """Determine if recursion is needed"""
        # Base cases - don't recurse
        if current_depth >= max_depth:
            return False
        if confidence >= 0.85:  # High confidence
            return False
        
        # Recursion triggers
        if confidence < 0.70:  # Low confidence
            return True
        if evaluation.has_contradictions:
            return True
        if evaluation.critical_gaps:
            return True
        if evaluation.primary_source_count == 0 and current_depth == 0:
            return True
        
        return False
    
    def _identify_knowledge_gaps(
        self,
        evaluation: Evaluation,
        sub_claims: List,
        evidence: List
    ) -> List[str]:
        """Generate new claims to investigate based on gaps"""
        new_claims = []
        
        # If low confidence, try to find more specific angles
        if len(evidence) < 3:
            new_claims.append(f"What additional context is needed for: {sub_claims[0].text if sub_claims else 'the claim'}?")
        
        # If contradictions exist, try to resolve them
        if evaluation.has_contradictions:
            new_claims.append(f"What is the authoritative source for: {sub_claims[0].text if sub_claims else 'this information'}?")
        
        # If no primary sources, look for them specifically
        if evaluation.primary_source_count == 0:
            new_claims.append(f"What are the official or primary sources for: {sub_claims[0].text if sub_claims else 'this claim'}?")
        
        return new_claims[:2]  # Limit to avoid explosion
