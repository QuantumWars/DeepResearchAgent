"""
Deep Research Framework - Main Module

This module provides the main entry point and initialization for the research framework.
"""

# Load environment variables from .env file when the package is imported
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    import warnings
    warnings.warn("python-dotenv not installed. Environment variables may not be loaded from .env file")

__version__ = "1.0.0"
__author__ = "Deep Research Framework Team"