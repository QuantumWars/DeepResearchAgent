"""Research planner for generating structured research plans using LLM."""

from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from research_agent.utils.models import ResearchPlan, ResearchTask
from research_agent.utils.logger import get_logger

logger = get_logger(__name__)


class ResearchPlanner:
    """Generates structured research plans using LLM with structured output."""
    
    def __init__(self, llm: BaseChatModel):
        """
        Initialize the research planner.
        
        Args:
            llm: Language model for generating research plans
        """
        self.llm = llm.with_structured_output(ResearchPlan)
        logger.info("ResearchPlanner initialized")
    
    async def create_plan(
        self,
        query: str,
        context: Optional[str] = None
    ) -> ResearchPlan:
        """
        Generate a structured research plan for the given query.
        
        Creates a plan with 1-5 research topics, each containing 3-5 specific tasks.
        Total tasks are limited to 15 to prevent excessive API calls.
        
        Args:
            query: The research query to plan for
            context: Optional additional context from previous research
            
        Returns:
            ResearchPlan with validated topics and tasks
            
        Raises:
            ValueError: If the generated plan exceeds task limits
        """
        logger.info(f"Creating research plan for query: {query[:100]}...")
        
        prompt = self._build_planning_prompt(query, context)
        
        try:
            # Generate plan using LLM with structured output
            plan = await self.llm.ainvoke(prompt)
            
            # Validate and potentially trim the plan
            validated_plan = self._validate_and_limit_plan(plan)
            
            logger.info(
                f"Research plan created: {len(validated_plan.topics)} topics, "
                f"{validated_plan.total_tasks} total tasks"
            )
            
            return validated_plan
            
        except Exception as e:
            logger.error(f"Failed to create research plan: {e}", exc_info=True)
            raise
    
    def _build_planning_prompt(
        self,
        query: str,
        context: Optional[str] = None
    ) -> list:
        """
        Build the planning prompt for the LLM.
        
        Args:
            query: The research query
            context: Optional additional context
            
        Returns:
            List of messages for the LLM
        """
        system_message = """You are an expert research planner. Your task is to break down research queries into structured, actionable research plans.

Create a research plan with the following structure:
- 1-5 research topics (broad areas to investigate)
- Each topic should have 3-5 specific tasks (concrete research actions)
- Total tasks across all topics must not exceed 15
- Each topic title should be 10-70 characters
- Tasks should be specific, actionable, and focused

Guidelines:
- Prioritize breadth over depth - cover multiple angles of the query
- Make tasks concrete and searchable (e.g., "Search for recent studies on X" not "Learn about X")
- Focus on information gathering tasks that can be executed via web search
- Avoid tasks that require subjective analysis or opinion
- Order tasks logically within each topic
- Keep the plan focused and achievable within 15 total tasks

Example structure:
Topic 1: "Core Concepts" (3-5 tasks)
Topic 2: "Current Research" (3-5 tasks)
Topic 3: "Applications" (3-5 tasks)
etc."""

        user_message = f"Research Query: {query}"
        
        if context:
            user_message += f"\n\nAdditional Context:\n{context}"
        
        user_message += "\n\nGenerate a structured research plan for this query."
        
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    
    def _validate_and_limit_plan(self, plan: ResearchPlan) -> ResearchPlan:
        """
        Validate and potentially trim the plan to meet constraints.
        
        Ensures:
        - 1-5 topics
        - 3-5 tasks per topic
        - Maximum 15 total tasks
        
        Args:
            plan: The generated research plan
            
        Returns:
            Validated and potentially trimmed research plan
            
        Raises:
            ValueError: If plan cannot be made valid
        """
        # Check topic count
        if len(plan.topics) < 1:
            raise ValueError("Plan must have at least 1 topic")
        
        if len(plan.topics) > 5:
            logger.warning(f"Plan has {len(plan.topics)} topics, trimming to 5")
            plan.topics = plan.topics[:5]
        
        # Check tasks per topic
        for i, topic in enumerate(plan.topics):
            if len(topic.tasks) < 3:
                logger.warning(
                    f"Topic '{topic.title}' has only {len(topic.tasks)} tasks, "
                    f"minimum is 3"
                )
            if len(topic.tasks) > 5:
                logger.warning(
                    f"Topic '{topic.title}' has {len(topic.tasks)} tasks, "
                    f"trimming to 5"
                )
                plan.topics[i].tasks = topic.tasks[:5]
        
        # Check total task limit
        total_tasks = plan.total_tasks
        if total_tasks > 15:
            logger.warning(
                f"Plan has {total_tasks} total tasks, trimming to 15"
            )
            plan = self._trim_plan_to_limit(plan, 15)
        
        logger.debug(
            f"Validated plan: {len(plan.topics)} topics, "
            f"{plan.total_tasks} tasks"
        )
        
        return plan
    
    def _trim_plan_to_limit(
        self,
        plan: ResearchPlan,
        max_tasks: int
    ) -> ResearchPlan:
        """
        Trim the plan to meet the maximum task limit.
        
        Strategy:
        1. Keep all topics but reduce tasks per topic proportionally
        2. Ensure each topic has at least 3 tasks
        3. Remove topics if necessary to meet the limit
        
        Args:
            plan: The research plan to trim
            max_tasks: Maximum number of tasks allowed
            
        Returns:
            Trimmed research plan
        """
        current_total = plan.total_tasks
        
        if current_total <= max_tasks:
            return plan
        
        # Calculate how many tasks to remove
        tasks_to_remove = current_total - max_tasks
        
        # Try to remove tasks proportionally from each topic
        trimmed_topics = []
        for topic in plan.topics:
            # Calculate proportion of tasks to keep
            tasks_to_keep = max(3, len(topic.tasks) - (tasks_to_remove // len(plan.topics)))
            
            trimmed_topic = ResearchTask(
                title=topic.title,
                tasks=topic.tasks[:tasks_to_keep]
            )
            trimmed_topics.append(trimmed_topic)
        
        # Use model_construct to bypass validation during intermediate trimming
        trimmed_plan = ResearchPlan.model_construct(topics=trimmed_topics)
        
        # If still over limit, remove entire topics from the end
        while trimmed_plan.total_tasks > max_tasks and len(trimmed_plan.topics) > 1:
            logger.warning(
                f"Removing topic '{trimmed_plan.topics[-1].title}' to meet task limit"
            )
            trimmed_plan = ResearchPlan.model_construct(topics=trimmed_plan.topics[:-1])
        
        # Final check - if still over, aggressively trim tasks
        if trimmed_plan.total_tasks > max_tasks:
            remaining_budget = max_tasks
            final_topics = []
            
            for topic in trimmed_plan.topics:
                tasks_for_topic = min(len(topic.tasks), remaining_budget)
                if tasks_for_topic >= 3:  # Only include if we can have at least 3 tasks
                    final_topics.append(
                        ResearchTask(
                            title=topic.title,
                            tasks=topic.tasks[:tasks_for_topic]
                        )
                    )
                    remaining_budget -= tasks_for_topic
                
                if remaining_budget <= 0:
                    break
            
            trimmed_plan = ResearchPlan.model_construct(topics=final_topics)
        
        logger.info(
            f"Trimmed plan from {current_total} to {trimmed_plan.total_tasks} tasks"
        )
        
        # Final validation - reconstruct with validation to ensure it's valid
        try:
            validated_plan = ResearchPlan(topics=trimmed_plan.topics)
            return validated_plan
        except Exception as e:
            logger.error(f"Failed to validate trimmed plan: {e}")
            # If validation still fails, return a minimal valid plan
            logger.warning("Creating minimal valid plan with first topic only")
            return ResearchPlan(topics=[trimmed_plan.topics[0]])
