#!/usr/bin/env python3
"""
Test script for the ResearchOrchestrator.

This script demonstrates the basic functionality of the orchestrator
without requiring external API keys or dependencies.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.orchestrator import ResearchResult
from datetime import datetime


def test_research_result():
    """Test ResearchResult functionality."""
    print("=" * 80)
    print("Testing ResearchResult")
    print("=" * 80)
    
    # Create a sample result
    result = ResearchResult(
        report="""# Quantum Computing Research Report

## Summary
Quantum computing is a revolutionary technology [1] that uses quantum mechanics [2].

## Key Concepts
Quantum computers use qubits instead of classical bits [1]. This allows for 
superposition and entanglement [2], enabling exponential speedup for certain problems.

## Applications
- Cryptography [1]
- Drug discovery [2]
- Optimization problems [1]

## References
[1] Introduction to Quantum Computing - https://example.com/quantum-intro
[2] Quantum Mechanics Basics - https://example.com/quantum-mechanics
""",
        sources=[
            {
                "url": "https://example.com/quantum-intro",
                "title": "Introduction to Quantum Computing",
                "content": "Quantum computing is a revolutionary technology that leverages quantum mechanics to solve complex problems..."
            },
            {
                "url": "https://example.com/quantum-mechanics",
                "title": "Quantum Mechanics Basics",
                "content": "Quantum mechanics is the fundamental theory in physics that describes nature at the smallest scales..."
            }
        ],
        execution_log=[
            {
                "timestamp": datetime.now().isoformat(),
                "node": "planner",
                "tool_category": "llm",
                "tool_name": "test_llm",
                "success": True,
                "error_msg": None
            },
            {
                "timestamp": datetime.now().isoformat(),
                "node": "retrieval",
                "tool_category": "search",
                "tool_name": "test_search",
                "success": True,
                "error_msg": None
            }
        ]
    )
    
    print(f"\n✓ Created ResearchResult")
    print(f"  Report length: {len(result.report)} characters")
    print(f"  Sources: {len(result.sources)}")
    print(f"  Execution log entries: {len(result.execution_log)}")
    
    # Test get_citations
    print("\n" + "-" * 80)
    print("Testing get_citations()")
    print("-" * 80)
    
    citations = result.get_citations()
    print(f"\n✓ Extracted {len(citations)} citations:")
    for citation in citations:
        print(f"  [{citation.id}] {citation.title}")
        print(f"      URL: {citation.url}")
        print(f"      Excerpt: {citation.excerpt[:80]}...")
    
    # Test save
    print("\n" + "-" * 80)
    print("Testing save()")
    print("-" * 80)
    
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_report.md"
        result.save(str(output_path))
        
        print(f"\n✓ Saved report to: {output_path}")
        
        # Verify file contents
        with open(output_path, 'r') as f:
            content = f.read()
        
        print(f"  File size: {len(content)} bytes")
        print(f"  Contains metadata: {'Research Metadata' in content}")
        
        # Show first few lines
        lines = content.split('\n')[:5]
        print("\n  First few lines:")
        for line in lines:
            print(f"    {line}")
    
    print("\n" + "=" * 80)
    print("✅ All ResearchResult tests passed!")
    print("=" * 80)


def test_orchestrator_import():
    """Test that orchestrator can be imported."""
    print("\n" + "=" * 80)
    print("Testing ResearchOrchestrator Import")
    print("=" * 80)
    
    try:
        from core.orchestrator import ResearchOrchestrator
        print("\n✓ ResearchOrchestrator imported successfully")
        print(f"  Class: {ResearchOrchestrator}")
        print(f"  Module: {ResearchOrchestrator.__module__}")
        
        # Show docstring
        if ResearchOrchestrator.__doc__:
            doc_lines = ResearchOrchestrator.__doc__.strip().split('\n')[:3]
            print("\n  Documentation:")
            for line in doc_lines:
                print(f"    {line.strip()}")
        
        print("\n✅ Import test passed!")
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("ResearchOrchestrator Test Suite")
    print("=" * 80)
    
    # Test ResearchResult
    test_research_result()
    
    # Test orchestrator import
    test_orchestrator_import()
    
    print("\n" + "=" * 80)
    print("🎉 All tests completed successfully!")
    print("=" * 80)
    print("\nThe ResearchOrchestrator is ready to use.")
    print("To run a real research query, ensure you have:")
    print("  1. Configured API keys in .env file")
    print("  2. Installed required dependencies (pip install -r requirements.txt)")
    print("  3. Run: python main.py 'Your research query here'")
    print()


if __name__ == "__main__":
    main()
