"""
Main entry point for the Journalist's Mind Fact-Checking System
"""

import asyncio
import sys
from src.core import InvestigationOrchestrator, ToolKit
from src.agents import (
    GatekeeperAgent,
    ProfilerAgent,
    InvestigatorAgent,
    HistorianAgent,
    JudgeAgent,
    LogicianAgent,
    WatchdogAgent,
    EditorAgent
)


def create_fact_checker() -> InvestigationOrchestrator:
    """
    Factory function to create a fully configured fact-checking system.
    
    Returns:
        Configured InvestigationOrchestrator
    """
    # Initialize toolkit
    toolkit = ToolKit()
    
    # Initialize all agents
    agents = {
        'Gatekeeper': GatekeeperAgent(),
        'Profiler': ProfilerAgent(toolkit),
        'Investigator': InvestigatorAgent(toolkit),
        'Historian': HistorianAgent(toolkit),
        'Judge': JudgeAgent(),
        'Logician': LogicianAgent(),
        'Watchdog': WatchdogAgent(toolkit),
        'Editor': EditorAgent()
    }
    
    # Create orchestrator
    orchestrator = InvestigationOrchestrator(agents, toolkit)
    
    return orchestrator


async def check_claim(claim: str, source: str = "Unknown", context: str = ""):
    """
    Check a single claim.
    
    Args:
        claim: The claim to fact-check
        source: Source of the claim
        context: Additional context
    """
    # Create fact-checker
    fact_checker = create_fact_checker()
    
    # Run investigation
    dossier = await fact_checker.investigate(claim, source, context)
    
    # Generate and print report
    report = fact_checker.generate_report(dossier)
    print("\n" + report)
    
    # Print detailed summary
    print("\n" + dossier.summary())
    
    return dossier


async def main():
    """Main entry point for CLI usage"""
    
    # Example claims to test
    example_claims = [
        {
            "claim": "A new study shows that drinking coffee reduces cancer risk by 50%",
            "source": "Social Media Post",
            "context": "Viral post shared 10,000 times"
        },
        {
            "claim": "The election results were fraudulent with over 100% voter turnout in multiple districts",
            "source": "Anonymous Blog",
            "context": "Posted day after election"
        },
        {
            "claim": "Scientists at MIT have developed a quantum computer that can break all encryption",
            "source": "Tech News Site",
            "context": "Breaking news article"
        }
    ]
    
    # Check if claim provided via command line
    if len(sys.argv) > 1:
        claim = ' '.join(sys.argv[1:])
        await check_claim(claim)
    else:
        # Run example claims
        print("=" * 80)
        print("JOURNALIST'S MIND FACT-CHECKING SYSTEM")
        print("Demonstrating with example claims")
        print("=" * 80)
        
        for i, example in enumerate(example_claims, 1):
            print(f"\n\n{'='*80}")
            print(f"EXAMPLE {i}/{len(example_claims)}")
            print(f"{'='*80}\n")
            
            await check_claim(
                example['claim'],
                example['source'],
                example['context']
            )
            
            if i < len(example_claims):
                print("\n\nPress Enter to continue to next example...")
                input()


if __name__ == "__main__":
    asyncio.run(main())
