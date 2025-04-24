"""
Logical View Diagram Generator implementation.

This module provides the LogicalViewGenerator class for creating UML diagrams
that represent the logical structure of a codebase (class diagrams, object models,
and state diagrams).
"""
import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple, Union

from file_analyzer.ai_providers.provider_interface import AIModelProvider
from file_analyzer.core.file_reader import FileReader
from file_analyzer.core.file_hasher import FileHasher
from file_analyzer.core.cache_provider import CacheProvider
from file_analyzer.core.code_analyzer import CodeAnalyzer
from file_analyzer.utils.exceptions import FileAnalyzerError

logger = logging.getLogger("file_analyzer.logical_view_generator")

class LogicalViewGenerator:
    """
    Generates UML Logical View diagrams for code repositories.
    
    Creates class diagrams, object models, and state diagrams
    using PlantUML or Mermaid syntax based on relationship data
    extracted during repository analysis.
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
        Initialize the logical view generator.
        
        Args:
            ai_provider: Provider for AI model access
            code_analyzer: CodeAnalyzer for analyzing code files (optional)
            file_reader: Component for reading files (optional)
            file_hasher: Component for hashing files (optional)
            cache_provider: Provider for caching results (optional)
        """
        self.ai_provider = ai_provider
        self.file_reader = file_reader or FileReader()
        self.file_hasher = file_hasher or FileHasher()
        self.cache_provider = cache_provider
        
        # Import at runtime to avoid circular imports
        if code_analyzer is None:
            from file_analyzer.core.code_analyzer import CodeAnalyzer as CA
            self.code_analyzer = CA(
                ai_provider=ai_provider,
                file_reader=self.file_reader,
                file_hasher=self.file_hasher,
                cache_provider=cache_provider
            )
        else:
            self.code_analyzer = code_analyzer
        
        # Statistics tracking
        self.stats = {
            "class_diagrams_generated": 0,
            "object_models_generated": 0,
            "state_diagrams_generated": 0,
            "total_classes": 0,
            "total_relationships": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }

    def generate_class_diagram(self, file_paths: List[Union[str, Path]], title: str = "Class Diagram") -> Dict[str, Any]:
        """
        Generate a UML class diagram for a set of files.
        
        Args:
            file_paths: List of file paths to include in the diagram
            title: Title for the diagram
            
        Returns:
            Dictionary containing diagram data with PlantUML or Mermaid syntax
        """
        # Normalize paths
        paths = [Path(p) if isinstance(p, str) else p for p in file_paths]
        
        # Check cache
        if self.cache_provider:
            cache_key = f"class_diagram:{self._hash_paths(paths)}"
            cached_result = self.cache_provider.get(cache_key)
            if cached_result:
                logger.debug(f"Using cached class diagram for {len(paths)} files")
                self.stats["cache_hits"] += 1
                return cached_result
            self.stats["cache_misses"] += 1
        
        # Collect class data from all files
        classes = []
        relationships = []
        
        for path in paths:
            # Analyze code for each file
            try:
                analysis = self.code_analyzer.analyze_code(str(path))
                
                # Extract classes and their properties
                for cls in analysis.get("structure", {}).get("classes", []):
                    classes.append({
                        "name": cls.get("name", "UnknownClass"),
                        "file_path": str(path),
                        "attributes": cls.get("attributes", []),
                        "methods": cls.get("methods", []),
                        "parent_classes": cls.get("inherits_from", []),
                        "interfaces": cls.get("implements", []),
                        "accessibility": cls.get("accessibility", "public")
                    })
                
                # Extract relationships
                for relationship in analysis.get("structure", {}).get("relationships", []):
                    relationships.append(relationship)
            except Exception as e:
                logger.error(f"Error analyzing {path} for class diagram: {str(e)}")
        
        # Generate diagram
        diagram = self._generate_mermaid_class_diagram(classes, relationships, title)
        
        # Prepare result
        result = {
            "title": title,
            "diagram_type": "class",
            "syntax_type": "mermaid",
            "content": diagram,
            "classes": classes,
            "relationships": relationships,
            "metadata": {
                "file_count": len(paths),
                "class_count": len(classes),
                "relationship_count": len(relationships)
            }
        }
        
        # Cache result
        if self.cache_provider:
            cache_key = f"class_diagram:{self._hash_paths(paths)}"
            self.cache_provider.set(cache_key, result)
        
        # Update stats
        self.stats["class_diagrams_generated"] += 1
        self.stats["total_classes"] += len(classes)
        self.stats["total_relationships"] += len(relationships)
        
        return result
    
    def generate_object_model(self, file_paths: List[Union[str, Path]], title: str = "Object Model") -> Dict[str, Any]:
        """
        Generate a UML object model diagram showing instance relationships.
        
        Args:
            file_paths: List of file paths to include in the diagram
            title: Title for the diagram
            
        Returns:
            Dictionary containing diagram data with PlantUML or Mermaid syntax
        """
        # Normalize paths
        paths = [Path(p) if isinstance(p, str) else p for p in file_paths]
        
        # Check cache
        if self.cache_provider:
            cache_key = f"object_model:{self._hash_paths(paths)}"
            cached_result = self.cache_provider.get(cache_key)
            if cached_result:
                logger.debug(f"Using cached object model for {len(paths)} files")
                self.stats["cache_hits"] += 1
                return cached_result
            self.stats["cache_misses"] += 1
        
        # Collect object instances and their relationships
        objects = []
        object_relationships = []
        
        for path in paths:
            try:
                # Analyze code for each file
                analysis = self.code_analyzer.analyze_code(str(path))
                
                # Find object instantiations (usually in functions or methods)
                for function in analysis.get("structure", {}).get("functions", []):
                    # Look for object instantiations in function body
                    if "body" in function:
                        self._extract_object_instances(
                            function.get("body", ""),
                            function.get("name", "unknown_function"),
                            str(path),
                            objects,
                            object_relationships
                        )
                
                # Also look in class methods
                for cls in analysis.get("structure", {}).get("classes", []):
                    for method in cls.get("methods", []):
                        if "body" in method:
                            self._extract_object_instances(
                                method.get("body", ""),
                                f"{cls.get('name', 'UnknownClass')}.{method.get('name', 'unknown_method')}",
                                str(path),
                                objects,
                                object_relationships
                            )
            except Exception as e:
                logger.error(f"Error analyzing {path} for object model: {str(e)}")
        
        # Generate diagram
        diagram = self._generate_mermaid_object_diagram(objects, object_relationships, title)
        
        # Prepare result
        result = {
            "title": title,
            "diagram_type": "object",
            "syntax_type": "mermaid",
            "content": diagram,
            "objects": objects,
            "relationships": object_relationships,
            "metadata": {
                "file_count": len(paths),
                "object_count": len(objects),
                "relationship_count": len(object_relationships)
            }
        }
        
        # Cache result
        if self.cache_provider:
            cache_key = f"object_model:{self._hash_paths(paths)}"
            self.cache_provider.set(cache_key, result)
        
        # Update stats
        self.stats["object_models_generated"] += 1
        
        return result
    
    def generate_state_diagram(self, file_path: Union[str, Path], title: str = None) -> Dict[str, Any]:
        """
        Generate a UML state diagram for a file that contains state machine behavior.
        
        Args:
            file_path: Path to the file to analyze
            title: Optional title for the diagram
            
        Returns:
            Dictionary containing diagram data with PlantUML or Mermaid syntax
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path
        
        if title is None:
            title = f"State Diagram: {path.name}"
        
        # Check cache
        if self.cache_provider:
            file_hash = self.file_hasher.get_file_hash(path)
            cache_key = f"state_diagram:{file_hash}"
            cached_result = self.cache_provider.get(cache_key)
            if cached_result:
                logger.debug(f"Using cached state diagram for {path}")
                self.stats["cache_hits"] += 1
                return cached_result
            self.stats["cache_misses"] += 1
        
        try:
            # Read file content
            content = self.file_reader.read_file(path)
            
            # Use AI to identify state machine behavior and generate diagram
            result = self._generate_state_diagram_with_ai(str(path), content, title)
            
            # Update stats
            self.stats["state_diagrams_generated"] += 1
            
            # Cache result
            if self.cache_provider:
                file_hash = self.file_hasher.get_file_hash(path)
                cache_key = f"state_diagram:{file_hash}"
                self.cache_provider.set(cache_key, result)
            
            return result
        except Exception as e:
            logger.error(f"Error generating state diagram for {path}: {str(e)}")
            return {
                "title": title,
                "diagram_type": "state",
                "syntax_type": "mermaid",
                "content": f"graph TD\n    A[Error] --> B[Could not generate state diagram: {str(e)}]",
                "states": [],
                "transitions": [],
                "error": str(e)
            }
    
    def generate_combined_class_diagram(self, repo_path: Union[str, Path], max_classes: int = 20) -> Dict[str, Any]:
        """
        Generate a combined class diagram for key components of a repository.
        
        Args:
            repo_path: Path to the repository root
            max_classes: Maximum number of classes to include
            
        Returns:
            Dictionary containing diagram data with PlantUML or Mermaid syntax
        """
        repo_path = Path(repo_path) if isinstance(repo_path, str) else repo_path
        
        # Check cache
        if self.cache_provider:
            cache_key = f"combined_class_diagram:{repo_path}:{max_classes}"
            cached_result = self.cache_provider.get(cache_key)
            if cached_result:
                logger.debug(f"Using cached combined class diagram for {repo_path}")
                self.stats["cache_hits"] += 1
                return cached_result
            self.stats["cache_misses"] += 1
        
        # Find all code files in the repository
        code_files = self._find_code_files(repo_path)
        
        # Select representative files based on importance
        important_files = self._select_important_files(code_files, max_classes)
        
        # Generate class diagram for selected files
        result = self.generate_class_diagram(
            important_files,
            title=f"Class Diagram: {repo_path.name} Key Components"
        )
        
        # Add repository context
        result["repository"] = str(repo_path)
        result["file_selection_strategy"] = "importance_based"
        
        # Cache result
        if self.cache_provider:
            cache_key = f"combined_class_diagram:{repo_path}:{max_classes}"
            self.cache_provider.set(cache_key, result)
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the diagram generation.
        
        Returns:
            Dictionary with generator statistics
        """
        return self.stats.copy()
    
    def _hash_paths(self, paths: List[Path]) -> str:
        """Calculate a hash for a list of file paths."""
        paths_str = "|".join(sorted([str(p) for p in paths]))
        return self.file_hasher.get_string_hash(paths_str)
    
    def _extract_object_instances(
        self, 
        code_snippet: str, 
        context: str, 
        file_path: str,
        objects: List[Dict[str, Any]], 
        relationships: List[Dict[str, Any]]
    ) -> None:
        """
        Extract object instances and their relationships from a code snippet.
        
        Args:
            code_snippet: Code to analyze for object instantiations
            context: Context where this code appears (function/method name)
            file_path: Path to the file
            objects: List to populate with found objects
            relationships: List to populate with found relationships
        """
        # Basic pattern for object instantiation in different languages
        # This is a simplified approach - in production, language-specific parsing would be better
        instantiation_patterns = {
            "python": r'(\w+)\s*=\s*(\w+)\((.*?)\)',  # var = Class(args)
            "java": r'(\w+)\s+(\w+)\s*=\s*new\s+(\w+)\((.*?)\)',  # Type var = new Type(args)
            "javascript": r'(const|let|var)?\s*(\w+)\s*=\s*new\s+(\w+)\((.*?)\)',  # const var = new Class(args)
        }
        
        # Determine language from file extension
        language = "python"  # Default
        if file_path.endswith(".java"):
            language = "java"
        elif file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
            language = "javascript"
        
        pattern = instantiation_patterns.get(language, instantiation_patterns["python"])
        
        # Extract instances
        import re
        for match in re.finditer(pattern, code_snippet):
            if language == "python":
                var_name, class_name, args = match.groups()
            elif language == "java":
                type_name, var_name, class_name, args = match.groups()
                # In Java, type and class might be different, check if class was matched
                if not class_name:
                    class_name = type_name
            else:  # javascript
                keyword, var_name, class_name, args = match.groups()
            
            # Add to objects list if not already there
            obj_id = f"{context}_{var_name}"
            if not any(o.get("id") == obj_id for o in objects):
                objects.append({
                    "id": obj_id,
                    "name": var_name,
                    "class": class_name,
                    "file_path": file_path,
                    "context": context,
                    "arguments": args.strip(),
                })
        
        # Look for relationships between objects (method calls, property access)
        relationship_pattern = r'(\w+)\.([\w_]+)\('  # obj.method()
        
        for match in re.finditer(relationship_pattern, code_snippet):
            obj_name, method_name = match.groups()
            
            # Find the object in our list
            source_obj = next((o for o in objects if o["name"] == obj_name), None)
            if source_obj:
                # Look for other objects that might be passed as arguments
                full_call = code_snippet[match.start():match.start() + 100]  # Look ahead 100 chars
                end_paren = full_call.find(')')
                if end_paren > 0:
                    args_text = full_call[full_call.find('(')+1:end_paren]
                    
                    # Check if any other known objects are in the arguments
                    for obj in objects:
                        if obj["name"] in args_text and obj["id"] != source_obj["id"]:
                            relationships.append({
                                "source_id": source_obj["id"],
                                "target_id": obj["id"],
                                "type": "method_call",
                                "label": method_name,
                                "context": context
                            })
    
    def _generate_mermaid_class_diagram(
        self, 
        classes: List[Dict[str, Any]], 
        relationships: List[Dict[str, Any]], 
        title: str
    ) -> str:
        """
        Generate a Mermaid class diagram from class and relationship data.
        
        Args:
            classes: List of class definitions
            relationships: List of relationships between classes
            title: Title for the diagram
            
        Returns:
            String with Mermaid diagram syntax
        """
        diagram = f"classDiagram\n    %% {title}\n"
        
        # Add classes
        for cls in classes:
            class_name = cls["name"]
            diagram += f"    class {class_name}\n"
            
            # Add attributes
            for attr in cls.get("attributes", []):
                visibility = "+"
                if attr.get("accessibility") == "private":
                    visibility = "-"
                elif attr.get("accessibility") == "protected":
                    visibility = "#"
                
                attr_type = attr.get("type", "")
                if attr_type:
                    attr_type = f" : {attr_type}"
                
                diagram += f"    {class_name} : {visibility}{attr.get('name', 'unknown')}{attr_type}\n"
            
            # Add methods
            for method in cls.get("methods", []):
                visibility = "+"
                if method.get("accessibility") == "private":
                    visibility = "-"
                elif method.get("accessibility") == "protected":
                    visibility = "#"
                
                return_type = method.get("return_type", "")
                if return_type:
                    return_type = f" {return_type}"
                
                # Format parameters
                params = []
                for param in method.get("parameters", []):
                    param_type = param.get("type", "")
                    if param_type:
                        params.append(f"{param.get('name', 'param')} : {param_type}")
                    else:
                        params.append(param.get('name', 'param'))
                
                params_str = ", ".join(params)
                
                diagram += f"    {class_name} : {visibility}{method.get('name', 'unknown')}({params_str}){return_type}\n"
        
        # Add relationships
        for rel in relationships:
            source = rel.get("source", "").split(".")[-1]  # Get class name without package
            target = rel.get("target", "").split(".")[-1]  # Get class name without package
            
            # Skip if source or target not in our diagram
            if not source or not target:
                continue
            if not any(c["name"] == source for c in classes) or not any(c["name"] == target for c in classes):
                continue
            
            rel_type = rel.get("type", "").lower()
            
            # Map relationship type to Mermaid syntax
            if rel_type == "inheritance":
                diagram += f"    {target} --|> {source}\n"
            elif rel_type == "implementation" or rel_type == "realization":
                diagram += f"    {target} ..|> {source}\n"
            elif rel_type == "composition":
                diagram += f"    {source} *-- {target}\n"
            elif rel_type == "aggregation":
                diagram += f"    {source} o-- {target}\n"
            elif rel_type == "association":
                diagram += f"    {source} --> {target}\n"
            elif rel_type == "dependency":
                diagram += f"    {source} ..> {target}\n"
            else:
                # Default to association
                diagram += f"    {source} --> {target}\n"
        
        # Add inheritance relationships from class data
        for cls in classes:
            class_name = cls["name"]
            for parent in cls.get("parent_classes", []):
                parent_name = parent.split(".")[-1]  # Get class name without package
                # Check if parent class is in diagram
                if any(c["name"] == parent_name for c in classes):
                    diagram += f"    {class_name} --|> {parent_name}\n"
            
            for interface in cls.get("interfaces", []):
                interface_name = interface.split(".")[-1]  # Get interface name without package
                # Check if interface is in diagram
                if any(c["name"] == interface_name for c in classes):
                    diagram += f"    {class_name} ..|> {interface_name}\n"
        
        return diagram
    
    def _generate_mermaid_object_diagram(
        self, 
        objects: List[Dict[str, Any]], 
        relationships: List[Dict[str, Any]], 
        title: str
    ) -> str:
        """
        Generate a Mermaid object diagram from object and relationship data.
        
        Args:
            objects: List of object instances
            relationships: List of relationships between objects
            title: Title for the diagram
            
        Returns:
            String with Mermaid diagram syntax
        """
        # For object diagrams in Mermaid, we have to use class diagrams with a specific style
        diagram = f"classDiagram\n    %% {title} - Object Diagram\n"
        
        # Add objects
        for obj in objects:
            object_id = obj["id"].replace(".", "_").replace(":", "_")
            class_name = obj["class"]
            object_name = obj["name"]
            
            # Add object as class
            diagram += f"    class {object_id}[\"{object_name}: {class_name}\"]\n"
            
            # Add arguments as attributes
            if obj.get("arguments"):
                args = obj["arguments"].split(",")
                for i, arg in enumerate(args):
                    arg = arg.strip()
                    if arg:
                        diagram += f"    {object_id} : arg{i+1}= {arg}\n"
        
        # Add relationships
        for rel in relationships:
            source_id = rel["source_id"].replace(".", "_").replace(":", "_")
            target_id = rel["target_id"].replace(".", "_").replace(":", "_")
            label = rel.get("label", "")
            
            # Skip if source or target not in our diagram
            if not any(o["id"] == rel["source_id"] for o in objects) or not any(o["id"] == rel["target_id"] for o in objects):
                continue
            
            diagram += f"    {source_id} --> {target_id} : {label}\n"
        
        return diagram
    
    def _generate_state_diagram_with_ai(self, file_path: str, content: str, title: str) -> Dict[str, Any]:
        """
        Use AI to generate a state diagram for a file.
        
        Args:
            file_path: Path to the file
            content: Content of the file
            title: Title for the diagram
            
        Returns:
            Dictionary containing state diagram data
        """
        try:
            # Send to AI for state machine analysis
            prompt = f"""Analyze this code file and identify any state machine behavior:

```
{content[:4000]}  # Limit content size for AI
```

If state machine behavior is found:
1. Identify all states
2. Identify transitions between states and their triggers
3. Identify the starting state
4. Identify any final states
5. Generate a Mermaid state diagram for this state machine

If no state machine behavior is found, generate a minimal state diagram
that captures the key operational states of the component.
"""
            result = self.ai_provider.analyze_content(file_path, prompt)
            
            # Extract diagram content and states from result
            diagram_content = ""
            states = []
            transitions = []
            
            if "mermaid" in result:
                diagram_content = result["mermaid"]
            elif "diagram" in result:
                diagram_content = result["diagram"]
            else:
                # Try to extract Mermaid diagram from text
                if "```mermaid" in result.get("text", ""):
                    parts = result.get("text", "").split("```mermaid")
                    if len(parts) > 1:
                        end_marker = "```"
                        if end_marker in parts[1]:
                            diagram_content = parts[1].split(end_marker)[0].strip()
                        else:
                            diagram_content = parts[1].strip()
            
            # If no diagram content detected, create a basic state diagram
            if not diagram_content or diagram_content.strip() == "":
                diagram_content = f"stateDiagram-v2\n    [*] --> Active\n    Active --> Processing\n    Processing --> Active\n    Active --> [*]"
            
            # Extract states and transitions from result if available
            if "states" in result:
                states = result["states"]
            
            if "transitions" in result:
                transitions = result["transitions"]
            
            # Clean diagram content
            if not diagram_content.startswith("stateDiagram") and not diagram_content.startswith("graph"):
                diagram_content = f"stateDiagram-v2\n{diagram_content}"
            
            return {
                "title": title,
                "diagram_type": "state",
                "syntax_type": "mermaid",
                "content": diagram_content,
                "states": states,
                "transitions": transitions,
                "file_path": file_path
            }
        
        except Exception as e:
            logger.error(f"Error in AI state diagram generation: {str(e)}")
            
            # Create a basic state diagram as fallback
            basic_diagram = f"""stateDiagram-v2
    [*] --> Active
    Active --> Processing
    Processing --> Active
    Active --> [*]
"""
            
            return {
                "title": title,
                "diagram_type": "state",
                "syntax_type": "mermaid",
                "content": basic_diagram,
                "states": [],
                "transitions": [],
                "file_path": file_path,
                "error": str(e)
            }
    
    def _find_code_files(self, repo_path: Path) -> List[Path]:
        """
        Find all code files in a repository.
        
        Args:
            repo_path: Path to the repository root
            
        Returns:
            List of file paths
        """
        code_extensions = [".py", ".java", ".js", ".jsx", ".ts", ".tsx", ".cs", ".cpp", ".c", ".go", ".rb"]
        
        exclude_dirs = {".git", "node_modules", "__pycache__", "venv", "env", ".venv", "build", "dist"}
        
        code_files = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in code_extensions):
                    code_files.append(Path(root) / file)
        
        return code_files
    
    def _select_important_files(self, code_files: List[Path], max_classes: int) -> List[Path]:
        """
        Select the most important files to include in a combined diagram.
        
        Args:
            code_files: List of all code files
            max_classes: Maximum number of classes to include
            
        Returns:
            List of selected file paths
        """
        # Score and rank files by importance
        file_scores = []
        
        for file in code_files:
            score = 0
            
            try:
                # Read file
                content = self.file_reader.read_file(file)
                
                # Score based on file location (core directories are more important)
                path_parts = str(file).lower().split(os.sep)
                
                # Core directories typically have names like:
                core_indicators = ["core", "main", "api", "service", "model", "entity", "domain"]
                for indicator in core_indicators:
                    if indicator in path_parts:
                        score += 10
                
                # Files that define multiple classes are usually more central
                class_count = len(re.findall(r"class\s+\w+", content))
                score += class_count * 5
                
                # Files that are imported a lot are usually important
                # This is a heuristic - ideally would check actual import references
                if "interface" in file.name.lower() or "base" in file.name.lower():
                    score += 15
                
                # Files with inheritance are usually important architecture elements
                if re.search(r"class\s+\w+\s*\(", content):
                    score += 10
                
                # Files with many methods likely contain important logic
                method_count = len(re.findall(r"def\s+\w+|function\s+\w+|public\s+\w+\s+\w+\s*\(", content))
                score += min(method_count, 20)  # Cap at 20 to avoid over-weighting huge files
                
                file_scores.append((file, score, class_count))
            
            except Exception as e:
                logger.error(f"Error scoring file {file}: {str(e)}")
        
        # Sort by score (highest first)
        file_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Select files based on max_classes limit
        selected_files = []
        total_classes = 0
        
        for file, score, class_count in file_scores:
            if class_count > 0 and total_classes < max_classes:
                selected_files.append(file)
                total_classes += class_count
                
                if total_classes >= max_classes:
                    break
        
        return selected_files