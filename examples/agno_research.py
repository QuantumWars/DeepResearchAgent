"""
Agno Research Example.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables may not be loaded from .env file")

from core.agno_orchestrator import AgnoResearchOrchestrator
from utils.logging_config import setup_logger

def main():
    setup_logger(level=logging.INFO)
    
    print("\n" + "="*70)
    print("AGNO RESEARCH EXAMPLE")
    print("="*70 + "\n")
    
    try:
        # Initialize orchestrator
        # Note: Requires OPENAI_API_KEY and SERPER_API_KEY in environment
        orchestrator = AgnoResearchOrchestrator(model_provider="openai", model_name="gpt-4o")
        
        query = "What are the latest developments in solid state batteries?"
        print(f"Query: {query}\n")
        
        result = orchestrator.research(query=query, max_loops=2)
        
        print("\n" + "="*70)
        print("FINAL REPORT")
        print("="*70 + "\n")
        print(result.report)
        
        print("\n" + "="*70)
        print("EXECUTION LOG")
        print("="*70 + "\n")
        for log in result.execution_log:
            print(f"[{log['timestamp']}] {log['node']}: {log.get('metadata', '')}")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
