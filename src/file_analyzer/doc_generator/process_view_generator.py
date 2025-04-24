"""
Process View Diagram Generator implementation.

This module provides the ProcessViewGenerator class for creating UML diagrams
that represent the process flow of a codebase (sequence diagrams and activity diagrams).
"""
import os
import re
import logging
import ast
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple, Union

from file_analyzer.doc_generator.base_diagram_generator import BaseDiagramGenerator
from file_analyzer.ai_providers.provider_interface import AIModelProvider
from file_analyzer.core.file_reader import FileReader
from file_analyzer.core.file_hasher import FileHasher
from file_analyzer.core.cache_provider import CacheProvider
from file_analyzer.core.code_analyzer import CodeAnalyzer
from file_analyzer.utils.exceptions import FileAnalyzerError

logger = logging.getLogger("file_analyzer.process_view_generator")


class ProcessViewGenerator(BaseDiagramGenerator):
    """
    Generates UML Process View diagrams for code repositories.
    
    Creates sequence diagrams and activity diagrams using Mermaid syntax
    based on interaction data extracted during repository analysis.
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
        Initialize the process view generator.
        
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
        
        # Extend stats with process view specific metrics
        self.stats.update({
            "sequence_diagrams_generated": 0,
            "activity_diagrams_generated": 0,
            "function_calls_traced": 0,
            "decision_points": 0
        })
    
    def generate_diagram(self, file_paths: List[Union[str, Path]], diagram_type: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a process view diagram of the specified type.
        
        Args:
            file_paths: List of file paths to include in the diagram
            diagram_type: Type of diagram to generate ('sequence', 'activity')
            **kwargs: Additional arguments for specific diagram types
            
        Returns:
            Dictionary containing diagram data with Mermaid syntax
        """
        result = None
        
        if diagram_type == "sequence":
            result = self.generate_sequence_diagram(file_paths, **kwargs)
        elif diagram_type == "activity":
            if len(file_paths) != 1:
                raise ValueError("Activity diagrams require exactly one file path")
            result = self.generate_activity_diagram(file_paths[0], **kwargs)
        else:
            raise ValueError(f"Unsupported diagram type: {diagram_type}")
        
        # Update base stats
        self.stats["diagrams_generated"] += 1
        
        return result
    
    def generate_sequence_diagram(
        self, 
        file_paths: List[Union[str, Path]], 
        entry_point: str = None,
        max_depth: int = 3, 
        title: str = "Sequence Diagram"
    ) -> Dict[str, Any]:
        """
        Generate a UML sequence diagram showing interactions between components.
        
        Args:
            file_paths: List of file paths to include in the diagram
            entry_point: Optional entry point function/method to start tracing (e.g., "module.Class.method")
            max_depth: Maximum depth of method call tracing
            title: Title for the diagram
            
        Returns:
            Dictionary containing diagram data with Mermaid syntax
        """
        # Normalize paths
        paths = [Path(p) if isinstance(p, str) else p for p in file_paths]
        
        # Check cache
        cache_key = f"sequence_diagram:{self._hash_paths(paths)}:{entry_point}:{max_depth}"
        cached_result = self._check_cache(cache_key)
        if cached_result:
            return cached_result
        
        # Collect components and their interactions
        components = []
        interactions = []
        call_stack = []
        
        # Initialize tracking variables for the current parsing state
        current_component = None
        
        # Dictionary to track all found methods by their full qualified name
        methods_by_name = {}
        
        # Find all classes and methods in the files
        for path in paths:
            try:
                # Analyze code
                analysis = self.code_analyzer.analyze_code(str(path))
                
                # Extract classes and their methods
                for cls in analysis.get("structure", {}).get("classes", []):
                    class_name = cls.get("name", "UnknownClass")
                    module_name = os.path.splitext(os.path.basename(str(path)))[0]
                    full_class_name = f"{module_name}.{class_name}"
                    
                    # Add component for the class
                    components.append({
                        "name": class_name,
                        "type": "class",
                        "file_path": str(path),
                        "full_name": full_class_name
                    })
                    
                    # Add all methods
                    for method in cls.get("methods", []):
                        method_name = method.get("name", "unknown_method")
                        full_method_name = f"{full_class_name}.{method_name}"
                        
                        # Save method info for later call tracing
                        methods_by_name[full_method_name] = {
                            "class": class_name,
                            "class_full_name": full_class_name,
                            "name": method_name,
                            "body": method.get("body", ""),
                            "file_path": str(path)
                        }
                
                # Also extract standalone functions
                for func in analysis.get("structure", {}).get("functions", []):
                    function_name = func.get("name", "unknown_function")
                    module_name = os.path.splitext(os.path.basename(str(path)))[0]
                    full_func_name = f"{module_name}.{function_name}"
                    
                    # Add component for the module (only once)
                    if not any(c["name"] == module_name and c["type"] == "module" for c in components):
                        components.append({
                            "name": module_name,
                            "type": "module",
                            "file_path": str(path),
                            "full_name": module_name
                        })
                    
                    # Save function info for later call tracing
                    methods_by_name[full_func_name] = {
                        "class": None,
                        "name": function_name,
                        "body": func.get("body", ""),
                        "file_path": str(path),
                        "module": module_name
                    }
            except Exception as e:
                logger.error(f"Error analyzing {path} for sequence diagram: {str(e)}")
        
        # If entry point was provided, start tracing from there
        if entry_point and entry_point in methods_by_name:
            # Start the call tracing from the entry point
            self._trace_method_calls(
                entry_point, 
                methods_by_name, 
                interactions, 
                call_stack, 
                0, 
                max_depth
            )
        else:
            # No entry point or invalid entry point, identify potential entry points
            entry_points = []
            for method_name, method_info in methods_by_name.items():
                # Look for methods with names that suggest entry points
                entry_indicators = ["main", "run", "start", "execute", "process", "handle", "init"]
                if any(indicator in method_info["name"].lower() for indicator in entry_indicators):
                    entry_points.append(method_name)
            
            # Process identified entry points
            for ep in entry_points[:3]:  # Limit to top 3 to avoid overcomplicated diagrams
                self._trace_method_calls(
                    ep, 
                    methods_by_name, 
                    interactions, 
                    call_stack, 
                    0, 
                    max_depth
                )
        
        # Generate diagram
        diagram = self._generate_mermaid_sequence_diagram(components, interactions, title)
        
        # Prepare result
        result = {
            "title": title,
            "diagram_type": "sequence",
            "syntax_type": "mermaid",
            "content": diagram,
            "components": components,
            "interactions": interactions,
            "metadata": {
                "file_count": len(paths),
                "component_count": len(components),
                "interaction_count": len(interactions),
                "entry_point": entry_point,
                "max_depth": max_depth
            }
        }
        
        # Cache result
        self._save_to_cache(cache_key, result)
        
        # Update stats
        self.stats["sequence_diagrams_generated"] += 1
        self.stats["function_calls_traced"] += len(interactions)
        
        return result
    
    def generate_activity_diagram(
        self, 
        file_path: Union[str, Path], 
        function_name: str = None,
        title: str = None
    ) -> Dict[str, Any]:
        """
        Generate a UML activity diagram showing the control flow of a process.
        
        Args:
            file_path: Path to the file to analyze
            function_name: Optional function or method name to focus on
            title: Optional title for the diagram
            
        Returns:
            Dictionary containing diagram data with Mermaid syntax
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path
        
        if title is None:
            display_name = function_name or path.name
            title = f"Activity Diagram: {display_name}"
        
        # Check cache
        file_hash = self.file_hasher.get_file_hash(path)
        cache_key = f"activity_diagram:{file_hash}:{function_name or ''}"
        cached_result = self._check_cache(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Read file content
            content = self.file_reader.read_file(path)
            
            # If function name is provided, find and extract that function's code
            target_code = content
            if function_name:
                try:
                    # Parse the AST to find the specific function
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                            # Check if this is the target function or a class containing it
                            if node.name == function_name or (
                                isinstance(node, ast.ClassDef) and 
                                any(m.name == function_name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)))
                            ):
                                # Extract the line numbers for this function
                                start_line = node.lineno - 1  # AST line numbers are 1-indexed
                                end_line = getattr(node, 'end_lineno', 0) - 1 if hasattr(node, 'end_lineno') else None
                                if end_line is None:
                                    # Find the end by looking at lines after the function
                                    lines = content.splitlines()
                                    indent = 0
                                    for i, line in enumerate(lines[start_line:], start_line):
                                        if i == start_line:
                                            # Get the indentation of the function definition
                                            indent = len(line) - len(line.lstrip())
                                        elif line.strip() and len(line) - len(line.lstrip()) <= indent:
                                            # Found a line with same or lower indentation, marks the end
                                            end_line = i - 1
                                            break
                                    
                                    if end_line is None:
                                        end_line = len(content.splitlines()) - 1
                                
                                # Extract the function code
                                target_code = "\n".join(content.splitlines()[start_line:end_line+1])
                                break
                except Exception as e:
                    logger.warning(f"Error extracting function {function_name} from AST: {str(e)}")
                    # Fall back to regex-based extraction
                    pattern = re.compile(r"(async\s+)?def\s+" + re.escape(function_name) + r"\s*\(.*?:((?:.|\n)*?)(?:^\s*(?:def|class)|$)", re.MULTILINE)
                    match = pattern.search(content)
                    if match:
                        target_code = match.group(0)
            
            # Use AI to analyze the code flow and generate activity diagram
            result = self._generate_activity_diagram_with_ai(str(path), target_code, function_name, title)
            
            # Update stats
            self.stats["activity_diagrams_generated"] += 1
            self.stats["decision_points"] += result.get("metadata", {}).get("decision_points", 0)
            
            # Cache result
            self._save_to_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating activity diagram for {path}: {str(e)}")
            return {
                "title": title,
                "diagram_type": "activity",
                "syntax_type": "mermaid",
                "content": f"graph TD\n    A[Error] --> B[Could not generate activity diagram: {str(e)}]",
                "activities": [],
                "flows": [],
                "error": str(e)
            }
    
    def _trace_method_calls(
        self, 
        method_name: str, 
        methods_by_name: Dict[str, Dict[str, Any]], 
        interactions: List[Dict[str, Any]], 
        call_stack: List[str],
        current_depth: int,
        max_depth: int
    ) -> None:
        """
        Trace method calls from a starting method to build sequence diagram data.
        
        Args:
            method_name: Full qualified name of the method to trace
            methods_by_name: Dictionary of all methods indexed by name
            interactions: List to populate with interactions
            call_stack: Current call stack to detect recursion
            current_depth: Current call depth
            max_depth: Maximum depth to trace
        """
        # Check for recursion or excessive depth
        if method_name in call_stack or current_depth >= max_depth:
            return
        
        # Get method info
        method_info = methods_by_name.get(method_name)
        if not method_info:
            return
        
        # Update call stack
        call_stack.append(method_name)
        
        # Extract the method's body
        method_body = method_info.get("body", "")
        
        # Find method calls in the body
        # This is a simple regex-based approach - in production, AST parsing would be better
        if method_info["class"]:
            # For class methods, look for self.method() calls
            method_call_pattern = r'self\.(\w+)\s*\('
            for match in re.finditer(method_call_pattern, method_body):
                called_method = match.group(1)
                called_method_full = f"{method_info['class_full_name']}.{called_method}"
                
                # Add the interaction
                if called_method_full in methods_by_name:
                    interactions.append({
                        "source": method_name,
                        "target": called_method_full,
                        "type": "method_call",
                        "depth": current_depth
                    })
                    
                    # Recursively trace this method call
                    self._trace_method_calls(
                        called_method_full,
                        methods_by_name,
                        interactions,
                        call_stack.copy(),
                        current_depth + 1,
                        max_depth
                    )
        
        # Look for direct instantiations and method calls on other classes
        # This is a simplified pattern - real implementation would need language-specific parsing
        class_call_pattern = r'(\w+)\.(\w+)\s*\('
        for match in re.finditer(class_call_pattern, method_body):
            instance_var = match.group(1)
            called_method = match.group(2)
            
            # Check if we know which class this instance belongs to
            # This is a simplified approach - in production, we'd need better type inference
            for other_method_name, other_method_info in methods_by_name.items():
                if other_method_info.get("class") and other_method_info["name"] == called_method:
                    # Found a possible match - add the interaction
                    interactions.append({
                        "source": method_name,
                        "target": other_method_name,
                        "type": "method_call",
                        "depth": current_depth,
                        "note": f"Potential call via {instance_var}"
                    })
        
        # Look for function calls (non-method)
        for other_method_name, other_method_info in methods_by_name.items():
            if not other_method_info.get("class"):  # It's a function, not a method
                function_name = other_method_info["name"]
                # Simple pattern matching - would need more sophisticated analysis in production
                if re.search(rf'\b{re.escape(function_name)}\s*\(', method_body):
                    # Found a function call
                    interactions.append({
                        "source": method_name,
                        "target": other_method_name,
                        "type": "function_call",
                        "depth": current_depth
                    })
                    
                    # Recursively trace this function call
                    self._trace_method_calls(
                        other_method_name,
                        methods_by_name,
                        interactions,
                        call_stack.copy(),
                        current_depth + 1,
                        max_depth
                    )
        
        # Remove from call stack before returning
        call_stack.pop()
    
    def _generate_mermaid_sequence_diagram(
        self, 
        components: List[Dict[str, Any]], 
        interactions: List[Dict[str, Any]], 
        title: str
    ) -> str:
        """
        Generate a Mermaid sequence diagram from component and interaction data.
        
        Args:
            components: List of components (classes/modules)
            interactions: List of interactions between components
            title: Title for the diagram
            
        Returns:
            String with Mermaid diagram syntax
        """
        diagram = f"sequenceDiagram\n    %% {title}\n"
        
        # Get unique participants (components) from interactions
        participants = set()
        for interaction in interactions:
            source_parts = interaction["source"].split(".")
            target_parts = interaction["target"].split(".")
            
            if len(source_parts) >= 2:
                # For methods, use the class/module as participant
                source = ".".join(source_parts[:-1])
                participants.add(source)
            
            if len(target_parts) >= 2:
                # For methods, use the class/module as participant
                target = ".".join(target_parts[:-1])
                participants.add(target)
        
        # If no interactions, use all components
        if not participants and components:
            participants = {c["full_name"] for c in components}
        
        # Add participants
        for participant in sorted(participants):
            short_name = participant.split(".")[-1]
            diagram += f"    participant {short_name} as {participant}\n"
        
        # Add interactions as messages
        # Sort interactions by depth to get a more logical flow
        sorted_interactions = sorted(interactions, key=lambda x: x.get("depth", 0))
        
        for idx, interaction in enumerate(sorted_interactions):
            source_parts = interaction["source"].split(".")
            target_parts = interaction["target"].split(".")
            
            source = ".".join(source_parts[:-1])
            source_method = source_parts[-1]
            
            target = ".".join(target_parts[:-1])
            target_method = target_parts[-1]
            
            message = f"{source_method}() -> {target_method}()"
            
            # Add the message to the diagram
            if source in participants and target in participants:
                diagram += f"    {source}->>+{target}: {message}\n"
                
                # Add return message for deeper understanding
                # Only add returns that don't have subsequent calls from the same source
                # to avoid cluttering the diagram
                is_last_from_source = idx == len(sorted_interactions) - 1 or \
                                     sorted_interactions[idx+1]["source"] != interaction["source"]
                
                if is_last_from_source:
                    diagram += f"    {target}-->>-{source}: return\n"
        
        return diagram
    
    def _generate_activity_diagram_with_ai(
        self, 
        file_path: str, 
        content: str, 
        function_name: str, 
        title: str
    ) -> Dict[str, Any]:
        """
        Use AI to generate an activity diagram for code.
        
        Args:
            file_path: Path to the file
            content: Content of the file or function
            function_name: Name of the function to diagram (or None)
            title: Title for the diagram
            
        Returns:
            Dictionary containing activity diagram data
        """
        try:
            # Count decision points (if/else, switch, try/except)
            decision_count = len(re.findall(r'\bif\b|\belif\b|\belse\b|\bswitch\b|\bcase\b|\btry\b|\bexcept\b|\bcatch\b', content))
            
            # Send to AI for flow analysis
            prompt = f"""Analyze this code and create an activity diagram that illustrates its control flow:

```
{content[:4000]}  # Limit content size for AI
```

Focus on:
1. The main process flow
2. Decision points (if/else, switch/case, try/except)
3. Loops and iterations
4. Key function calls

Generate a Mermaid activity diagram (flowchart TD syntax) that clearly illustrates this process flow.
Include decision diamonds for conditionals, rectangular nodes for actions, and appropriate labels.
Use clear and concise node text that captures the essence of each step.
"""
            result = self.ai_provider.analyze_content(file_path, prompt)
            
            # Extract diagram content
            diagram_content = ""
            activities = []
            flows = []
            
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
                elif "```" in result.get("text", ""):
                    # Try to extract any code block
                    parts = result.get("text", "").split("```")
                    if len(parts) > 1:
                        potential_diagram = parts[1].strip()
                        if potential_diagram.startswith("graph") or potential_diagram.startswith("flowchart"):
                            diagram_content = potential_diagram
            
            # If no diagram content detected, create a basic activity diagram
            if not diagram_content or diagram_content.strip() == "":
                diagram_content = self._create_fallback_activity_diagram(content, function_name)
            
            # Ensure the diagram starts with a proper header if not already there
            if not diagram_content.startswith("graph") and not diagram_content.startswith("flowchart"):
                diagram_content = f"flowchart TD\n{diagram_content}"
            
            # Extract activities and flows from result if available
            if "activities" in result:
                activities = result["activities"]
            
            if "flows" in result:
                flows = result["flows"]
            
            return {
                "title": title,
                "diagram_type": "activity",
                "syntax_type": "mermaid",
                "content": diagram_content,
                "activities": activities,
                "flows": flows,
                "file_path": file_path,
                "function": function_name,
                "metadata": {
                    "decision_points": decision_count,
                    "code_length": len(content.splitlines())
                }
            }
        
        except Exception as e:
            logger.error(f"Error in AI activity diagram generation: {str(e)}")
            
            # Create a basic activity diagram as fallback
            fallback_diagram = self._create_fallback_activity_diagram(content, function_name)
            
            return {
                "title": title,
                "diagram_type": "activity",
                "syntax_type": "mermaid",
                "content": fallback_diagram,
                "activities": [],
                "flows": [],
                "file_path": file_path,
                "function": function_name,
                "error": str(e),
                "metadata": {
                    "decision_points": 0,
                    "code_length": len(content.splitlines())
                }
            }
    
    def _create_fallback_activity_diagram(self, content: str, function_name: str = None) -> str:
        """
        Create a fallback activity diagram based on basic code analysis.
        
        Args:
            content: Code content to analyze
            function_name: Optional function name for diagram
            
        Returns:
            Mermaid diagram content
        """
        diagram = "flowchart TD\n"
        
        # Add start node
        diagram += "    Start([Start])\n"
        
        # Function label
        func_label = function_name or "Function"
        diagram += f"    Process[Process {func_label}]\n"
        diagram += "    Start --> Process\n"
        
        # Basic analysis of the code structure
        has_if = "if " in content
        has_loop = any(pattern in content for pattern in ["for ", "while ", "foreach"])
        has_try = "try" in content
        has_return = "return " in content
        
        # Add conditional if found
        if has_if:
            diagram += "    Process --> Condition{Condition check}\n"
            diagram += "    Condition -->|True| TrueAction[Process if true]\n"
            diagram += "    Condition -->|False| FalseAction[Process if false]\n"
            diagram += "    TrueAction --> EndIf\n"
            diagram += "    FalseAction --> EndIf\n"
            diagram += "    EndIf[End conditional] --> Next\n"
        else:
            diagram += "    Process --> Next\n"
        
        # Add loop if found
        if has_loop:
            diagram += "    Next[Next step] --> LoopStart([Loop start])\n"
            diagram += "    LoopStart --> LoopBody[Process loop body]\n"
            diagram += "    LoopBody --> LoopCondition{Continue loop?}\n"
            diagram += "    LoopCondition -->|Yes| LoopBody\n"
            diagram += "    LoopCondition -->|No| AfterLoop\n"
            last_node = "AfterLoop"
        else:
            last_node = "Next"
        
        # Add try/catch if found
        if has_try:
            diagram += f"    {last_node}[Next step] --> TryBlock[Try block]\n"
            diagram += "    TryBlock --> |Exception| CatchBlock[Exception handling]\n"
            diagram += "    TryBlock --> |No exception| AfterTry\n"
            diagram += "    CatchBlock --> AfterTry\n"
            last_node = "AfterTry"
        
        # Add return
        if has_return:
            diagram += f"    {last_node}[Next step] --> ReturnValue[Return value]\n"
            last_node = "ReturnValue"
        
        # Add end node
        diagram += f"    {last_node} --> End([End])\n"
        
        return diagram