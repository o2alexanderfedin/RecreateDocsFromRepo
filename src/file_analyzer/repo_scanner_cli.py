#!/usr/bin/env python3
"""
Command-line interface for the Repository Scanner.

This module provides a command-line tool for scanning repositories
and analyzing files using the File Type Analyzer.
"""
import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from file_analyzer.core.file_type_analyzer import FileTypeAnalyzer
from file_analyzer.core.cache_provider import InMemoryCache
from file_analyzer.repo_scanner import RepositoryScanner
from file_analyzer.ai_providers.mistral_provider import MistralProvider
from file_analyzer.ai_providers.openai_provider import OpenAIProvider
from file_analyzer.ai_providers.mock_provider import MockAIProvider
from file_analyzer.utils.exceptions import FileAnalyzerError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("file_analyzer.repo_scanner_cli")


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
        cache_provider=InMemoryCache()
    )


def print_progress(processed: int, total: int) -> None:
    """
    Print progress bar to stderr.
    
    Args:
        processed: Number of processed files
        total: Total number of files
    """
    bar_length = 40
    if total == 0:
        percent = 100
        filled_length = bar_length
    else:
        percent = processed * 100 // total
        filled_length = bar_length * processed // total
        
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    
    sys.stderr.write(f'\rAnalyzing: [{bar}] {percent}% ({processed}/{total} files)')
    sys.stderr.flush()
    
    if processed == total:
        sys.stderr.write('\n')


def main() -> int:
    """
    Main entry point for the CLI.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(
        description='Scan a repository and analyze files to determine their types and purposes.'
    )
    parser.add_argument('repo_path', help='Path to repository to analyze')
    parser.add_argument('--provider', choices=['mistral', 'openai', 'mock'], default='mistral',
                        help='AI provider to use for analysis (default: mistral)')
    parser.add_argument('--api-key', help='API key for the selected provider')
    parser.add_argument('--output', help='Output file for results (JSON format)')
    parser.add_argument('--async', action='store_true', dest='use_async',
                        help='Use asynchronous processing')
    parser.add_argument('--exclude', action='append', default=[],
                        help='Additional patterns to exclude (can be specified multiple times)')
    parser.add_argument('--max-size', type=int, default=10 * 1024 * 1024,
                        help='Maximum file size to analyze in bytes (default: 10MB)')
    parser.add_argument('--concurrency', type=int, default=5,
                        help='Maximum number of concurrent analysis tasks (default: 5)')
    parser.add_argument('--batch-size', type=int, default=10,
                        help='Number of files to analyze in each batch (default: 10)')
    parser.add_argument('--no-progress', action='store_true',
                        help='Disable progress bar')
    parser.add_argument('--verbose', '-v', action='store_true', 
                        help='Enable verbose logging')
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger("file_analyzer").setLevel(logging.DEBUG)
    
    try:
        # Create analyzer with specified provider
        analyzer = create_analyzer(args.provider, args.api_key)
        
        # Create repository scanner
        scanner = RepositoryScanner(
            analyzer=analyzer,
            exclusions=args.exclude,
            max_file_size=args.max_size,
            concurrency=args.concurrency,
            batch_size=args.batch_size,
            progress_callback=None if args.no_progress else print_progress
        )
        
        # Analyze the specified path
        repo_path = Path(args.repo_path)
        if not repo_path.exists():
            logger.error(f"Repository path does not exist: {repo_path}")
            return 1
        
        # Run scan
        if args.use_async:
            logger.info("Using asynchronous processing")
            # Create event loop and run async scan
            if sys.platform == 'win32':
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            
            loop = asyncio.get_event_loop()
            results = loop.run_until_complete(scanner.scan_repository_async(repo_path))
        else:
            # Run synchronous scan
            results = scanner.scan_repository(repo_path)
        
        # Output results
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results written to {output_path}")
        else:
            print(json.dumps(results, indent=2))
        
        # Print summary
        stats = results["statistics"]
        print(f"\nSummary:", file=sys.stderr)
        print(f"- Files found: {stats['total_files']}", file=sys.stderr)
        print(f"- Files analyzed: {stats['analyzed_files']}", file=sys.stderr)
        print(f"- Files excluded: {stats['excluded_files']}", file=sys.stderr)
        print(f"- Files with errors: {stats['error_files']}", file=sys.stderr)
        print(f"- Processing time: {stats['processing_time']:.2f} seconds", file=sys.stderr)
        
        # Print language breakdown
        if stats['languages']:
            print(f"\nLanguage breakdown:", file=sys.stderr)
            for lang, count in sorted(stats['languages'].items(), key=lambda x: x[1], reverse=True):
                print(f"- {lang}: {count} files", file=sys.stderr)
        
        # Print file type breakdown
        if stats['file_types']:
            print(f"\nFile type breakdown:", file=sys.stderr)
            for ftype, count in sorted(stats['file_types'].items(), key=lambda x: x[1], reverse=True):
                print(f"- {ftype}: {count} files", file=sys.stderr)
        
        return 0
        
    except FileAnalyzerError as e:
        logger.error(str(e))
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())