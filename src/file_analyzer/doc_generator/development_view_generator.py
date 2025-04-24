"""
Development View Diagram Generator implementation.

This module provides the DevelopmentViewGenerator class for creating UML diagrams
that represent the development structure of a codebase (package diagrams and component diagrams).
"""
import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from collections import defaultdict

from file_analyzer.doc_generator.base_diagram_generator import BaseDiagramGenerator
from file_analyzer.ai_providers.provider_interface import AIModelProvider
from file_analyzer.core.file_reader import FileReader
from file_analyzer.core.file_hasher import FileHasher
from file_analyzer.core.cache_provider import CacheProvider
from file_analyzer.core.code_analyzer import CodeAnalyzer
from file_analyzer.utils.exceptions import FileAnalyzerError

logger = logging.getLogger("file_analyzer.development_view_generator")


class DevelopmentViewGenerator(BaseDiagramGenerator):
    """
    Generates UML Development View diagrams for code repositories.
    
    Creates package diagrams and component diagrams using Mermaid syntax
    based on structure data extracted during repository analysis.
    """
    
    def __init__(
        self,
        ai_provider: AIModelProvider,
        code_analyzer: Optional[CodeAnalyzer] = None,
        file_reader: Optional[FileReader] = None,
        file_hasher: Optional[FileHasher] = None,
        cache_provider: Optional[CacheProvider] = None,
    ):
        """
        Initialize the development view generator.
        
        Args:
            ai_provider: Provider for AI model access
            code_analyzer: CodeAnalyzer for analyzing code files (optional)
            file_reader: Component for reading files (optional)
            file_hasher: Component for hashing files (optional)
            cache_provider: Provider for caching results (optional)
        """
        super().__init__(
            ai_provider=ai_provider,
            code_analyzer=code_analyzer,
            file_reader=file_reader,
            file_hasher=file_hasher,
            cache_provider=cache_provider
        )
        
        # Extend stats with development view specific metrics
        self.stats.update({
            "package_diagrams_generated": 0,
            "component_diagrams_generated": 0,
            "packages_identified": 0,
            "components_identified": 0,
            "dependencies_mapped": 0
        })
    
    def generate_diagram(self, repo_path: Union[str, Path], diagram_type: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a development view diagram of the specified type.
        
        Args:
            repo_path: Path to the repository root
            diagram_type: Type of diagram to generate ('package', 'component')
            **kwargs: Additional arguments for specific diagram types
            
        Returns:
            Dictionary containing diagram data with Mermaid syntax
        """
        result = None
        
        if diagram_type == "package":
            result = self.generate_package_diagram(repo_path, **kwargs)
        elif diagram_type == "component":
            result = self.generate_component_diagram(repo_path, **kwargs)
        else:
            raise ValueError(f"Unsupported diagram type: {diagram_type}")
        
        # Update base stats
        self.stats["diagrams_generated"] += 1
        
        return result
    
    def generate_package_diagram(
        self, 
        repo_path: Union[str, Path], 
        max_depth: int = 3,
        include_patterns: List[str] = None,
        exclude_patterns: List[str] = None,
        title: str = "Package Diagram"
    ) -> Dict[str, Any]:
        """
        Generate a UML package diagram showing the organization of code.
        
        Args:
            repo_path: Path to the repository root
            max_depth: Maximum depth of packages to display
            include_patterns: Optional list of patterns to include (e.g., ["src/**"])
            exclude_patterns: Optional list of patterns to exclude (e.g., ["**/test/**"])
            title: Title for the diagram
            
        Returns:
            Dictionary containing diagram data with Mermaid syntax
        """
        repo_path = Path(repo_path) if isinstance(repo_path, str) else repo_path
        
        # Prepare include/exclude patterns
        include_patterns = include_patterns or ["**"]
        exclude_patterns = exclude_patterns or [
            "**/.git/**", "**/node_modules/**", "**/__pycache__/**", 
            "**/venv/**", "**/env/**", "**/.venv/**", "**/build/**", "**/dist/**"
        ]
        
        # Check cache with normalized patterns
        patterns_key = f"{sorted(include_patterns)}:{sorted(exclude_patterns)}:{max_depth}"
        cache_key = f"package_diagram:{repo_path}:{self.file_hasher.get_string_hash(patterns_key)}"
        cached_result = self._check_cache(cache_key)
        if cached_result:
            return cached_result
        
        # Identify packages from directory structure
        packages, dependencies = self._analyze_package_structure(
            repo_path, max_depth, include_patterns, exclude_patterns
        )
        
        # Generate diagram
        diagram = self._generate_mermaid_package_diagram(packages, dependencies, title)
        
        # Prepare result
        result = {
            "title": title,
            "diagram_type": "package",
            "syntax_type": "mermaid",
            "content": diagram,
            "packages": packages,
            "dependencies": dependencies,
            "metadata": {
                "repository": str(repo_path),
                "package_count": len(packages),
                "dependency_count": len(dependencies),
                "max_depth": max_depth
            }
        }
        
        # Cache result
        self._save_to_cache(cache_key, result)
        
        # Update stats
        self.stats["package_diagrams_generated"] += 1
        self.stats["packages_identified"] += len(packages)
        self.stats["dependencies_mapped"] += len(dependencies)
        
        return result
    
    def generate_component_diagram(
        self, 
        repo_path: Union[str, Path], 
        focus_area: str = None,
        title: str = "Component Diagram"
    ) -> Dict[str, Any]:
        """
        Generate a UML component diagram showing high-level components and interfaces.
        
        Args:
            repo_path: Path to the repository root
            focus_area: Optional sub-path to focus on
            title: Title for the diagram
            
        Returns:
            Dictionary containing diagram data with Mermaid syntax
        """
        repo_path = Path(repo_path) if isinstance(repo_path, str) else repo_path
        
        # Determine focus path
        focus_path = repo_path
        if focus_area:
            focus_path = repo_path / focus_area
            if not focus_path.exists() or not focus_path.is_dir():
                raise FileNotFoundError(f"Focus area not found: {focus_path}")
        
        # Check cache
        cache_key = f"component_diagram:{focus_path}"
        cached_result = self._check_cache(cache_key)
        if cached_result:
            return cached_result
        
        # Identify components and interfaces
        components, interfaces, dependencies = self._analyze_component_structure(focus_path)
        
        # Generate diagram
        diagram = self._generate_mermaid_component_diagram(components, interfaces, dependencies, title)
        
        # Prepare result
        result = {
            "title": title,
            "diagram_type": "component",
            "syntax_type": "mermaid",
            "content": diagram,
            "components": components,
            "interfaces": interfaces,
            "dependencies": dependencies,
            "metadata": {
                "repository": str(repo_path),
                "focus_area": focus_area,
                "component_count": len(components),
                "interface_count": len(interfaces),
                "dependency_count": len(dependencies)
            }
        }
        
        # Cache result
        self._save_to_cache(cache_key, result)
        
        # Update stats
        self.stats["component_diagrams_generated"] += 1
        self.stats["components_identified"] += len(components)
        self.stats["dependencies_mapped"] += len(dependencies)
        
        return result
    
    def _analyze_package_structure(
        self, 
        repo_path: Path, 
        max_depth: int,
        include_patterns: List[str],
        exclude_patterns: List[str]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Analyze the package structure of a repository.
        
        Args:
            repo_path: Path to the repository root
            max_depth: Maximum depth of packages to analyze
            include_patterns: List of patterns to include
            exclude_patterns: List of patterns to exclude
            
        Returns:
            Tuple of (packages, dependencies)
        """
        packages = []
        dependencies = []
        package_map = {}  # Map package paths to their indices
        
        # Helper function to check if a path should be included
        def should_include(path: Path) -> bool:
            rel_path = str(path.relative_to(repo_path))
            
            # Check exclude patterns first
            for pattern in exclude_patterns:
                if self._match_glob_pattern(rel_path, pattern):
                    return False
            
            # Check include patterns
            for pattern in include_patterns:
                if self._match_glob_pattern(rel_path, pattern):
                    return True
            
            return False
        
        # First pass: identify packages
        for root, dirs, files in os.walk(repo_path):
            root_path = Path(root)
            
            # Skip if should be excluded
            if not should_include(root_path):
                # Also remove directories to avoid descending into them
                dirs[:] = []
                continue
            
            # Calculate depth
            depth = len(root_path.relative_to(repo_path).parts)
            if depth > max_depth:
                dirs[:] = []  # Don't go deeper
                continue
            
            # Check for package markers (e.g., __init__.py for Python)
            is_python_package = any(f == "__init__.py" for f in files)
            is_java_package = any(f.endswith(".java") for f in files)
            is_js_module = any(f in ["package.json", "index.js"] for f in files)
            
            # Determine package type
            package_type = None
            if is_python_package:
                package_type = "python"
            elif is_java_package:
                package_type = "java"
            elif is_js_module:
                package_type = "javascript"
            elif files:  # Any directory with code files is considered a package
                package_type = "generic"
            
            if package_type:
                # Create package info
                rel_path = root_path.relative_to(repo_path)
                package_name = rel_path.name
                package_path = str(rel_path)
                parent_path = str(rel_path.parent) if rel_path.parent != Path(".") else None
                
                package_info = {
                    "id": len(packages),
                    "name": package_name,
                    "path": package_path,
                    "parent": parent_path,
                    "type": package_type,
                    "depth": depth,
                    "file_count": len([f for f in files if not f.startswith(".") and not f.startswith("__")])
                }
                
                packages.append(package_info)
                package_map[package_path] = package_info["id"]
        
        # Second pass: identify dependencies between packages
        for package_info in packages:
            package_path = Path(repo_path) / package_info["path"]
            
            # Check imports in files
            for root, _, files in os.walk(package_path):
                for file in files:
                    file_path = Path(root) / file
                    
                    # Skip non-code files
                    if not self._is_code_file(file_path):
                        continue
                    
                    try:
                        # Get file content
                        content = self.file_reader.read_file(file_path)
                        
                        # Find imports based on file type
                        imports = self._extract_imports(file_path, content)
                        
                        # Map imports to packages
                        for imp in imports:
                            target_package = self._find_package_for_import(imp, packages, repo_path)
                            if target_package and target_package["id"] != package_info["id"]:
                                # Add dependency if not already exists
                                dependency = {
                                    "source": package_info["id"],
                                    "target": target_package["id"],
                                    "type": "import"
                                }
                                
                                # Check if dependency already exists
                                if not any(
                                    d["source"] == dependency["source"] and 
                                    d["target"] == dependency["target"] 
                                    for d in dependencies
                                ):
                                    dependencies.append(dependency)
                    except Exception as e:
                        logger.error(f"Error analyzing imports in {file_path}: {str(e)}")
        
        return packages, dependencies
    
    def _analyze_component_structure(
        self, 
        focus_path: Path
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Analyze the component structure of a repository area.
        
        Args:
            focus_path: Path to analyze
            
        Returns:
            Tuple of (components, interfaces, dependencies)
        """
        components = []
        interfaces = []
        dependencies = []
        
        # Maps to track components and interfaces
        component_map = {}  # name -> id
        interface_map = {}  # name -> id
        
        # Find all code files
        code_files = []
        for root, _, files in os.walk(focus_path):
            for file in files:
                file_path = Path(root) / file
                if self._is_code_file(file_path):
                    code_files.append(file_path)
        
        # Group files into components based on directories
        component_files = defaultdict(list)
        for file in code_files:
            rel_path = file.relative_to(focus_path)
            
            # Use the first directory level as component
            if len(rel_path.parts) > 1:
                component_name = rel_path.parts[0]
            else:
                # Files at the root level go into a "core" component
                component_name = "core"
            
            component_files[component_name].append(file)
        
        # Analyze each component
        for component_name, files in component_files.items():
            # Create component
            component_info = {
                "id": len(components),
                "name": component_name,
                "files": [str(f.relative_to(focus_path)) for f in files],
                "file_count": len(files),
                "provides": [],  # Interfaces provided
                "requires": []   # Interfaces required
            }
            
            components.append(component_info)
            component_map[component_name] = component_info["id"]
            
            # Analyze files to find interfaces and dependencies
            for file in files:
                try:
                    # Check if file might define an interface
                    if self._is_potential_interface(file):
                        # Add as an interface provided by this component
                        interface_name = file.stem
                        if "interface" in interface_name.lower():
                            # Clean up name
                            interface_name = re.sub(r'interface|Interface', '', interface_name)
                        
                        # Create interface if new
                        if interface_name not in interface_map:
                            interface_info = {
                                "id": len(interfaces),
                                "name": interface_name,
                                "file": str(file.relative_to(focus_path))
                            }
                            interfaces.append(interface_info)
                            interface_map[interface_name] = interface_info["id"]
                        
                        # Add to component's provided interfaces
                        if interface_map[interface_name] not in component_info["provides"]:
                            component_info["provides"].append(interface_map[interface_name])
                    
                    # Check for dependencies on other components
                    content = self.file_reader.read_file(file)
                    for other_component_name, other_component_id in component_map.items():
                        # Skip self
                        if other_component_name == component_name:
                            continue
                        
                        # Check if this file imports from other component
                        if self._check_component_dependency(content, other_component_name):
                            # Create dependency
                            dependency = {
                                "source": component_info["id"],
                                "target": other_component_id,
                                "type": "uses"
                            }
                            
                            # Check if dependency already exists
                            if not any(
                                d["source"] == dependency["source"] and 
                                d["target"] == dependency["target"] 
                                for d in dependencies
                            ):
                                dependencies.append(dependency)
                                
                                # Check if there's an interface involved
                                for interface_id in components[other_component_id]["provides"]:
                                    # Add interface to required list
                                    if interface_id not in component_info["requires"]:
                                        component_info["requires"].append(interface_id)
                except Exception as e:
                    logger.error(f"Error analyzing component file {file}: {str(e)}")
        
        return components, interfaces, dependencies
    
    def _match_glob_pattern(self, path: str, pattern: str) -> bool:
        """
        Check if a path matches a glob pattern.
        
        Args:
            path: Path to check
            pattern: Glob pattern
            
        Returns:
            True if the path matches the pattern
        """
        # Convert glob pattern to regex pattern
        regex_pattern = pattern.replace(".", r"\.").replace("**", ".+").replace("*", "[^/]+")
        return bool(re.match(f"^{regex_pattern}$", path))
    
    def _is_code_file(self, file_path: Path) -> bool:
        """
        Check if a file is a code file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if it's a code file
        """
        code_extensions = [".py", ".java", ".js", ".jsx", ".ts", ".tsx", ".cs", ".cpp", ".c", ".go", ".rb"]
        return file_path.suffix in code_extensions
    
    def _extract_imports(self, file_path: Path, content: str) -> List[str]:
        """
        Extract imports from file content.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            List of imported modules/packages
        """
        imports = []
        
        # Check file type based on extension
        if file_path.suffix == ".py":
            # Python imports
            import_patterns = [
                r'import\s+([\w\.]+)',
                r'from\s+([\w\.]+)\s+import'
            ]
            
            for pattern in import_patterns:
                for match in re.finditer(pattern, content):
                    imports.append(match.group(1))
        
        elif file_path.suffix in [".java"]:
            # Java imports
            import_pattern = r'import\s+([\w\.]+)[\.\*];'
            
            for match in re.finditer(import_pattern, content):
                imports.append(match.group(1))
        
        elif file_path.suffix in [".js", ".jsx", ".ts", ".tsx"]:
            # JavaScript/TypeScript imports
            import_patterns = [
                r'import.*from\s+[\'"]([\.\/\w]+)[\'"]',
                r'require\s*\(\s*[\'"]([\.\/\w]+)[\'"]\s*\)'
            ]
            
            for pattern in import_patterns:
                for match in re.finditer(pattern, content):
                    # Clean up relative paths
                    imp = match.group(1)
                    if imp.startswith("./") or imp.startswith("../"):
                        continue  # Skip relative imports for now (would need path resolution)
                    
                    # Handle node_modules imports
                    if not imp.startswith("."):
                        parts = imp.split("/")
                        if parts[0].startswith("@"):
                            # Scoped package
                            if len(parts) > 1:
                                imports.append(f"{parts[0]}/{parts[1]}")
                        else:
                            imports.append(parts[0])
        
        return imports
    
    def _find_package_for_import(self, import_path: str, packages: List[Dict[str, Any]], repo_path: Path) -> Optional[Dict[str, Any]]:
        """
        Find the package that provides an import.
        
        Args:
            import_path: Import path
            packages: List of packages
            repo_path: Repository root path
            
        Returns:
            Package info or None if not found
        """
        # Convert import path to possible file paths
        import_parts = import_path.split(".")
        
        for i in range(len(import_parts), 0, -1):
            # Try with decreasing specificity
            partial_path = os.path.join(*import_parts[:i])
            
            # Check if any package path matches
            for package in packages:
                package_path = package["path"]
                
                # Check if import path is in this package
                if package_path.endswith(partial_path) or partial_path.endswith(package_path):
                    return package
        
        return None
    
    def _is_potential_interface(self, file_path: Path) -> bool:
        """
        Check if a file might define an interface.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file might define an interface
        """
        # Check filename for clues
        filename = file_path.stem.lower()
        if "interface" in filename or "abstract" in filename:
            return True
        
        # Check by extension
        if file_path.suffix == ".py":
            # For Python, look for abstract classes or protocol classes
            try:
                content = self.file_reader.read_file(file_path)
                if "ABC" in content or "metaclass=ABCMeta" in content or "Protocol" in content:
                    return True
                
                # Check for abstract methods
                if "@abstractmethod" in content:
                    return True
                
                # Check for interface-like classes (only abstract methods)
                if re.search(r"class\s+\w+.*:", content) and "pass" in content:
                    return True
            except:
                pass
        
        elif file_path.suffix == ".java":
            # For Java, check if it's an interface or abstract class
            try:
                content = self.file_reader.read_file(file_path)
                if "interface " in content or "abstract class " in content:
                    return True
            except:
                pass
        
        elif file_path.suffix in [".ts", ".tsx"]:
            # For TypeScript, check for interface definitions
            try:
                content = self.file_reader.read_file(file_path)
                if "interface " in content or "abstract class " in content:
                    return True
            except:
                pass
        
        return False
    
    def _check_component_dependency(self, content: str, component_name: str) -> bool:
        """
        Check if content has dependencies on a component.
        
        Args:
            content: File content
            component_name: Component name to check for
            
        Returns:
            True if dependency found
        """
        # Simple check for imports containing component name
        import_patterns = [
            rf'import\s+[\w\s{{}}]+\s+from\s+[\'"].*{component_name}[\'"]',
            rf'import\s+[\w\.{component_name}]+',
            rf'from\s+[\w\.]*{component_name}[\w\.]*\s+import',
            rf'require\s*\(\s*[\'"].*{component_name}.*[\'"]\s*\)'
        ]
        
        for pattern in import_patterns:
            if re.search(pattern, content):
                return True
        
        return False
    
    def _generate_mermaid_package_diagram(
        self, 
        packages: List[Dict[str, Any]], 
        dependencies: List[Dict[str, Any]], 
        title: str
    ) -> str:
        """
        Generate a Mermaid package diagram from package and dependency data.
        
        Args:
            packages: List of packages
            dependencies: List of dependencies between packages
            title: Title for the diagram
            
        Returns:
            String with Mermaid diagram syntax
        """
        diagram = f"flowchart TB\n    %% {title}\n"
        
        # Add packages
        for pkg in packages:
            pkg_id = f"pkg{pkg['id']}"
            pkg_name = pkg["name"]
            
            diagram += f"    {pkg_id}[\"<&folder> {pkg_name}\"]\n"
            
            # Create subgraph for nested packages
            nested_packages = [p for p in packages if p.get("parent") == pkg["path"]]
            if nested_packages:
                diagram += f"    subgraph {pkg_id}_sg[\"{pkg_name}\"]\n"
                for nested in nested_packages:
                    diagram += f"        pkg{nested['id']}\n"
                diagram += "    end\n"
        
        # Add dependencies
        for dep in dependencies:
            source_id = f"pkg{dep['source']}"
            target_id = f"pkg{dep['target']}"
            
            # Add arrow showing dependency
            diagram += f"    {source_id} --> {target_id}\n"
        
        return diagram
    
    def _generate_mermaid_component_diagram(
        self, 
        components: List[Dict[str, Any]], 
        interfaces: List[Dict[str, Any]], 
        dependencies: List[Dict[str, Any]], 
        title: str
    ) -> str:
        """
        Generate a Mermaid component diagram from component, interface and dependency data.
        
        Args:
            components: List of components
            interfaces: List of interfaces
            dependencies: List of dependencies between components
            title: Title for the diagram
            
        Returns:
            String with Mermaid diagram syntax
        """
        diagram = f"flowchart LR\n    %% {title}\n"
        
        # Add components
        for comp in components:
            comp_id = f"comp{comp['id']}"
            comp_name = comp["name"]
            
            diagram += f"    {comp_id}[[\"<&cog> {comp_name}\"]]\n"
        
        # Add interfaces
        for intf in interfaces:
            intf_id = f"intf{intf['id']}"
            intf_name = intf["name"]
            
            diagram += f"    {intf_id}([\"<&transfer> {intf_name}\"])\n"
        
        # Add component-interface relationships
        for comp in components:
            comp_id = f"comp{comp['id']}"
            
            # Add provided interfaces
            for intf_id in comp.get("provides", []):
                diagram += f"    {comp_id} --> intf{intf_id}\n"
            
            # Add required interfaces
            for intf_id in comp.get("requires", []):
                diagram += f"    intf{intf_id} --> {comp_id}\n"
        
        # Add direct dependencies between components
        for dep in dependencies:
            source_id = f"comp{dep['source']}"
            target_id = f"comp{dep['target']}"
            
            # Check if there's already an interface connecting them
            source_comp = components[dep["source"]]
            target_comp = components[dep["target"]]
            
            has_interface_connection = any(
                intf_id in target_comp.get("provides", []) and
                intf_id in source_comp.get("requires", [])
                for intf_id in range(len(interfaces))
            )
            
            # Only add direct connection if no interface connects them
            if not has_interface_connection:
                diagram += f"    {source_id} -.-> {target_id}\n"
        
        return diagram