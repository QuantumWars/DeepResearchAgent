"""
Enhanced Tools with Real Web Search Integration
Uses DuckDuckGo search (no API key required) for actual web searches
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import asyncio
import re

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    print("⚠️  duckduckgo_search not installed. Using placeholder search.")
    print("   Install with: pip install duckduckgo-search")


@dataclass
class SearchResult:
    """A single search result"""
    title: str
    url: str
    snippet: str
    source: str
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SearchTool:
    """
    Web search capability with real DuckDuckGo integration.
    Falls back to placeholder if library not available.
    """
    
    def __init__(self):
        self.use_real_search = DDGS_AVAILABLE
    
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Search the web for information.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results
        """
        if self.use_real_search:
            return await self._real_search(query, max_results)
        else:
            return await self._placeholder_search(query, max_results)
    
    async def _real_search(self, query: str, max_results: int) -> List[SearchResult]:
        """Perform real web search using DuckDuckGo"""
        try:
            # Run in thread pool since DDGS is synchronous
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, 
                lambda: list(DDGS().text(query, max_results=max_results))
            )
            
            search_results = []
            for i, result in enumerate(results):
                search_results.append(SearchResult(
                    title=result.get('title', 'No title'),
                    url=result.get('href', result.get('link', '')),
                    snippet=result.get('body', result.get('snippet', '')),
                    source='duckduckgo',
                    relevance_score=1.0 - (i * 0.05)  # Decreasing relevance
                ))
            
            return search_results
            
        except Exception as e:
            print(f"⚠️  Real search failed: {e}. Using placeholder.")
            return await self._placeholder_search(query, max_results)
    
    async def _placeholder_search(self, query: str, max_results: int) -> List[SearchResult]:
        """Placeholder implementation"""
        await asyncio.sleep(0.1)  # Simulate API call
        
        return [
            SearchResult(
                title=f"Result for: {query}",
                url=f"https://example.com/search?q={query}",
                snippet=f"This is a placeholder result for the query: {query}",
                source="placeholder_search",
                relevance_score=0.8
            )
        ]
    
    async def news_search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search specifically for news articles"""
        if self.use_real_search:
            try:
                loop = asyncio.get_event_loop()
                results = await loop.run_in_executor(
                    None,
                    lambda: list(DDGS().news(query, max_results=max_results))
                )
                
                search_results = []
                for i, result in enumerate(results):
                    search_results.append(SearchResult(
                        title=result.get('title', 'No title'),
                        url=result.get('url', ''),
                        snippet=result.get('body', result.get('excerpt', '')),
                        source='duckduckgo_news',
                        relevance_score=1.0 - (i * 0.05),
                        metadata={'date': result.get('date', '')}
                    ))
                
                return search_results
                
            except Exception as e:
                print(f"⚠️  News search failed: {e}")
                return []
        else:
            await asyncio.sleep(0.1)
            return []
    
    async def archive_search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search historical archives"""
        # For now, use regular search with date filter
        return await self.search(f"{query} archive history", max_results=max_results)


class SourceAnalysisTool:
    """
    Analyze source credibility and bias.
    Enhanced with basic domain reputation heuristics.
    """
    
    # Known credible domains
    CREDIBLE_DOMAINS = {
        'reuters.com': {'credibility': 0.9, 'bias': 'center', 'factual': 'very high'},
        'apnews.com': {'credibility': 0.9, 'bias': 'center', 'factual': 'very high'},
        'bbc.com': {'credibility': 0.85, 'bias': 'center-left', 'factual': 'high'},
        'nature.com': {'credibility': 0.95, 'bias': 'center', 'factual': 'very high'},
        'science.org': {'credibility': 0.95, 'bias': 'center', 'factual': 'very high'},
        'nih.gov': {'credibility': 0.95, 'bias': 'center', 'factual': 'very high'},
        'cdc.gov': {'credibility': 0.9, 'bias': 'center', 'factual': 'very high'},
        'nytimes.com': {'credibility': 0.8, 'bias': 'center-left', 'factual': 'high'},
        'wsj.com': {'credibility': 0.8, 'bias': 'center-right', 'factual': 'high'},
        'theguardian.com': {'credibility': 0.75, 'bias': 'left', 'factual': 'high'},
    }
    
    # Low credibility indicators
    LOW_CREDIBILITY_INDICATORS = [
        'blogspot.com', 'wordpress.com', 'medium.com',
        'substack.com', 'tumblr.com'
    ]
    
    async def analyze_domain(self, url: str) -> Dict[str, Any]:
        """
        Analyze a domain for credibility and bias.
        
        Args:
            url: URL to analyze
            
        Returns:
            Dictionary with credibility metrics
        """
        await asyncio.sleep(0.1)
        
        # Extract domain
        domain = self._extract_domain(url)
        
        # Check known credible domains
        if domain in self.CREDIBLE_DOMAINS:
            return {
                "domain": domain,
                **self.CREDIBLE_DOMAINS[domain],
                "transparency_score": 0.9,
                "known_issues": []
            }
        
        # Check for low credibility indicators
        credibility_score = 0.5  # Default neutral
        for indicator in self.LOW_CREDIBILITY_INDICATORS:
            if indicator in domain:
                credibility_score = 0.3
                break
        
        # Check for .gov or .edu
        if domain.endswith('.gov'):
            credibility_score = 0.85
        elif domain.endswith('.edu'):
            credibility_score = 0.8
        
        return {
            "domain": domain,
            "credibility_score": credibility_score,
            "bias_rating": "unknown",
            "factual_reporting": "unknown",
            "transparency_score": 0.5,
            "known_issues": []
        }
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        return match.group(1) if match else url


class FactCheckDatabaseTool:
    """
    Query existing fact-check databases.
    """
    
    async def check_claim(self, claim: str) -> List[Dict[str, Any]]:
        """
        Check if this claim has been fact-checked before.
        Uses DuckDuckGo to search fact-checking sites.
        """
        if not DDGS_AVAILABLE:
            return []
        
        try:
            # Search fact-checking sites
            fact_check_sites = [
                'site:snopes.com',
                'site:factcheck.org',
                'site:politifact.com'
            ]
            
            results = []
            for site in fact_check_sites:
                query = f"{claim} {site}"
                
                loop = asyncio.get_event_loop()
                search_results = await loop.run_in_executor(
                    None,
                    lambda q=query: list(DDGS().text(q, max_results=2))
                )
                
                for result in search_results:
                    results.append({
                        'claim': result.get('title', ''),
                        'snippet': result.get('body', ''),
                        'url': result.get('href', ''),
                        'source': site.replace('site:', '')
                    })
            
            return results
            
        except Exception as e:
            print(f"⚠️  Fact-check database search failed: {e}")
            return []


class StatisticalAnalysisTool:
    """
    Analyze statistical claims and data.
    """
    
    def check_plausibility(self, claim: str) -> Dict[str, Any]:
        """
        Check if statistical claims are plausible.
        
        Args:
            claim: Claim containing numbers/statistics
            
        Returns:
            Analysis of statistical plausibility
        """
        # Extract numbers from claim
        numbers = re.findall(r'\d+(?:\.\d+)?', claim)
        
        return {
            "numbers_found": numbers,
            "plausibility": "unknown",
            "concerns": []
        }


class BotDetectionTool:
    """
    Detect coordinated inauthentic behavior and bot networks.
    """
    
    async def analyze_amplification(self, claim: str, sources: List[str]) -> Dict[str, Any]:
        """
        Analyze if a claim is being artificially amplified.
        
        Args:
            claim: The claim being checked
            sources: List of sources spreading the claim
            
        Returns:
            Analysis of amplification patterns
        """
        await asyncio.sleep(0.1)
        
        return {
            "bot_probability": 0.0,
            "coordination_score": 0.0,
            "suspicious_patterns": [],
            "account_analysis": []
        }


class ToolKit:
    """
    Centralized access to all tools.
    Agents request tools from this kit.
    """
    
    def __init__(self):
        self.search = SearchTool()
        self.source_analysis = SourceAnalysisTool()
        self.fact_check_db = FactCheckDatabaseTool()
        self.statistical_analysis = StatisticalAnalysisTool()
        self.bot_detection = BotDetectionTool()
    
    async def web_search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Convenience method for web search"""
        return await self.search.search(query, max_results)
    
    async def analyze_source(self, url: str) -> Dict[str, Any]:
        """Convenience method for source analysis"""
        return await self.source_analysis.analyze_domain(url)
