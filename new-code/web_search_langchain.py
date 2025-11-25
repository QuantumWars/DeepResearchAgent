"""
Web Search Tool in Python using LangChain
Converted from TypeScript web-search.ts

Requirements:
pip install langchain langchain-openai exa-python parallel-firecrawl tavily-python firecrawl-py
"""

import asyncio
import re
import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
from urllib.parse import urlparse
from dataclasses import dataclass

# LangChain imports
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from langchain.callbacks import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun

# Search provider imports
import exa
from parallel import Parallel
from tavily import TavilyClient
from firecrawl import FirecrawlApp


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class SearchResult:
    """Single search result"""
    url: str
    title: str
    content: str
    published_date: Optional[str] = None
    author: Optional[str] = None


@dataclass
class ImageResult:
    """Single image result"""
    url: str
    description: str


@dataclass
class SearchResponse:
    """Complete search response"""
    query: str
    results: List[SearchResult]
    images: List[ImageResult]
    status: str = "completed"


# ============================================================================
# Helper Functions (Python equivalents of TypeScript helpers)
# ============================================================================

def extract_domain(url: Optional[str]) -> str:
    """Extract domain from URL"""
    if not url or not isinstance(url, str):
        return ""

    try:
        parsed = urlparse(url)
        return parsed.netloc or url
    except:
        return url


def clean_title(title: str) -> str:
    """Clean title by removing brackets and extra whitespace"""
    if not isinstance(title, str):
        return ""

    # Remove content within square brackets and parentheses
    title = re.sub(r'\[.*?\]', '', title)
    title = re.sub(r'\(.*?\)', '', title)
    # Replace multiple spaces with single space and trim
    title = re.sub(r'\s+', ' ', title).strip()
    return title


def deduplicate_by_domain_and_url(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicates by domain and URL"""
    seen_domains = set()
    seen_urls = set()
    filtered_items = []

    for item in items:
        if 'url' not in item:
            continue

        domain = extract_domain(item['url'])
        is_new_url = item['url'] not in seen_urls
        is_new_domain = domain not in seen_domains

        if is_new_url and is_new_domain:
            seen_urls.add(item['url'])
            seen_domains.add(domain)
            filtered_items.append(item)

    return filtered_items


def sanitize_url(url: str) -> str:
    """Sanitize URL by parsing and reconstructing"""
    try:
        parsed = urlparse(url)
        return parsed.geturl()
    except:
        return url


async def is_valid_image_url(url: str) -> Tuple[bool, Optional[str]]:
    """Validate image URL (simplified version)"""
    # For now, just return valid - can add more sophisticated validation later
    return True, url


# ============================================================================
# Search Strategy Interface
# ============================================================================

class SearchStrategy(ABC):
    """Abstract base class for search strategies"""

    @abstractmethod
    async def search(
        self,
        queries: List[str],
        options: Dict[str, Any],
        data_stream: Optional[Any] = None
    ) -> List[SearchResponse]:
        """Execute search for multiple queries"""
        pass


# ============================================================================
# Parallel AI Search Strategy
# ============================================================================

class ParallelSearchStrategy(SearchStrategy):
    """Parallel AI search implementation"""

    def __init__(self, parallel_client: Parallel, firecrawl_client: FirecrawlApp):
        self.parallel = parallel_client
        self.firecrawl = firecrawl_client

    async def search(
        self,
        queries: List[str],
        options: Dict[str, Any],
        data_stream: Optional[Any] = None
    ) -> List[SearchResponse]:
        """Search using Parallel AI with Firecrawl for images"""

        # Limit queries to first 5 (as in original)
        limited_queries = queries[:5]
        print(f"Using Parallel AI batch processing for queries: {limited_queries}")

        # Send start notifications
        for i, query in enumerate(limited_queries):
            if data_stream:
                await self._send_stream_update(
                    data_stream, query, i, len(limited_queries), "started"
                )

        try:
            # Process queries concurrently
            tasks = []
            for i, query in enumerate(limited_queries):
                task = self._process_query(query, i, options, data_stream)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions and return valid results
            valid_results = []
            for result in results:
                if isinstance(result, SearchResponse):
                    valid_results.append(result)
                else:
                    print(f"Error in search result: {result}")

            return valid_results

        except Exception as e:
            print(f"Parallel AI batch orchestration error: {e}")

            # Send error notifications
            for i, query in enumerate(limited_queries):
                if data_stream:
                    await self._send_stream_update(
                        data_stream, query, i, len(limited_queries), "error"
                    )

            return [SearchResponse(query=q, results=[], images=[], status="error")
                   for q in limited_queries]

    async def _process_query(
        self,
        query: str,
        index: int,
        options: Dict[str, Any],
        data_stream: Optional[Any]
    ) -> SearchResponse:
        """Process individual query"""
        current_quality = options.get('quality', ['default'])
        current_quality = current_quality[index] if index < len(current_quality) else current_quality[0]
        current_max_results = options.get('maxResults', [10])
        current_max_results = current_max_results[index] if index < len(current_max_results) else current_max_results[0]

        try:
            # Run Parallel AI search and Firecrawl images concurrently
            parallel_task = self._parallel_search(query, current_quality, current_max_results)
            images_task = self._firecrawl_images_search(query)

            single_response, firecrawl_images = await asyncio.gather(
                parallel_task, images_task, return_exceptions=True
            )

            # Process results
            results = []
            if single_response and hasattr(single_response, 'results'):
                for result in single_response.results:
                    content = ""
                    if hasattr(result, 'excerpts') and result.excerpts:
                        content = " ".join(result.excerpts)[:1000]
                    elif hasattr(result, 'content'):
                        content = str(result.content)[:1000]

                    results.append(SearchResult(
                        url=getattr(result, 'url', ''),
                        title=clean_title(getattr(result, 'title', '')),
                        content=content
                    ))

            # Process images
            images = []
            if firecrawl_images and hasattr(firecrawl_images, 'images'):
                for item in firecrawl_images.images:
                    if hasattr(item, 'url') or hasattr(item, 'imageUrl'):
                        img_url = getattr(item, 'imageUrl', None) or getattr(item, 'url', '')
                        if img_url:
                            images.append(ImageResult(
                                url=img_url,
                                description=clean_title(getattr(item, 'title', ''))
                            ))

            # Send completion notification
            if data_stream:
                await self._send_stream_update(
                    data_stream, query, index, len(options.get('queries', [])), "completed",
                    len(results), len(images)
                )

            return SearchResponse(
                query=query,
                results=self._deduplicate_results([r.__dict__ for r in results]),
                images=self._deduplicate_images([i.__dict__ for i in images]),
                status="completed"
            )

        except Exception as e:
            print(f"Parallel AI search error for query '{query}': {e}")

            if data_stream:
                await self._send_stream_update(
                    data_stream, query, index, len(options.get('queries', [])), "error"
                )

            return SearchResponse(query=query, results=[], images=[], status="error")

    async def _parallel_search(self, query: str, quality: str, max_results: int):
        """Execute Parallel AI search"""
        processor = "pro" if quality == "best" else "base"
        return await self.parallel.beta.search(
            objective=query,
            search_queries=[query],
            processor=processor,
            max_results=max(max_results, 10),
            max_chars_per_result=1000,
        )

    async def _firecrawl_images_search(self, query: str):
        """Search for images using Firecrawl"""
        try:
            return await self.firecrawl.search(
                query,
                sources=["images"],
                limit=3
            )
        except Exception as e:
            print(f"Firecrawl error for query '{query}': {e}")
            return type('MockResponse', (), {'images': []})()

    def _deduplicate_results(self, results: List[Dict]) -> List[SearchResult]:
        """Deduplicate search results"""
        deduped = deduplicate_by_domain_and_url(results)
        return [SearchResult(**r) for r in deduped]

    def _deduplicate_images(self, images: List[Dict]) -> List[ImageResult]:
        """Deduplicate image results"""
        deduped = deduplicate_by_domain_and_url(images)
        return [ImageResult(**i) for i in deduped if i.get('url')]

    async def _send_stream_update(
        self,
        data_stream: Any,
        query: str,
        index: int,
        total: int,
        status: str,
        results_count: int = 0,
        images_count: int = 0
    ):
        """Send progress update via data stream"""
        if hasattr(data_stream, 'write'):
            try:
                await data_stream.write({
                    'type': 'data-query_completion',
                    'data': {
                        'query': query,
                        'index': index,
                        'total': total,
                        'status': status,
                        'resultsCount': results_count,
                        'imagesCount': images_count,
                    }
                })
            except Exception as e:
                print(f"Error sending stream update: {e}")


# ============================================================================
# Tavily Search Strategy
# ============================================================================

class TavilySearchStrategy(SearchStrategy):
    """Tavily search implementation"""

    def __init__(self, tavily_client: TavilyClient):
        self.tavily = tavily_client

    async def search(
        self,
        queries: List[str],
        options: Dict[str, Any],
        data_stream: Optional[Any] = None
    ) -> List[SearchResponse]:
        """Search using Tavily"""

        tasks = []
        for i, query in enumerate(queries):
            task = self._process_query(query, i, options, data_stream)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, SearchResponse):
                valid_results.append(result)

        return valid_results

    async def _process_query(
        self,
        query: str,
        index: int,
        options: Dict[str, Any],
        data_stream: Optional[Any]
    ) -> SearchResponse:
        """Process individual query with Tavily"""

        current_topic = options.get('topics', ['general'])
        current_topic = current_topic[index] if index < len(current_topic) else current_topic[0]
        current_max_results = options.get('maxResults', [10])
        current_max_results = current_max_results[index] if index < len(current_max_results) else current_max_results[0]
        current_quality = options.get('quality', ['default'])
        current_quality = current_quality[index] if index < len(current_quality) else current_quality[0]

        try:
            # Send start notification
            if data_stream:
                await self._send_stream_update(
                    data_stream, query, index, len(options.get('queries', [])), "started"
                )

            # Execute Tavily search
            search_params = {
                'topic': current_topic or 'general',
                'max_results': current_max_results,
                'search_depth': 'advanced' if current_quality == 'best' else 'basic',
                'include_answer': True,
                'include_images': True,
                'include_image_descriptions': True,
            }

            if current_topic == 'news':
                search_params['days'] = 7

            tavily_data = self.tavily.search(query, **search_params)

            # Process results
            results = []
            if 'results' in tavily_data:
                deduped_results = deduplicate_by_domain_and_url(tavily_data['results'])
                for obj in deduped_results:
                    published_date = obj.get('published_date') if current_topic == 'news' else None
                    results.append(SearchResult(
                        url=obj.get('url', ''),
                        title=clean_title(obj.get('title', '')),
                        content=obj.get('content', ''),
                        published_date=published_date
                    ))

            # Process images
            images = []
            if 'images' in tavily_data:
                deduped_images = deduplicate_by_domain_and_url(tavily_data['images'])
                for img_data in deduped_images:
                    url = sanitize_url(img_data.get('url', ''))
                    is_valid, redirected_url = await is_valid_image_url(url)

                    if is_valid and img_data.get('description'):
                        images.append(ImageResult(
                            url=redirected_url or url,
                            description=img_data.get('description', '')
                        ))

            # Send completion notification
            if data_stream:
                await self._send_stream_update(
                    data_stream, query, index, len(options.get('queries', [])), "completed",
                    len(results), len(images)
                )

            return SearchResponse(
                query=query,
                results=results,
                images=images,
                status="completed"
            )

        except Exception as e:
            print(f"Tavily search error for query '{query}': {e}")

            if data_stream:
                await self._send_stream_update(
                    data_stream, query, index, len(options.get('queries', [])), "error"
                )

            return SearchResponse(query=query, results=[], images=[], status="error")

    async def _send_stream_update(
        self,
        data_stream: Any,
        query: str,
        index: int,
        total: int,
        status: str,
        results_count: int = 0,
        images_count: int = 0
    ):
        """Send progress update via data stream"""
        if hasattr(data_stream, 'write'):
            try:
                await data_stream.write({
                    'type': 'data-query_completion',
                    'data': {
                        'query': query,
                        'index': index,
                        'total': total,
                        'status': status,
                        'resultsCount': results_count,
                        'imagesCount': images_count,
                    }
                })
            except Exception as e:
                print(f"Error sending stream update: {e}")


# ============================================================================
# Firecrawl Search Strategy
# ============================================================================

class FirecrawlSearchStrategy(SearchStrategy):
    """Firecrawl search implementation"""

    def __init__(self, firecrawl_client: FirecrawlApp):
        self.firecrawl = firecrawl_client

    async def search(
        self,
        queries: List[str],
        options: Dict[str, Any],
        data_stream: Optional[Any] = None
    ) -> List[SearchResponse]:
        """Search using Firecrawl"""

        tasks = []
        for i, query in enumerate(queries):
            task = self._process_query(query, i, options, data_stream)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, SearchResponse):
                valid_results.append(result)

        return valid_results

    async def _process_query(
        self,
        query: str,
        index: int,
        options: Dict[str, Any],
        data_stream: Optional[Any]
    ) -> SearchResponse:
        """Process individual query with Firecrawl"""

        current_topic = options.get('topics', ['general'])
        current_topic = current_topic[index] if index < len(current_topic) else current_topic[0]
        current_max_results = options.get('maxResults', [10])
        current_max_results = current_max_results[index] if index < len(current_max_results) else current_max_results[0]

        try:
            # Send start notification
            if data_stream:
                await self._send_stream_update(
                    data_stream, query, index, len(options.get('queries', [])), "started"
                )

            # Map topics to Firecrawl sources
            sources = ['web']
            if current_topic == 'news':
                sources.append('news')
            sources.append('images')  # Always include images

            # Execute Firecrawl search
            firecrawl_data = self.firecrawl.search(
                query,
                sources=sources,
                limit=current_max_results
            )

            results = []

            # Process web results
            if hasattr(firecrawl_data, 'web') and firecrawl_data.web:
                web_results = [r for r in firecrawl_data.web if hasattr(r, 'url')]
                deduped_results = deduplicate_by_domain_and_url(
                    [{'url': r.url, 'title': getattr(r, 'title', ''), 'description': getattr(r, 'description', '')}
                     for r in web_results]
                )
                for result in deduped_results:
                    results.append(SearchResult(
                        url=result['url'],
                        title=clean_title(result['title']),
                        content=result['description']
                    ))

            # Process news results
            if (current_topic == 'news' and
                hasattr(firecrawl_data, 'news') and firecrawl_data.news):
                news_results = [r for r in firecrawl_data.news
                               if hasattr(r, 'url') and r.url]
                deduped_news = deduplicate_by_domain_and_url(
                    [{'url': r.url, 'title': getattr(r, 'title', ''), 'snippet': getattr(r, 'snippet', ''),
                      'date': getattr(r, 'date', None)} for r in news_results]
                )

                # Create news result objects
                news_search_results = []
                for result in deduped_news:
                    news_search_results.append(SearchResult(
                        url=result['url'],
                        title=clean_title(result['title']),
                        content=result['snippet'],
                        published_date=result.get('date')
                    ))

                # Combine news and web results, prioritizing news
                results = news_search_results + results

            # Process images
            images = []
            if hasattr(firecrawl_data, 'images') and firecrawl_data.images:
                image_results = [r for r in firecrawl_data.images
                               if hasattr(r, 'url') or hasattr(r, 'imageUrl')]
                processed_images = []
                for image in image_results:
                    img_url = getattr(image, 'imageUrl', None) or getattr(image, 'url', '')
                    if img_url:
                        processed_images.append({
                            'url': img_url,
                            'title': getattr(image, 'title', '')
                        })

                deduped_images = deduplicate_by_domain_and_url(processed_images)
                for img in deduped_images:
                    if img['url']:
                        images.append(ImageResult(
                            url=img['url'],
                            description=clean_title(img['title'])
                        ))

            # Send completion notification
            if data_stream:
                await self._send_stream_update(
                    data_stream, query, index, len(options.get('queries', [])), "completed",
                    len(results), len(images)
                )

            return SearchResponse(
                query=query,
                results=results,
                images=images,
                status="completed"
            )

        except Exception as e:
            print(f"Firecrawl search error for query '{query}': {e}")

            if data_stream:
                await self._send_stream_update(
                    data_stream, query, index, len(options.get('queries', [])), "error"
                )

            return SearchResponse(query=query, results=[], images=[], status="error")

    async def _send_stream_update(
        self,
        data_stream: Any,
        query: str,
        index: int,
        total: int,
        status: str,
        results_count: int = 0,
        images_count: int = 0
    ):
        """Send progress update via data stream"""
        if hasattr(data_stream, 'write'):
            try:
                await data_stream.write({
                    'type': 'data-query_completion',
                    'data': {
                        'query': query,
                        'index': index,
                        'total': total,
                        'status': status,
                        'resultsCount': results_count,
                        'imagesCount': images_count,
                    }
                })
            except Exception as e:
                print(f"Error sending stream update: {e}")


# ============================================================================
# Exa Search Strategy
# ============================================================================

class ExaSearchStrategy(SearchStrategy):
    """Exa search implementation"""

    def __init__(self, exa_client: exa.Exa):
        self.exa = exa_client

    async def search(
        self,
        queries: List[str],
        options: Dict[str, Any],
        data_stream: Optional[Any] = None
    ) -> List[SearchResponse]:
        """Search using Exa"""

        tasks = []
        for i, query in enumerate(queries):
            task = self._process_query(query, i, options, data_stream)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, SearchResponse):
                valid_results.append(result)

        return valid_results

    async def _process_query(
        self,
        query: str,
        index: int,
        options: Dict[str, Any],
        data_stream: Optional[Any]
    ) -> SearchResponse:
        """Process individual query with Exa"""

        current_topic = options.get('topics', ['general'])
        current_topic = current_topic[index] if index < len(current_topic) else current_topic[0]
        current_max_results = options.get('maxResults', [10])
        current_max_results = current_max_results[index] if index < len(current_max_results) else current_max_results[0]
        current_quality = options.get('quality', ['default'])
        current_quality = current_quality[index] if index < len(current_quality) else current_quality[0]

        try:
            # Send start notification
            if data_stream:
                await self._send_stream_update(
                    data_stream, query, index, len(options.get('queries', [])), "started"
                )

            # Configure search options
            search_options = {
                'text': True,
                'numResults': max(current_max_results, 10),
                'livecrawl': 'preferred',
                'useAutoprompt': True,
            }

            if current_quality == 'best':
                search_options['type'] = 'hybrid'
            else:
                search_options['type'] = 'auto'

            if current_topic == 'news':
                search_options['category'] = 'news'

            # Execute Exa search
            data = self.exa.search_and_contents(query, **search_options)

            # Collect images and process results
            collected_images = []
            results = []

            for result in data.results:
                # Collect images
                if hasattr(result, 'image') and result.image:
                    collected_images.append({
                        'url': result.image,
                        'description': clean_title(
                            (getattr(result, 'title', '') or
                             (getattr(result, 'text', '')[:100] + '...' if hasattr(result, 'text') else ''))
                        )
                    })

                # Process main result
                content = getattr(result, 'text', '')[:1000] if hasattr(result, 'text') else ''
                published_date = None
                if (current_topic == 'news' and
                    hasattr(result, 'publishedDate') and
                    result.publishedDate):
                    published_date = result.publishedDate

                results.append(SearchResult(
                    url=getattr(result, 'url', ''),
                    title=clean_title(getattr(result, 'title', '')),
                    content=content,
                    published_date=published_date,
                    author=getattr(result, 'author', None)
                ))

            # Deduplicate images
            images = []
            deduped_images = deduplicate_by_domain_and_url(collected_images)
            for img in deduped_images:
                if img.get('url'):
                    images.append(ImageResult(
                        url=img['url'],
                        description=img['description']
                    ))

            # Send completion notification
            if data_stream:
                await self._send_stream_update(
                    data_stream, query, index, len(options.get('queries', [])), "completed",
                    len(results), len(images)
                )

            return SearchResponse(
                query=query,
                results=results,
                images=images,
                status="completed"
            )

        except Exception as e:
            print(f"Exa search error for query '{query}': {e}")

            if data_stream:
                await self._send_stream_update(
                    data_stream, query, index, len(options.get('queries', [])), "error"
                )

            return SearchResponse(query=query, results=[], images=[], status="error")

    async def _send_stream_update(
        self,
        data_stream: Any,
        query: str,
        index: int,
        total: int,
        status: str,
        results_count: int = 0,
        images_count: int = 0
    ):
        """Send progress update via data stream"""
        if hasattr(data_stream, 'write'):
            try:
                await data_stream.write({
                    'type': 'data-query_completion',
                    'data': {
                        'query': query,
                        'index': index,
                        'total': total,
                        'status': status,
                        'resultsCount': results_count,
                        'imagesCount': images_count,
                    }
                })
            except Exception as e:
                print(f"Error sending stream update: {e}")


# ============================================================================
# Search Strategy Factory
# ============================================================================

def create_search_strategy(
    provider: str,
    clients: Dict[str, Any]
) -> SearchStrategy:
    """Create search strategy instance"""

    strategies = {
        'parallel': lambda: ParallelSearchStrategy(clients['parallel'], clients['firecrawl']),
        'tavily': lambda: TavilySearchStrategy(clients['tavily']),
        'firecrawl': lambda: FirecrawlSearchStrategy(clients['firecrawl']),
        'exa': lambda: ExaSearchStrategy(clients['exa']),
    }

    if provider not in strategies:
        raise ValueError(f"Unknown search provider: {provider}")

    return strategies[provider]()


# ============================================================================
# LangChain Web Search Tool
# ============================================================================

class WebSearchInput(BaseModel):
    """Input schema for web search tool"""
    queries: List[str] = Field(
        description="Array of 3-5 search queries to look up on the web. Default is 5. Minimum is 3.",
        min_items=3
    )
    max_results: Optional[List[int]] = Field(
        description="Array of maximum number of results to return per query. Default is 10. Minimum is 8. Maximum is 15.",
        default=None
    )
    topics: Optional[List[str]] = Field(
        description="Array of topic types to search for. Default is general. Other options are news.",
        default=None
    )
    quality: Optional[List[str]] = Field(
        description="Array of quality levels for the search. Default is default. Other option is best.",
        default=None
    )


class WebSearchTool(BaseTool):
    """Web search tool using multiple providers"""

    name = "web_search"
    description = """Search the web for information with multiple queries, max results, search depth, topics, and quality.

    Very important Rules:
    - The queries should always be in the same language as the user's message
    - Count of queries should be 3-5
    - Do not use best quality unless absolutely required since it is time expensive
    - CRITICAL: ALWAYS include date/time context in search queries:
      * For current events: "latest", "2025", "today", "current", "recent"
      * For historical info: specific years or date ranges
      * For time-sensitive topics: "newest", "updated", "2025"
      * NO TEMPORAL ASSUMPTIONS: Never assume time periods - always be explicit about dates/years
      * Examples: "latest AI news 2025", "current stock prices today", "recent developments in 2025"
    """

    args_schema = WebSearchInput

    def __init__(
        self,
        data_stream: Optional[Any] = None,
        search_provider: str = "parallel",
        **kwargs
    ):
        """Initialize web search tool"""
        super().__init__(**kwargs)
        self.data_stream = data_stream
        self.search_provider = search_provider
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize search provider clients"""

        # Get API keys from environment variables
        exa_api_key = os.getenv('EXA_API_KEY')
        parallel_api_key = os.getenv('PARALLEL_API_KEY')
        firecrawl_api_key = os.getenv('FIRECRAWL_API_KEY')
        tavily_api_key = os.getenv('TAVILY_API_KEY')

        if not all([exa_api_key, parallel_api_key, firecrawl_api_key, tavily_api_key]):
            raise ValueError("Missing required API keys in environment variables")

        # Initialize clients
        self.clients = {
            'exa': exa.Exa(api_key=exa_api_key),
            'parallel': Parallel(api_key=parallel_api_key),
            'firecrawl': FirecrawlApp(api_key=firecrawl_api_key),
            'tavily': TavilyClient(api_key=tavily_api_key),
        }

        # Create search strategy
        self.strategy = create_search_strategy(self.search_provider, self.clients)

    def _run(
        self,
        queries: List[str],
        max_results: Optional[List[int]] = None,
        topics: Optional[List[str]] = None,
        quality: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """Run web search synchronously"""

        # For synchronous execution, run the async version in an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(queries, max_results, topics, quality, run_manager)
            )
        finally:
            loop.close()

    async def _arun(
        self,
        queries: List[str],
        max_results: Optional[List[int]] = None,
        topics: Optional[List[str]] = None,
        quality: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """Run web search asynchronously"""

        print(f"Queries: {queries}")
        print(f"Max Results: {max_results}")
        print(f"Topics: {topics}")
        print(f"Quality: {quality}")
        print(f"Search Provider: {self.search_provider}")

        # Set defaults
        if not max_results:
            max_results = [10] * len(queries)
        if not topics:
            topics = ['general'] * len(queries)
        if not quality:
            quality = ['default'] * len(queries)

        # Prepare options
        options = {
            'queries': queries,
            'maxResults': max_results,
            'topics': topics,
            'quality': quality,
        }

        # Execute search
        try:
            results = await self.strategy.search(
                queries, options, self.data_stream
            )

            # Convert results to dictionary format
            searches = []
            for result in results:
                searches.append({
                    'query': result.query,
                    'results': [
                        {
                            'url': r.url,
                            'title': r.title,
                            'content': r.content,
                            'published_date': r.published_date,
                            'author': r.author,
                        }
                        for r in result.results
                    ],
                    'images': [
                        {
                            'url': i.url,
                            'description': i.description,
                        }
                        for i in result.images
                    ],
                    'status': result.status,
                })

            return {'searches': searches}

        except Exception as e:
            print(f"Search execution error: {e}")
            # Return error results
            searches = []
            for query in queries:
                searches.append({
                    'query': query,
                    'results': [],
                    'images': [],
                    'status': 'error',
                })

            return {'searches': searches}


# ============================================================================
# Convenience Functions
# ============================================================================

def create_web_search_tool(
    data_stream: Optional[Any] = None,
    search_provider: str = "parallel"
) -> WebSearchTool:
    """Create and return a web search tool instance"""
    return WebSearchTool(data_stream=data_stream, search_provider=search_provider)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example of how to use the web search tool

    async def example_usage():
        """Example of using the web search tool"""

        # Create the tool
        tool = create_web_search_tool(search_provider="parallel")

        # Execute search
        result = await tool._arun(
            queries=[
                "latest AI developments 2025",
                "machine learning breakthroughs recent",
                "neural network improvements current"
            ],
            max_results=[8, 10, 12],
            topics=['general', 'news', 'general'],
            quality=['default', 'best', 'default']
        )

        print("Search Results:")
        print(json.dumps(result, indent=2))

    # Run example
    asyncio.run(example_usage())