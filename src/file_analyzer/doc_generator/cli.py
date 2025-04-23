"""
CLI for documentation generation.

This module provides a command-line interface for generating per-file
documentation from repository analysis results.
"""
import argparse
import json
import logging
import os
import sys
from typing import Dict, Any, Optional

from file_analyzer.repo_scanner import RepositoryScanner
from file_analyzer.core.file_type_analyzer import FileTypeAnalyzer
from file_analyzer.core.code_analyzer import CodeAnalyzer
from file_analyzer.core.framework_detector import FrameworkDetector
from file_analyzer.ai_providers.mock_provider import MockAIProvider
from file_analyzer.ai_providers.mistral_provider import MistralProvider
from file_analyzer.ai_providers.openai_provider import OpenAIProvider
from file_analyzer.core.cache_provider import InMemoryCache, FileSystemCache
from file_analyzer.doc_generator.markdown_generator import generate_documentation

logger = logging.getLogger("file_analyzer.doc_generator.cli")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate per-file documentation for a repository"
    )
    
    parser.add_argument(
        "repo_path",
        help="Path to the repository to analyze"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        default="docs/generated",
        help="Directory where documentation will be generated"
    )
    
    parser.add_argument(
        "--template-dir", "-t",
        help="Directory with custom templates"
    )
    
    parser.add_argument(
        "--provider", "-p",
        choices=["mock", "mistral", "openai"],
        default="mock",
        help="AI provider to use for analysis"
    )
    
    parser.add_argument(
        "--api-key", "-k",
        help="API key for the AI provider"
    )
    
    parser.add_argument(
        "--model", "-m",
        help="Model name for the AI provider"
    )
    
    parser.add_argument(
        "--exclude", "-e",
        action="append",
        default=[],
        help="Patterns to exclude from analysis (can be specified multiple times)"
    )
    
    parser.add_argument(
        "--no-code-snippets",
        action="store_true",
        help="Deprecated: Code snippets have been replaced with source file links"
    )
    
    parser.add_argument(
        "--max-code-lines",
        type=int,
        default=15,
        help="Deprecated: Code snippets have been replaced with source file links"
    )
    
    parser.add_argument(
        "--no-relationships",
        action="store_true",
        help="Disable file relationship analysis"
    )
    
    parser.add_argument(
        "--no-framework-details",
        action="store_true",
        help="Disable detailed framework usage information"
    )
    
    parser.add_argument(
        "--no-ai-documentation",
        action="store_true",
        help="Disable AI-generated documentation"
    )
    
    parser.add_argument(
        "--cache-dir",
        help="Directory for caching analysis results"
    )
    
    parser.add_argument(
        "--analysis-file",
        help="JSON file with existing analysis results"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def configure_logging(verbose: bool):
    """Configure logging level based on verbosity."""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def create_ai_provider(provider_name: str, api_key: Optional[str], model_name: Optional[str]):
    """Create an AI provider based on name and configuration."""
    if provider_name == "mistral":
        api_key = api_key or os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            logger.error("Mistral API key not provided")
            sys.exit(1)
        
        model = model_name or "mistral-small"
        return MistralProvider(api_key=api_key, model_name=model)
    
    elif provider_name == "openai":
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("OpenAI API key not provided")
            sys.exit(1)
        
        model = model_name or "gpt-3.5-turbo"
        return OpenAIProvider(api_key=api_key, model_name=model)
    
    else:  # Default to mock provider
        return MockAIProvider()

def load_analysis_results(file_path: str) -> Dict[str, Any]:
    """Load analysis results from a JSON file."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading analysis results: {str(e)}")
        sys.exit(1)

def main():
    """Main entry point for documentation generation CLI."""
    args = parse_args()
    configure_logging(args.verbose)
    
    # Create AI provider (used for both analysis and documentation)
    ai_provider = create_ai_provider(args.provider, args.api_key, args.model)
    
    # If analysis results are provided, load them
    if args.analysis_file:
        logger.info(f"Loading analysis results from {args.analysis_file}")
        repo_analysis = load_analysis_results(args.analysis_file)
    
    # Otherwise, perform repository analysis
    else:
        logger.info(f"Analyzing repository: {args.repo_path}")
        
        # Create cache provider
        cache_provider = None
        if args.cache_dir:
            cache_provider = FileSystemCache(args.cache_dir)
        else:
            cache_provider = InMemoryCache()
        
        # Create analyzers
        file_type_analyzer = FileTypeAnalyzer(
            ai_provider=ai_provider,
            cache_provider=cache_provider
        )
        
        code_analyzer = CodeAnalyzer(
            ai_provider=ai_provider,
            file_type_analyzer=file_type_analyzer,
            cache_provider=cache_provider
        )
        
        framework_detector = FrameworkDetector(
            ai_provider=ai_provider,
            code_analyzer=code_analyzer,
            file_type_analyzer=file_type_analyzer,
            cache_provider=cache_provider
        )
        
        # Create repository scanner
        repo_scanner = RepositoryScanner(
            file_analyzer=file_type_analyzer,
            code_analyzer=code_analyzer,
            framework_detector=framework_detector
        )
        
        # Scan repository
        repo_analysis = repo_scanner.scan(
            repo_path=args.repo_path,
            exclude_patterns=args.exclude
        )
    
    # Generate documentation
    logger.info(f"Generating documentation in {args.output_dir}")
    
    # Notify about code snippets deprecation if those arguments were used
    if args.no_code_snippets or args.max_code_lines != 15:
        logger.warning("Code snippets have been replaced with direct links to source files. "
                       "The --no-code-snippets and --max-code-lines arguments are deprecated.")
    
    stats = generate_documentation(
        repo_analysis=repo_analysis,
        output_dir=args.output_dir,
        template_dir=args.template_dir,
        include_code_snippets=False,  # Always use source file links instead
        max_code_snippet_lines=args.max_code_lines,
        include_relationships=not args.no_relationships,
        include_framework_details=not args.no_framework_details,
        include_ai_documentation=not args.no_ai_documentation,
        ai_provider=ai_provider,  # Pass the AI provider to documentation generator
        exclude_patterns=args.exclude
    )
    
    logger.info(f"Documentation generation complete")
    logger.info(f"Files processed: {stats['total_files']}")
    logger.info(f"Documentation files generated: {stats['documentation_files_generated']}")
    logger.info(f"Files skipped: {stats['skipped_files']}")
    logger.info(f"Index files created: {stats['index_files']}")
    
    logger.info(f"Documentation is available at: {os.path.abspath(args.output_dir)}")

if __name__ == "__main__":
    main()