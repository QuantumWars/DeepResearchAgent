#!/usr/bin/env python3
"""
Test script for full research execution.
"""

from dotenv import load_dotenv
load_dotenv()

from core.orchestrator import ResearchOrchestrator
import sys

def main():
    print('=' * 80)
    print('Deep Research Framework - Test Execution')
    print('=' * 80)
    
    # Initialize orchestrator
    print('\n1. Initializing orchestrator...')
    orchestrator = ResearchOrchestrator('config/tool_config.yaml')
    print('   ✓ Orchestrator initialized')
    
    # Check available tools
    tools = orchestrator.registry.get_registered_tools()
    print('\n2. Available tools:')
    for category, tool_list in tools.items():
        if tool_list:
            print(f'   {category}: {", ".join(tool_list)}')
        else:
            print(f'   {category}: (none - will use fallback behavior)')
    
    # Execute research
    query = "What are the key benefits of using Python for data science?"
    print(f'\n3. Executing research query:')
    print(f'   "{query}"')
    print('   (This may take 30-60 seconds...)')
    
    try:
        result = orchestrator.research(
            query=query,
            max_loops=1  # Limit to 1 loop for testing
        )
        
        print('\n' + '=' * 80)
        print('RESEARCH COMPLETED SUCCESSFULLY')
        print('=' * 80)
        
        # Display statistics
        print(f'\nStatistics:')
        print(f'  Report length: {len(result.report)} characters')
        print(f'  Sources retrieved: {len(result.sources)}')
        print(f'  Tool calls made: {len(result.execution_log)}')
        
        # Count successful vs failed
        successful = sum(1 for log in result.execution_log if log.get('success'))
        failed = len(result.execution_log) - successful
        print(f'  Successful tool calls: {successful}')
        print(f'  Failed tool calls: {failed}')
        
        # Display execution log
        print(f'\nExecution Log:')
        for log in result.execution_log:
            status = '✓' if log.get('success') else '✗'
            node = log.get('node', 'unknown')
            category = log.get('tool_category', 'unknown')
            tool = log.get('tool_name', 'unknown')
            print(f'  {status} {node:12s} {category:10s} {tool}')
        
        # Display report preview
        print('\n' + '-' * 80)
        print('REPORT PREVIEW (first 800 characters):')
        print('-' * 80)
        print(result.report[:800])
        if len(result.report) > 800:
            print('...\n(truncated)')
        
        # Save report
        output_file = 'test_report.md'
        result.save(output_file)
        print(f'\n✓ Full report saved to: {output_file}')
        
        # Test citations
        citations = result.get_citations()
        if citations:
            print(f'\nCitations extracted: {len(citations)}')
            for citation in citations[:3]:  # Show first 3
                print(f'  [{citation.id}] {citation.title}')
        
        print('\n' + '=' * 80)
        print('✅ TEST COMPLETED SUCCESSFULLY')
        print('=' * 80)
        
        return 0
        
    except Exception as e:
        print(f'\n✗ Research failed: {e}')
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
