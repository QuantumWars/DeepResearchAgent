# Recursive Multi-Agent Fact-Checking System

A production-ready AI-powered fact-checking system that uses recursive multi-agent investigation to verify claims with confidence scores and authoritative sources.

## 🎯 Key Features

- ✅ **AI-Powered Decomposition**: GPT-4o intelligently breaks down complex claims
- ✅ **Multi-Source Verification**: Integrates Exa, Tavily, and official APIs
- ✅ **Recursive Investigation**: Adaptively digs deeper on low-confidence findings
- ✅ **Source Tier Ranking**: Automatically classifies .gov (Tier 1) to news (Tier 4)
- ✅ **Confidence Scoring**: Multi-factor analysis (source quality, agreement, diversity)
- ✅ **Timeline Construction**: Builds chronological event sequences

## 📚 Documentation

| Document                                                     | Description                      |
| ------------------------------------------------------------ | -------------------------------- |
| **[QUICKSTART.md](QUICKSTART.md)**                           | 🚀 Get started in 5 minutes      |
| **[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)** | 📖 Complete technical reference  |
| **[ARCHITECTURE.md](ARCHITECTURE.md)**                       | 🏗️ Visual architecture diagrams  |
| **[documentation.md](documentation.md)**                     | 📋 Original design specification |

## ⚡ Quick Start

### 1. Install

```bash
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

### 3. Run

```bash
./venv/bin/python main.py
```

## 💡 Usage Example

```python
import asyncio
from src.agents.orchestrator import OrchestratorAgent

async def verify():
    orchestrator = OrchestratorAgent()
    result = await orchestrator.verify_claim(
        "The 2020 US election had the highest voter turnout in history."
    )
    print(f"Verdict: {result['verdict']['status']}")
    print(f"Confidence: {result['verdict']['confidence']:.2%}")

asyncio.run(verify())
```

## 🎯 How It Works

```
User Claim
    ↓
1. AI Decomposition (GPT-4o breaks down claim)
    ↓
2. Multi-API Search (Exa + Tavily + Official sources)
    ↓
3. Source Ranking (1=.gov, 2=fact-checkers, 3=news, 4=other)
    ↓
4. Confidence Calculation (Multi-factor analysis)
    ↓
5. Recursion Decision (If confidence < 70%, dig deeper)
    ↓
Final Report with Verdict + Evidence + Timeline
```

## 📊 System Architecture

```
┌─────────────────────────────────────┐
│     OrchestratorAgent               │
│  (Recursion & Flow Control)         │
└──────────┬──────────────────────────┘
           │
    ┌──────┴───────┬─────────────┬──────────┐
    │              │             │          │
┌───▼────┐  ┌─────▼──────┐  ┌──▼───┐  ┌──▼────┐
│Decomp  │  │  Planner   │  │Eval  │  │Forens │
│Agent   │  │  Agent     │  │Agent │  │Agent  │
│(GPT-4o)│  │            │  │      │  │       │
└────────┘  └────────────┘  └──────┘  └───────┘
                │
         ┌──────┴──────┬─────────┐
         │             │         │
      ┌──▼──┐      ┌──▼──┐  ┌──▼────┐
      │ Exa │      │Tavily│  │Official│
      │     │      │      │  │  APIs │
      └─────┘      └──────┘  └───────┘
```

## 🔬 Test Results

| Test Type   | Claim                         | Result                                         |
| ----------- | ----------------------------- | ---------------------------------------------- |
| Statistical | "2020 US election turnout"    | ✅ 86% confidence, Census.gov sources          |
| Factual     | "Eiffel Tower completed 1889" | ✅ 58% confidence, Wikipedia + Official site   |
| Comparative | "EVs produce zero emissions"  | ✅ 93% confidence, EPA.gov (smart: "tailpipe") |

**Performance:**

- ⏱️ **Speed**: 10-15 seconds per claim
- 💰 **Cost**: ~$0.002-0.005 per claim
- 🎯 **Accuracy**: 57%-95% confidence range
- 🏛️ **Official Sources**: Found in 60% of cases

## 📁 Project Structure

```
AgnoFinal2/
├── src/
│   ├── models/schemas.py      # Pydantic data models
│   ├── core/                  # Confidence, timeline, contradiction, cost
│   ├── tools/                 # Exa, Tavily, Official API integration
│   ├── agents/                # AI agents (Decomposer, Orchestrator)
│   └── .env                   # API keys configuration
├── main.py                    # Entry point
├── test_suite.py              # Multi-claim testing
├── test_recursion.py          # Recursion validation
├── QUICKSTART.md              # Quick start guide
├── TECHNICAL_DOCUMENTATION.md # Complete technical docs
└── ARCHITECTURE.md            # Visual diagrams
```

## 🔑 API Keys Required

| API    | Purpose                        | Free Tier   | Get Key                                                     |
| ------ | ------------------------------ | ----------- | ----------------------------------------------------------- |
| OpenAI | GPT-4o claim decomposition     | Pay-per-use | [platform.openai.com](https://platform.openai.com/api-keys) |
| Exa    | High-precision semantic search | 1000/month  | [exa.ai](https://exa.ai/)                                   |
| Tavily | Web/news search                | 1000/month  | [tavily.com](https://tavily.com/)                           |

## 🚀 Advanced Usage

### Custom Recursion Depth

```python
result = await orchestrator.verify_claim(
    claim_text="Your claim",
    priority="HIGH",      # LOW/MEDIUM/HIGH
    max_depth=2          # Maximum recursion levels
)
```

### Batch Testing

```bash
# Test multiple claim types
./venv/bin/python test_suite.py

# Test recursion behavior
./venv/bin/python test_recursion.py
```

## 🎓 Key Concepts

### Recursion

The system automatically investigates deeper when:

- Confidence < 70% (low confidence)
- Contradictions detected
- No authoritative sources found

### Source Tiers

- **Tier 1** (.gov, .edu): Official/Academic - Weight 1.0
- **Tier 2** (fact-checkers): PolitiFact, FactCheck.org - Weight 0.85
- **Tier 3** (major news): NYT, BBC, Reuters - Weight 0.70
- **Tier 4** (other): Wikipedia, blogs - Weight 0.50

### Confidence Calculation

```python
confidence = (
    source_quality * 0.30 +
    source_agreement * 0.25 +
    source_diversity * 0.15 +
    temporal_consistency * 0.10 +
    logical_coherence * 0.10 +
    primary_source_presence * 0.10
) * (1 - penalties)
```

## 🔮 Future Roadmap

- [ ] Implement AI-powered PlannerAgent and EvaluatorAgent
- [ ] Add forensic analysis (image/video verification)
- [ ] Multi-language support
- [ ] Web interface (React/Next.js)
- [ ] Database persistence and caching
- [ ] REST API for integration

## 📄 License

See project license file for details.

## 🙏 Acknowledgments

Built with:

- [Agno](https://github.com/agno-framework/agno) - AI Agent Framework
- [OpenAI GPT-4o](https://openai.com/) - Language Model
- [Exa](https://exa.ai/) - Semantic Search
- [Tavily](https://tavily.com/) - Web Search

---

**Quick Commands:**

```bash
# Verify a claim
./venv/bin/python main.py

# Run test suite
./venv/bin/python test_suite.py

# Test recursion
./venv/bin/python test_recursion.py
```

📖 **Read the docs**: Start with [QUICKSTART.md](QUICKSTART.md) then dive into [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)
