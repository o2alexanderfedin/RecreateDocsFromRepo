"""
Per-file Markdown documentation generator.

This module provides functionality to generate detailed Markdown documentation
for each file in a repository based on analysis results.
"""
import logging
import os
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import jinja2

logger = logging.getLogger("file_analyzer.doc_generator")

class DocumentationConfig:
    """Configuration for documentation generation."""
    
    def __init__(
        self,
        output_dir: str,
        template_dir: Optional[str] = None,
        include_code_snippets: bool = True,
        max_code_snippet_lines: int = 15,
        include_relationships: bool = True,
        include_framework_details: bool = True,
        exclude_patterns: Optional[List[str]] = None
    ):
        """
        Initialize documentation configuration.
        
        Args:
            output_dir: Directory where documentation will be generated
            template_dir: Custom template directory (optional)
            include_code_snippets: Whether to include code snippets
            max_code_snippet_lines: Maximum lines for code snippets
            include_relationships: Whether to include file relationships
            include_framework_details: Whether to include framework details
            exclude_patterns: Patterns of files to exclude from documentation
        """
        self.output_dir = output_dir
        self.template_dir = template_dir
        self.include_code_snippets = include_code_snippets
        self.max_code_snippet_lines = max_code_snippet_lines
        self.include_relationships = include_relationships
        self.include_framework_details = include_framework_details
        self.exclude_patterns = exclude_patterns or []


class MarkdownGenerator:
    """
    Generates per-file Markdown documentation from repository analysis.
    
    This class takes repository analysis results and generates one Markdown
    file per source file, as well as index files for navigation.
    """
    
    def __init__(self, config: DocumentationConfig):
        """
        Initialize the Markdown generator.
        
        Args:
            config: Documentation generation configuration
        """
        self.config = config
        
        # Set up Jinja2 environment
        template_dirs = []
        
        # Add custom template directory if provided
        if config.template_dir:
            template_dirs.append(config.template_dir)
        
        # Add default template directory
        default_template_dir = os.path.join(
            os.path.dirname(__file__), "templates"
        )
        template_dirs.append(default_template_dir)
        
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dirs),
            autoescape=jinja2.select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Create output directory if it doesn't exist
        os.makedirs(config.output_dir, exist_ok=True)
    
    def generate_documentation(self, repo_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Markdown documentation for a repository.
        
        Args:
            repo_analysis: Repository analysis results
            
        Returns:
            Dictionary with documentation generation statistics
        """
        repo_path = repo_analysis.get("repo_path", "")
        file_results = repo_analysis.get("file_results", {})
        frameworks = repo_analysis.get("frameworks", [])
        
        logger.info(f"Generating documentation for {len(file_results)} files")
        
        # Track documentation statistics
        stats = {
            "total_files": len(file_results),
            "documentation_files_generated": 0,
            "skipped_files": 0,
            "index_files": 0
        }
        
        # Generate a documentation file for each source file
        for file_path, file_result in file_results.items():
            if self._should_exclude(file_path):
                stats["skipped_files"] += 1
                continue
            
            try:
                doc_file_path = self._generate_file_documentation(
                    file_path, file_result, repo_path, frameworks, file_results
                )
                stats["documentation_files_generated"] += 1
                logger.debug(f"Generated documentation for {file_path}")
            except Exception as e:
                logger.error(f"Error generating documentation for {file_path}: {str(e)}")
        
        # Generate index files
        self._generate_indexes(repo_path, file_results, frameworks)
        stats["index_files"] += 1
        
        logger.info(f"Documentation generation complete: {stats['documentation_files_generated']} files")
        return stats
    
    def _should_exclude(self, file_path: str) -> bool:
        """Check if a file should be excluded from documentation."""
        for pattern in self.config.exclude_patterns:
            if pattern in file_path:
                return True
        return False
    
    def _generate_file_documentation(
        self, 
        file_path: str, 
        file_result: Dict[str, Any],
        repo_path: str,
        frameworks: List[Dict[str, Any]],
        file_results: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate documentation for a single file.
        
        Args:
            file_path: Path to the source file
            file_result: Analysis results for the file
            repo_path: Root path of the repository
            frameworks: List of frameworks used in the repository
            
        Returns:
            Path to the generated documentation file
        """
        # Create relative path for documentation
        rel_path = self._get_relative_path(file_path, repo_path)
        doc_file_path = os.path.join(
            self.config.output_dir, 
            f"{rel_path}.md"
        )
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(doc_file_path), exist_ok=True)
        
        # Get file information
        file_type = file_result.get("file_type", "unknown")
        language = file_result.get("language", "unknown")
        
        # Get code structure
        code_structure = file_result.get("code_structure", {})
        classes = code_structure.get("structure", {}).get("classes", [])
        functions = code_structure.get("structure", {}).get("functions", [])
        imports = code_structure.get("structure", {}).get("imports", [])
        variables = code_structure.get("structure", {}).get("variables", [])
        
        # Get frameworks used in this file
        file_frameworks = file_result.get("frameworks", [])
        file_framework_details = []
        
        # Match file frameworks with repository frameworks for details
        for file_fw in file_frameworks:
            fw_name = file_fw.get("name", "")
            for repo_fw in frameworks:
                if repo_fw.get("name", "") == fw_name:
                    file_framework_details.append(repo_fw)
                    break
        
        # We've moved away from code snippets to direct links to source files
        code_snippet = None
        # Keep the parameter in context for backward compatibility
        # but the value will always be None
        
        # Get file relationships if enabled
        relationships = None
        if self.config.include_relationships:
            # Use file_results parameter for relationship analysis
            if file_results is None:
                file_results = {file_path: file_result}
            relationships = self._get_file_relationships(file_path, repo_path, file_results)
        
        # Prepare template context
        context = {
            "file_path": file_path,
            "rel_path": rel_path,
            "file_type": file_type,
            "language": language,
            "classes": classes,
            "functions": functions,
            "imports": imports,
            "variables": variables,
            "frameworks": file_frameworks,
            "framework_details": file_framework_details if self.config.include_framework_details else None,
            "code_snippet": code_snippet,
            "relationships": relationships
        }
        
        # Determine which template to use based on language or file type
        template_name = self._get_template_for_file(language, file_type)
        
        # Render template
        template = self.jinja_env.get_template(template_name)
        doc_content = template.render(**context)
        
        # Write documentation file
        with open(doc_file_path, "w") as f:
            f.write(doc_content)
        
        return doc_file_path
    
    def _generate_indexes(
        self, 
        repo_path: str, 
        file_results: Dict[str, Any],
        frameworks: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate index files for documentation navigation.
        
        Args:
            repo_path: Root path of the repository
            file_results: Analysis results for all files
            frameworks: List of frameworks used in the repository
            
        Returns:
            List of generated index file paths
        """
        # Generate main index file
        main_index_path = os.path.join(self.config.output_dir, "index.md")
        
        # Group files by directory
        directories = {}
        for file_path in file_results.keys():
            rel_path = self._get_relative_path(file_path, repo_path)
            directory = os.path.dirname(rel_path)
            
            if directory not in directories:
                directories[directory] = []
            
            directories[directory].append(rel_path)
        
        # Prepare template context
        context = {
            "repo_path": repo_path,
            "directories": directories,
            "frameworks": frameworks,
            "total_files": len(file_results),
            "is_root_index": True,
            "now": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Render main index template
        template = self.jinja_env.get_template("index.md.j2")
        index_content = template.render(**context)
        
        # Write main index file
        with open(main_index_path, "w") as f:
            f.write(index_content)
        
        # Generate directory-level index files
        generated_indexes = [main_index_path]
        
        # Create a list of all directories and subdirectories
        all_dirs = set()
        for file_path in file_results.keys():
            rel_path = self._get_relative_path(file_path, repo_path)
            dir_components = os.path.dirname(rel_path).split(os.path.sep)
            
            # Add all parent directories to the set
            current_path = ""
            for component in dir_components:
                if not component:  # Skip empty components
                    continue
                
                if current_path:
                    current_path = os.path.join(current_path, component)
                else:
                    current_path = component
                
                all_dirs.add(current_path)
        
        # Sort directories by depth (parent directories first)
        sorted_dirs = sorted(all_dirs, key=lambda x: x.count(os.path.sep))
        
        # Create index file for each directory
        for directory in sorted_dirs:
            # Filter files that are directly in this directory
            dir_files = []
            
            # Get all subdirectories of this directory
            subdirs = set()
            
            for file_path, file_result in file_results.items():
                rel_path = self._get_relative_path(file_path, repo_path)
                file_dir = os.path.dirname(rel_path)
                
                # Check if this file is directly in the current directory
                if file_dir == directory:
                    dir_files.append({
                        "path": rel_path,
                        "name": os.path.basename(rel_path),
                        "file_type": file_result.get("file_type", "unknown"),
                        "language": file_result.get("language", "unknown")
                    })
                
                # Check if this file is in a subdirectory of the current directory
                elif file_dir.startswith(directory + os.path.sep):
                    # Get the next level subdirectory
                    subdir = file_dir.split(directory + os.path.sep, 1)[1].split(os.path.sep)[0]
                    subdirs.add(os.path.join(directory, subdir))
            
            # Create the directory index context
            dir_context = {
                "directory": directory,
                "files": dir_files,
                "subdirectories": sorted(subdirs),
                "is_root_index": False,
                "parent_directory": os.path.dirname(directory) if directory.count(os.path.sep) > 0 else "",
                "repo_path": repo_path,
                "now": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Render the directory index template
            dir_index_content = template.render(**dir_context)
            
            # Create output directory if it doesn't exist
            dir_index_path = os.path.join(self.config.output_dir, directory, "index.md")
            os.makedirs(os.path.dirname(dir_index_path), exist_ok=True)
            
            # Write the directory index file
            with open(dir_index_path, "w") as f:
                f.write(dir_index_content)
            
            generated_indexes.append(dir_index_path)
            logger.debug(f"Generated directory index for {directory}")
        
        return generated_indexes
    
    def _get_relative_path(self, file_path: str, repo_path: str) -> str:
        """Get relative path from repository root."""
        if file_path.startswith(repo_path):
            return file_path[len(repo_path):].lstrip("/").lstrip("\\")
        return file_path
    
    def _get_code_snippet(self, file_path: str) -> Optional[str]:
        """
        Get a code snippet from the file.
        
        Note: This method is deprecated as we now use direct links to source files
        instead of embedding code snippets. Kept for backward compatibility.
        """
        logger.debug(f"Code snippets have been replaced with direct links to source files")
        return None
    
    def _get_file_relationships(
        self, 
        file_path: str, 
        repo_path: str,
        file_results: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Identify relationships between files.
        
        This method attempts to find:
        - Files that import this file
        - Files that this file imports
        - Related files (shared classes, etc.)
        
        Args:
            file_path: Path to the source file
            repo_path: Root path of the repository
            file_results: Analysis results for all files
            
        Returns:
            Dictionary with relationship information
        """
        # Initialize relationships
        relationships = {
            "imports": [],     # Files this file imports
            "imported_by": [], # Files that import this file
            "related": []      # Other related files
        }
        
        # Get information about this file
        file_result = file_results.get(file_path, {})
        imports = file_result.get("code_structure", {}).get("structure", {}).get("imports", [])
        classes = file_result.get("code_structure", {}).get("structure", {}).get("classes", [])
        language = file_result.get("language", "").lower()
        
        # Get the file's basename and module name for import matching
        file_basename = os.path.basename(file_path)
        module_name = os.path.splitext(file_basename)[0]
        
        # Get the file's directory for relative import matching
        file_dir = os.path.dirname(file_path)
        
        # Advanced import matching based on language
        import_patterns = self._get_language_import_patterns(file_path, module_name)
        
        # Check all other files for relationships
        for other_path, other_result in file_results.items():
            if other_path == file_path:
                continue
            
            # Get other file's information
            other_imports = other_result.get("code_structure", {}).get("structure", {}).get("imports", [])
            other_classes = other_result.get("code_structure", {}).get("structure", {}).get("classes", [])
            other_language = other_result.get("language", "").lower()
            
            # Get other file's basename and module for matching
            other_basename = os.path.basename(other_path)
            other_module = os.path.splitext(other_basename)[0]
            
            # Get other file's patterns for import matching
            other_import_patterns = self._get_language_import_patterns(other_path, other_module)
            
            # Check if the other file imports this file
            imported_by = False
            for imp in other_imports:
                for pattern in import_patterns:
                    if pattern in imp:
                        rel_path = self._get_relative_path(other_path, repo_path)
                        if rel_path not in relationships["imported_by"]:
                            relationships["imported_by"].append(rel_path)
                            imported_by = True
                            break
                if imported_by:
                    break
            
            # Check if this file imports the other file
            imports_other = False
            for imp in imports:
                for pattern in other_import_patterns:
                    if pattern in imp:
                        rel_path = self._get_relative_path(other_path, repo_path)
                        if rel_path not in relationships["imports"]:
                            relationships["imports"].append(rel_path)
                            imports_other = True
                            break
                if imports_other:
                    break
            
            # Look for related files based on shared classes/inheritance
            if classes and other_classes and language == other_language:
                # Simple check for classes with the same name in both files
                this_class_names = [c.get("name", "") for c in classes]
                other_class_names = [c.get("name", "") for c in other_classes]
                
                # Check for class name prefix matches (potential inheritance)
                for this_class in this_class_names:
                    for other_class in other_class_names:
                        if (this_class and other_class and 
                            (this_class.startswith(other_class) or 
                             other_class.startswith(this_class) or
                             this_class == other_class)):
                            rel_path = self._get_relative_path(other_path, repo_path)
                            if (rel_path not in relationships["related"] and
                                rel_path not in relationships["imports"] and
                                rel_path not in relationships["imported_by"]):
                                relationships["related"].append(rel_path)
                                break
        
        # Sort relationships for consistent output
        relationships["imports"].sort()
        relationships["imported_by"].sort()
        relationships["related"].sort()
                    
        return relationships
    
    def _get_template_for_file(self, language: str, file_type: str) -> str:
        """
        Determine the appropriate template for a file based on language and type.
        
        Args:
            language: The programming language of the file
            file_type: The type of the file
            
        Returns:
            The name of the template to use
        """
        # Convert to lowercase for consistent matching
        language = language.lower() if language else ""
        file_type = file_type.lower() if file_type else ""
        
        # Available templates (in priority order)
        available_templates = self.jinja_env.list_templates()
        
        # Check for language-specific template
        if f"{language}_file.md.j2" in available_templates:
            return f"{language}_file.md.j2"
        
        # Special case for web-related files
        if language in ["html", "css"] or file_type in ["html", "css"]:
            if "web_file.md.j2" in available_templates:
                return "web_file.md.j2"
        
        # Special case for JavaScript/TypeScript files
        if language in ["javascript", "typescript", "jsx", "tsx"] or file_type in ["javascript", "typescript"]:
            if "javascript_file.md.j2" in available_templates:
                return "javascript_file.md.j2"
            elif "web_file.md.j2" in available_templates:  # Fallback to web_file if javascript template doesn't exist
                return "web_file.md.j2"
        
        # Special case for Java files
        if language in ["java", "kotlin"] or file_type in ["java", "kotlin"]:
            if "java_file.md.j2" in available_templates:
                return "java_file.md.j2"
        
        # Special case for C/C++ files
        if language in ["c", "cpp", "c++"] or file_type in ["c", "cpp", "c++"]:
            if "c_cpp_file.md.j2" in available_templates:
                return "c_cpp_file.md.j2"
        
        # Special case for configuration files
        if file_type == "config" or language in ["json", "yaml", "toml", "ini"]:
            if "config_file.md.j2" in available_templates:
                return "config_file.md.j2"
        
        # Special case for markup files
        if language in ["markdown", "restructuredtext", "asciidoc"] or file_type in ["markdown", "markup", "documentation"]:
            if "markup_file.md.j2" in available_templates:
                return "markup_file.md.j2"
        
        # Fallback to generic template
        return "generic_file.md.j2"
    
    def _get_language_import_patterns(self, file_path: str, module_name: str) -> List[str]:
        """
        Get language-specific import patterns for a file.
        
        Args:
            file_path: Path to the file
            module_name: Name of the module (filename without extension)
            
        Returns:
            List of patterns to match imports of this file
        """
        # Initialize with the basic module name pattern
        patterns = [module_name]
        
        # Get file extension (language indicator)
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Python-specific import patterns
        if ext in ['.py', '.pyi', '.pyx']:
            # Handle potential absolute and relative imports
            file_dir = os.path.dirname(file_path)
            dir_parts = file_dir.split(os.path.sep)
            
            # Add potential Python import patterns
            for i in range(len(dir_parts), 0, -1):
                pkg_path = '.'.join(dir_parts[-i:] + [module_name])
                if pkg_path:
                    patterns.append(pkg_path)
            
            # Add patterns for module elements (.function or .Class)
            patterns.append(f"{module_name}.")
            
            # Add patterns for 'from x import y' style
            patterns.append(f"from {module_name}")
            patterns.append(f"from {module_name}.")
        
        # JavaScript/TypeScript specific import patterns
        elif ext in ['.js', '.jsx', '.ts', '.tsx']:
            # Handle potential relative imports
            patterns.append(f"from '{module_name}")
            patterns.append(f"from \"./{module_name}")
            patterns.append(f"from '../{module_name}")
            patterns.append(f"import {module_name}")
            patterns.append(f"import {{ {module_name}")
            patterns.append(f"require('{module_name}")
            patterns.append(f"require(\"./{module_name}")
        
        # Java/Kotlin specific patterns
        elif ext in ['.java', '.kt', '.scala']:
            # Handle package imports
            patterns.append(f"import {module_name}")
            patterns.append(f"import static {module_name}")
            
        # C/C++ specific patterns
        elif ext in ['.c', '.cpp', '.h', '.hpp', '.cc', '.cxx', '.c++', '.hxx', '.h++']:
            # Handle different include patterns
            patterns.append(f'#include "{module_name}')
            patterns.append(f'#include "{module_name}.h')
            patterns.append(f'#include "{module_name}.hpp')
            patterns.append(f'#include <{module_name}')
            patterns.append(f'#include <{module_name}.h')
            patterns.append(f'#include <{module_name}.hpp')
            
            # Handle directory-based includes
            file_dir = os.path.dirname(file_path)
            dir_name = os.path.basename(file_dir)
            if dir_name:
                patterns.append(f'#include "{dir_name}/{module_name}')
                patterns.append(f'#include <{dir_name}/{module_name}')
        
        return patterns


def generate_documentation(
    repo_analysis: Dict[str, Any],
    output_dir: str,
    template_dir: Optional[str] = None,
    include_code_snippets: bool = True,
    max_code_snippet_lines: int = 15,
    include_relationships: bool = True,
    include_framework_details: bool = True,
    exclude_patterns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate Markdown documentation for a repository.
    
    This is a convenience function that creates a MarkdownGenerator
    and generates documentation in one step.
    
    Args:
        repo_analysis: Repository analysis results
        output_dir: Directory where documentation will be generated
        template_dir: Custom template directory (optional)
        include_code_snippets: Whether to include code snippets
        max_code_snippet_lines: Maximum lines for code snippets
        include_relationships: Whether to include file relationships
        include_framework_details: Whether to include framework details
        exclude_patterns: Patterns of files to exclude from documentation
        
    Returns:
        Dictionary with documentation generation statistics
    """
    config = DocumentationConfig(
        output_dir=output_dir,
        template_dir=template_dir,
        include_code_snippets=include_code_snippets,
        max_code_snippet_lines=max_code_snippet_lines,
        include_relationships=include_relationships,
        include_framework_details=include_framework_details,
        exclude_patterns=exclude_patterns or []
    )
    
    generator = MarkdownGenerator(config)
    return generator.generate_documentation(repo_analysis)