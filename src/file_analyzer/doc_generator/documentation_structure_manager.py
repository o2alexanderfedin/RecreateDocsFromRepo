"""
Documentation structure manager for creating hierarchical and logically organized documentation.

This module extends the basic documentation generation by providing a hierarchical
structure that groups files by module, package, or functionality rather than just
by directory structure.
"""
import os
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
import jinja2

from file_analyzer.doc_generator.markdown_formatter import (
    sanitize_markdown,
    create_anchor_link
)

logger = logging.getLogger("file_analyzer.doc_generator")


class DocumentationStructureConfig:
    """Configuration for documentation structure organization."""
    
    def __init__(
        self,
        output_dir: str,
        template_dir: Optional[str] = None,
        max_depth: int = 3,
        adapt_depth_to_size: bool = True,
        group_by_functionality: bool = True,
        min_files_for_grouping: int = 3,
        include_architecture_view: bool = True,
        include_component_view: bool = True,
        exclude_patterns: Optional[List[str]] = None
    ):
        """
        Initialize documentation structure configuration.
        
        Args:
            output_dir: Directory where documentation will be generated
            template_dir: Custom template directory (optional)
            max_depth: Maximum depth for hierarchical structure
            adapt_depth_to_size: Whether to adjust depth based on repository size
            group_by_functionality: Whether to group files by functionality
            min_files_for_grouping: Minimum files required to create a group
            include_architecture_view: Whether to include architecture view
            include_component_view: Whether to include component view
            exclude_patterns: Patterns of files to exclude from documentation
        """
        self.output_dir = output_dir
        self.template_dir = template_dir
        self.max_depth = max_depth
        self.adapt_depth_to_size = adapt_depth_to_size
        self.group_by_functionality = group_by_functionality
        self.min_files_for_grouping = min_files_for_grouping
        self.include_architecture_view = include_architecture_view
        self.include_component_view = include_component_view
        self.exclude_patterns = exclude_patterns or []


class DocumentationStructureManager:
    """
    Manages the structure and organization of generated documentation.
    
    This class implements a hierarchical documentation structure that goes beyond
    simple directory-based organization, creating logical groupings based on
    functionality, modules, and relationships between files.
    """
    
    def __init__(self, config: DocumentationStructureConfig):
        """
        Initialize the documentation structure manager.
        
        Args:
            config: Documentation structure configuration
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
        self.jinja_env.filters['sanitize_markdown'] = sanitize_markdown
        self.jinja_env.filters['create_anchor'] = create_anchor_link
        
        # Create output directory if it doesn't exist
        os.makedirs(config.output_dir, exist_ok=True)
    
    def organize_documentation_structure(
        self,
        repo_path: str,
        file_results: Dict[str, Any],
        frameworks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create an organized documentation structure.
        
        Args:
            repo_path: Root path of the repository
            file_results: Analysis results for all files
            frameworks: List of frameworks used in the repository
            
        Returns:
            Dictionary with structure organization information
        """
        # Extract relationships from file_results
        relationships = self._extract_relationships(file_results)
        
        # Create logical grouping of files
        logical_groups = self.create_logical_grouping(repo_path, file_results, relationships)
        
        # Generate hierarchical structure
        hierarchy = self.generate_hierarchical_structure(repo_path, file_results, relationships)
        
        # Generate component view if enabled
        component_view = None
        if self.config.include_component_view:
            component_view = self.generate_component_view(repo_path, file_results, relationships)
        
        # Generate architecture view if enabled
        architecture_view = None
        if self.config.include_architecture_view:
            architecture_view = self.generate_architecture_view(
                repo_path, file_results, relationships, frameworks
            )
        
        # Create structure organization
        structure = self.create_structure_organization(repo_path, file_results, frameworks)
        
        # Generate structure index files
        index_files = self.generate_structure_indexes(
            repo_path, file_results, relationships, frameworks,
            hierarchy, logical_groups, component_view, architecture_view
        )
        
        # Return structure information
        return {
            "logical_groups": logical_groups,
            "hierarchy": hierarchy,
            "component_view": component_view,
            "architecture_view": architecture_view,
            "structure": structure,
            "index_files": index_files
        }
    
    def create_structure_organization(
        self,
        repo_path: str,
        file_results: Dict[str, Any],
        frameworks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create structure organization for the documentation.
        
        Args:
            repo_path: Root path of the repository
            file_results: Analysis results for all files
            frameworks: List of frameworks used in the repository
            
        Returns:
            Dictionary with structure organization information
        """
        # Initialize structure
        structure = {
            "modules": {},  # Organized by module/package
            "components": {},  # Organized by functional component
            "configs": [],  # Configuration files
            "docs": [],  # Documentation files
            "tests": [],  # Test files
            "misc": []  # Miscellaneous files
        }
        
        # Process each file
        for file_path, file_result in file_results.items():
            # Skip excluded files
            if self._should_exclude(file_path):
                continue
            
            # Get relative path
            rel_path = self._get_relative_path(file_path, repo_path)
            
            # Get file information
            file_type = file_result.get("file_type", "unknown")
            language = file_result.get("language", "unknown")
            
            # Categorize file
            if file_type.lower() == "config" or language.lower() in ["json", "yaml", "toml", "ini"]:
                structure["configs"].append(rel_path)
            elif file_type.lower() in ["test", "tests"]:
                structure["tests"].append(rel_path)
            elif file_type.lower() in ["documentation", "markdown", "markup"]:
                structure["docs"].append(rel_path)
            else:
                # Organize by module
                module_path = os.path.dirname(rel_path)
                module_parts = module_path.split(os.path.sep)
                
                # Handle root files
                if not module_path:
                    if not "root" in structure["modules"]:
                        structure["modules"]["root"] = []
                    structure["modules"]["root"].append(rel_path)
                else:
                    # Get top-level module
                    top_module = module_parts[0]
                    
                    # Initialize module if not exists
                    if top_module not in structure["modules"]:
                        structure["modules"][top_module] = {}
                    
                    # Handle first-level module files
                    if len(module_parts) == 1:
                        if "files" not in structure["modules"][top_module]:
                            structure["modules"][top_module]["files"] = []
                        structure["modules"][top_module]["files"].append(rel_path)
                    else:
                        # Handle submodules
                        current_module = structure["modules"][top_module]
                        for i in range(1, len(module_parts)):
                            submodule = module_parts[i]
                            if "submodules" not in current_module:
                                current_module["submodules"] = {}
                            if submodule not in current_module["submodules"]:
                                current_module["submodules"][submodule] = {}
                            current_module = current_module["submodules"][submodule]
                            
                            # Add file to the deepest submodule
                            if i == len(module_parts) - 1:
                                if "files" not in current_module:
                                    current_module["files"] = []
                                current_module["files"].append(rel_path)
        
        # Sort files in each category
        structure["configs"].sort()
        structure["docs"].sort()
        structure["tests"].sort()
        structure["misc"].sort()
        
        # Sort files in modules
        self._sort_module_files(structure["modules"])
        
        return structure
    
    def create_logical_grouping(
        self,
        repo_path: str,
        file_results: Dict[str, Any],
        relationships: Dict[str, Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """
        Create logical grouping of files based on relationships and structure.
        
        Args:
            repo_path: Root path of the repository
            file_results: Analysis results for all files
            relationships: Relationships between files
            
        Returns:
            Dictionary mapping group names to lists of file paths
        """
        # Initialize groups by directory first
        directory_groups = {}
        
        # Group files by directory
        for file_path in file_results.keys():
            if self._should_exclude(file_path):
                continue
                
            rel_path = self._get_relative_path(file_path, repo_path)
            directory = os.path.dirname(rel_path)
            
            # Handle empty directory (root files)
            group_name = directory or "root"
            
            # Extract top-level directory as the main group
            if directory and "/" in directory:
                group_name = directory.split("/")[0]
            
            if group_name not in directory_groups:
                directory_groups[group_name] = []
            
            directory_groups[group_name].append(rel_path)
        
        # If not grouping by functionality, return directory groups
        if not self.config.group_by_functionality:
            return directory_groups
        
        # Initialize logical groups with directory groups
        logical_groups = directory_groups.copy()
        
        # Get file relationships to enhance grouping
        file_relationships = self._analyze_file_relationships(repo_path, file_results, relationships)
        
        # Identify strongly related files that should be grouped together
        for file_path, related_files in file_relationships.items():
            if len(related_files) >= 2:  # Files with multiple relationships
                rel_path = self._get_relative_path(file_path, repo_path)
                
                # Find files that are related but in different directories
                cross_directory_relations = []
                for related_file in related_files:
                    related_dir = os.path.dirname(related_file)
                    file_dir = os.path.dirname(rel_path)
                    
                    if related_dir and related_dir != file_dir:
                        cross_directory_relations.append(related_file)
                
                # If file has cross-directory relationships, consider functional grouping
                if cross_directory_relations:
                    self._process_functional_grouping(
                        logical_groups, rel_path, cross_directory_relations, file_results
                    )
        
        # Filter out groups that are too small
        return {k: v for k, v in logical_groups.items() if len(v) >= self.config.min_files_for_grouping}
    
    def generate_hierarchical_structure(
        self,
        repo_path: str,
        file_results: Dict[str, Any],
        relationships: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate hierarchical documentation structure.
        
        Args:
            repo_path: Root path of the repository
            file_results: Analysis results for all files
            relationships: Relationships between files
            
        Returns:
            Dictionary with hierarchical structure information
        """
        # Calculate optimal depth based on repository size
        optimal_depth = self._calculate_optimal_depth(file_results)
        
        # Initialize hierarchical structure
        hierarchy = {
            "root": {"files": [], "description": "Root level files"},
            "modules": {},
            "components": {}
        }
        
        # Process each file for the hierarchy
        for file_path, file_result in file_results.items():
            if self._should_exclude(file_path):
                continue
                
            rel_path = self._get_relative_path(file_path, repo_path)
            directory = os.path.dirname(rel_path)
            
            # Determine file category and description
            category, description = self._categorize_file(file_path, file_result)
            
            # Add root files to the root category
            if not directory:
                hierarchy["root"]["files"].append(rel_path)
                continue
            
            # Split directory into components
            components = directory.split(os.path.sep)
            
            # Limit depth based on optimal depth
            if len(components) > optimal_depth:
                # Only use top N levels for organization
                components = components[:optimal_depth]
            
            # Start with the modules section
            current_level = hierarchy["modules"]
            
            # Build the hierarchy
            for i, component in enumerate(components):
                if component not in current_level:
                    current_level[component] = {
                        "files": [],
                        "description": f"{component} module"
                    }
                
                # Add file to the current level if it's directly in this directory
                if i == len(components) - 1:
                    current_level[component]["files"].append(rel_path)
                
                # Move to the next level
                if "children" not in current_level[component]:
                    current_level[component]["children"] = {}
                current_level = current_level[component]["children"]
        
        # Create component-based grouping for hierarchy
        if self.config.include_component_view:
            component_view = self.generate_component_view(repo_path, file_results, relationships)
            hierarchy["components"] = component_view
        
        return hierarchy
    
    def generate_component_view(
        self,
        repo_path: str,
        file_results: Dict[str, Any],
        relationships: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate component-based view of the repository.
        
        Args:
            repo_path: Root path of the repository
            file_results: Analysis results for all files
            relationships: Relationships between files
            
        Returns:
            Dictionary with component view information
        """
        # Initialize component view
        components = {}
        
        # Define standard component categories
        standard_components = {
            "API": {
                "files": [],
                "description": "API and external interfaces",
                "keywords": ["api", "controller", "route", "endpoint", "service", "interface"]
            },
            "Core": {
                "files": [],
                "description": "Core business logic",
                "keywords": ["core", "main", "service", "model", "domain", "business"]
            },
            "Data": {
                "files": [],
                "description": "Data access and storage",
                "keywords": ["data", "repository", "dao", "database", "store", "storage", "model"]
            },
            "UI": {
                "files": [],
                "description": "User interface components",
                "keywords": ["ui", "view", "component", "page", "screen", "template"]
            },
            "Utilities": {
                "files": [],
                "description": "Utility functions and helpers",
                "keywords": ["util", "helper", "common", "toolkit", "lib", "tools"]
            },
            "Configuration": {
                "files": [],
                "description": "Configuration and settings",
                "keywords": ["config", "setting", "property", "env", "environment"]
            },
            "Infrastructure": {
                "files": [],
                "description": "Infrastructure and platform code",
                "keywords": ["infrastructure", "platform", "system", "framework", "setup"]
            }
        }
        
        # Initialize components with standard categories
        components = standard_components.copy()
        
        # Process each file for component classification
        for file_path, file_result in file_results.items():
            if self._should_exclude(file_path):
                continue
                
            rel_path = self._get_relative_path(file_path, repo_path)
            
            # Get file information
            file_type = file_result.get("file_type", "unknown").lower()
            language = file_result.get("language", "unknown").lower()
            documentation = file_result.get("code_structure", {}).get("documentation", "")
            
            # Default to "Other" category
            assigned_component = "Other"
            
            # Check for config files
            if file_type == "config" or language in ["json", "yaml", "toml", "ini"]:
                assigned_component = "Configuration"
            else:
                # Use filename, path, and documentation to assign component
                file_info = f"{rel_path} {documentation}".lower()
                
                # Check for component keywords
                for component, info in standard_components.items():
                    for keyword in info["keywords"]:
                        if keyword.lower() in file_info:
                            assigned_component = component
                            break
                    if assigned_component != "Other":
                        break
            
            # Create "Other" component if needed
            if assigned_component == "Other" and "Other" not in components:
                components["Other"] = {
                    "files": [],
                    "description": "Other components",
                    "keywords": []
                }
            
            # Add file to the assigned component
            components[assigned_component]["files"].append(rel_path)
        
        # Remove empty components
        components = {k: v for k, v in components.items() if v["files"]}
        
        # Sort files in each component
        for component in components.values():
            component["files"].sort()
        
        return components
    
    def generate_architecture_view(
        self,
        repo_path: str,
        file_results: Dict[str, Any],
        relationships: Dict[str, Dict[str, Any]],
        frameworks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate architecture view of the repository.
        
        Args:
            repo_path: Root path of the repository
            file_results: Analysis results for all files
            relationships: Relationships between files
            frameworks: List of frameworks used in the repository
            
        Returns:
            Dictionary with architecture view information
        """
        # Initialize architecture view
        architecture = {
            "layers": {
                "Presentation": {
                    "files": [],
                    "description": "UI, views, and presenters",
                    "keywords": ["ui", "view", "presenter", "component", "page", "screen"]
                },
                "Application": {
                    "files": [],
                    "description": "Application services and use cases",
                    "keywords": ["service", "usecase", "app", "application", "controller"]
                },
                "Domain": {
                    "files": [],
                    "description": "Domain model and business logic",
                    "keywords": ["domain", "model", "entity", "business", "core"]
                },
                "Infrastructure": {
                    "files": [],
                    "description": "Infrastructure and data access",
                    "keywords": ["infrastructure", "repository", "dao", "data", "database", "storage"]
                }
            },
            "cross_cutting": {
                "Configuration": {
                    "files": [],
                    "description": "Application configuration",
                    "keywords": ["config", "setting", "property", "env"]
                },
                "Security": {
                    "files": [],
                    "description": "Security and authentication",
                    "keywords": ["security", "auth", "authenticate", "permission", "access"]
                },
                "Logging": {
                    "files": [],
                    "description": "Logging and monitoring",
                    "keywords": ["log", "logger", "monitor", "trace", "debug"]
                },
                "Utils": {
                    "files": [],
                    "description": "Utilities and helpers",
                    "keywords": ["util", "helper", "common", "toolkit", "lib"]
                }
            },
            "frameworks": frameworks
        }
        
        # Process each file for architecture classification
        for file_path, file_result in file_results.items():
            if self._should_exclude(file_path):
                continue
                
            rel_path = self._get_relative_path(file_path, repo_path)
            
            # Get file information
            file_type = file_result.get("file_type", "unknown").lower()
            language = file_result.get("language", "unknown").lower()
            documentation = file_result.get("code_structure", {}).get("documentation", "")
            
            # Check for configuration files
            if file_type == "config" or language in ["json", "yaml", "toml", "ini"]:
                architecture["cross_cutting"]["Configuration"]["files"].append(rel_path)
                continue
            
            # Use filename, path, and documentation to assign architectural layer
            file_info = f"{rel_path} {documentation}".lower()
            
            # Try to assign to a layer
            assigned = False
            
            # Check for layer keywords
            for layer, info in architecture["layers"].items():
                for keyword in info["keywords"]:
                    if keyword.lower() in file_info:
                        architecture["layers"][layer]["files"].append(rel_path)
                        assigned = True
                        break
                if assigned:
                    break
            
            # If not assigned to a layer, check cross-cutting concerns
            if not assigned:
                for concern, info in architecture["cross_cutting"].items():
                    for keyword in info["keywords"]:
                        if keyword.lower() in file_info:
                            architecture["cross_cutting"][concern]["files"].append(rel_path)
                            assigned = True
                            break
                    if assigned:
                        break
            
            # If still not assigned, put in the most appropriate layer based on heuristics
            if not assigned:
                if "/api/" in rel_path.lower() or "controller" in rel_path.lower():
                    architecture["layers"]["Application"]["files"].append(rel_path)
                elif "/ui/" in rel_path.lower() or "/view/" in rel_path.lower():
                    architecture["layers"]["Presentation"]["files"].append(rel_path)
                elif "/model/" in rel_path.lower() or "/domain/" in rel_path.lower():
                    architecture["layers"]["Domain"]["files"].append(rel_path)
                elif "/data/" in rel_path.lower() or "/repository/" in rel_path.lower():
                    architecture["layers"]["Infrastructure"]["files"].append(rel_path)
                else:
                    # Default to Application layer if no better match
                    architecture["layers"]["Application"]["files"].append(rel_path)
        
        # Sort files in each layer and cross-cutting concern
        for layer in architecture["layers"].values():
            layer["files"].sort()
        
        for concern in architecture["cross_cutting"].values():
            concern["files"].sort()
        
        return architecture
    
    def generate_structure_indexes(
        self,
        repo_path: str,
        file_results: Dict[str, Any],
        relationships: Dict[str, Dict[str, Any]],
        frameworks: List[Dict[str, Any]],
        hierarchy: Optional[Dict[str, Any]] = None,
        logical_groups: Optional[Dict[str, List[str]]] = None,
        component_view: Optional[Dict[str, Any]] = None,
        architecture_view: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Generate index files for the documentation structure.
        
        For testing purposes: if hierarchy, logical_groups, component_view, or 
        architecture_view are None, they will be generated.
        
        Args:
            repo_path: Root path of the repository
            file_results: Analysis results for all files
            relationships: Relationships between files
            frameworks: List of frameworks used in the repository
            hierarchy: Hierarchical structure information (optional)
            logical_groups: Logical groups information (optional)
            component_view: Component view information (optional)
            architecture_view: Architecture view information (optional)
            
        Returns:
            List of generated index file paths
        """
        # List of generated index files
        index_files = []
        
        # Generate main index file
        main_index_path = os.path.join(self.config.output_dir, "index.md")
        
        # Calculate key statistics
        total_files = len(file_results)
        total_modules = len(logical_groups) if logical_groups else 0
        total_components = len(component_view) if component_view else 0
        
        # Find key files (most connected)
        key_files = self._identify_key_files(repo_path, file_results, relationships)
        
        # Prepare main index context
        main_context = {
            "repo_path": repo_path,
            "total_files": total_files,
            "total_modules": total_modules,
            "total_components": total_components,
            "frameworks": frameworks,
            "key_files": key_files,
            "logical_groups": logical_groups,
            "is_root_index": True,
            "now": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "has_component_view": component_view is not None,
            "has_architecture_view": architecture_view is not None
        }
        
        # Render main index template
        if self._template_exists("structure_index.md.j2"):
            template = self.jinja_env.get_template("structure_index.md.j2")
        else:
            # Fall back to standard index template
            template = self.jinja_env.get_template("index.md.j2")
            
        index_content = template.render(**main_context)
        
        # Write main index file
        os.makedirs(os.path.dirname(main_index_path), exist_ok=True)
        with open(main_index_path, "w") as f:
            f.write(index_content)
        
        index_files.append(main_index_path)
        
        # Generate architecture view index if available
        if architecture_view and self.config.include_architecture_view:
            architecture_index_path = os.path.join(self.config.output_dir, "architecture", "index.md")
            os.makedirs(os.path.dirname(architecture_index_path), exist_ok=True)
            
            # Prepare architecture context
            arch_context = {
                "architecture": architecture_view,
                "repo_path": repo_path,
                "frameworks": frameworks,
                "is_root_index": False,
                "now": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Render architecture index template
            if self._template_exists("architecture_index.md.j2"):
                template = self.jinja_env.get_template("architecture_index.md.j2")
                arch_content = template.render(**arch_context)
                
                # Write architecture index file
                with open(architecture_index_path, "w") as f:
                    f.write(arch_content)
                
                index_files.append(architecture_index_path)
        
        # Generate component view index if available
        if component_view and self.config.include_component_view:
            component_index_path = os.path.join(self.config.output_dir, "components", "index.md")
            os.makedirs(os.path.dirname(component_index_path), exist_ok=True)
            
            # Prepare component context
            comp_context = {
                "components": component_view,
                "repo_path": repo_path,
                "frameworks": frameworks,
                "is_root_index": False,
                "now": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Render component index template
            if self._template_exists("component_index.md.j2"):
                template = self.jinja_env.get_template("component_index.md.j2")
                comp_content = template.render(**comp_context)
                
                # Write component index file
                with open(component_index_path, "w") as f:
                    f.write(comp_content)
                
                index_files.append(component_index_path)
        
        # Generate module indexes if hierarchy is available
        if hierarchy and "modules" in hierarchy:
            # Create module index for each top-level module
            for module_name, module_info in hierarchy["modules"].items():
                module_index_path = os.path.join(self.config.output_dir, "modules", module_name, "index.md")
                os.makedirs(os.path.dirname(module_index_path), exist_ok=True)
                
                # Prepare module context
                module_context = {
                    "module_name": module_name,
                    "module_info": module_info,
                    "repo_path": repo_path,
                    "is_root_index": False,
                    "now": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Render module index template
                if self._template_exists("module_index.md.j2"):
                    template = self.jinja_env.get_template("module_index.md.j2")
                    module_content = template.render(**module_context)
                    
                    # Write module index file
                    with open(module_index_path, "w") as f:
                        f.write(module_content)
                    
                    index_files.append(module_index_path)
        
        # Return list of generated index files
        return index_files
    
    def _extract_relationships(self, file_results: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract relationships from file results."""
        relationships = {}
        
        # Check if relationships are already included in file results
        for file_path, file_result in file_results.items():
            if "relationships" in file_result:
                relationships[file_path] = file_result["relationships"]
        
        return relationships
    
    def _should_exclude(self, file_path: str) -> bool:
        """Check if a file should be excluded from documentation."""
        for pattern in self.config.exclude_patterns:
            if pattern in file_path:
                return True
        return False
    
    def _get_relative_path(self, file_path: str, repo_path: str) -> str:
        """Get relative path from repository root."""
        if file_path.startswith(repo_path):
            return file_path[len(repo_path):].lstrip("/").lstrip("\\")
        return file_path
    
    def _categorize_file(self, file_path: str, file_result: Dict[str, Any]) -> Tuple[str, str]:
        """Categorize a file and generate a description."""
        # Get file information
        file_type = file_result.get("file_type", "unknown")
        language = file_result.get("language", "unknown")
        documentation = file_result.get("code_structure", {}).get("documentation", "")
        
        # Default category
        category = "code"
        
        # Determine category based on file type and language
        if file_type.lower() == "config" or language.lower() in ["json", "yaml", "toml", "ini"]:
            category = "config"
        elif file_type.lower() in ["test", "tests"]:
            category = "test"
        elif file_type.lower() in ["documentation", "markdown", "markup"]:
            category = "docs"
        
        # Generate description
        description = documentation.split("\n")[0][:100] if documentation else ""
        if not description:
            basename = os.path.basename(file_path)
            description = f"{file_type} {language} file: {basename}"
        
        return category, description
    
    def _sort_module_files(self, modules: Dict[str, Any]) -> None:
        """Recursively sort files in modules and submodules."""
        for module_name, module_info in modules.items():
            if isinstance(module_info, dict):
                if "files" in module_info:
                    module_info["files"].sort()
                if "submodules" in module_info:
                    self._sort_module_files(module_info["submodules"])
            elif isinstance(module_info, list):
                # Handle case where module_info is just a list of files
                modules[module_name] = sorted(module_info)
    
    def _analyze_file_relationships(
        self,
        repo_path: str,
        file_results: Dict[str, Any],
        relationships: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Set[str]]:
        """
        Analyze relationships between files.
        
        Args:
            repo_path: Root path of the repository
            file_results: Analysis results for all files
            relationships: Relationships between files
            
        Returns:
            Dictionary mapping file paths to sets of related file paths
        """
        # Initialize relationship mapping
        file_relationships = {}
        
        # Process each file's relationships
        for file_path, file_result in file_results.items():
            if self._should_exclude(file_path):
                continue
                
            rel_path = self._get_relative_path(file_path, repo_path)
            file_relationships[rel_path] = set()
            
            # Get relationships for this file
            rel_data = relationships.get(file_path, {})
            
            # Add related files
            for rel_type in ["imports", "imported_by", "inherits_from", "inherited_by", "references", "referenced_by"]:
                if rel_type in rel_data and isinstance(rel_data[rel_type], list):
                    for related_file in rel_data[rel_type]:
                        file_relationships[rel_path].add(related_file)
        
        return file_relationships
    
    def _process_functional_grouping(
        self,
        logical_groups: Dict[str, List[str]],
        file_path: str,
        related_files: List[str],
        file_results: Dict[str, Any]
    ) -> None:
        """
        Process functional grouping for a file based on relationships.
        
        Args:
            logical_groups: Dictionary of logical groups
            file_path: Path to the file to process
            related_files: List of related file paths
            file_results: Analysis results for all files
        """
        # Get the current group for this file
        current_group = None
        for group, files in logical_groups.items():
            if file_path in files:
                current_group = group
                break
        
        # If the file doesn't have a current group, skip
        if not current_group:
            return
        
        # Count relationship groups
        relation_group_counts = {}
        
        # Count which groups the related files belong to
        for related_file in related_files:
            related_group = None
            for group, files in logical_groups.items():
                if related_file in files:
                    related_group = group
                    break
            
            if related_group and related_group != current_group:
                relation_group_counts[related_group] = relation_group_counts.get(related_group, 0) + 1
        
        # If there's a dominant relationship group, consider moving the file
        if relation_group_counts:
            dominant_group = max(relation_group_counts.items(), key=lambda x: x[1])[0]
            
            # Only move if the relationship is strong enough
            if relation_group_counts[dominant_group] >= 2:
                # Remove from current group
                logical_groups[current_group].remove(file_path)
                
                # Add to dominant relationship group
                logical_groups[dominant_group].append(file_path)
                
                # Clean up empty groups
                if not logical_groups[current_group]:
                    del logical_groups[current_group]
    
    def _calculate_optimal_depth(self, file_results: Dict[str, Any]) -> int:
        """Calculate optimal depth for hierarchical structure based on repository size."""
        # Default to configured max_depth
        depth = self.config.max_depth
        
        # If not adapting to size, return configured depth
        if not self.config.adapt_depth_to_size:
            return depth
        
        # Count total files
        total_files = len(file_results)
        
        # Adjust depth based on repository size
        if total_files < 20:
            depth = 1  # Very small repository
        elif total_files < 50:
            depth = 2  # Small repository
        elif total_files < 200:
            depth = 3  # Medium repository
        elif total_files < 500:
            depth = 4  # Large repository
        else:
            depth = 5  # Very large repository
        
        # Cap at configured max_depth
        return min(depth, self.config.max_depth)
    
    def _identify_key_files(
        self,
        repo_path: str,
        file_results: Dict[str, Any],
        relationships: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify key files in the repository based on relationships."""
        # List of key files
        key_files = []
        
        # Process each file
        for file_path, file_result in file_results.items():
            if self._should_exclude(file_path):
                continue
                
            rel_path = self._get_relative_path(file_path, repo_path)
            
            # Skip if this file should be excluded
            if self._should_exclude(file_path):
                continue
            
            # Get relationships for this file
            rel_data = relationships.get(file_path, {})
            
            # Calculate relationship count
            relationship_count = 0
            for rel_type in ["imports", "imported_by", "inherits_from", "inherited_by", "references", "referenced_by"]:
                if rel_type in rel_data and isinstance(rel_data[rel_type], list):
                    relationship_count += len(rel_data[rel_type])
            
            # Skip files with no relationships
            if relationship_count == 0:
                continue
            
            # Get a description for the file from code structure if available
            description = ""
            if "code_structure" in file_result:
                doc = file_result.get("code_structure", {}).get("documentation", "")
                if doc:
                    description = doc.split("\n")[0][:100]  # First line, truncated
            
            # Add to key files
            key_files.append({
                "path": rel_path,
                "name": os.path.basename(rel_path),
                "relationship_count": relationship_count,
                "description": description
            })
        
        # Sort by relationship count (most related files first)
        key_files.sort(key=lambda x: x["relationship_count"], reverse=True)
        
        # Limit to top 10 most connected files
        return key_files[:10]
    
    def _template_exists(self, template_name: str) -> bool:
        """Check if a template exists in the Jinja environment."""
        try:
            self.jinja_env.get_template(template_name)
            return True
        except jinja2.exceptions.TemplateNotFound:
            return False