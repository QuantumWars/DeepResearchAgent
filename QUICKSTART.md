# Quick Start Guide

## Running the Fact-Checker

### Option 1: Using the Run Script (Easiest)

```bash
# Make the script executable (first time only)
chmod +x run.sh

# Run with example claims
./run.sh

# Check a specific claim
./run.sh "Your claim to fact-check here"

# Example
./run.sh "Breaking: New study shows coffee cures cancer"
```

### Option 2: Manual Execution

```bash
# Create virtual environment (first time only)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Run with example claims
python main.py

# Check a specific claim
python main.py "Your claim to fact-check here"

# Deactivate when done
deactivate
```

### Option 3: Direct Python (if venv already activated)

```bash
source venv/bin/activate
python main.py "Your claim here"
```

## Example Claims to Test

Try these different claim types to see the dynamic adaptation:

### Breaking News

```bash
./run.sh "Breaking: Scientists discover that drinking 8 glasses of water daily is a myth"
```

### Scientific Claim

```bash
./run.sh "A study published in Nature shows that eating chocolate daily improves memory by 40%"
```

### Political Claim

```bash
./run.sh "The election results were fraudulent with over 100% voter turnout in multiple districts"
```

### Statistical Claim

```bash
./run.sh "Crime rates have increased by 300% in the last year according to new data"
```

### Historical Claim

```bash
./run.sh "In 1969, the moon landing was filmed in a Hollywood studio"
```

## Understanding the Output

The system will show:

1. **Investigation Phases**

   - Phase 1: Initial Assessment (Gatekeeper)
   - Phase 2: Core Investigation (Profiler, Investigator, Historian in parallel)
   - Phase 3: Analysis & Synthesis (Judge, Logician in parallel)
   - Phase 4: Meta-Analysis & Final Verdict (Watchdog, Editor)

2. **Final Report**

   - Verdict (CONFIRMED, HIGHLY_LIKELY, PROBABLE, UNCLEAR, UNLIKELY, FALSE)
   - Confidence Score (0-100%)
   - Evidence Summary
   - Red Flags
   - Caveats
   - Recommendations

3. **Detailed Dossier Summary**
   - Investigation strategy used
   - Evidence breakdown by tier
   - Number of hypotheses generated
   - Unanswered questions

## Troubleshooting

### Python not found

```bash
# Use python3 explicitly
python3 -m venv venv
```

### Permission denied on run.sh

```bash
chmod +x run.sh
```

### Module not found errors

Make sure you're in the correct directory:

```bash
cd /home/doniel/Desktop/Tmp/Hackathon/Final
```

## Next Steps

- Review [README.md](file:///home/doniel/Desktop/Tmp/Hackathon/Final/README.md) for architecture details
- Check [walkthrough.md](file:///home/doniel/.gemini/antigravity/brain/217d8ea6-da95-4e3f-ab25-c9c1710c5f70/walkthrough.md) for implementation details
- Modify [main.py](file:///home/doniel/Desktop/Tmp/Hackathon/Final/main.py) to add your own claims
- Integrate real APIs in [src/core/tools.py](file:///home/doniel/Desktop/Tmp/Hackathon/Final/src/core/tools.py)
