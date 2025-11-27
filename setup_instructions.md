# Setup Instructions for Real API Integration

## Current Status

✅ API libraries installed (exa-py, tavily-python)
✅ System updated to use real search tools
⏳ Need API keys configured

## Get Your API Keys

### 1. OpenAI API Key (Required for Agents)

- Go to: https://platform.openai.com/api-keys
- Click "Create new secret key"
- Copy the key (starts with `sk-`)
- **Cost**: ~$0.002 per claim with GPT-4o

### 2. Exa API Key (For High-Quality Search)

- Go to: https://exa.ai/
- Sign up for free account
- Get API key from dashboard
- **Free tier**: 1000 searches/month

### 3. Tavily API Key (For Web Search)

- Go to: https://tavily.com/
- Sign up for free account
- Get API key from dashboard
- **Free tier**: 1000 searches/month

## Configure API Keys

Edit the `.env` file in your project root:

```bash
# Open the .env file
nano .env

# Or use your preferred editor
code .env
```

Replace the placeholder values:

```env
OPENAI_API_KEY=sk-your-actual-openai-key-here
EXA_API_KEY=your-actual-exa-key-here
TAVILY_API_KEY=tvly-your-actual-tavily-key-here
```

**Important**: Keep these keys secret! Never commit them to git.

## Test the System

Once you've added the keys:

```bash
# Run the system
python3 main.py
```

You should see:

```
=== API Key Status ===
OpenAI: ✓ Found
Exa: ✓ Found
Tavily: ✓ Found
```

## What Will Change

With real APIs enabled:

1. **DecomposerAgent** will use GPT-4o to intelligently break down claims
2. **Search Tools** will fetch real data from Exa and Tavily
3. **Evidence** will be from actual sources (news articles, official documents)
4. **Confidence scores** will be based on real source quality

## Cost Estimates

Per claim verification:

- OpenAI (GPT-4o): ~$0.002-0.005
- Exa searches: Free (within tier)
- Tavily searches: Free (within tier)

**Total**: ~$0.002-0.005 per claim

## Troubleshooting

### "API key not found"

- Make sure `.env` file is in project root
- Check for typos in key names
- Ensure no extra spaces around `=`

### "Invalid API key"

- Verify you copied the complete key
- Check if key is still active in the API dashboard
- Some keys have usage limits or require payment setup

### "Module not found"

```bash
# Reinstall dependencies
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install exa-py tavily-python python-dotenv
```

## Next: Enable Real Agent Intelligence

After API keys are working, we can:

1. Uncomment the real agent.run() calls in `src/agents/specialized.py`
2. Add recursion logic for complex claims
3. Implement better prompt engineering for more accurate decomposition
