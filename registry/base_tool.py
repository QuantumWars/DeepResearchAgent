"""Abstract base classes for all tool types."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Type, Union
from pydantic import BaseModel

from models.tool_schemas import SearchResult, ScrapedContent


class ModelType(Enum):
    """Enum for LLM model complexity types."""
    FAST = "fast"
    BALANCED = "balanced"
    POWERFUL = "powerful"


class BaseSearchTool(ABC):
    """Abstract base class for search tools."""
    
    name: str
    priority: int
    requires_api_key: bool
    
    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        Execute search and return results.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        pass


class BaseScraperTool(ABC):
    """Abstract base class for web scraping tools."""
    
    name: str
    priority: int
    
    @abstractmethod
    def scrape(self, url: str) -> ScrapedContent:
        """
        Extract content from URL.
        
        Args:
            url: URL to scrape
            
        Returns:
            ScrapedContent object with extracted content
        """
        pass


class BaseLLMTool(ABC):
    """Abstract base class for LLM tools."""
    
    name: str
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        model_type: ModelType,
        structured_output_schema: Optional[Type[BaseModel]] = None
    ) -> Union[str, BaseModel]:
        """
        Generate text or structured output.
        
        Args:
            prompt: Input prompt for the LLM
            model_type: Type of model to use (fast/balanced/powerful)
            structured_output_schema: Optional Pydantic schema for structured output
            
        Returns:
            Generated text string or Pydantic model instance if schema provided
        """
        pass


class BaseCustomTool(ABC):
    """Abstract base class for custom user-defined tools."""
    
    name: str
    description: str
    
    @abstractmethod
    def execute(self, input_data: Dict) -> Dict:
        """
        Execute custom logic.
        
        Args:
            input_data: Dictionary containing input parameters
            
        Returns:
            Dictionary containing execution results
        """
        pass
