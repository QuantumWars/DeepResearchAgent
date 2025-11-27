#!/bin/bash
# Run the fact-checker with proper environment setup

# Unset any dummy values
unset OPENAI_API_KEY

# Load environment from src/.env
export $(cat src/.env | grep -v '^#' | xargs)

# Run the main script
./venv/bin/python main.py
