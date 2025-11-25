"""Code execution tool for running Python code in a sandbox environment."""

import ast
import asyncio
import base64
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
from langchain_core.tools import tool

from research_agent.utils.models import CodeExecutionResult
from research_agent.utils.logger import get_logger


logger = get_logger(__name__)


# Standard library modules that don't need installation
STANDARD_LIBRARY = {
    "json", "csv", "datetime", "math", "statistics", "collections",
    "itertools", "functools", "os", "sys", "re", "time", "random",
    "pathlib", "typing", "enum", "abc", "copy", "io", "tempfile"
}


def detect_imports(code: str) -> Set[str]:
    """
    Detect required libraries from import statements in Python code.
    
    Args:
        code: Python code to analyze
        
    Returns:
        Set of library names that need to be imported
    """
    imports = set()
    
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Get the top-level package name
                    package = alias.name.split('.')[0]
                    imports.add(package)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Get the top-level package name
                    package = node.module.split('.')[0]
                    imports.add(package)
    except SyntaxError as e:
        logger.warning(
            f"Failed to parse code for imports: {str(e)}",
            extra={"context": {"error": str(e)}}
        )
    
    return imports


def extract_charts_from_output(output: str, work_dir: Path) -> List[Dict[str, Any]]:
    """
    Extract chart data from execution artifacts.
    
    Looks for saved image files (PNG, JPG, SVG) in the working directory
    and converts them to base64 for embedding.
    
    Args:
        output: Execution output text
        work_dir: Working directory where code was executed
        
    Returns:
        List of chart dictionaries with format and data
    """
    charts = []
    
    # Look for image files in the working directory
    image_extensions = ['.png', '.jpg', '.jpeg', '.svg']
    
    try:
        for file_path in work_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                try:
                    # Read the file and encode as base64
                    with open(file_path, 'rb') as f:
                        image_data = f.read()
                        encoded = base64.b64encode(image_data).decode('utf-8')
                    
                    # Determine MIME type
                    mime_type = {
                        '.png': 'image/png',
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.svg': 'image/svg+xml'
                    }.get(file_path.suffix.lower(), 'image/png')
                    
                    charts.append({
                        'filename': file_path.name,
                        'format': file_path.suffix.lstrip('.'),
                        'mime_type': mime_type,
                        'data': encoded
                    })
                    
                    logger.debug(
                        f"Extracted chart: {file_path.name}",
                        extra={"context": {"filename": file_path.name}}
                    )
                    
                except Exception as e:
                    logger.warning(
                        f"Failed to read chart file {file_path.name}: {str(e)}",
                        extra={"context": {"filename": file_path.name, "error": str(e)}}
                    )
    except Exception as e:
        logger.warning(
            f"Failed to scan for charts: {str(e)}",
            extra={"context": {"error": str(e)}}
        )
    
    return charts


async def execute_in_sandbox(
    code: str,
    required_libraries: Set[str],
    timeout: int = 30
) -> tuple[str, str, List[Dict[str, Any]]]:
    """
    Execute Python code in a sandboxed environment.
    
    Creates a temporary directory, installs required libraries,
    executes the code, and captures output and charts.
    
    Args:
        code: Python code to execute
        required_libraries: Set of library names to install
        timeout: Maximum execution time in seconds
        
    Returns:
        Tuple of (stdout, stderr, charts)
    """
    # Create temporary working directory
    with tempfile.TemporaryDirectory() as temp_dir:
        work_dir = Path(temp_dir)
        code_file = work_dir / "script.py"
        
        # Write code to file
        code_file.write_text(code)
        
        logger.debug(
            f"Created sandbox in {temp_dir}",
            extra={"context": {"work_dir": temp_dir}}
        )
        
        # Filter out standard library modules and get libraries to install
        libraries_to_install = required_libraries - STANDARD_LIBRARY
        
        # Install missing libraries if needed
        if libraries_to_install:
            logger.info(
                f"Installing libraries: {', '.join(libraries_to_install)}",
                extra={"context": {"libraries": list(libraries_to_install)}}
            )
            
            try:
                install_cmd = [
                    "pip", "install", "--quiet", "--target", str(work_dir / "packages")
                ] + list(libraries_to_install)
                
                install_process = await asyncio.create_subprocess_exec(
                    *install_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(work_dir)
                )
                
                try:
                    await asyncio.wait_for(
                        install_process.communicate(),
                        timeout=60  # Give more time for installation
                    )
                except asyncio.TimeoutError:
                    install_process.kill()
                    logger.warning(
                        "Library installation timed out",
                        extra={"context": {"libraries": list(libraries_to_install)}}
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to install libraries: {str(e)}",
                    extra={"context": {"libraries": list(libraries_to_install), "error": str(e)}}
                )
        
        # Set up environment with custom package path
        env = os.environ.copy()
        packages_dir = work_dir / "packages"
        if packages_dir.exists():
            python_path = str(packages_dir)
            if "PYTHONPATH" in env:
                env["PYTHONPATH"] = f"{python_path}:{env['PYTHONPATH']}"
            else:
                env["PYTHONPATH"] = python_path
        
        # Execute the code
        logger.info(
            "Executing Python code",
            extra={"context": {"timeout": timeout}}
        )
        
        try:
            process = await asyncio.create_subprocess_exec(
                "python3", str(code_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(work_dir),
                env=env
            )
            
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                stdout = stdout_bytes.decode('utf-8', errors='replace')
                stderr = stderr_bytes.decode('utf-8', errors='replace')
                
                logger.debug(
                    f"Code execution completed with return code {process.returncode}",
                    extra={"context": {"return_code": process.returncode}}
                )
                
            except asyncio.TimeoutError:
                process.kill()
                await process.communicate()
                logger.error(
                    f"Code execution timed out after {timeout} seconds",
                    extra={"context": {"timeout": timeout}}
                )
                return "", f"Execution timed out after {timeout} seconds", []
                
        except Exception as e:
            logger.error(
                f"Failed to execute code: {str(e)}",
                exc_info=True,
                extra={"context": {"error": str(e)}}
            )
            return "", f"Execution failed: {str(e)}", []
        
        # Extract charts from working directory
        charts = extract_charts_from_output(stdout, work_dir)
        
        return stdout, stderr, charts


@tool
async def execute_python_code(
    title: str,
    code: str
) -> CodeExecutionResult:
    """
    Execute Python code in a sandboxed environment.
    
    This tool runs Python code in an isolated environment, automatically installs
    required libraries, captures output and errors, and extracts any generated
    charts or visualizations.
    
    Data science libraries (pandas, numpy, matplotlib, scipy, seaborn, plotly,
    scikit-learn) will be automatically installed if detected in import statements.
    Standard library modules are available without installation.
    
    To save charts, use matplotlib's savefig() or similar functions. Supported
    formats: PNG, JPG, SVG.
    
    Args:
        title: Brief description of what the code does (for logging/tracking)
        code: Python code to execute. Should be complete and runnable.
        
    Returns:
        CodeExecutionResult with:
        - output: Standard output from code execution
        - error: Standard error output (if any)
        - charts: List of generated charts as base64-encoded images
        
    Examples:
        >>> result = await execute_python_code(
        ...     title="Calculate statistics",
        ...     code="import numpy as np\\nprint(np.mean([1,2,3,4,5]))"
        ... )
        
        >>> result = await execute_python_code(
        ...     title="Create visualization",
        ...     code='''
        ... import matplotlib.pyplot as plt
        ... plt.plot([1,2,3,4])
        ... plt.savefig('chart.png')
        ... '''
        ... )
    """
    logger.info(
        f"Starting code execution: {title}",
        extra={"context": {
            "title": title,
            "code_length": len(code)
        }}
    )
    
    try:
        # Detect required libraries from imports
        required_libraries = detect_imports(code)
        
        logger.debug(
            f"Detected imports: {', '.join(required_libraries) if required_libraries else 'none'}",
            extra={"context": {"imports": list(required_libraries)}}
        )
        
        # Execute code in sandbox
        stdout, stderr, charts = await execute_in_sandbox(
            code=code,
            required_libraries=required_libraries,
            timeout=30
        )
        
        # Prepare result
        result = CodeExecutionResult(
            output=stdout,
            error=stderr if stderr else None,
            charts=charts
        )
        
        logger.info(
            f"Code execution completed: {title}",
            extra={"context": {
                "title": title,
                "output_length": len(stdout),
                "has_error": bool(stderr),
                "charts_count": len(charts)
            }}
        )
        
        return result
        
    except Exception as e:
        logger.error(
            f"Code execution failed for '{title}': {str(e)}",
            exc_info=True,
            extra={"context": {
                "title": title,
                "error": str(e)
            }}
        )
        
        # Return error result instead of raising
        return CodeExecutionResult(
            output="",
            error=f"Code execution failed: {str(e)}",
            charts=[]
        )
