#!/usr/bin/env python3
"""CLI entry point for the Deep Research Agent."""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from research_agent.agent.research_agent import DeepResearchAgent
from research_agent.utils.config import get_config
from research_agent.utils.logger import get_logger


logger = get_logger(__name__)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Deep Research Agent - Autonomous AI-powered research",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        # Basic research
        python main.py "What is quantum computing?"
        
        # With specific search provider
        python main.py "AI trends 2024" --provider tavily
        
        # With user ID for memory
        python main.py "Machine learning basics" --user-id user123
        
        # JSON output format
        python main.py "Climate change" --format json
        
        # Debug mode
        python main.py "Python async" --log-level DEBUG
        """
    )
    
    parser.add_argument(
        "query",
        type=str,
        help="Research query to investigate"
    )
    
    parser.add_argument(
        "--user-id",
        type=str,
        default=None,
        help="User identifier for memory isolation (optional)"
    )
    
    parser.add_argument(
        "--provider",
        type=str,
        choices=["exa", "tavily", "firecrawl", "parallel"],
        default=None,
        help="Search provider to use (default: from config)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="Logging level (default: from config)"
    )
    
    parser.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: stdout)"
    )
    
    return parser.parse_args()


def print_text_output(result):
    """Print research result in human-readable text format."""
    print("\n" + "=" * 80)
    print("RESEARCH RESULTS")
    print("=" * 80)
    
    print(f"\nQuery: {result.query}")
    print(f"Execution Time: {result.execution_time:.2f}s")
    
    if result.plan:
        print(f"\nResearch Plan:")
        print(f"  Topics: {len(result.plan.topics)}")
        print(f"  Total Tasks: {result.plan.total_tasks}")
        
        for i, topic in enumerate(result.plan.topics, 1):
            print(f"\n  {i}. {topic.title}")
            for j, task in enumerate(topic.tasks, 1):
                print(f"     {i}.{j}. {task}")
    
    print(f"\n{'-' * 80}")
    print("FINDINGS")
    print("-" * 80)
    print(f"\n{result.text}\n")
    
    if result.sources:
        print(f"\n{'-' * 80}")
        print(f"SOURCES ({len(result.sources)})")
        print("-" * 80)
        
        for i, source in enumerate(result.sources, 1):
            print(f"\n{i}. {source.title}")
            print(f"   URL: {source.url}")
            if source.published_date:
                print(f"   Published: {source.published_date}")
            if source.content:
                # Print first 200 chars of content
                content_preview = source.content[:200].replace('\n', ' ')
                if len(source.content) > 200:
                    content_preview += "..."
                print(f"   Preview: {content_preview}")
    
    if result.charts:
        print(f"\n{'-' * 80}")
        print(f"CHARTS ({len(result.charts)})")
        print("-" * 80)
        for i, chart in enumerate(result.charts, 1):
            print(f"\n{i}. {chart.get('filename', 'chart.png')}")
            print(f"   Format: {chart.get('format', 'png')}")
    
    print("\n" + "=" * 80)


def print_json_output(result):
    """Print research result in JSON format."""
    output = {
        "query": result.query,
        "execution_time": result.execution_time,
        "plan": {
            "topics": [
                {
                    "title": topic.title,
                    "tasks": topic.tasks
                }
                for topic in result.plan.topics
            ],
            "total_tasks": result.plan.total_tasks
        } if result.plan else None,
        "text": result.text,
        "sources": [
            {
                "title": source.title,
                "url": source.url,
                "content": source.content,
                "published_date": source.published_date,
                "author": source.author
            }
            for source in result.sources
        ],
        "charts": result.charts,
        "sources_count": len(result.sources),
        "charts_count": len(result.charts)
    }
    
    print(json.dumps(output, indent=2))


async def main():
    """Main CLI entry point."""
    args = parse_args()
    
    try:
        # Load configuration
        config = get_config()
        
        # Override config with CLI arguments
        if args.log_level:
            config.log_level = args.log_level
        
        if args.provider:
            config.search_provider = args.provider
        
        logger.info(
            f"Starting research",
            extra={"context": {
                "query": args.query,
                "provider": config.search_provider,
                "user_id": args.user_id
            }}
        )
        
        # Initialize LLM
        if config.llm_provider == "openai":
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                api_key=config.openai_api_key
            )
            logger.info("Using OpenAI LLM")
        else:
            llm = ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                temperature=0.7,
                api_key=config.anthropic_api_key
            )
            logger.info("Using Anthropic LLM")
        
        # Create agent
        agent = DeepResearchAgent(
            llm=llm,
            search_provider=config.search_provider
        )
        
        # Execute research
        print(f"\n🔍 Researching: {args.query}")
        print("⏳ This may take a few minutes...\n")
        
        result = await agent.research(
            query=args.query,
            user_id=args.user_id
        )
        
        # Output results
        if args.format == "json":
            output_text = json.dumps({
                "query": result.query,
                "execution_time": result.execution_time,
                "plan": {
                    "topics": [
                        {
                            "title": topic.title,
                            "tasks": topic.tasks
                        }
                        for topic in result.plan.topics
                    ],
                    "total_tasks": result.plan.total_tasks
                } if result.plan else None,
                "text": result.text,
                "sources": [
                    {
                        "title": source.title,
                        "url": source.url,
                        "content": source.content,
                        "published_date": source.published_date,
                        "author": source.author
                    }
                    for source in result.sources
                ],
                "charts": result.charts,
                "sources_count": len(result.sources),
                "charts_count": len(result.charts)
            }, indent=2)
        else:
            # Capture text output
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                print_text_output(result)
            output_text = f.getvalue()
        
        # Write to file or stdout
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(output_text)
            print(f"\n✅ Results saved to: {output_path}")
        else:
            print(output_text)
        
        logger.info(
            f"Research completed successfully",
            extra={"context": {
                "query": args.query,
                "sources_count": len(result.sources),
                "execution_time": result.execution_time
            }}
        )
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Research interrupted by user")
        logger.info("Research interrupted by user")
        return 130
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}", file=sys.stderr)
        logger.error(f"Research failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
