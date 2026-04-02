"""
Example custom tool implementation demonstrating the extension pattern.

This module shows how to create a custom tool by inheriting from BaseCustomTool.
Custom tools can be used to add domain-specific functionality to the research framework.
"""

import logging
from typing import Dict
from registry.base_tool import BaseCustomTool

logger = logging.getLogger(__name__)


class PDFExtractor(BaseCustomTool):
    """
    Custom tool for extracting text content from PDF files.
    
    This example demonstrates:
    1. Inheriting from BaseCustomTool
    2. Implementing the required execute() method
    3. Proper error handling and logging
    4. Returning structured results
    
    Extension Pattern:
    ------------------
    To create your own custom tool:
    1. Create a new class inheriting from BaseCustomTool
    2. Set the 'name' and 'description' class attributes
    3. Implement the execute(input_data: Dict) -> Dict method
    4. Handle errors gracefully and return success/failure status
    5. Add logging for debugging and monitoring
    """
    
    # Required class attributes
    name = "pdf_extractor"
    description = "Extracts text content from PDF files via URL or file path"
    
    def __init__(self, max_pages: int = 50):
        """
        Initialize the PDF extractor.
        
        Args:
            max_pages: Maximum number of pages to extract (prevents memory issues)
        """
        self.max_pages = max_pages
        logger.info(f"Initialized {self.name} with max_pages={max_pages}")
    
    def execute(self, input_data: Dict) -> Dict:
        """
        Extract text from a PDF file.
        
        Args:
            input_data: Dictionary containing:
                - 'url' (str): URL to PDF file, OR
                - 'file_path' (str): Local path to PDF file
                - 'extract_metadata' (bool, optional): Whether to extract metadata
        
        Returns:
            Dictionary containing:
                - 'success' (bool): Whether extraction succeeded
                - 'content' (str): Extracted text content (if successful)
                - 'metadata' (dict): PDF metadata like author, title (if requested)
                - 'error' (str): Error message (if failed)
                - 'pages_extracted' (int): Number of pages processed
        
        Example:
            >>> extractor = PDFExtractor()
            >>> result = extractor.execute({
            ...     'url': 'https://example.com/paper.pdf',
            ...     'extract_metadata': True
            ... })
            >>> if result['success']:
            ...     print(result['content'])
        """
        try:
            # Validate input
            url = input_data.get('url')
            file_path = input_data.get('file_path')
            extract_metadata = input_data.get('extract_metadata', False)
            
            if not url and not file_path:
                return {
                    'success': False,
                    'error': 'Either url or file_path must be provided',
                    'content': '',
                    'pages_extracted': 0
                }
            
            # Log the operation
            source = url or file_path
            logger.info(f"Extracting PDF from: {source}")
            
            # Simulate PDF extraction (in real implementation, use PyPDF2 or pdfplumber)
            # This is a placeholder showing the pattern
            content = self._extract_pdf_content(url, file_path)
            metadata = self._extract_metadata(url, file_path) if extract_metadata else {}
            
            # Return success result
            result = {
                'success': True,
                'content': content,
                'pages_extracted': min(10, self.max_pages),  # Simulated
                'metadata': metadata
            }
            
            logger.info(f"Successfully extracted {result['pages_extracted']} pages")
            return result
            
        except Exception as e:
            # Handle errors gracefully - never let exceptions propagate
            error_msg = f"PDF extraction failed: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'content': '',
                'pages_extracted': 0
            }
    
    def _extract_pdf_content(self, url: str = None, file_path: str = None) -> str:
        """
        Internal method to extract PDF content.
        
        In a real implementation, this would:
        1. Download PDF from URL or read from file_path
        2. Use PyPDF2, pdfplumber, or similar library
        3. Extract text from each page
        4. Clean and format the text
        
        Args:
            url: URL to PDF file
            file_path: Local path to PDF file
            
        Returns:
            Extracted text content
        """
        # Placeholder implementation
        # Real implementation would use:
        # import PyPDF2
        # or
        # import pdfplumber
        
        return f"""
        [Simulated PDF Content]
        
        This is placeholder text demonstrating the PDF extraction pattern.
        In a real implementation, this would contain the actual extracted text
        from the PDF file at {url or file_path}.
        
        The extraction would handle:
        - Multiple pages (up to {self.max_pages})
        - Text formatting and cleanup
        - Tables and structured content
        - Handling of scanned PDFs with OCR if needed
        """
    
    def _extract_metadata(self, url: str = None, file_path: str = None) -> Dict:
        """
        Extract metadata from PDF.
        
        Args:
            url: URL to PDF file
            file_path: Local path to PDF file
            
        Returns:
            Dictionary with metadata fields
        """
        # Placeholder implementation
        return {
            'title': 'Example PDF Document',
            'author': 'Unknown',
            'pages': min(10, self.max_pages),
            'source': url or file_path
        }


class ArXivSearchTool(BaseCustomTool):
    """
    Another example custom tool for searching academic papers on arXiv.
    
    This demonstrates how multiple custom tools can coexist and be used
    for specialized research tasks.
    """
    
    name = "arxiv_search"
    description = "Searches arXiv for academic papers and returns metadata"
    
    def __init__(self, max_results: int = 10):
        """Initialize arXiv search tool."""
        self.max_results = max_results
        logger.info(f"Initialized {self.name} with max_results={max_results}")
    
    def execute(self, input_data: Dict) -> Dict:
        """
        Search arXiv for papers.
        
        Args:
            input_data: Dictionary containing:
                - 'query' (str): Search query
                - 'category' (str, optional): arXiv category filter
                - 'max_results' (int, optional): Override default max results
        
        Returns:
            Dictionary containing:
                - 'success' (bool): Whether search succeeded
                - 'papers' (list): List of paper metadata dicts
                - 'error' (str): Error message if failed
        """
        try:
            query = input_data.get('query')
            if not query:
                return {
                    'success': False,
                    'error': 'Query parameter is required',
                    'papers': []
                }
            
            category = input_data.get('category', 'all')
            max_results = input_data.get('max_results', self.max_results)
            
            logger.info(f"Searching arXiv: query='{query}', category={category}")
            
            # Placeholder - real implementation would use arxiv API
            papers = [
                {
                    'title': f'Example Paper {i+1}',
                    'authors': ['Author A', 'Author B'],
                    'abstract': f'Abstract for paper matching query: {query}',
                    'arxiv_id': f'2024.{i+1:05d}',
                    'pdf_url': f'https://arxiv.org/pdf/2024.{i+1:05d}.pdf'
                }
                for i in range(min(3, max_results))
            ]
            
            return {
                'success': True,
                'papers': papers,
                'count': len(papers)
            }
            
        except Exception as e:
            error_msg = f"arXiv search failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'papers': []
            }


# Usage example in comments:
"""
To use these custom tools in your research workflow:

1. Import the tool class:
   from examples.custom_tool_example import PDFExtractor, ArXivSearchTool

2. Create an instance:
   pdf_tool = PDFExtractor(max_pages=100)
   arxiv_tool = ArXivSearchTool(max_results=20)

3. Register with the orchestrator:
   orchestrator = ResearchOrchestrator()
   orchestrator.registry.register_tool(pdf_tool, category="custom")
   orchestrator.registry.register_tool(arxiv_tool, category="custom")

4. Use in custom nodes or directly:
   result = pdf_tool.execute({'url': 'https://example.com/paper.pdf'})
   if result['success']:
       print(result['content'])

5. Or retrieve from registry:
   pdf_tool = orchestrator.registry.get_tool("custom", "pdf_extractor")
   result = pdf_tool.execute({'file_path': '/path/to/paper.pdf'})
"""
