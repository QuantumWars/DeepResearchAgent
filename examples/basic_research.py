"""
Basic usage examples for the Deep Research Framework.

This script demonstrates how to use the ResearchOrchestrator to perform
research queries and work with the results.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path to import framework modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables may not be loaded from .env file")

from core.orchestrator import ResearchOrchestrator, ResearchResult
from examples.custom_tool_example import PDFExtractor, ArXivSearchTool
from utils.logging_config import setup_logger


def example_1_basic_research():
    """
    Example 1: Basic research query.
    
    Demonstrates the simplest usage pattern - initialize orchestrator
    and execute a research query.
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Research Query")
    print("="*70 + "\n")
    
    # Initialize the orchestrator with default configuration
    orchestrator = ResearchOrchestrator(config_path="config/tool_config.yaml")
    
    # Execute research with a simple query
    query = "What are the latest developments in quantum computing?"
    print(f"Query: {query}\n")
    
    result = orchestrator.research(query=query, max_loops=2)
    
    # Display results
    print(f"Report Preview (first 500 chars):")
    print("-" * 70)
    print(result.report[:500] + "...")
    print("-" * 70)
    print(f"\nSources Retrieved: {len(result.sources)}")
    print(f"Tool Calls Made: {len(result.execution_log)}")
    
    return result


def example_2_save_report():
    """
    Example 2: Execute research and save the report to a file.
    
    Demonstrates how to save research results to disk for later use.
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Save Research Report")
    print("="*70 + "\n")
    
    orchestrator = ResearchOrchestrator()
    
    query = "What is machine learning and how does it work?"
    print(f"Query: {query}\n")
    
    result = orchestrator.research(query=query, max_loops=2)
    
    # Save the report to a file
    output_path = "ml_report.md"
    result.save(output_path)
    
    print(f"✓ Report saved to: {output_path}")
    print(f"  - Report length: {len(result.report)} characters")
    print(f"  - Sources: {len(result.sources)}")
    
    return result


def example_3_access_sources():
    """
    Example 3: Access and display source documents.
    
    Demonstrates how to iterate through retrieved sources and
    access their metadata.
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Access Source Documents")
    print("="*70 + "\n")
    
    orchestrator = ResearchOrchestrator()
    
    query = "What are the benefits of renewable energy?"
    print(f"Query: {query}\n")
    
    result = orchestrator.research(query=query, max_loops=1)
    
    # Display information about each source
    print(f"Retrieved {len(result.sources)} sources:\n")
    
    for idx, source in enumerate(result.sources, 1):
        print(f"Source {idx}:")
        print(f"  Title: {source.get('title', 'Untitled')}")
        print(f"  URL: {source.get('url', 'N/A')}")
        print(f"  Content Length: {len(source.get('content', ''))} characters")
        print()
    
    return result


def example_4_extract_citations():
    """
    Example 4: Extract and display citations from the report.
    
    Demonstrates how to use the get_citations() method to extract
    structured citation information.
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Extract Citations")
    print("="*70 + "\n")
    
    orchestrator = ResearchOrchestrator()
    
    query = "What is the impact of climate change on biodiversity?"
    print(f"Query: {query}\n")
    
    result = orchestrator.research(query=query, max_loops=2)
    
    # Extract citations
    citations = result.get_citations()
    
    print(f"Found {len(citations)} citations in the report:\n")
    
    for citation in citations:
        print(f"[{citation.id}] {citation.title}")
        print(f"    URL: {citation.url}")
        print(f"    Excerpt: {citation.excerpt[:100]}...")
        print()
    
    return result


def example_5_custom_tool():
    """
    Example 5: Register and use a custom tool.
    
    Demonstrates how to create a custom tool and register it with
    the orchestrator for use during research.
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Using Custom Tools")
    print("="*70 + "\n")
    
    orchestrator = ResearchOrchestrator()
    
    # Create custom tool instances
    pdf_extractor = PDFExtractor(max_pages=50)
    arxiv_search = ArXivSearchTool(max_results=10)
    
    print("Custom tools created:")
    print(f"  - {pdf_extractor.name}: {pdf_extractor.description}")
    print(f"  - {arxiv_search.name}: {arxiv_search.description}")
    print()
    
    # Execute research with custom tools
    query = "What are the latest research papers on neural networks?"
    print(f"Query: {query}\n")
    
    result = orchestrator.research(
        query=query,
        custom_tools=[pdf_extractor, arxiv_search],
        max_loops=2
    )
    
    print(f"✓ Research completed with custom tools")
    print(f"  - Report length: {len(result.report)} characters")
    print(f"  - Sources: {len(result.sources)}")
    print(f"  - Tool calls: {len(result.execution_log)}")
    
    # Show which tools were used
    tools_used = set(log.get('tool_name', 'unknown') for log in result.execution_log)
    print(f"  - Tools used: {', '.join(tools_used)}")
    
    return result


def example_6_execution_log():
    """
    Example 6: Analyze the execution log.
    
    Demonstrates how to inspect the tool execution log to understand
    what happened during research.
    """
    print("\n" + "="*70)
    print("EXAMPLE 6: Analyze Execution Log")
    print("="*70 + "\n")
    
    orchestrator = ResearchOrchestrator()
    
    query = "What is artificial intelligence?"
    print(f"Query: {query}\n")
    
    result = orchestrator.research(query=query, max_loops=2)
    
    # Analyze execution log
    print(f"Execution Log ({len(result.execution_log)} entries):\n")
    
    for idx, log_entry in enumerate(result.execution_log, 1):
        status = "✓" if log_entry.get('success') else "✗"
        node = log_entry.get('node', 'unknown')
        tool_name = log_entry.get('tool_name', 'unknown')
        timestamp = log_entry.get('timestamp', 'N/A')
        
        print(f"{idx}. {status} [{node}] {tool_name} at {timestamp}")
        
        if not log_entry.get('success'):
            error = log_entry.get('error_msg', 'Unknown error')
            print(f"   Error: {error}")
    
    # Summary statistics
    successful = sum(1 for log in result.execution_log if log.get('success'))
    failed = len(result.execution_log) - successful
    
    print(f"\nSummary:")
    print(f"  - Successful: {successful}")
    print(f"  - Failed: {failed}")
    print(f"  - Success Rate: {successful/len(result.execution_log)*100:.1f}%")
    
    return result


def example_7_custom_max_loops():
    """
    Example 7: Control research depth with max_loops parameter.
    
    Demonstrates how to adjust the research depth by controlling
    the maximum number of research iterations.
    """
    print("\n" + "="*70)
    print("EXAMPLE 7: Control Research Depth")
    print("="*70 + "\n")
    
    orchestrator = ResearchOrchestrator()
    
    query = "What are the applications of blockchain technology?"
    
    # Try different max_loops values
    for max_loops in [1, 2, 3]:
        print(f"\nResearch with max_loops={max_loops}:")
        print("-" * 70)
        
        result = orchestrator.research(query=query, max_loops=max_loops)
        
        print(f"  - Report length: {len(result.report)} characters")
        print(f"  - Sources: {len(result.sources)}")
        print(f"  - Tool calls: {len(result.execution_log)}")
        print(f"  - Actual loops: {max([log.get('metadata', {}).get('loop_count', 0) for log in result.execution_log] or [0])}")


def example_8_direct_tool_usage():
    """
    Example 8: Use custom tools directly without orchestrator.
    
    Demonstrates how to use custom tools independently for
    specific tasks outside the research workflow.
    """
    print("\n" + "="*70)
    print("EXAMPLE 8: Direct Tool Usage")
    print("="*70 + "\n")
    
    # Create tool instance
    pdf_extractor = PDFExtractor(max_pages=20)
    
    # Use tool directly
    print("Extracting PDF content directly:")
    result = pdf_extractor.execute({
        'url': 'https://example.com/research-paper.pdf',
        'extract_metadata': True
    })
    
    if result['success']:
        print(f"✓ Extraction successful")
        print(f"  - Pages extracted: {result['pages_extracted']}")
        print(f"  - Content length: {len(result['content'])} characters")
        
        if 'metadata' in result:
            print(f"  - Metadata: {result['metadata']}")
    else:
        print(f"✗ Extraction failed: {result.get('error')}")
    
    # Try arXiv search
    print("\n" + "-"*70)
    print("Searching arXiv directly:")
    
    arxiv_tool = ArXivSearchTool(max_results=5)
    result = arxiv_tool.execute({
        'query': 'deep learning',
        'category': 'cs.AI'
    })
    
    if result['success']:
        print(f"✓ Search successful")
        print(f"  - Papers found: {result['count']}")
        
        for idx, paper in enumerate(result['papers'], 1):
            print(f"\n  Paper {idx}:")
            print(f"    Title: {paper['title']}")
            print(f"    Authors: {', '.join(paper['authors'])}")
            print(f"    arXiv ID: {paper['arxiv_id']}")
    else:
        print(f"✗ Search failed: {result.get('error')}")


def main():
    """
    Main function to run all examples.
    
    You can run specific examples by commenting out the ones you don't want.
    """
    # Set up logging
    setup_logger(level=logging.INFO)
    
    print("\n" + "="*70)
    print("DEEP RESEARCH FRAMEWORK - USAGE EXAMPLES")
    print("="*70)
    
    try:
        # Run examples (comment out any you don't want to run)
        example_1_basic_research()
        example_2_save_report()
        example_3_access_sources()
        example_4_extract_citations()
        example_5_custom_tool()
        example_6_execution_log()
        example_7_custom_max_loops()
        example_8_direct_tool_usage()
        
        print("\n" + "="*70)
        print("ALL EXAMPLES COMPLETED")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
