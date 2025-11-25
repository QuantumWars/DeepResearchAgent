"""
Example usage of the Web Search Tool converted from TypeScript to Python

This demonstrates how to use the converted web search tool with LangChain.
"""

import asyncio
import os
from dotenv import load_dotenv

# Import our converted web search tool
from web_search_langchain import create_web_search_tool

# Load environment variables
load_dotenv()


async def basic_web_search_example():
    """Basic web search example"""
    print("=== Basic Web Search Example ===\n")

    # Create the web search tool
    web_tool = create_web_search_tool(search_provider="parallel")

    # Perform search
    result = await web_tool._arun(
        queries=[
            "latest AI developments 2025",
            "machine learning breakthroughs recent",
            "neural network improvements current"
        ],
        max_results=[8, 10, 12],
        topics=['general', 'news', 'general'],
        quality=['default', 'best', 'default']
    )

    # Display results
    for i, search in enumerate(result['searches'], 1):
        print(f"\n--- Search {i}: {search['query']} ---")
        print(f"Status: {search['status']}")
        print(f"Results: {len(search['results'])}")
        print(f"Images: {len(search['images'])}")

        for j, res in enumerate(search['results'][:3], 1):  # Show first 3 results
            print(f"\n{j}. {res['title']}")
            print(f"   URL: {res['url']}")
            print(f"   Content: {res['content'][:150]}...")


async def different_providers_example():
    """Example using different search providers"""
    print("\n\n=== Different Providers Example ===\n")

    providers = ["parallel", "tavily", "exa", "firecrawl"]
    query = "artificial intelligence trends 2025"

    for provider in providers:
        print(f"\n--- {provider.upper()} Search ---")

        try:
            # Create tool with specific provider
            web_tool = create_web_search_tool(search_provider=provider)

            # Perform search
            result = await web_tool._arun(
                queries=[query],
                max_results=[5],
                topics=['general'],
                quality=['default']
            )

            search = result['searches'][0]
            print(f"Query: {search['query']}")
            print(f"Status: {search['status']}")
            print(f"Results found: {len(search['results'])}")

            for i, res in enumerate(search['results'][:2], 1):
                print(f"\n{i}. {res['title']}")
                print(f"   Content: {res['content'][:100]}...")

        except Exception as e:
            print(f"Error with {provider}: {e}")


async def news_search_example():
    """Example focused on news search"""
    print("\n\n=== News Search Example ===\n")

    web_tool = create_web_search_tool(search_provider="tavily")

    result = await web_tool._arun(
        queries=[
            "Tesla FSD developments latest news",
            "autonomous vehicle regulations 2025",
            "self-driving car safety updates"
        ],
        max_results=[8, 8, 8],
        topics=['news', 'news', 'news'],  # Focus on news
        quality=['best', 'default', 'default']
    )

    for i, search in enumerate(result['searches'], 1):
        print(f"\n--- News Search {i}: {search['query']} ---")
        print(f"Status: {search['status']}")

        for j, res in enumerate(search['results'][:3], 1):
            print(f"\n{j}. {res['title']}")
            if res.get('published_date'):
                print(f"   Published: {res['published_date']}")
            print(f"   URL: {res['url']}")
            print(f"   Content: {res['content'][:150]}...")


async def image_search_example():
    """Example showing image search capabilities"""
    print("\n\n=== Image Search Example ===\n")

    web_tool = create_web_search_tool(search_provider="tavily")

    result = await web_tool._arun(
        queries=["AI neural network diagrams", "machine learning architecture charts"],
        max_results=[5, 5],
        topics=['general', 'general'],
        quality=['default', 'default']
    )

    for i, search in enumerate(result['searches'], 1):
        print(f"\n--- Image Search {i}: {search['query']} ---")
        print(f"Text Results: {len(search['results'])}")
        print(f"Images Found: {len(search['images'])}")

        # Show some images
        for j, img in enumerate(search['images'][:3], 1):
            print(f"\nImage {j}: {img['description']}")
            print(f"URL: {img['url']}")


async def error_handling_example():
    """Example demonstrating error handling"""
    print("\n\n=== Error Handling Example ===\n")

    # Try with invalid provider
    try:
        web_tool = create_web_search_tool(search_provider="invalid_provider")
    except ValueError as e:
        print(f"Expected error for invalid provider: {e}")

    # Try with no API keys (simulate missing environment)
    original_keys = {}
    for key in ['EXA_API_KEY', 'PARALLEL_API_KEY', 'FIRECRAWL_API_KEY', 'TAVILY_API_KEY']:
        original_keys[key] = os.getenv(key)
        os.environ[key] = "invalid_key"

    try:
        web_tool = create_web_search_tool(search_provider="parallel")
        print("Created tool (but it will fail when used)")

        # This will likely fail due to invalid API keys
        result = await web_tool._arun(
            queries=["test query"],
            max_results=[1],
            topics=['general'],
            quality=['default']
        )

        print("Search completed (unexpected with invalid keys)")

    except Exception as e:
        print(f"Expected error with invalid API keys: {e}")
    finally:
        # Restore original keys
        for key, value in original_keys.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def setup_environment():
    """Setup environment variables check"""
    print("=== Environment Setup Check ===\n")

    required_keys = [
        'EXA_API_KEY',
        'PARALLEL_API_KEY',
        'FIRECRAWL_API_KEY',
        'TAVILY_API_KEY'
    ]

    missing_keys = []
    for key in required_keys:
        value = os.getenv(key)
        if not value:
            missing_keys.append(key)
        else:
            print(f"✓ {key}: {'*' * 8}{value[-4:] if len(value) > 4 else ''}")

    if missing_keys:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_keys)}")
        print("Please set these in your .env file or environment")
        return False
    else:
        print(f"\n✅ All required API keys are configured!")
        return True


async def main():
    """Main function to run all examples"""
    print("Web Search Tool - Python/LangChain Implementation")
    print("=" * 60)

    # Check environment setup
    if not setup_environment():
        print("\nSome examples may fail due to missing API keys.")

    try:
        # Run examples
        await basic_web_search_example()
        # await different_providers_example()
        # await news_search_example()
        # await image_search_example()
        # await error_handling_example()

        print("\n\n=== All Examples Completed ===")

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())