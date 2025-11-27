# Recursive Multi-Agent Fact-Checking System

## Quick Start Guide

This is a streamlined guide to get you up and running quickly. For detailed technical documentation, see [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md).

## What This System Does

Automatically fact-checks claims using:

- **AI-powered decomposition** (GPT-4o breaks down complex claims)
- **Multi-source verification** (Searches Exa, Tavily, official APIs)
- **Smart recursion** (Digs deeper on low-confidence findings)
- **Source ranking** (.gov sources ranked highest)

## Quick Setup

### 1. Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# Install packages
pip install -r requirements.txt
pip install exa-py tavily-python python-dotenv
```

### 2. Configure API Keys

Edit `src/.env`:

```bash
OPENAI_API_KEY=sk-proj-your-key-here
EXA_API_KEY=your-exa-key-here
TAVILY_API_KEY=tvly-your-key-here
```

**Get API Keys:**

- OpenAI: https://platform.openai.com/api-keys
- Exa: https://exa.ai/
- Tavily: https://tavily.com/

### 3. Run Your First Fact-Check

```bash
./venv/bin/python main.py
```

## Usage Examples

### Basic Verification

```python
import asyncio
from src.agents.orchestrator import OrchestratorAgent

async def verify():
    orchestrator = OrchestratorAgent()
    result = await orchestrator.verify_claim(
        "The Eiffel Tower was completed in 1889."
    )
    print(f"Verdict: {result['verdict']['status']}")
    print(f"Confidence: {result['verdict']['confidence']:.2%}")

asyncio.run(verify())
```

### With Recursion Control

```python
result = await orchestrator.verify_claim(
    claim_text="Your claim here",
    priority="HIGH",      # LOW, MEDIUM, or HIGH
    max_depth=2          # Maximum recursion depth
)
```

### Batch Testing

```bash
# Test multiple claim types
./venv/bin/python test_suite.py

# Test recursion behavior
./venv/bin/python test_recursion.py
```

## Understanding the Output

```json
{
  "claim": {
    "original_text": "The 2020 US election had the highest voter turnout..."
  },
  "verdict": {
    "status": "TRUE",
    "confidence": 0.8625,
    "summary": "The claim is true based on official sources."
  },
  "sub_claims": [
    {
      "id": "C1",
      "text": "The 2020 election occurred",
      "claim_type": "FACTUAL"
    }
  ],
  "key_evidence": [
    {
      "source": "U.S. Census Bureau",
      "source_tier": 1,
      "url": "https://www.census.gov/...",
      "confidence": 0.99
    }
  ]
}
```

## How It Works (Simple Version)

```
Your Claim
    ↓
1. AI breaks it down into sub-claims
    ↓
2. Searches multiple sources (Exa, Tavily, official APIs)
    ↓
3. Ranks sources by authority (1=.gov, 2=fact-checkers, 3=news, 4=other)
    ↓
4. If confidence < 70%: Recursively investigate deeper
    ↓
5. Calculate final confidence score
    ↓
Return detailed report with verdict
```

## Key Features

✅ **Smart Decomposition**: GPT-4o breaks down complex claims intelligently  
✅ **Multi-API Search**: Exa (semantic) + Tavily (web/news)  
✅ **Source Ranking**: Automatically ranks .gov sources highest  
✅ **Adaptive Recursion**: Digs deeper only when needed  
✅ **Timeline Building**: Constructs chronological event sequences  
✅ **Confidence Scoring**: Multi-factor analysis (source quality, agreement, diversity)

## Recursion Explained

**When does it trigger?**

- Confidence < 70%
- Contradictory evidence found
- No authoritative sources found

**What happens?**

1. Identifies knowledge gaps
2. Generates follow-up claims
3. Recursively investigates (up to max_depth)
4. Merges evidence from deeper levels
5. Re-calculates confidence

**Example:**

```
Depth 0: "Vaccines cause autism"
    ↓ (Low confidence, need authoritative sources)
  Depth 1: "What are the official medical sources on vaccine safety?"
    ↓ (Finds CDC, WHO sources)
  Merge evidence → Final confidence: 95%
```

## Performance

- **Speed**: 10-15 seconds per claim
- **Cost**: ~$0.002-0.005 per claim
- **Sources**: Finds official .gov sources 60% of the time
- **Accuracy**: 57%-95% confidence range based on evidence quality

## Common Issues

### "API key not found"

- Check `src/.env` file exists and has valid keys
- Make sure no spaces around the `=` sign

### "Module not found"

```bash
# Run from project root as a module
./venv/bin/python main.py
# NOT: python src/main.py
```

### High costs

- System prioritizes free sources first (.gov, free tier APIs)
- Average cost: $0.002-0.005 per claim
- Stay within free tiers: Exa (1000/month), Tavily (1000/month)

## Project Structure

```
AgnoFinal2/
├── src/
│   ├── models/schemas.py      # Data structures
│   ├── core/                  # Core logic (confidence, timeline, etc.)
│   ├── tools/                 # API integrations (Exa, Tavily)
│   ├── agents/                # AI agents (Decomposer, Orchestrator)
│   └── .env                   # API keys (create this!)
├── main.py                    # Run this to start
├── test_suite.py              # Test multiple claims
└── test_recursion.py          # Test recursion behavior
```

## Next Steps

1. **Try different claims** - Edit `main.py` and change the claim
2. **Adjust recursion depth** - Set `max_depth` to control investigation depth
3. **Review the code** - Start with `src/agents/orchestrator.py`
4. **Read full docs** - See `TECHNICAL_DOCUMENTATION.md` for architecture details

## Getting Help

- **Technical Details**: See [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)
- **Original Spec**: See [documentation.md](documentation.md)
- **Implementation Notes**: See [walkthrough.md](.gemini/antigravity/brain/.../walkthrough.md)

---

**Quick Commands:**

```bash
# Verify a claim
./venv/bin/python main.py

# Test multiple claims
./venv/bin/python test_suite.py

# Test recursion
./venv/bin/python test_recursion.py

# Test API keys
./venv/bin/python test_api.py
```

Enjoy fact-checking! 🎯
