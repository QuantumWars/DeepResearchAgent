# Journalist's Mind: Agentic Fact-Checking Architecture

An advanced fact-checking system that mimics the cognitive processes of expert investigative journalists through an 8-layer agentic architecture.

## Overview

This system implements a sophisticated multi-agent architecture inspired by how professional journalists verify claims. Each agent represents a different cognitive layer in the fact-checking process, from initial assessment to final verdict.

## Architecture

### The 8 Cognitive Layers

1. **Gatekeeper** (Initial Assessment) - The "smell test"

   - Rapid triage and skepticism calibration
   - Identifies red flags and verifiable elements
   - Determines investigation strategy

2. **Profiler** (Source Evaluation) - Deep background checks

   - Assesses source credibility and authority
   - Detects bias and conflicts of interest
   - Evaluates expertise domains

3. **Investigator** (Cross-Verification) - Independent corroboration

   - Searches for diverse, independent sources
   - Detects circular reporting
   - Triangulates evidence

4. **Historian** (Context & Historical Intelligence) - Pattern recognition

   - Analyzes historical context and precedents
   - Performs "cui bono" (who benefits) analysis
   - Identifies missing information

5. **Judge** (Evidence Hierarchy Manager) - Evidence weighing

   - Categorizes evidence by tier (primary to unverified)
   - Resolves contradictions based on evidence quality
   - Assesses evidence independence

6. **Logician** (Logical Consistency Auditor) - Internal coherence

   - Checks temporal, quantitative, and narrative logic
   - Identifies logical fallacies
   - Calculates coherence scores

7. **Watchdog** (Meta-Analytical Observer) - Counter-intelligence

   - Detects coordinated information operations
   - Checks for cognitive biases in the analysis
   - Identifies unknown unknowns

8. **Editor** (Confidence Calibration & Output) - Final synthesis
   - Synthesizes all findings into final verdict
   - Generates caveats and recommendations
   - Determines publication readiness

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd Final

# Install dependencies (none required for basic functionality)
# For production use, install: requests, beautifulsoup4, etc.
```

## Usage

### Command Line

```bash
# Check a specific claim
python main.py "Your claim to fact-check here"

# Run with example claims
python main.py
```

### Programmatic Usage

```python
import asyncio
from main import create_fact_checker

async def check_my_claim():
    fact_checker = create_fact_checker()

    dossier = await fact_checker.investigate(
        claim="Your claim here",
        source="Source name",
        context="Additional context"
    )

    # Generate report
    report = fact_checker.generate_report(dossier)
    print(report)

    # Access detailed findings
    print(f"Verdict: {dossier.truth_value.value}")
    print(f"Confidence: {dossier.confidence_matrix.overall_confidence:.0%}")

asyncio.run(check_my_claim())
```

## Dynamic Adaptation

The system adapts its strategy based on claim type:

- **Breaking News**: Compressed timeline, institutional sources, prominent uncertainty flagging
- **Historical Claim**: Deep archive search, academic sources, extensive context
- **Scientific Claim**: Methodology scrutiny, peer review essential, expert consultation
- **Political Claim**: Hyper-vigilant for bias, opposing perspectives required
- **Statistical Claim**: Data verification, methodology examination, reproducibility check

## Evidence Hierarchy

Evidence is categorized into 5 tiers:

1. **Tier 1 (Primary)**: First-hand documents, direct observation, original data
2. **Tier 2 (Expert)**: Expert analysis of primary sources
3. **Tier 3 (Credible)**: Credible reporting citing primary sources
4. **Tier 4 (Secondary)**: Secondary analysis
5. **Tier 5 (Unverified)**: Anonymous/unverified claims

## Truth Values

Final verdicts are categorized as:

- **Confirmed**: Multiple independent high-tier sources
- **Highly Likely**: Convergent tier 2-3 evidence
- **Probable**: Single strong or multiple weak sources
- **Unclear**: Contradictory evidence
- **Unlikely**: Weak evidence with strong counter-evidence
- **False**: Definitive counter-evidence

## Feedback Loops

The system includes automatic feedback loops that trigger deeper investigation when:

- Overall confidence is low (<0.4)
- High-stakes claims have moderate confidence
- Multiple contradictions are found
- High information warfare risk is detected

## Project Structure

```
Final/
├── src/
│   ├── core/
│   │   ├── dossier.py          # Investigation state management
│   │   ├── base_agent.py       # Base agent class
│   │   ├── tools.py            # External tool abstractions
│   │   └── orchestrator.py     # Agent coordination
│   └── agents/
│       ├── gatekeeper.py       # Layer 1: Initial Assessment
│       ├── profiler.py         # Layer 2: Source Evaluation
│       ├── investigator.py     # Layer 3: Cross-Verification
│       ├── historian.py        # Layer 4: Context & History
│       ├── judge.py            # Layer 5: Evidence Hierarchy
│       ├── logician.py         # Layer 6: Logical Consistency
│       ├── watchdog.py         # Layer 7: Meta-Analysis
│       └── editor.py           # Layer 8: Final Verdict
├── docs/
│   └── check.md                # Original architecture research
└── main.py                     # Entry point
```

## Extending the System

### Adding Real Tool Integration

The current implementation uses placeholder tools. To integrate real APIs:

1. Edit `src/core/tools.py`
2. Implement actual API calls in the tool classes
3. Add API keys via environment variables

Example integrations:

- Google Custom Search API
- NewsAPI
- Media Bias/Fact Check API
- Academic databases (PubMed, arXiv)

### Adding New Agents

1. Create new agent class inheriting from `BaseAgent`
2. Implement the `analyze()` method
3. Add to orchestrator workflow
4. Update `src/agents/__init__.py`

## Future Enhancements

- [ ] Real-time web search integration
- [ ] NLP-based semantic analysis
- [ ] Machine learning for pattern recognition
- [ ] Multi-language support
- [ ] Web interface
- [ ] Database for historical claims
- [ ] API endpoints for external integration

## License

[Your License Here]

## Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

## Citation

If you use this architecture in research, please cite:

```
[Citation information]
```
