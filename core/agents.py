"""
Agno Agents for the Deep Research Framework.
"""

import logging
from typing import List, Optional

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude
from agno.models.google import Gemini

from tools.agno_tools import ResearchTools

logger = logging.getLogger(__name__)

class ResearchAgents:
    def __init__(self, model_provider: str = "openai", model_name: str = "gpt-4o"):
        self.model_provider = model_provider
        self.model_name = model_name
        self.tools = ResearchTools()
        
    def get_model(self):
        if self.model_provider == "openai":
            return OpenAIChat(id=self.model_name)
        elif self.model_provider == "anthropic":
            return Claude(id=self.model_name)
        elif self.model_provider == "google":
            return Gemini(id=self.model_name)
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")

    def make_planner_agent(self) -> Agent:
        return Agent(
            name="Planner",
            role="Research Planner",
            model=self.get_model(),
            instructions=[
                "You are a research planning assistant.",
                "Your goal is to break down a research query into specific sub-questions.",
                "Generate 3-5 focused sub-questions that cover different aspects of the main query.",
                "Ensure questions are specific and answerable through web search.",
                "Return ONLY the sub-questions, one per line."
            ],
            # show_tool_calls=True,
            markdown=True
        )

    def make_researcher_agent(self) -> Agent:
        return Agent(
            name="Researcher",
            role="Web Researcher",
            model=self.get_model(),
            tools=[self.tools],
            instructions=[
                "You are a web researcher.",
                "Your goal is to find information to answer specific research questions.",
                "Use the 'search_google' tool to find relevant URLs.",
                "Use the 'scrape_website' tool to extract content from promising URLs.",
                "Focus on high-quality, authoritative sources.",
                "Summarize the findings for each question."
            ],
            # show_tool_calls=True,
            markdown=True
        )

    def make_reviewer_agent(self) -> Agent:
        return Agent(
            name="Reviewer",
            role="Research Reviewer",
            model=self.get_model(),
            instructions=[
                "You are a research quality evaluator.",
                "Analyze the gathered information against the original query.",
                "Identify any missing information or gaps.",
                "If gaps exist, specify what additional information is needed.",
                "If the information is sufficient, respond with 'COMPLETE'."
            ],
            # show_tool_calls=True,
            markdown=True
        )

    def make_writer_agent(self) -> Agent:
        return Agent(
            name="Writer",
            role="Report Writer",
            model=self.get_model(),
            instructions=[
                "You are a research synthesis expert.",
                "Create a comprehensive, well-structured research report based on the provided information.",
                "Use inline citations [1], [2], etc. to reference specific sources if available.",
                "Organize the report with clear sections.",
                "Include a 'References' section at the end.",
                "Write in a clear, professional style."
            ],
            # show_tool_calls=True,
            markdown=True
        )
