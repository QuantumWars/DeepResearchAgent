#!/usr/bin/env python3
"""
Deep Research Framework - Main Entry Point

This module provides the command-line interface for the Deep Research Framework.
"""

import argparse
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging for the application.
    
    Sets up structured logging with consistent formatting across all components.
    
    Args:
        verbose: If True, sets log level to DEBUG for detailed output.
                 If False, sets log level to INFO for standard output.
    
    Example:
        >>> setup_logging(verbose=True)  # Enable debug logging
        >>> setup_logging(verbose=False) # Standard logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main() -> int:
    """
    Main entry point for the Deep Research Framework CLI.
    
    Parses command-line arguments, initializes the research orchestrator,
    executes the research workflow, and displays/saves results.
    
    Returns:
        Exit code: 0 for success, 1 for failure
    
    Command-line Arguments:
        query: Research question to investigate (required)
        --config: Path to tool configuration file (default: config/tool_config.yaml)
        --max-loops: Maximum research iterations (default: 3)
        --output: Output file path for report (optional)
        --verbose: Enable debug logging (optional)
    
    Examples:
        $ python main.py "What is quantum computing?"
        $ python main.py "Climate change" --max-loops 5 --output report.md
        $ python main.py "AI safety" --config custom.yaml --verbose
    """
    parser = argparse.ArgumentParser(
        description='Deep Research Framework - AI-powered research assistant',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        python main.py "What is quantum computing?"
        python main.py "Explain climate change" --max-loops 5 --output report.md
        python main.py "AI safety research" --config custom_config.yaml --verbose
                """
    )
    
    parser.add_argument(
        'query',
        type=str,
        help='Research query to investigate'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/tool_config.yaml',
        help='Path to tool configuration file (default: config/tool_config.yaml)'
    )
    
    parser.add_argument(
        '--max-loops',
        type=int,
        default=3,
        help='Maximum number of research iterations (default: 3)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path for the research report (optional)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Import here to avoid loading heavy dependencies if just showing help
        from core.orchestrator import ResearchOrchestrator
        
        logger.info(f"Starting research for query: {args.query}")
        logger.info(f"Configuration: {args.config}")
        logger.info(f"Max loops: {args.max_loops}")
        
        # Initialize orchestrator
        orchestrator = ResearchOrchestrator(config_path=args.config)
        
        # Execute research
        result = orchestrator.research(
            query=args.query,
            max_loops=args.max_loops
        )
        
        # Display results
        print("\n" + "="*80)
        print("RESEARCH REPORT")
        print("="*80 + "\n")
        print(result.report)
        print("\n" + "="*80)
        print(f"Sources: {len(result.sources)}")
        print(f"Tool calls: {len(result.execution_log)}")
        print("="*80 + "\n")
        
        # Save to file if requested
        if args.output:
            output_path = Path(args.output)
            result.save(str(output_path))
            logger.info(f"Report saved to: {output_path}")
        
        logger.info("Research completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        return 1
    except ImportError as e:
        logger.error(f"Missing dependencies: {e}")
        logger.error("Please install requirements: pip install -r requirements.txt")
        return 1
    except Exception as e:
        logger.error(f"Research failed: {e}", exc_info=args.verbose)
        return 1


if __name__ == '__main__':
    sys.exit(main())
