#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# Unset any dummy values
if os.getenv('OPENAI_API_KEY') == 'dummy':
    del os.environ['OPENAI_API_KEY']

# Load from src/.env
load_dotenv('src/.env')

print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY')[:20]}...")
print(f"EXA_API_KEY: {os.getenv('EXA_API_KEY')}")
print(f"TAVILY_API_KEY: {os.getenv('TAVILY_API_KEY')[:20]}...")

# Test OpenAI
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say 'API key works!'"}],
        max_tokens=10
    )
    print(f"\n✓ OpenAI API Test: {response.choices[0].message.content}")
except Exception as e:
    print(f"\n✗ OpenAI API Test Failed: {e}")
