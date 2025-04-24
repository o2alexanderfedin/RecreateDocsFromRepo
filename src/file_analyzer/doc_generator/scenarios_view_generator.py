"""
Scenarios View Diagram Generator implementation.

This module provides the ScenariosViewGenerator class for creating UML diagrams
that represent the scenarios and user interactions with a system (use case and user flow diagrams).
"""
import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple, Union

from file_analyzer.doc_generator.base_diagram_generator import BaseDiagramGenerator
from file_analyzer.ai_providers.provider_interface import AIModelProvider
from file_analyzer.core.file_reader import FileReader
from file_analyzer.core.file_hasher import FileHasher
from file_analyzer.core.cache_provider import CacheProvider
from file_analyzer.core.code_analyzer import CodeAnalyzer
from file_analyzer.utils.exceptions import FileAnalyzerError

logger = logging.getLogger("file_analyzer.scenarios_view_generator")


class ScenariosViewGenerator(BaseDiagramGenerator):
    """
    Generates UML Scenarios View diagrams for code repositories.
    
    Creates use case diagrams and user flow diagrams using Mermaid syntax
    based on extracted requirements and user interactions.
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
        Initialize the scenarios view generator.
        
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
        
        # Extend stats with scenarios view specific metrics
        self.stats.update({
            "use_case_diagrams_generated": 0,
            "user_flow_diagrams_generated": 0,
            "actors_identified": 0,
            "use_cases_identified": 0,
            "user_flows_identified": 0
        })
    
    def generate_diagram(self, file_paths: List[Union[str, Path]], diagram_type: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a scenarios view diagram of the specified type.
        
        Args:
            file_paths: Path to the repository or specific files
            diagram_type: Type of diagram to generate ('use_case', 'user_flow')
            **kwargs: Additional arguments for specific diagram types
            
        Returns:
            Dictionary containing diagram data with Mermaid syntax
        """
        result = None
        
        if diagram_type == "use_case":
            # For use case diagrams, file_paths is typically a repository path
            repo_path = file_paths[0] if isinstance(file_paths, list) else file_paths
            result = self.generate_use_case_diagram(repo_path, **kwargs)
        elif diagram_type == "user_flow":
            # For user flow diagrams, file_paths is typically a repository path
            repo_path = file_paths[0] if isinstance(file_paths, list) else file_paths
            # Ensure we pass title=None if not specified
            if 'title' not in kwargs:
                kwargs['title'] = None
            result = self.generate_user_flow_diagram(repo_path, **kwargs)
        else:
            raise ValueError(f"Unsupported diagram type: {diagram_type}")
        
        # Update base stats
        self.stats["diagrams_generated"] += 1
        
        return result
    
    def generate_use_case_diagram(
        self, 
        repo_path: Union[str, Path], 
        focus_area: str = None,
        title: str = "Use Case Diagram"
    ) -> Dict[str, Any]:
        """
        Generate a UML use case diagram showing actors and system functionality.
        
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
        cache_key = f"use_case_diagram:{focus_path}"
        cached_result = self._check_cache(cache_key)
        if cached_result:
            return cached_result
        
        # Find files that might contain use case information
        doc_files = self._find_documentation_files(focus_path)
        test_files = self._find_test_files(focus_path)
        route_files = self._find_route_files(focus_path)
        
        relevant_files = doc_files + route_files
        if not relevant_files:
            logger.warning(f"No relevant files found for use case analysis in {focus_path}")
            # Create a minimal use case diagram
            actors = [{"id": "user", "name": "User", "type": "human"}]
            use_cases = [{"id": "use-system", "name": "Use System", "description": "Generic system usage"}]
            relationships = [{"actor": "user", "use_case": "use-system"}]
        else:
            # Load and analyze the files
            file_contents = {}
            for file_path in relevant_files:
                try:
                    content = self.file_reader.read_file(file_path)
                    file_contents[str(file_path)] = content
                except Exception as e:
                    logger.error(f"Error reading {file_path}: {str(e)}")
            
            # Use AI to analyze files and extract use cases
            actors, use_cases, relationships = self._analyze_use_cases(relevant_files, file_contents)
        
        # Generate diagram
        diagram = self._generate_mermaid_use_case_diagram(actors, use_cases, relationships, title)
        
        # Prepare result
        result = {
            "title": title,
            "diagram_type": "use_case",
            "syntax_type": "mermaid",
            "content": diagram,
            "actors": actors,
            "use_cases": use_cases,
            "relationships": relationships,
            "metadata": {
                "repository": str(repo_path),
                "focus_area": focus_area,
                "actor_count": len(actors),
                "use_case_count": len(use_cases),
                "relationship_count": len(relationships)
            }
        }
        
        # Cache result
        self._save_to_cache(cache_key, result)
        
        # Update stats
        self.stats["use_case_diagrams_generated"] += 1
        self.stats["actors_identified"] += len(actors)
        self.stats["use_cases_identified"] += len(use_cases)
        
        return result
    
    def generate_user_flow_diagram(
        self, 
        repo_path: Union[str, Path], 
        use_case: str = None,
        title: str = None
    ) -> Dict[str, Any]:
        """
        Generate a UML user flow diagram showing step-by-step user interactions.
        
        Args:
            repo_path: Path to the repository root
            use_case: Optional use case name to focus on
            title: Optional title for the diagram
            
        Returns:
            Dictionary containing diagram data with Mermaid syntax
        """
        repo_path = Path(repo_path) if isinstance(repo_path, str) else repo_path
        
        if title is None:
            title = f"User Flow: {use_case}" if use_case else "User Flow Diagram"
        
        # Check cache
        cache_key = f"user_flow_diagram:{repo_path}:{use_case or 'general'}"
        cached_result = self._check_cache(cache_key)
        if cached_result:
            return cached_result
        
        # Find files that might contain user flow information
        test_files = self._find_test_files(repo_path)
        ui_files = self._find_ui_files(repo_path)
        
        # If use case is specified, filter files to those likely to contain that use case
        if use_case:
            # Normalize use case name for matching
            use_case_norm = use_case.lower().replace(" ", "_").replace("-", "_")
            
            test_files = [f for f in test_files if use_case_norm in str(f).lower()]
            ui_files = [f for f in ui_files if use_case_norm in str(f).lower()]
        
        relevant_files = test_files + ui_files
        
        if not relevant_files:
            logger.warning(f"No relevant files found for user flow analysis: {use_case or 'general'}")
            # Create a minimal user flow diagram
            steps = [
                {"id": "start", "name": "Start", "type": "start"},
                {"id": "action", "name": "Perform Action", "type": "action"},
                {"id": "end", "name": "End", "type": "end"}
            ]
            flows = [
                {"source": "start", "target": "action"},
                {"source": "action", "target": "end"}
            ]
        else:
            # Load and analyze the files
            file_contents = {}
            for file_path in relevant_files:
                try:
                    content = self.file_reader.read_file(file_path)
                    file_contents[str(file_path)] = content
                except Exception as e:
                    logger.error(f"Error reading {file_path}: {str(e)}")
            
            # Use AI to analyze files and extract user flows
            steps, flows = self._analyze_user_flows(relevant_files, file_contents, use_case)
        
        # Generate diagram
        diagram = self._generate_mermaid_user_flow_diagram(steps, flows, title)
        
        # Prepare result
        result = {
            "title": title,
            "diagram_type": "user_flow",
            "syntax_type": "mermaid",
            "content": diagram,
            "use_case": use_case,
            "steps": steps,
            "flows": flows,
            "metadata": {
                "repository": str(repo_path),
                "step_count": len(steps),
                "flow_count": len(flows)
            }
        }
        
        # Cache result
        self._save_to_cache(cache_key, result)
        
        # Update stats
        self.stats["user_flow_diagrams_generated"] += 1
        self.stats["user_flows_identified"] += 1
        
        return result
    
    def _find_documentation_files(self, path: Path) -> List[Path]:
        """
        Find documentation files in the repository.
        
        Args:
            path: Repository path to search in
            
        Returns:
            List of file paths for documentation files
        """
        doc_files = []
        
        # Define patterns for documentation files
        doc_patterns = [
            "*.md",
            "*/README*",
            "*/docs/**",
            "*/documentation/**",
            "*/wiki/**",
            "*/specifications/**",
            "*/requirements/**"
        ]
        
        # Collect files that match documentation patterns
        for root, dirs, files in os.walk(path):
            # Skip version control and dependency directories
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", "venv"}]
            
            for file in files:
                file_path = Path(root) / file
                rel_path = str(file_path.relative_to(path))
                
                # Check for pattern matches
                for pattern in doc_patterns:
                    if self._match_glob_pattern(rel_path, pattern):
                        doc_files.append(file_path)
                        break
        
        return doc_files
    
    def _find_test_files(self, path: Path) -> List[Path]:
        """
        Find test files that might contain user interaction scenarios.
        
        Args:
            path: Repository path to search in
            
        Returns:
            List of file paths for test files
        """
        test_files = []
        
        # Define patterns for test files
        test_patterns = [
            "*/test*/**",
            "*/tests/**",
            "*/spec/**",
            "*/e2e/**",
            "*/integration/**",
            "*/acceptance/**",
            "*/*_test.*",
            "*/test_*.*",
            "*/spec_*.*"
        ]
        
        # Collect files that match test patterns
        for root, dirs, files in os.walk(path):
            # Skip version control and dependency directories
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", "venv"}]
            
            for file in files:
                file_path = Path(root) / file
                rel_path = str(file_path.relative_to(path))
                
                # Check for pattern matches
                for pattern in test_patterns:
                    if self._match_glob_pattern(rel_path, pattern):
                        # Prioritize UI, integration, and end-to-end tests
                        priority_keywords = ["ui", "user", "flow", "journey", "e2e", "end-to-end", "integration"]
                        if any(keyword in str(file_path).lower() for keyword in priority_keywords):
                            test_files.insert(0, file_path)  # Add to beginning
                        else:
                            test_files.append(file_path)
                        break
        
        return test_files
    
    def _find_route_files(self, path: Path) -> List[Path]:
        """
        Find files that define routes, endpoints, or controllers.
        
        Args:
            path: Repository path to search in
            
        Returns:
            List of file paths for route files
        """
        route_files = []
        
        # Define route file patterns by common frameworks and naming conventions
        route_patterns = {
            # Web frameworks (route definitions)
            "**/routes/**": None,
            "**/controllers/**": None,
            "**/views/**": None,
            "**/pages/**": None,
            "**/screens/**": None,
            
            # API definitions
            "**/api/**": None,
            "**/endpoints/**": None,
            "**/resources/**": None,
            
            # Common specific files
            "*routes*.py": None,
            "*routes*.js": None,
            "*routes*.ts": None,
            "*controller*.py": None,
            "*controller*.js": None,
            "*controller*.ts": None,
            "*controller*.java": None,
            "*resource*.java": None,
            "*endpoints*.py": None,
            "*endpoints*.java": None,
            
            # OpenAPI/Swagger definitions
            "**/*swagger*.{yaml,yml,json}": None,
            "**/*openapi*.{yaml,yml,json}": None
        }
        
        # Collect files that match route patterns
        for root, dirs, files in os.walk(path):
            # Skip version control and dependency directories
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", "venv"}]
            
            for file in files:
                file_path = Path(root) / file
                rel_path = str(file_path.relative_to(path))
                
                # Check for pattern matches
                for pattern in route_patterns:
                    if self._match_glob_pattern(rel_path, pattern):
                        route_files.append(file_path)
                        break
        
        return route_files
    
    def _find_ui_files(self, path: Path) -> List[Path]:
        """
        Find UI-related files that might contain user interaction information.
        
        Args:
            path: Repository path to search in
            
        Returns:
            List of file paths for UI files
        """
        ui_files = []
        
        # Define UI file patterns
        ui_patterns = {
            # Web UI files
            "**/components/**": None,
            "**/pages/**": None,
            "**/screens/**": None,
            "**/views/**": None,
            "**/templates/**": None,
            
            # Mobile UI files
            "**/activities/**": None,
            "**/fragments/**": None,
            "**/layouts/**": None,
            
            # UI test files
            "**/ui/tests/**": None,
            "**/e2e/tests/**": None,
            
            # Common UI file types
            "**.jsx": None,
            "**.tsx": None,
            "**.vue": None,
            "**.html": None,
            "**.cshtml": None,
            "**.razor": None,
            "**.xml": None,
        }
        
        # Collect files that match UI patterns
        for root, dirs, files in os.walk(path):
            # Skip version control and dependency directories
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", "venv"}]
            
            for file in files:
                file_path = Path(root) / file
                rel_path = str(file_path.relative_to(path))
                
                # Check for pattern matches
                for pattern in ui_patterns:
                    if self._match_glob_pattern(rel_path, pattern):
                        ui_files.append(file_path)
                        break
        
        return ui_files
    
    def _analyze_use_cases(
        self, 
        files: List[Path], 
        file_contents: Dict[str, str]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Analyze files to extract actors, use cases, and their relationships.
        
        Args:
            files: List of file paths
            file_contents: Dictionary of file contents by path
            
        Returns:
            Tuple of (actors, use_cases, relationships)
        """
        # Prepare input for AI analysis
        file_info = []
        for file_path in files:
            content = file_contents.get(str(file_path), "")
            file_type = self._get_file_type(file_path)
            
            file_info.append({
                "path": str(file_path),
                "type": file_type,
                "content": content[:5000]  # Limit content size for AI
            })
        
        # Prepare the analysis prompt
        prompt = f"""Analyze the following files to identify system actors, use cases, and their interactions:

{json.dumps(file_info, indent=2)}

Identify:
1. External actors (users, systems) that interact with the system
2. Primary use cases (system functions)
3. Relationships between actors and use cases
4. Inclusions and extensions between use cases

Format your response as a structured JSON object with the following structure:
{{
  "actors": [
    {{"id": "actor-id", "name": "Human readable name", "type": "human|system"}},
    ...
  ],
  "use_cases": [
    {{"id": "usecase-id", "name": "Human readable name", "description": "Brief description"}},
    ...
  ],
  "relationships": [
    {{"actor": "actor-id", "use_case": "usecase-id", "type": "uses|includes|extends"}},
    ...
  ]
}}
"""
        
        try:
            # Use AI to analyze the files
            result = self.ai_provider.analyze_content(
                ", ".join(str(f) for f in files), 
                prompt
            )
            
            # Extract the components from the AI response
            actors = result.get("actors", [])
            use_cases = result.get("use_cases", [])
            relationships = result.get("relationships", [])
            
            return actors, use_cases, relationships
            
        except Exception as e:
            logger.error(f"Error in AI use case analysis: {str(e)}")
            
            # Provide a minimal fallback if AI analysis fails
            actors = [{"id": "user", "name": "User", "type": "human"}]
            use_cases = [{"id": "use-system", "name": "Use System", "description": "Generic system usage"}]
            relationships = [{"actor": "user", "use_case": "use-system"}]
            
            return actors, use_cases, relationships
    
    def _analyze_user_flows(
        self, 
        files: List[Path], 
        file_contents: Dict[str, str],
        use_case: str = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Analyze files to extract user flow steps and connections.
        
        Args:
            files: List of file paths
            file_contents: Dictionary of file contents by path
            use_case: Optional use case to focus on
            
        Returns:
            Tuple of (steps, flows)
        """
        # Prepare input for AI analysis
        file_info = []
        for file_path in files:
            content = file_contents.get(str(file_path), "")
            file_type = self._get_file_type(file_path)
            
            file_info.append({
                "path": str(file_path),
                "type": file_type,
                "content": content[:5000]  # Limit content size for AI
            })
        
        # Prepare the analysis prompt
        use_case_text = f" for the '{use_case}' use case" if use_case else ""
        prompt = f"""Analyze the following files to extract a detailed user flow{use_case_text}:

{json.dumps(file_info, indent=2)}

Identify:
1. All steps in the user interaction flow
2. Decision points where the flow can branch
3. The connections between steps
4. Start and end points of the flow

Format your response as a structured JSON object with the following structure:
{{
  "title": "User Flow Title",
  "actor": "Primary Actor (e.g., User, Admin)",
  "steps": [
    {{"id": "step-id", "name": "Human readable name", "type": "start|action|decision|end"}},
    ...
  ],
  "flows": [
    {{"source": "source-step-id", "target": "target-step-id", "label": "Optional label for decision paths"}},
    ...
  ]
}}
"""
        
        try:
            # Use AI to analyze the files
            result = self.ai_provider.analyze_content(
                ", ".join(str(f) for f in files), 
                prompt
            )
            
            # Extract the components from the AI response
            steps = result.get("steps", [])
            flows = result.get("flows", [])
            
            return steps, flows
            
        except Exception as e:
            logger.error(f"Error in AI user flow analysis: {str(e)}")
            
            # Provide a minimal fallback if AI analysis fails
            steps = [
                {"id": "start", "name": "Start", "type": "start"},
                {"id": "action", "name": "Perform Action", "type": "action"},
                {"id": "end", "name": "End", "type": "end"}
            ]
            flows = [
                {"source": "start", "target": "action"},
                {"source": "action", "target": "end"}
            ]
            
            return steps, flows
    
    def _generate_mermaid_use_case_diagram(
        self, 
        actors: List[Dict[str, Any]], 
        use_cases: List[Dict[str, Any]], 
        relationships: List[Dict[str, Any]], 
        title: str
    ) -> str:
        """
        Generate a Mermaid use case diagram from actors, use cases, and relationships.
        
        Args:
            actors: List of actors (users, systems)
            use_cases: List of use cases (system functions)
            relationships: List of relationships between actors and use cases
            title: Title for the diagram
            
        Returns:
            String with Mermaid diagram syntax
        """
        diagram = f"graph TD\n    %% {title}\n"
        
        # Add actors
        for actor in actors:
            actor_id = actor["id"]
            actor_name = actor.get("name", actor_id)
            actor_type = actor.get("type", "human")
            
            # Use different shapes for human vs system actors
            if actor_type.lower() == "human":
                diagram += f"    {actor_id}((\"{actor_name}\"))\n"
            else:
                diagram += f"    {actor_id}[[\"{actor_name}\"]]\n"
        
        # Add use cases
        for use_case in use_cases:
            use_case_id = use_case["id"]
            use_case_name = use_case.get("name", use_case_id)
            
            diagram += f"    {use_case_id}[{use_case_name}]\n"
        
        # Add relationships
        for rel in relationships:
            source = rel.get("actor", "")
            target = rel.get("use_case", "")
            rel_type = rel.get("type", "")
            
            if source and target:
                if rel_type == "include":
                    diagram += f"    {source} -.-> {target}\n"
                elif rel_type == "extend":
                    diagram += f"    {source} -.-> |extends| {target}\n"
                else:
                    diagram += f"    {source} --> {target}\n"
        
        return diagram
    
    def _generate_mermaid_user_flow_diagram(
        self, 
        steps: List[Dict[str, Any]], 
        flows: List[Dict[str, Any]], 
        title: str
    ) -> str:
        """
        Generate a Mermaid user flow diagram from steps and flows.
        
        Args:
            steps: List of steps in the flow
            flows: List of connections between steps
            title: Title for the diagram
            
        Returns:
            String with Mermaid diagram syntax
        """
        diagram = f"flowchart TD\n    %% {title}\n"
        
        # Add steps with appropriate shapes based on type
        for step in steps:
            step_id = step["id"]
            step_name = step.get("name", step_id)
            step_type = step.get("type", "action").lower()
            
            if step_type == "start" or step_type == "end":
                diagram += f"    {step_id}([{step_name}])\n"
            elif step_type == "decision":
                diagram += f"    {step_id}{{{step_name}}}\n"
            elif step_type == "input":
                diagram += f"    {step_id}[/{step_name}/]\n"
            elif step_type == "output":
                diagram += f"    {step_id}[\\{step_name}\\]\n"
            else:  # Default to action
                diagram += f"    {step_id}[{step_name}]\n"
        
        # Add flows between steps
        for flow in flows:
            source = flow["source"]
            target = flow["target"]
            label = flow.get("label", "")
            
            if label:
                diagram += f"    {source} -->|{label}| {target}\n"
            else:
                diagram += f"    {source} --> {target}\n"
        
        return diagram
    
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
    
    def _get_file_type(self, file_path: Path) -> str:
        """
        Determine the type of a file based on its extension and name.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File type string
        """
        file_name = file_path.name.lower()
        suffix = file_path.suffix.lower()
        
        # Documentation files
        if suffix == ".md":
            if file_name.startswith("readme"):
                return "readme"
            else:
                return "markdown"
        
        # Test files
        elif "test" in file_name or "spec" in file_name:
            if suffix == ".py":
                return "python-test"
            elif suffix in [".js", ".jsx", ".ts", ".tsx"]:
                return "javascript-test"
            elif suffix == ".java":
                return "java-test"
            else:
                return "test"
        
        # API/route files
        elif "route" in file_name or "controller" in file_name or "api" in file_name:
            if suffix == ".py":
                return "python-routes"
            elif suffix in [".js", ".jsx", ".ts", ".tsx"]:
                return "javascript-routes"
            elif suffix == ".java":
                return "java-routes"
            else:
                return "routes"
        
        # UI files
        elif suffix in [".jsx", ".tsx", ".vue", ".html", ".htm"]:
            return "ui"
        
        # API specification files
        elif suffix in [".yaml", ".yml", ".json"]:
            if "swagger" in file_name or "openapi" in file_name:
                return "api-spec"
            else:
                return suffix[1:]
        
        # Default to the file extension without the dot
        return suffix[1:] if suffix else "unknown"