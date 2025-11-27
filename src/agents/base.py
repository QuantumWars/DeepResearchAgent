from agno.agent import Agent
from agno.models.openai import OpenAIChat

def get_base_agent(name: str, instructions: str) -> Agent:
    return Agent(
        name=name,
        model=OpenAIChat(id="gpt-4o"),
        instructions=instructions,
        markdown=True
    )
