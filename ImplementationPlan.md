Based on the architectural documents provided, here is the comprehensive technical strategy for building the **"Fact-Check Ops"** system using **Agno AI (formerly Phidata)** for orchestration and **LangChain** for infrastructure.

---

### Part 1: Agno AI + LangChain Integration Architecture

The core philosophy is "Agno for Brains, LangChain for Hands."

Agno excels at defining agent behaviors, roles, and lightweight coordination. LangChain excels at the heavy lifting of data ingestion, vector storage, and standardized tool interfaces.

#### 1. The Technical Bridge

You do not need to choose between them. You will inject LangChain tools into Agno agents.

- **Agno AI Handles:** Agent identity (Instructions), Orchestration (Teams/Runners), State Management, Multimodal (Vision) processing, and Human-in-the-loop UI.
    
- **LangChain Handles:** Vector Database connections (Qdrant/Pinecone), Document Loading (PDF/HTML), Text Splitting, and standardized API wrappers (Search/Wikipedia).
    

#### 2. Code Integration Pattern

Here is the specific Python pattern to bridge the two frameworks:

Python

```
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.vectorstores import Qdrant
from langchain_core.tools import Tool

# --- STEP 1: LangChain Infrastructure (The "Hands") ---
# Define the heavy-lifting tools using LangChain
lc_search = DuckDuckGoSearchRun()
lc_vector_tool = Tool(
    name="KnowledgeBase",
    func=lambda q: "Results from Qdrant...", # Connects to LangChain retriever
    description="Search the internal database of verified facts."
)

# --- STEP 2: Agno Wrapper (The "Bridge") ---
# Agno can accept native Python functions or LangChain tools
def search_wrapper(query: str) -> str:
    """Useful for searching the web for current events."""
    return lc_search.run(query)

# --- STEP 3: Agno Agent (The "Brain") ---
political_agent = Agent(
    name="Political Specialist",
    role="Verify political claims using primary sources",
    model=OpenAIChat(id="gpt-4-turbo"),
    # Injecting the LangChain capability here
    tools=[search_wrapper, lc_vector_tool], 
    instructions=[
        "Always cite sources.",
        "Check for cherry-picked timeframes."
    ],
    show_tool_calls=True,
    markdown=True
)

# Usage
political_agent.print_response("Verify if Senator X voted for the infrastructure bill.")
```

---

### Part 2: Phase-Wise Implementation Plan

This roadmap aligns with the **"Implementation Roadmap"** section of the _Compass Artifact_, adapted for the Agno/LangChain stack.

#### Phase 1: The "Cognitive MVP" (Weeks 1-4)

**Goal:** A text-based multi-agent system capable of verifying Political and Scientific claims using web search.

- **Agent Roster (Agno):**
    
    1. **Supervisor Agent:** Uses Agno `Team` or `Runner` to route queries.
        
    2. **Political Specialist:** Instructions focused on "Cherry-picking detection" and "Policy verification."
        
    3. **Scientific Specialist:** Instructions focused on "Hierarchy of evidence" (RCT > Observational).
        
- **Tools (LangChain):**
    
    - `GoogleSearchAPIWrapper` (for real-time data).
        
    - `PubMedRetriever` (specifically for the scientific agent).
        
- **Memory:**
    
    - Use Agno’s built-in `SqlAgentStorage` for conversational memory (Working Memory).
        
- **Outcome:** A CLI or Streamlit interface where users input a claim, and the system outputs a verdict with citations.
    

#### Phase 2: The "Memory & RAG" Layer (Weeks 5-8)

**Goal:** Implement the "Four-Tier Memory Architecture" described in _BrainStorming.md_ to prevent amnesia and enable learning.

- **Infrastructure Update:**
    
    - Deploy **Qdrant** (via Docker).
        
    - Create **LangChain Ingestion Pipelines** (`PyPDFLoader`, `RecursiveCharacterTextSplitter`) to load government reports and medical journals.
        
- **New Components:**
    
    - **Episodic Memory (LangChain + Qdrant):** Store every Phase 1 verification result. Before searching the web, agents must query this vector store to see if the claim was already checked.
        
    - **Semantic Memory:** A curated vector store of "Trusted Sources" and "Known Logical Fallacies."
        
- **Agent Update:**
    
    - **Source Verification Agent:** A new Agno agent that doesn't check facts, but checks _domains_ against a whitelist/blacklist (using the Tier 1-4 system from the docs).
        

#### Phase 3: Multimodal & Advanced Orchestration (Weeks 9-12)

**Goal:** Add Visual Agents and the "Iterative Consensus" logic.

- **Multimodal Integration (Agno Strength):**
    
    - **Visual Specialist Agent:** Uses `gpt-4o` or `gpt-4-vision-preview`.
        
    - _Task:_ Upload an image. The agent uses Agno's native vision capabilities to describe the image, then passes that description to the Search Agent to perform "Reverse Image Search" via tool.
        
- **Advanced Logic (The "Think Like a Fact-Checker" bit):**
    
    - Implement the **Iterative Consensus Ensemble (ICE)**.
        
    - _Workflow:_
        
        1. Supervisor asks Political Agent for a verdict.
            
        2. Supervisor asks Statistical Agent for a verdict.
            
        3. If they disagree, Agno starts a "Chat" between the two agents (Multi-Agent Debate) to resolve the conflict before outputting to the user.
            
- **Confidence Scoring:**
    
    - Implement the Python scoring logic (from `BrainStorming.md`) as a utility function that agents call before finalizing their response.
        

---

### Summary of Responsibilities

|**Feature**|**Component Handling It**|
|---|---|
|**Agent Personality/Prompts**|**Agno AI** (`instructions` parameter)|
|**Routing/Orchestration**|**Agno AI** (`Team` / `Agent` delegation)|
|**Web Search / API Calls**|**LangChain** (`Tools` wrapped for Agno)|
|**Document RAG (PDFs)**|**LangChain** (`RetrievalQA` chain)|
|**Long-term Fact DB**|**LangChain** + **Qdrant**|
|**Image/Video Analysis**|**Agno AI** (Native Multimodal support)|
|**User Interface**|**Agno UI** (Playground) or Streamlit|

This approach utilizes Agno's modern, lightweight orchestration to manage the "Cognitive" aspects (planning, debating, seeing) while leveraging LangChain's mature ecosystem for the "Functional" aspects (retrieving, scraping, indexing).