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

from file_analyzer.core.file_reader import FileReader
from file_analyzer.doc_generator.ai_documentation_generator import (
    generate_file_documentation,
    AiDocumentationGenerator
)

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
        include_ai_documentation: bool = True,
        ai_provider: Optional[Any] = None,
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
            include_ai_documentation: Whether to include AI-generated documentation
            ai_provider: AI provider to use for documentation generation
            exclude_patterns: Patterns of files to exclude from documentation
        """
        self.output_dir = output_dir
        self.template_dir = template_dir
        self.include_code_snippets = include_code_snippets
        self.max_code_snippet_lines = max_code_snippet_lines
        self.include_relationships = include_relationships
        self.include_framework_details = include_framework_details
        self.include_ai_documentation = include_ai_documentation
        self.ai_provider = ai_provider
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
        
        # Add custom filters
        self.jinja_env.filters['basename'] = lambda path: os.path.basename(path)
        
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
        
        # Generate AI documentation if enabled
        ai_documentation = None
        if self.config.include_ai_documentation:
            try:
                # Read file content
                file_reader = FileReader()
                try:
                    file_content = file_reader.read_file(file_path)
                    
                    # Generate AI documentation
                    ai_documentation = generate_file_documentation(
                        file_path=file_path,
                        content=file_content,
                        metadata=file_result,
                        ai_provider=self.config.ai_provider
                    )
                    logger.debug(f"Generated AI documentation for {file_path}")
                except Exception as e:
                    logger.warning(f"Could not read file content for AI documentation: {file_path}: {str(e)}")
            except Exception as e:
                logger.error(f"Error generating AI documentation for {file_path}: {str(e)}")
        
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
            "relationships": relationships,
            "graph_data": relationships.get("graph_data") if relationships else None,
            "ai_documentation": ai_documentation
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
        
        # Find key files in the repository (files with most relationships)
        key_files = []
        
        # Calculate relationship count for each file
        for file_path, file_result in file_results.items():
            rel_path = self._get_relative_path(file_path, repo_path)
            
            # Skip if this file should be excluded
            if self._should_exclude(file_path):
                continue
            
            if self.config.include_relationships:
                relationships = self._get_file_relationships(file_path, repo_path, file_results)
                relationship_count = sum(len(relationships[rel_type]) for rel_type in relationships 
                                         if rel_type != "graph_data")
                
                if relationship_count > 0:
                    # Get a description for the file from code structure if available
                    description = ""
                    if "code_structure" in file_result:
                        doc = file_result.get("code_structure", {}).get("documentation", "")
                        if doc:
                            description = doc.split("\n")[0][:100]  # First line, truncated
                    
                    key_files.append({
                        "path": rel_path,
                        "name": os.path.basename(rel_path),
                        "relationship_count": relationship_count,
                        "description": description
                    })
        
        # Sort by relationship count (most related files first)
        key_files.sort(key=lambda x: x["relationship_count"], reverse=True)
        
        # Limit to top 10 most connected files
        key_files = key_files[:10]
        
        # Prepare template context
        context = {
            "repo_path": repo_path,
            "directories": directories,
            "frameworks": frameworks,
            "total_files": len(file_results),
            "is_root_index": True,
            "now": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "key_files": key_files
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
                    # Calculate relationship count if enabled
                    relationship_count = 0
                    if self.config.include_relationships:
                        relationships = self._get_file_relationships(file_path, repo_path, file_results)
                        relationship_count = sum(len(relationships[rel_type]) for rel_type in relationships 
                                               if rel_type != "graph_data")
                    
                    dir_files.append({
                        "path": rel_path,
                        "name": os.path.basename(rel_path),
                        "file_type": file_result.get("file_type", "unknown"),
                        "language": file_result.get("language", "unknown"),
                        "relationship_count": relationship_count
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
    ) -> Dict[str, Any]:
        """
        Identify relationships between files.
        
        This method attempts to find:
        - Files that import this file
        - Files that this file imports
        - Related files through inheritance
        - Related files through shared types/classes
        - Referenced files (function calls, etc.)
        
        Args:
            file_path: Path to the source file
            repo_path: Root path of the repository
            file_results: Analysis results for all files
            
        Returns:
            Dictionary with relationship information and graph data
        """
        # Initialize relationships
        relationships = {
            "imports": [],           # Files this file imports
            "imported_by": [],       # Files that import this file
            "inherits_from": [],     # Files whose classes this file inherits from
            "inherited_by": [],      # Files with classes that inherit from this file's classes
            "references": [],        # Files this file references (function calls, etc.)
            "referenced_by": [],     # Files that reference this file (function calls, etc.)
            "related": []            # Other related files (shared types, etc.)
        }
        
        # Get information about this file
        file_result = file_results.get(file_path, {})
        imports = file_result.get("code_structure", {}).get("structure", {}).get("imports", [])
        classes = file_result.get("code_structure", {}).get("structure", {}).get("classes", [])
        functions = file_result.get("code_structure", {}).get("structure", {}).get("functions", [])
        language = file_result.get("language", "").lower()
        
        # Get the file's basename and module name for import matching
        file_basename = os.path.basename(file_path)
        module_name = os.path.splitext(file_basename)[0]
        
        # Get the file's directory for relative import matching
        file_dir = os.path.dirname(file_path)
        
        # Advanced import matching based on language
        import_patterns = self._get_language_import_patterns(file_path, module_name)
        
        # Get inheritance info for classes in this file
        inheritance_info = self._extract_inheritance_info(classes, language)
        
        # Get function calls to detect references
        function_calls = self._extract_function_calls(file_result, language)
        
        # Check all other files for relationships
        for other_path, other_result in file_results.items():
            if other_path == file_path:
                continue
            
            # Get other file's information
            other_imports = other_result.get("code_structure", {}).get("structure", {}).get("imports", [])
            other_classes = other_result.get("code_structure", {}).get("structure", {}).get("classes", [])
            other_functions = other_result.get("code_structure", {}).get("structure", {}).get("functions", [])
            other_language = other_result.get("language", "").lower()
            
            # Get other file's basename and module for matching
            other_basename = os.path.basename(other_path)
            other_module = os.path.splitext(other_basename)[0]
            
            # Get other file's patterns for import matching
            other_import_patterns = self._get_language_import_patterns(other_path, other_module)
            
            # Get relative path for the other file
            rel_path = self._get_relative_path(other_path, repo_path)
            
            # Check if the other file imports this file
            imported_by = False
            for imp in other_imports:
                for pattern in import_patterns:
                    if pattern in imp:
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
                        if rel_path not in relationships["imports"]:
                            relationships["imports"].append(rel_path)
                            imports_other = True
                            break
                if imports_other:
                    break
            
            # Skip further relationship checks if languages don't match
            if language != other_language:
                continue
                
            # Check for inheritance relationships
            other_inheritance_info = self._extract_inheritance_info(other_classes, other_language)
            
            # Check if this file's classes inherit from other file's classes
            for this_class, parent_classes in inheritance_info['inherits'].items():
                for parent in parent_classes:
                    if parent in [c.get("name", "") for c in other_classes]:
                        if rel_path not in relationships["inherits_from"]:
                            relationships["inherits_from"].append(rel_path)
            
            # Check if other file's classes inherit from this file's classes
            for other_class, parent_classes in other_inheritance_info['inherits'].items():
                for parent in parent_classes:
                    if parent in [c.get("name", "") for c in classes]:
                        if rel_path not in relationships["inherited_by"]:
                            relationships["inherited_by"].append(rel_path)
            
            # Check for function references
            other_function_calls = self._extract_function_calls(other_result, other_language)
            
            # Check if this file references functions in other file
            for func_call in function_calls:
                if func_call in [f.get("name", "") for f in other_functions]:
                    if rel_path not in relationships["references"]:
                        relationships["references"].append(rel_path)
            
            # Check if other file references functions in this file
            for func_call in other_function_calls:
                if func_call in [f.get("name", "") for f in functions]:
                    if rel_path not in relationships["referenced_by"]:
                        relationships["referenced_by"].append(rel_path)
            
            # Look for related files based on shared types/classes
            if classes and other_classes:
                # Check for shared class names or similar class names
                this_class_names = [c.get("name", "") for c in classes]
                other_class_names = [c.get("name", "") for c in other_classes]
                
                # Check for class name similarities
                for this_class in this_class_names:
                    for other_class in other_class_names:
                        # Skip if already in another relationship category
                        if (rel_path in relationships["imports"] or 
                            rel_path in relationships["imported_by"] or
                            rel_path in relationships["inherits_from"] or
                            rel_path in relationships["inherited_by"] or
                            rel_path in relationships["references"] or
                            rel_path in relationships["referenced_by"]):
                            continue
                            
                        # Check for similarity in class names (potential relation)
                        if (this_class and other_class and 
                            (this_class.startswith(other_class) or 
                             other_class.startswith(this_class) or
                             this_class == other_class or
                             self._are_names_related(this_class, other_class))):
                            if rel_path not in relationships["related"]:
                                relationships["related"].append(rel_path)
                                break
        
        # Sort relationships for consistent output
        for key in relationships:
            relationships[key].sort()
        
        # Generate dependency graph data for visualization
        graph_data = self._generate_graph_data(file_path, repo_path, relationships)
        
        # Add graph data to relationships dictionary
        relationships["graph_data"] = graph_data
                    
        return relationships
        
    def _extract_inheritance_info(self, classes: List[Dict[str, Any]], language: str) -> Dict[str, Dict[str, List[str]]]:
        """
        Extract inheritance information from classes.
        
        Args:
            classes: List of class definitions
            language: Programming language
            
        Returns:
            Dictionary with inheritance information
        """
        inheritance = {
            "inherits": {},    # Maps class names to their parent classes
            "inherited_by": {} # Maps class names to classes that inherit from them
        }
        
        for cls in classes:
            class_name = cls.get("name", "")
            parent_classes = []
            
            # Extract parent classes based on language
            if language == "python":
                # Look for Python-style inheritance in class definition
                definition = cls.get("definition", "")
                if definition and "(" in definition and ")" in definition:
                    parents_str = definition.split("(", 1)[1].split(")", 1)[0].strip()
                    if parents_str and parents_str != "object":
                        parent_classes = [p.strip() for p in parents_str.split(",")]
            
            elif language in ["java", "kotlin"]:
                # Look for Java-style inheritance
                extends = cls.get("extends", "")
                implements = cls.get("implements", [])
                
                if extends:
                    parent_classes.append(extends)
                if implements:
                    parent_classes.extend(implements)
            
            elif language in ["javascript", "typescript"]:
                # Look for JavaScript/TypeScript inheritance
                extends = cls.get("extends", "")
                if extends:
                    parent_classes.append(extends)
            
            elif language in ["c++", "cpp", "c"]:
                # Look for C++ inheritance
                if "inherits" in cls:
                    parent_classes = cls.get("inherits", [])
            
            # Store inheritance information
            if parent_classes:
                inheritance["inherits"][class_name] = parent_classes
                
                # Also track classes that are inherited from
                for parent in parent_classes:
                    if parent not in inheritance["inherited_by"]:
                        inheritance["inherited_by"][parent] = []
                    inheritance["inherited_by"][parent].append(class_name)
        
        return inheritance
    
    def _extract_function_calls(self, file_result: Dict[str, Any], language: str) -> List[str]:
        """
        Extract function calls from file content to detect references.
        
        Args:
            file_result: Analysis results for a file
            language: Programming language
            
        Returns:
            List of potential function call names
        """
        function_calls = []
        
        # Extract function calls from content analysis if available
        if "function_calls" in file_result.get("code_structure", {}).get("structure", {}):
            return file_result["code_structure"]["structure"]["function_calls"]
        
        # Fallback: analyze imports for potential function references
        imports = file_result.get("code_structure", {}).get("structure", {}).get("imports", [])
        for imp in imports:
            # Look for specific imports that might indicate function usage
            if language == "python":
                # Python from x import y pattern often indicates function usage
                if imp.startswith("from ") and " import " in imp:
                    modules = imp.split(" import ")[1].split(",")
                    for module in modules:
                        module = module.strip().split(" as ")[0]
                        if not module.startswith("_") and module[0].islower():  # Likely a function not a class
                            function_calls.append(module)
            
            elif language in ["javascript", "typescript"]:
                # ES6 destructuring imports often include functions
                if "import {" in imp:
                    imports_str = imp.split("{")[1].split("}")[0]
                    items = [item.strip().split(" as ")[0] for item in imports_str.split(",")]
                    for item in items:
                        if item and item[0].islower():  # Likely a function not a class
                            function_calls.append(item)
        
        return function_calls
    
    def _are_names_related(self, name1: str, name2: str) -> bool:
        """
        Check if two names are semantically related.
        
        Args:
            name1: First name
            name2: Second name
            
        Returns:
            True if names are related, False otherwise
        """
        # Check for common prefixes/suffixes that might indicate relationship
        if len(name1) > 3 and len(name2) > 3:
            # Check if one name contains the other
            name1_lower = name1.lower()
            name2_lower = name2.lower()
            
            # Check for common root (removing common prefixes/suffixes)
            prefixes = ["base", "abstract", "generic", "i"]  # Interface prefix
            suffixes = ["impl", "implementation", "service", "handler", "manager", "factory", "builder"]
            
            # Remove prefixes
            name1_cleaned = name1_lower
            name2_cleaned = name2_lower
            
            for prefix in prefixes:
                if name1_cleaned.startswith(prefix):
                    name1_cleaned = name1_cleaned[len(prefix):]
                if name2_cleaned.startswith(prefix):
                    name2_cleaned = name2_cleaned[len(prefix):]
            
            # Remove suffixes
            for suffix in suffixes:
                if name1_cleaned.endswith(suffix):
                    name1_cleaned = name1_cleaned[:-len(suffix)]
                if name2_cleaned.endswith(suffix):
                    name2_cleaned = name2_cleaned[:-len(suffix)]
            
            # Check if the cleaned names are similar
            if (name1_cleaned and name2_cleaned and
                (name1_cleaned in name2_cleaned or
                 name2_cleaned in name1_cleaned)):
                return True
        
        return False
        
    def _generate_graph_data(self, file_path: str, repo_path: str, relationships: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Generate data for dependency graph visualization.
        
        Args:
            file_path: Path to the current file
            repo_path: Root path of the repository
            relationships: Dictionary of relationships
            
        Returns:
            Dictionary with graph data
        """
        rel_path = self._get_relative_path(file_path, repo_path)
        
        # Initialize graph data
        graph_data = {
            "current_file": rel_path,
            "nodes": [
                {"id": rel_path, "type": "current", "label": os.path.basename(rel_path)}
            ],
            "edges": []
        }
        
        # Add nodes and edges for each relationship type
        relationship_types = {
            "imports": {"direction": "outgoing", "color": "#3498db", "label": "imports"},
            "imported_by": {"direction": "incoming", "color": "#2ecc71", "label": "imports"},
            "inherits_from": {"direction": "outgoing", "color": "#e74c3c", "label": "inherits from"},
            "inherited_by": {"direction": "incoming", "color": "#9b59b6", "label": "inherits from"},
            "references": {"direction": "outgoing", "color": "#f1c40f", "label": "references"},
            "referenced_by": {"direction": "incoming", "color": "#1abc9c", "label": "references"},
            "related": {"direction": "bidirectional", "color": "#95a5a6", "label": "related to"}
        }
        
        # Track added nodes to avoid duplicates
        added_nodes = {rel_path}
        
        # Add nodes and edges for each relationship type
        for rel_type, files in relationships.items():
            if rel_type == "graph_data":
                continue
                
            rel_config = relationship_types.get(rel_type)
            if not rel_config:
                continue
                
            for related_file in files:
                # Add node if not already added
                if related_file not in added_nodes:
                    graph_data["nodes"].append({
                        "id": related_file,
                        "type": rel_type,
                        "label": os.path.basename(related_file)
                    })
                    added_nodes.add(related_file)
                
                # Add edge based on direction
                if rel_config["direction"] == "outgoing":
                    graph_data["edges"].append({
                        "from": rel_path,
                        "to": related_file,
                        "type": rel_type,
                        "color": rel_config["color"],
                        "label": rel_config["label"]
                    })
                elif rel_config["direction"] == "incoming":
                    graph_data["edges"].append({
                        "from": related_file,
                        "to": rel_path,
                        "type": rel_type,
                        "color": rel_config["color"],
                        "label": rel_config["label"]
                    })
                else:  # bidirectional
                    graph_data["edges"].append({
                        "from": rel_path,
                        "to": related_file,
                        "type": rel_type,
                        "color": rel_config["color"],
                        "label": rel_config["label"],
                        "bidirectional": True
                    })
        
        return graph_data
    
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
    include_ai_documentation: bool = True,
    ai_provider: Optional[Any] = None,
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
        include_ai_documentation: Whether to include AI-generated documentation
        ai_provider: AI provider to use for documentation generation
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
        include_ai_documentation=include_ai_documentation,
        ai_provider=ai_provider,
        exclude_patterns=exclude_patterns or []
    )
    
    generator = MarkdownGenerator(config)
    return generator.generate_documentation(repo_analysis)