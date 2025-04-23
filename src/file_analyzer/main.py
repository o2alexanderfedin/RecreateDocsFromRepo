"""
Main entry point for the file analyzer CLI.

This module provides the command-line interface for the file analyzer tool,
which can analyze files to determine their type, language, and purpose.
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
from file_analyzer.core.cache_provider import InMemoryCache, CacheFactory, CacheManager
from file_analyzer.core.cache_config import get_cache_settings
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


def create_analyzer(
    provider_name: str, 
    api_key: Optional[str] = None,
    cache_enabled: bool = True,
    cache_type: Optional[str] = None,
    cache_ttl: Optional[int] = None,
    cache_dir: Optional[str] = None,
    cache_db_path: Optional[str] = None,
    cache_max_size: Optional[int] = None
) -> FileTypeAnalyzer:
    """
    Create a FileTypeAnalyzer with the specified provider and caching options.
    
    Args:
        provider_name: Name of the AI provider to use
        api_key: API key for the provider (optional)
        cache_enabled: Whether to enable caching
        cache_type: Type of cache to use (memory, sqlite, filesystem, tiered)
        cache_ttl: Time-to-live for cache entries in seconds
        cache_dir: Directory for filesystem cache
        cache_db_path: Path to SQLite database file
        cache_max_size: Maximum items for in-memory cache
        
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
    
    # Set up caching
    cache_provider = None
    cache_config = None
    
    if cache_enabled:
        # Get cache settings with CLI overrides
        cache_config = get_cache_settings(
            cache_type=cache_type,
            ttl=cache_ttl,
            max_size=cache_max_size,
            cache_dir=cache_dir,
            db_path=cache_db_path
        )
        logger.debug(f"Using cache configuration: {cache_config}")
    
    # Create and return the analyzer
    return FileTypeAnalyzer(
        ai_provider=ai_provider,
        file_reader=FileReader(),
        file_hasher=FileHasher(),
        cache_provider=cache_provider,
        cache_config=cache_config if cache_enabled else None
    )


def analyze_path(
    analyzer: FileTypeAnalyzer, 
    path: Path, 
    exclude_patterns: List[str] = None,
    report_progress: bool = True
) -> Dict[str, Any]:
    """
    Analyze a file or directory.
    
    Args:
        analyzer: FileTypeAnalyzer instance
        path: Path to file or directory to analyze
        exclude_patterns: List of glob patterns to exclude
        report_progress: Whether to report progress during analysis
        
    Returns:
        Dictionary mapping file paths to analysis results
    """
    results = {}
    exclude_patterns = exclude_patterns or []
    files_processed = 0
    total_files = 0
    cache_hits = 0
    
    if path.is_file():
        # Analyze a single file
        logger.info(f"Analyzing file: {path}")
        results[str(path)] = analyzer.analyze_file(path)
        cache_stats = analyzer.get_cache_stats()
        if cache_stats.get("enabled"):
            logger.info(f"Cache statistics: {cache_stats}")
    else:
        # Analyze all files in a directory
        logger.info(f"Analyzing directory: {path}")
        
        # First, count total files (for progress reporting)
        if report_progress:
            all_files = []
            for file_path in path.glob('**/*'):
                if not file_path.is_file():
                    continue
                    
                # Check exclude patterns
                skip = False
                for pattern in exclude_patterns:
                    if file_path.match(pattern):
                        skip = True
                        break
                
                if not skip:
                    all_files.append(file_path)
            
            total_files = len(all_files)
            logger.info(f"Found {total_files} files to analyze")
        
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
            files_processed += 1
            
            if report_progress and total_files > 0 and files_processed % 10 == 0:
                logger.info(f"Progress: {files_processed}/{total_files} files ({files_processed/total_files*100:.1f}%)")
                
                # Report cache statistics periodically
                cache_stats = analyzer.get_cache_stats()
                if cache_stats.get("enabled"):
                    hits = cache_stats.get("hit", 0)
                    misses = cache_stats.get("miss", 0)
                    total = hits + misses
                    hit_rate = 0
                    if total > 0:
                        hit_rate = hits / total * 100
                    logger.info(f"Cache hit rate: {hit_rate:.1f}% ({hits}/{total})")
            
            logger.debug(f"Analyzing: {file_path}")
            results[str(file_path)] = analyzer.analyze_file(file_path)
        
        if report_progress:
            logger.info(f"Completed analysis of {files_processed} files")
            
            # Report final cache stats
            cache_stats = analyzer.get_cache_stats()
            if cache_stats.get("enabled"):
                logger.info(f"Cache statistics: {cache_stats}")
    
    return results


def main() -> int:
    """
    Main entry point for the CLI.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description='Analyze files to determine their type and purpose.')
    parser.add_argument('path', help='Path to file or directory to analyze')
    
    # Provider options
    provider_group = parser.add_argument_group('Provider Options')
    provider_group.add_argument('--provider', choices=['mistral', 'openai', 'mock'], default='mistral',
                       help='AI provider to use for analysis (default: mistral)')
    provider_group.add_argument('--api-key', help='API key for the selected provider')
    
    # Caching options
    cache_group = parser.add_argument_group('Caching Options')
    cache_group.add_argument('--cache', choices=['on', 'off'], default='on',
                       help='Enable or disable caching (default: on)')
    cache_group.add_argument('--cache-type', choices=['memory', 'sqlite', 'filesystem', 'tiered'],
                       help='Type of cache to use (default: tiered)')
    cache_group.add_argument('--cache-ttl', type=int,
                       help='Time-to-live for cache entries in seconds')
    cache_group.add_argument('--cache-dir', 
                       help='Directory for filesystem cache')
    cache_group.add_argument('--cache-db',
                       help='Path to SQLite database file')
    cache_group.add_argument('--cache-max-size', type=int,
                       help='Maximum items for in-memory cache')
    cache_group.add_argument('--cache-stats', action='store_true', 
                       help='Show detailed cache statistics at the end of the run')
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument('--output', help='Output file for results (JSON format)')
    output_group.add_argument('--exclude', action='append', default=[],
                       help='Glob patterns to exclude (can be specified multiple times)')
    output_group.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    output_group.add_argument('--no-progress', action='store_true',
                       help='Disable progress reporting')
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        # Check cache settings
        cache_enabled = args.cache != 'off'
        
        # Create analyzer with specified provider and cache settings
        analyzer = create_analyzer(
            provider_name=args.provider, 
            api_key=args.api_key,
            cache_enabled=cache_enabled,
            cache_type=args.cache_type,
            cache_ttl=args.cache_ttl,
            cache_dir=args.cache_dir,
            cache_db_path=args.cache_db,
            cache_max_size=args.cache_max_size
        )
        
        # Show initial cache status
        cache_stats = analyzer.get_cache_stats()
        if cache_stats.get("enabled"):
            logger.info(f"Cache enabled: {args.cache_type or 'tiered'}")
        else:
            logger.info("Cache disabled")
        
        # Analyze the specified path
        path = Path(args.path)
        if not path.exists():
            logger.error(f"Path does not exist: {path}")
            return 1
            
        # Default exclude patterns
        exclude_patterns = ['**/.git/**', '**/__pycache__/**', '**/node_modules/**', '**/.venv/**']
        exclude_patterns.extend(args.exclude)
        
        # Run analysis
        results = analyze_path(analyzer, path, exclude_patterns, report_progress=not args.no_progress)
        
        # Show detailed cache stats if requested
        if args.cache_stats and cache_stats.get("enabled"):
            final_stats = analyzer.get_cache_stats()
            print("\nCache Statistics:")
            print(f"- Enabled: {final_stats.get('enabled', False)}")
            print(f"- Hits: {final_stats.get('hit', 0)}")
            print(f"- Misses: {final_stats.get('miss', 0)}")
            print(f"- Stores: {final_stats.get('store', 0)}")
            
            total_lookups = final_stats.get('hit', 0) + final_stats.get('miss', 0)
            hit_rate = 0
            if total_lookups > 0:
                hit_rate = final_stats.get('hit', 0) / total_lookups * 100
            print(f"- Hit Rate: {hit_rate:.1f}%")
            
            # Show provider-specific stats if available
            if 'provider' in final_stats:
                print("\nProvider Statistics:")
                for key, value in final_stats['provider'].items():
                    if isinstance(value, dict):
                        print(f"- {key}:")
                        for k, v in value.items():
                            if k in ["hit_rate", "size", "max_size"]:
                                print(f"  - {k}: {v}")
                    else:
                        print(f"- {key}: {value}")
        
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