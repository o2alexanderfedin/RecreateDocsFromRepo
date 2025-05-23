"""
CLI for documentation generation.

This module provides a command-line interface for generating per-file
documentation from repository analysis results, as well as UML diagrams
for different architectural views.
"""
import argparse
import json
import logging
import os
import sys
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from file_analyzer.repo_scanner import RepositoryScanner
from file_analyzer.core.file_type_analyzer import FileTypeAnalyzer
from file_analyzer.core.code_analyzer import CodeAnalyzer
from file_analyzer.core.framework_detector import FrameworkDetector
from file_analyzer.ai_providers.mock_provider import MockAIProvider
from file_analyzer.ai_providers.mistral_provider import MistralProvider
from file_analyzer.ai_providers.openai_provider import OpenAIProvider
from file_analyzer.core.cache_provider import InMemoryCache, FileSystemCache
from file_analyzer.doc_generator.markdown_generator import generate_documentation
from file_analyzer.doc_generator.documentation_structure_manager import (
    DocumentationStructureManager,
    DocumentationStructureConfig
)
from file_analyzer.doc_generator.documentation_navigation_manager import (
    DocumentationNavigationManager,
    NavigationConfig
)
from file_analyzer.doc_generator.diagram_factory import DiagramFactory

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
    
    # Documentation Structure Options
    parser.add_argument(
        "--no-structure-manager",
        action="store_true",
        help="Disable enhanced documentation structure manager"
    )
    
    parser.add_argument(
        "--max-depth",
        type=int,
        default=3,
        help="Maximum depth for hierarchical structure"
    )
    
    parser.add_argument(
        "--no-adapt-depth",
        action="store_true",
        help="Don't adapt depth based on repository size"
    )
    
    parser.add_argument(
        "--no-component-view",
        action="store_true",
        help="Disable component view in documentation structure"
    )
    
    parser.add_argument(
        "--no-architecture-view",
        action="store_true",
        help="Disable architecture view in documentation structure"
    )
    
    # Navigation Options
    parser.add_argument(
        "--no-navigation",
        action="store_true",
        help="Disable enhanced navigation elements"
    )
    
    parser.add_argument(
        "--no-breadcrumbs",
        action="store_true",
        help="Disable breadcrumb navigation"
    )
    
    parser.add_argument(
        "--no-toc",
        action="store_true",
        help="Disable table of contents"
    )
    
    parser.add_argument(
        "--no-section-nav",
        action="store_true",
        help="Disable section navigation"
    )
    
    parser.add_argument(
        "--no-cross-references",
        action="store_true",
        help="Disable cross-references"
    )
    
    # UML Diagram Generation Options
    parser.add_argument(
        "--generate-diagrams",
        action="store_true",
        help="Enable UML diagram generation"
    )
    
    parser.add_argument(
        "--diagram-views",
        default="logical,process,development",
        help="Comma-separated list of architectural views to generate diagrams for"
    )
    
    parser.add_argument(
        "--diagram-types",
        default="class,sequence,package",
        help="Comma-separated list of diagram types to generate"
    )
    
    parser.add_argument(
        "--diagram-output-dir",
        help="Directory where diagrams will be generated (default: output-dir/diagrams)"
    )
    
    parser.add_argument(
        "--diagram-title-prefix",
        help="Optional prefix for diagram titles"
    )
    
    parser.add_argument(
        "--diagram-entry-point",
        help="Entry point for sequence diagrams (e.g., module.Class.method)"
    )
    
    parser.add_argument(
        "--diagram-max-depth",
        type=int,
        default=3,
        help="Maximum depth for hierarchical diagrams"
    )
    
    parser.add_argument(
        "--diagram-file-patterns",
        help="Comma-separated list of file patterns to include in diagrams"
    )
    
    # Final Assembly Options
    parser.add_argument(
        "--final-assembly",
        action="store_true",
        help="Enable final documentation assembly"
    )
    
    parser.add_argument(
        "--assembly-output-dir",
        help="Directory for final assembled documentation (default: output-dir/assembled)"
    )
    
    parser.add_argument(
        "--assembly-input-dirs",
        help="Additional input directories for assembly (comma-separated)"
    )
    
    parser.add_argument(
        "--assembly-template-dir",
        help="Custom template directory for assembly"
    )
    
    parser.add_argument(
        "--no-self-contained",
        action="store_true",
        help="Disable self-contained documentation package"
    )
    
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Disable documentation validation"
    )
    
    parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="Disable documentation optimization"
    )
    
    parser.add_argument(
        "--no-readme",
        action="store_true",
        help="Disable README generation"
    )
    
    parser.add_argument(
        "--assembly-format",
        choices=["markdown", "html", "pdf"],
        help="Format for final documentation assembly (default: markdown)"
    )
    
    # Cache and Analysis Options
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
    
    # Create cache provider
    cache_provider = None
    if args.cache_dir:
        cache_provider = FileSystemCache(args.cache_dir)
    else:
        cache_provider = InMemoryCache()
    
    # If analysis results are provided, load them
    if args.analysis_file:
        logger.info(f"Loading analysis results from {args.analysis_file}")
        repo_analysis = load_analysis_results(args.analysis_file)
    
    # Otherwise, perform repository analysis
    else:
        logger.info(f"Analyzing repository: {args.repo_path}")
        
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
    
    # Generate per-file documentation
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
    
    # Apply documentation structure manager if enabled
    if not args.no_structure_manager:
        logger.info("Applying documentation structure manager")
        
        # Create structure manager configuration
        structure_config = DocumentationStructureConfig(
            output_dir=args.output_dir,
            template_dir=args.template_dir,
            max_depth=args.max_depth,
            adapt_depth_to_size=not args.no_adapt_depth,
            include_component_view=not args.no_component_view,
            include_architecture_view=not args.no_architecture_view,
            exclude_patterns=args.exclude
        )
        
        # Create structure manager
        structure_manager = DocumentationStructureManager(structure_config)
        
        # Organize documentation structure
        structure_results = structure_manager.organize_documentation_structure(
            repo_path=repo_analysis.get("repo_path", ""),
            file_results=repo_analysis.get("file_results", {}),
            frameworks=repo_analysis.get("frameworks", [])
        )
        
        # Update stats
        if "index_files" in structure_results:
            stats["structure_index_files"] = len(structure_results.get("index_files", []))
            stats["index_files"] += stats["structure_index_files"]
            logger.info(f"Structure index files created: {stats['structure_index_files']}")
    
    # Apply documentation navigation if enabled
    if not args.no_navigation:
        logger.info("Applying documentation navigation elements")
        
        # Create navigation configuration
        navigation_config = NavigationConfig(
            output_dir=args.output_dir,
            template_dir=args.template_dir,
            include_breadcrumbs=not args.no_breadcrumbs,
            include_toc=not args.no_toc,
            include_section_nav=not args.no_section_nav,
            include_cross_references=not args.no_cross_references
        )
        
        # Create navigation manager
        navigation_manager = DocumentationNavigationManager(navigation_config)
        
        # Find all generated documentation files
        document_files = []
        for root, dirs, files in os.walk(args.output_dir):
            for file in files:
                if file.endswith(".md"):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, args.output_dir).replace("\\", "/")
                    document_files.append({
                        "file_path": file_path,
                        "metadata": {
                            "path": rel_path,
                            "title": os.path.basename(file)
                        }
                    })
        
        # Build document structure
        doc_structure = navigation_manager.build_doc_structure([f["file_path"] for f in document_files])
        
        # Process navigation elements
        nav_results = navigation_manager.process_documentation_structure(document_files, doc_structure)
        
        # Update stats
        stats["navigation_processed"] = nav_results["processed_files"]
        stats["navigation_skipped"] = nav_results["skipped_files"]
        logger.info(f"Navigation elements added to {nav_results['processed_files']} files")
    
    # Generate UML diagrams if enabled
    if args.generate_diagrams:
        logger.info("Generating UML diagrams")
        
        # Import diagram related modules
        from file_analyzer.doc_generator.diagram_factory import DiagramFactory
        
        # Set the diagram output directory
        diagram_output_dir = args.diagram_output_dir
        if not diagram_output_dir:
            diagram_output_dir = os.path.join(args.output_dir, "diagrams")
        
        # Make sure the output directory exists
        os.makedirs(diagram_output_dir, exist_ok=True)
        
        # Create diagram factory
        diagram_factory = DiagramFactory(
            ai_provider=ai_provider,
            code_analyzer=code_analyzer if 'code_analyzer' in locals() else None,
            file_reader=None,  # Will be created by factory if needed
            file_hasher=None,  # Will be created by factory if needed
            cache_provider=cache_provider
        )
        
        # Parse view and diagram types
        view_types = args.diagram_views.split(',')
        diagram_types = args.diagram_types.split(',')
        
        # Track diagram statistics
        diagram_stats = {
            "diagrams_generated": 0,
            "errors": 0
        }
        
        # Get file paths from repository analysis
        file_results = repo_analysis.get("file_results", {})
        file_paths = [file_path for file_path, _ in file_results.items()]
        
        # Filter by file patterns if specified
        if args.diagram_file_patterns:
            import fnmatch
            patterns = args.diagram_file_patterns.split(',')
            filtered_paths = []
            for path in file_paths:
                if any(fnmatch.fnmatch(path, pattern) for pattern in patterns):
                    filtered_paths.append(path)
            file_paths = filtered_paths
        
        # Generate diagrams for each view type and diagram type
        for view_type in view_types:
            # Skip if view type is not supported
            if view_type not in diagram_factory.get_supported_views():
                logger.warning(f"Skipping unsupported view type: {view_type}")
                continue
            
            # Get supported diagram types for this view
            supported_diagrams = diagram_factory.get_supported_views()[view_type]
            
            # Create generator for this view
            try:
                generator = diagram_factory.create_generator(view_type)
            except Exception as e:
                logger.error(f"Error creating generator for view {view_type}: {str(e)}")
                diagram_stats["errors"] += 1
                continue
            
            # Process each requested diagram type
            for diagram_type in diagram_types:
                if diagram_type not in supported_diagrams:
                    logger.warning(f"Skipping unsupported diagram type '{diagram_type}' for view '{view_type}'")
                    continue
                
                logger.info(f"Generating {view_type} {diagram_type} diagram")
                
                # Prepare diagram title
                title_prefix = args.diagram_title_prefix or ""
                title = f"{title_prefix} {view_type.capitalize()} {diagram_type.capitalize()} Diagram"
                title = title.strip()
                
                # Set up specific diagram parameters
                diagram_params = {
                    "title": title
                }
                
                # Add view-specific parameters
                if view_type == "process" and diagram_type == "sequence":
                    diagram_params["max_depth"] = args.diagram_max_depth
                    if args.diagram_entry_point:
                        diagram_params["entry_point"] = args.diagram_entry_point
                
                elif view_type == "development":
                    diagram_params["max_depth"] = args.diagram_max_depth
                
                # Different handling based on view type
                try:
                    if view_type in ["logical", "process"]:
                        # These views work with file paths
                        result = generator.generate_diagram(file_paths, diagram_type, **diagram_params)
                    elif view_type in ["development", "physical"]:
                        # These views work with the repository root
                        repo_path = repo_analysis.get("repo_path", "")
                        result = generator.generate_diagram(repo_path, diagram_type, **diagram_params)
                    else:
                        # Generic case, try with file paths first
                        result = generator.generate_diagram(file_paths, diagram_type, **diagram_params)
                    
                    # Save diagram to file
                    diagram_filename = f"{view_type}_{diagram_type}_diagram.md"
                    diagram_path = os.path.join(diagram_output_dir, diagram_filename)
                    
                    with open(diagram_path, "w") as f:
                        f.write(f"# {result['title']}\n\n")
                        f.write("```mermaid\n")
                        f.write(result["content"])
                        f.write("\n```\n\n")
                        
                        # Add metadata if available
                        if "metadata" in result:
                            f.write("## Diagram Metadata\n\n")
                            for key, value in result["metadata"].items():
                                f.write(f"- **{key}**: {value}\n")
                    
                    logger.info(f"Generated diagram: {diagram_path}")
                    diagram_stats["diagrams_generated"] += 1
                    
                except Exception as e:
                    logger.error(f"Error generating {view_type} {diagram_type} diagram: {str(e)}")
                    diagram_stats["errors"] += 1
        
        # Update stats
        stats["diagrams_generated"] = diagram_stats["diagrams_generated"]
        stats["diagram_errors"] = diagram_stats["errors"]
        logger.info(f"Generated {stats['diagrams_generated']} diagrams with {stats['diagram_errors']} errors")
    
    # Apply final assembly if enabled
    assembly_output_dir = None
    if args.final_assembly:
        logger.info("Performing final documentation assembly")
        
        from file_analyzer.doc_generator.documentation_assembler import DocumentationAssembler, AssemblyConfig
        
        # Create input dirs list
        input_dirs = [args.output_dir]
        if args.assembly_input_dirs:
            input_dirs.extend(args.assembly_input_dirs.split(','))
        
        # Create assembly output dir
        assembly_output_dir = args.assembly_output_dir
        if not assembly_output_dir:
            assembly_output_dir = os.path.join(args.output_dir, "assembled")
        
        # Create assembly config
        assembly_config = AssemblyConfig(
            output_dir=assembly_output_dir,
            input_dirs=input_dirs,
            template_dir=args.assembly_template_dir or args.template_dir,
            self_contained=not args.no_self_contained,
            validate_output=not args.no_validate,
            optimize_output=not args.no_optimize,
            include_readme=not args.no_readme,
            output_format=args.assembly_format or "markdown"
        )
        
        # Create and run assembler
        assembler = DocumentationAssembler(assembly_config)
        assembly_stats = assembler.assemble_documentation()
        
        # Generate README with project info
        project_name = os.path.basename(os.path.abspath(args.repo_path))
        repo_url = ""  # Would need Git integration to detect remote URL
        assembler.generate_readme(project_name=project_name, repo_url=repo_url)
        
        # Update stats
        stats["assembly_files_processed"] = assembly_stats.get("files_processed", 0)
        stats["assembly_errors"] = len(assembly_stats.get("errors", []))
        
        if "validation_result" in assembly_stats:
            validation = assembly_stats["validation_result"]
            stats["validation_issues"] = (
                validation.get("broken_links", 0) + 
                validation.get("missing_sections", 0) +
                validation.get("formatting_issues", 0)
            )
        
        if "optimization_result" in assembly_stats:
            stats["files_optimized"] = assembly_stats["optimization_result"].get("files_optimized", 0)
            stats["size_reduction"] = assembly_stats["optimization_result"].get("size_reduction", 0)
        
        logger.info(f"Assembly complete with {stats['assembly_files_processed']} files processed")
        logger.info(f"Final documentation is available at: {os.path.abspath(assembly_output_dir)}")
    
    logger.info(f"Documentation generation complete")
    logger.info(f"Files processed: {stats['total_files']}")
    logger.info(f"Documentation files generated: {stats['documentation_files_generated']}")
    logger.info(f"Files skipped: {stats['skipped_files']}")
    logger.info(f"Index files created: {stats['index_files']}")
    
    # Report diagram stats if diagrams were generated
    if args.generate_diagrams:
        logger.info(f"Diagrams generated: {stats.get('diagrams_generated', 0)}")
        if stats.get('diagram_errors', 0) > 0:
            logger.warning(f"Diagram errors: {stats.get('diagram_errors', 0)}")
    
    # Determine the final documentation location
    docs_location = os.path.abspath(assembly_output_dir) if args.final_assembly and assembly_output_dir else os.path.abspath(args.output_dir)
    logger.info(f"Documentation is available at: {docs_location}")

if __name__ == "__main__":
    main()