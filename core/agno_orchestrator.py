"""
Agno Orchestrator for the Deep Research Framework.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from core.agents import ResearchAgents
# Import ResearchResult from the original orchestrator to maintain compatibility
# If we were fully replacing, we'd move this to a shared model file
from core.orchestrator import ResearchResult

logger = logging.getLogger(__name__)

class AgnoResearchOrchestrator:
    """
    Orchestrator using Agno Agents for research.
    """
    
    def __init__(self, model_provider: str = "openai", model_name: str = "gpt-4o"):
        self.agents = ResearchAgents(model_provider, model_name)
        self.planner = self.agents.make_planner_agent()
        self.researcher = self.agents.make_researcher_agent()
        self.reviewer = self.agents.make_reviewer_agent()
        self.writer = self.agents.make_writer_agent()
        
        logger.info(f"AgnoResearchOrchestrator initialized with {model_provider}/{model_name}")

    def research(self, query: str, max_loops: int = 3) -> ResearchResult:
        """
        Execute research using Agno agents.
        """
        logger.info(f"Starting research for: {query}")
        
        execution_log = []
        all_sources = []
        
        # Step 1: Planning
        logger.info("Step 1: Planning")
        plan_response = self.planner.run(f"Research Query: {query}")
        plan_content = plan_response.content
        sub_questions = [line.strip() for line in plan_content.split('\n') if line.strip()]
        
        execution_log.append({
            "node": "planner",
            "tool_name": "llm",
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "metadata": {"sub_questions": sub_questions}
        })
        
        logger.info(f"Generated {len(sub_questions)} sub-questions")
        
        # Research Loop
        gathered_info = []
        loop_count = 0
        
        while loop_count < max_loops:
            loop_count += 1
            logger.info(f"Research Loop {loop_count}/{max_loops}")
            
            # Step 2: Researching
            for question in sub_questions:
                logger.info(f"Researching: {question}")
                research_response = self.researcher.run(f"Find information for: {question}")
                gathered_info.append(f"Question: {question}\nFindings: {research_response.content}")
                
                # Log tool usage (simplified)
                execution_log.append({
                    "node": "researcher",
                    "tool_name": "search/scrape",
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {"question": question}
                })
                
                # In a real implementation, we'd extract sources from the agent's tool calls
                # For now, we'll just simulate it or parse if possible
                # Agno agents store tool calls in their memory/history
            
            # Step 3: Reviewing
            logger.info("Step 3: Reviewing")
            current_info = "\n\n".join(gathered_info)
            review_prompt = f"""
            Original Query: {query}
            Current Findings:
            {current_info}
            
            Are there any gaps?
            """
            review_response = self.reviewer.run(review_prompt)
            review_content = review_response.content
            
            execution_log.append({
                "node": "reviewer",
                "tool_name": "llm",
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "metadata": {"review": review_content}
            })
            
            if "COMPLETE" in review_content.upper():
                logger.info("Research complete according to reviewer")
                break
            else:
                logger.info("Gaps identified, continuing...")
                # Update sub-questions based on review (simplified)
                # In a full implementation, we'd parse the review to get new questions
                # For this demo, we might just stop or continue with original questions if we had more logic
                if loop_count >= max_loops:
                    logger.info("Max loops reached")
                    break
        
        # Step 4: Writing
        logger.info("Step 4: Writing Report")
        write_prompt = f"""
        Original Query: {query}
        All Findings:
        {current_info}
        
        Generate a final report.
        """
        report_response = self.writer.run(write_prompt)
        final_report = report_response.content
        
        execution_log.append({
            "node": "writer",
            "tool_name": "llm",
            "success": True,
            "timestamp": datetime.now().isoformat()
        })
        
        return ResearchResult(
            report=final_report,
            sources=all_sources, # We'd populate this from tool outputs
            execution_log=execution_log
        )
