"""
Main entry point for the file analyzer CLI.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from file_analyzer.core.file_type_analyzer import FileTypeAnalyzer
from file_analyzer.core.file_reader import FileReader
from file_analyzer.core.file_hasher import FileHasher
from file_analyzer.core.cache_provider import InMemoryCache
from file_analyzer.ai_providers.mistral_provider import MistralProvider
from file_analyzer.ai_providers.openai_provider import OpenAIProvider
from file_analyzer.ai_providers.mock_provider import MockAIProvider
from file_analyzer.utils.exceptions import FileAnalyzerError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("file_analyzer")


def create_analyzer(provider_name: str, api_key: Optional[str] = None) -> FileTypeAnalyzer:
    """
    Create a FileTypeAnalyzer with the specified provider.
    
    Args:
        provider_name: Name of the AI provider to use
        api_key: API key for the provider (optional)
        
    Returns:
        Configured FileTypeAnalyzer instance
        
    Raises:
        FileAnalyzerError: If the provider cannot be created
    """
    # Use environment variable if no API key provided
    if not api_key:
        if provider_name == "mock":
            # No API key needed for mock
            pass
        elif provider_name == "mistral":
            api_key = os.environ.get("MISTRAL_API_KEY")
            if not api_key:
                raise FileAnalyzerError("MISTRAL_API_KEY environment variable not set")
        elif provider_name == "openai":
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise FileAnalyzerError("OPENAI_API_KEY environment variable not set")
    
    # Create the appropriate provider
    if provider_name == "mistral":
        ai_provider = MistralProvider(api_key=api_key)
    elif provider_name == "openai":
        ai_provider = OpenAIProvider(api_key=api_key)
    elif provider_name == "mock":
        ai_provider = MockAIProvider()
    else:
        raise FileAnalyzerError(f"Unknown provider: {provider_name}")
    
    # Create and return the analyzer
    return FileTypeAnalyzer(
        ai_provider=ai_provider,
        file_reader=FileReader(),
        file_hasher=FileHasher(),
        cache_provider=InMemoryCache()
    )


def analyze_path(analyzer: FileTypeAnalyzer, path: Path, exclude_patterns: List[str] = None) -> Dict[str, Any]:
    """
    Analyze a file or directory.
    
    Args:
        analyzer: FileTypeAnalyzer instance
        path: Path to file or directory to analyze
        exclude_patterns: List of glob patterns to exclude
        
    Returns:
        Dictionary mapping file paths to analysis results
    """
    results = {}
    exclude_patterns = exclude_patterns or []
    
    if path.is_file():
        # Analyze a single file
        logger.info(f"Analyzing file: {path}")
        results[str(path)] = analyzer.analyze_file(path)
    else:
        # Analyze all files in a directory
        logger.info(f"Analyzing directory: {path}")
        
        # Walk through directory
        for file_path in path.glob('**/*'):
            # Skip directories and excluded patterns
            if not file_path.is_file():
                continue
                
            # Check exclude patterns
            skip = False
            for pattern in exclude_patterns:
                if file_path.match(pattern):
                    skip = True
                    break
            
            if skip:
                continue
                
            # Analyze file
            logger.debug(f"Analyzing: {file_path}")
            results[str(file_path)] = analyzer.analyze_file(file_path)
    
    return results


def main() -> int:
    """
    Main entry point for the CLI.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description='Analyze files to determine their type and purpose.')
    parser.add_argument('path', help='Path to file or directory to analyze')
    parser.add_argument('--provider', choices=['mistral', 'openai', 'mock'], default='mistral',
                       help='AI provider to use for analysis (default: mistral)')
    parser.add_argument('--api-key', help='API key for the selected provider')
    parser.add_argument('--output', help='Output file for results (JSON format)')
    parser.add_argument('--exclude', action='append', default=[],
                       help='Glob patterns to exclude (can be specified multiple times)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        # Create analyzer with specified provider
        analyzer = create_analyzer(args.provider, args.api_key)
        
        # Analyze the specified path
        path = Path(args.path)
        if not path.exists():
            logger.error(f"Path does not exist: {path}")
            return 1
            
        # Default exclude patterns
        exclude_patterns = ['**/.git/**', '**/__pycache__/**', '**/node_modules/**', '**/.venv/**']
        exclude_patterns.extend(args.exclude)
        
        # Run analysis
        results = analyze_path(analyzer, path, exclude_patterns)
        
        # Output results
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results written to {output_path}")
        else:
            print(json.dumps(results, indent=2))
        
        return 0
        
    except FileAnalyzerError as e:
        logger.error(str(e))
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())