#!/bin/bash
# Run script for Journalist's Mind Fact-Checking System

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Journalist's Mind Fact-Checking System${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Check if claim is provided as argument
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}No claim provided. Running with example claims...${NC}"
    echo ""
    python main.py
else
    echo -e "${GREEN}Checking claim: $*${NC}"
    echo ""
    python main.py "$*"
fi

# Deactivate virtual environment
deactivate
