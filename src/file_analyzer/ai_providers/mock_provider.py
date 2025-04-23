"""
Mock AI provider for testing.
"""
import os
import re
from typing import Dict, Any, List, Optional

from file_analyzer.ai_providers.provider_interface import AIModelProvider


class MockAIProvider(AIModelProvider):
    """Mock AI provider implementation for testing."""
    
    def analyze_content(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Return mock analysis results based on file path.
        
        Args:
            file_path: Path to the file being analyzed
            content: Content of the file to analyze
            
        Returns:
            Dictionary with mock analysis results
        """
        if ".py" in file_path.lower():
            return {
                "file_type": "code",
                "language": "python",
                "purpose": "implementation",
                "characteristics": ["functions", "classes", "module"],
                "confidence": 0.9
            }
        elif ".ts" in file_path.lower() and not ".d.ts" in file_path.lower():
            return {
                "file_type": "code",
                "language": "typescript",
                "purpose": "implementation", 
                "characteristics": ["functions", "classes", "interfaces", "types"],
                "confidence": 0.9
            }
        elif ".js" in file_path.lower() and not ".json" in file_path.lower():
            return {
                "file_type": "code",
                "language": "javascript",
                "purpose": "implementation",
                "characteristics": ["functions", "module"],
                "confidence": 0.9
            }
        elif ".java" in file_path.lower():
            return {
                "file_type": "code",
                "language": "java",
                "purpose": "implementation",
                "characteristics": ["classes", "interfaces", "package"],
                "confidence": 0.9
            }
        elif ".json" in file_path.lower():
            return {
                "file_type": "code",
                "language": "json",
                "purpose": "configuration",
                "characteristics": ["settings", "data"],
                "confidence": 0.9
            }
        elif ".md" in file_path.lower():
            return {
                "file_type": "documentation",
                "language": "markdown",
                "purpose": "documentation",
                "characteristics": ["text", "formatting"],
                "confidence": 0.9
            }
        elif ".yml" in file_path.lower() or ".yaml" in file_path.lower():
            return {
                "file_type": "configuration",
                "language": "yaml",
                "purpose": "configuration",
                "characteristics": ["settings", "environment"],
                "confidence": 0.9
            }
        elif ".html" in file_path.lower():
            return {
                "file_type": "markup",
                "language": "html",
                "purpose": "user interface",
                "characteristics": ["markup", "structure"],
                "confidence": 0.9
            }
        elif ".css" in file_path.lower():
            return {
                "file_type": "code",
                "language": "css",
                "purpose": "styling",
                "characteristics": ["styles", "presentation"],
                "confidence": 0.9
            }
        elif ".sh" in file_path.lower():
            return {
                "file_type": "code",
                "language": "shell",
                "purpose": "automation",
                "characteristics": ["commands", "script"],
                "confidence": 0.9
            }
        else:
            # Default for unknown files
            # Handle special cases for common files
            if "requirements.txt" in file_path.lower():
                return {
                    "file_type": "configuration",
                    "language": "text",
                    "purpose": "dependencies",
                    "characteristics": ["packages", "dependencies"],
                    "confidence": 0.9
                }
            elif ".toml" in file_path.lower():
                return {
                    "file_type": "configuration",
                    "language": "toml",
                    "purpose": "project configuration",
                    "characteristics": ["settings", "metadata"],
                    "confidence": 0.9
                }
            else:
                # Default for other unknown files
                return {
                    "file_type": "unknown",
                    "language": "unknown",
                    "purpose": "unknown",
                    "characteristics": ["binary" if b"\0" in content.encode() else "text"],
                    "confidence": 0.5
                }
    
    def analyze_code(self, file_path: str, content: str, language: str) -> Dict[str, Any]:
        """
        Analyze code structure for the given language.
        
        This method overrides the default implementation in AIModelProvider
        to provide specialized code analysis for different languages.
        
        Args:
            file_path: Path to the file being analyzed
            content: Content of the file to analyze
            language: Programming language of the code
            
        Returns:
            Dictionary with code structure analysis
        """
        # Parse code structure based on language
        if language == "python":
            return self._analyze_python(content)
        elif language == "java":
            return self._analyze_java(content)
        elif language == "javascript":
            return self._analyze_javascript(content)
        elif language == "typescript":
            return self._analyze_typescript(content)
        else:
            # Default for unsupported languages
            return {
                "structure": {
                    "imports": [],
                    "classes": [],
                    "functions": [],
                    "variables": [],
                    "language_specific": {},
                    "confidence": 0.5
                }
            }
    
    def _analyze_python(self, content: str) -> Dict[str, Any]:
        """Analyze Python code structure."""
        lines = content.split('\n')
        structure = {
            "imports": [],
            "classes": [],
            "functions": [],
            "variables": [],
            "language_specific": {"modules": []},
            "confidence": 0.9
        }
        
        # Extract imports
        for line in lines:
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                structure["imports"].append(line)
        
        # Extract classes with methods and properties
        class_pattern = re.compile(r'^class\s+(\w+)(?:\(.*\))?:')
        method_pattern = re.compile(r'^\s+def\s+(\w+)')
        property_pattern = re.compile(r'^\s+self\.(\w+)\s*=')
        func_pattern = re.compile(r'^def\s+(\w+)')
        var_pattern = re.compile(r'^([A-Z][A-Z0-9_]*)\s*=')
        
        current_class = None
        docstring_buffer = []
        collecting_docstring = False
        
        for i, line in enumerate(lines):
            # Handle classes
            class_match = class_pattern.match(line)
            if class_match:
                class_name = class_match.group(1)
                docstring = self._extract_python_docstring(lines, i)
                current_class = {
                    "name": class_name,
                    "methods": [],
                    "properties": [],
                    "documentation": docstring
                }
                structure["classes"].append(current_class)
                continue
            
            # Handle methods in classes
            if current_class:
                method_match = method_pattern.match(line)
                if method_match:
                    method_name = method_match.group(1)
                    if method_name != "__init__":  # Skip constructor for simplicity
                        current_class["methods"].append(method_name)
                    continue
                
                # Handle properties
                property_match = property_pattern.match(line)
                if property_match:
                    property_name = property_match.group(1)
                    if property_name not in current_class["properties"]:
                        current_class["properties"].append(property_name)
                    continue
            
            # Handle free functions
            func_match = func_pattern.match(line)
            if func_match and not line.startswith(' '):  # Ensure it's not a method
                func_name = func_match.group(1)
                docstring = self._extract_python_docstring(lines, i)
                # Extract parameters from function definition
                params = []
                param_str = line.split('(')[1].split(')')[0] if '(' in line else ""
                for param in param_str.split(','):
                    param = param.strip()
                    if param and param != 'self':
                        params.append(param.split(':')[0].strip())
                
                structure["functions"].append({
                    "name": func_name,
                    "parameters": params,
                    "documentation": docstring
                })
                continue
            
            # Handle module-level variables (constants)
            var_match = var_pattern.match(line)
            if var_match:
                var_name = var_match.group(1)
                structure["variables"].append({
                    "name": var_name,
                    "scope": "module"
                })
        
        return {"structure": structure}
    
    def _extract_python_docstring(self, lines: List[str], start_index: int) -> str:
        """Extract Python docstring after class or function definition."""
        if start_index + 1 >= len(lines):
            return ""
        
        next_line = lines[start_index + 1].strip()
        if not (next_line.startswith('"""') or next_line.startswith("'''")):
            return ""
        
        # Single line docstring
        if (next_line.startswith('"""') and next_line.endswith('"""')) or \
           (next_line.startswith("'''") and next_line.endswith("'''")):
            return next_line[3:-3].strip()
        
        # Multi-line docstring
        docstring_lines = []
        quote_type = next_line[:3]
        docstring_lines.append(next_line[3:])
        
        for i in range(start_index + 2, len(lines)):
            line = lines[i]
            if quote_type == '"""' and '"""' in line:
                docstring_lines.append(line.split('"""')[0])
                break
            elif quote_type == "'''" and "'''" in line:
                docstring_lines.append(line.split("'''")[0])
                break
            else:
                docstring_lines.append(line)
        
        return "\n".join(docstring_lines).strip()
    
    def _analyze_java(self, content: str) -> Dict[str, Any]:
        """Analyze Java code structure."""
        lines = content.split('\n')
        structure = {
            "imports": [],
            "classes": [],
            "functions": [],
            "variables": [],
            "language_specific": {
                "packages": [],
                "interfaces": []
            },
            "confidence": 0.9
        }
        
        # Extract package and imports
        for line in lines:
            line = line.strip()
            if line.startswith('package '):
                package = line[8:].strip().rstrip(';')
                structure["language_specific"]["packages"].append(package)
            elif line.startswith('import '):
                structure["imports"].append(line)
        
        # Extract classes, interfaces, methods, and fields
        in_class = False
        in_interface = False
        current_item = None
        
        class_pattern = re.compile(r'(?:public|protected|private)?\s*class\s+(\w+)')
        interface_pattern = re.compile(r'(?:public|protected|private)?\s*interface\s+(\w+)')
        method_pattern = re.compile(r'(?:public|protected|private)\s+\w+\s+(\w+)\s*\(')
        field_pattern = re.compile(r'(?:public|protected|private)\s+\w+\s+(\w+)\s*[;=]')
        
        for i, line in enumerate(lines):
            # Handle class declaration
            class_match = class_pattern.search(line)
            if class_match:
                in_class = True
                in_interface = False
                class_name = class_match.group(1)
                javadoc = self._extract_java_javadoc(lines, i)
                current_item = {
                    "name": class_name,
                    "methods": [],
                    "properties": [],
                    "documentation": javadoc
                }
                structure["classes"].append(current_item)
                continue
            
            # Handle interface declaration
            interface_match = interface_pattern.search(line)
            if interface_match:
                in_class = False
                in_interface = True
                interface_name = interface_match.group(1)
                javadoc = self._extract_java_javadoc(lines, i)
                current_item = {
                    "name": interface_name,
                    "methods": [],
                    "documentation": javadoc
                }
                structure["language_specific"]["interfaces"].append(current_item)
                continue
            
            # Handle methods
            method_match = method_pattern.search(line)
            if method_match and (in_class or in_interface):
                method_name = method_match.group(1)
                if current_item and method_name not in current_item["methods"]:
                    current_item["methods"].append(method_name)
                continue
            
            # Handle fields (only in classes)
            if in_class:
                field_match = field_pattern.search(line)
                if field_match:
                    field_name = field_match.group(1)
                    if current_item and "properties" in current_item and field_name not in current_item["properties"]:
                        current_item["properties"].append(field_name)
        
        return {"structure": structure}
    
    def _extract_java_javadoc(self, lines: List[str], start_index: int) -> str:
        """Extract Java javadoc before class, interface, or method declaration."""
        if start_index <= 0:
            return ""
        
        # Look for javadoc starting with "/**" before the current line
        javadoc_lines = []
        in_javadoc = False
        
        for i in range(start_index - 1, -1, -1):
            line = lines[i].strip()
            
            if line.endswith("*/"):
                in_javadoc = True
                javadoc_lines.insert(0, line[:-2].strip())
            elif in_javadoc and line.startswith("*"):
                javadoc_lines.insert(0, line[1:].strip())
            elif in_javadoc and line.startswith("/**"):
                javadoc_lines.insert(0, line[3:].strip())
                break
            elif in_javadoc:
                javadoc_lines.insert(0, line)
            elif not line:
                # Skip empty lines
                continue
            else:
                # Stop if we hit a non-javadoc line
                break
        
        return "\n".join(javadoc_lines).strip() if in_javadoc else ""
    
    def _analyze_javascript(self, content: str) -> Dict[str, Any]:
        """Analyze JavaScript code structure."""
        lines = content.split('\n')
        structure = {
            "imports": [],
            "classes": [],
            "functions": [],
            "variables": [],
            "language_specific": {
                "exports": [],
                "imports": []
            },
            "confidence": 0.9
        }
        
        # Extract imports and exports
        for line in lines:
            line = line.strip()
            if line.startswith('import '):
                structure["imports"].append(line)
                structure["language_specific"]["imports"].append(line)
            elif line.startswith('export '):
                structure["language_specific"]["exports"].append(line)
            elif 'require(' in line:
                structure["imports"].append(line)
        
        # Extract classes, methods, functions, and variables
        class_pattern = re.compile(r'class\s+(\w+)')
        method_pattern = re.compile(r'\s+(\w+)\s*\(.*\)\s*\{')
        func_pattern = re.compile(r'function\s+(\w+)\s*\(')
        arrow_func_pattern = re.compile(r'const\s+(\w+)\s*=\s*\(.*\)\s*=>')
        var_pattern = re.compile(r'(?:const|let|var)\s+(\w+)\s*=')
        
        in_class = False
        current_class = None
        
        for i, line in enumerate(lines):
            # Handle class declaration
            class_match = class_pattern.search(line)
            if class_match:
                in_class = True
                class_name = class_match.group(1)
                jsdoc = self._extract_js_jsdoc(lines, i)
                current_class = {
                    "name": class_name,
                    "methods": [],
                    "properties": [],
                    "documentation": jsdoc
                }
                structure["classes"].append(current_class)
                continue
            
            # Handle methods in classes
            if in_class:
                method_match = method_pattern.search(line)
                if method_match:
                    method_name = method_match.group(1)
                    if method_name != "constructor" and method_name not in current_class["methods"]:
                        current_class["methods"].append(method_name)
                    continue
                
                # Handle properties in constructor
                if "constructor" in line:
                    # Find property assignments in constructor
                    for j in range(i + 1, min(i + 10, len(lines))):
                        prop_line = lines[j].strip()
                        if prop_line.startswith("this."):
                            prop_name = prop_line.split("this.")[1].split("=")[0].strip()
                            if prop_name not in current_class["properties"]:
                                current_class["properties"].append(prop_name)
                        elif prop_line.startswith("}"):
                            break
            
            # Handle functions
            func_match = func_pattern.search(line)
            if func_match:
                func_name = func_match.group(1)
                jsdoc = self._extract_js_jsdoc(lines, i)
                
                # Extract parameters
                params = []
                param_str = line.split('(')[1].split(')')[0] if '(' in line else ""
                params = [p.strip() for p in param_str.split(',') if p.strip()]
                
                structure["functions"].append({
                    "name": func_name,
                    "parameters": params,
                    "documentation": jsdoc
                })
                continue
            
            # Handle arrow functions
            arrow_func_match = arrow_func_pattern.search(line)
            if arrow_func_match:
                func_name = arrow_func_match.group(1)
                jsdoc = self._extract_js_jsdoc(lines, i)
                
                # Extract parameters
                params = []
                param_str = line.split('(')[1].split(')')[0] if '(' in line else ""
                params = [p.strip() for p in param_str.split(',') if p.strip()]
                
                structure["functions"].append({
                    "name": func_name,
                    "parameters": params,
                    "documentation": jsdoc
                })
                continue
            
            # Handle variables
            var_match = var_pattern.search(line)
            if var_match:
                var_name = var_match.group(1)
                structure["variables"].append({
                    "name": var_name,
                    "scope": "module"
                })
        
        return {"structure": structure}
    
    def _extract_js_jsdoc(self, lines: List[str], start_index: int) -> str:
        """Extract JSDoc comment before class, function, or variable declaration."""
        if start_index <= 0:
            return ""
        
        # Look for JSDoc starting with "/**" before the current line
        jsdoc_lines = []
        in_jsdoc = False
        
        for i in range(start_index - 1, -1, -1):
            line = lines[i].strip()
            
            if line.endswith("*/"):
                in_jsdoc = True
                jsdoc_lines.insert(0, line[:-2].strip())
            elif in_jsdoc and line.startswith("*"):
                jsdoc_lines.insert(0, line[1:].strip())
            elif in_jsdoc and line.startswith("/**"):
                jsdoc_lines.insert(0, line[3:].strip())
                break
            elif in_jsdoc:
                jsdoc_lines.insert(0, line)
            elif not line:
                # Skip empty lines
                continue
            else:
                # Stop if we hit a non-jsdoc line
                break
        
        return "\n".join(jsdoc_lines).strip() if in_jsdoc else ""
    
    def _analyze_typescript(self, content: str) -> Dict[str, Any]:
        """Analyze TypeScript code structure."""
        # Start with JavaScript analysis as base
        js_result = self._analyze_javascript(content)
        structure = js_result["structure"]
        
        # Add TypeScript-specific elements
        structure["language_specific"]["interfaces"] = []
        structure["language_specific"]["types"] = []
        
        lines = content.split('\n')
        
        # Extract interfaces and types
        interface_pattern = re.compile(r'interface\s+(\w+)')
        type_pattern = re.compile(r'type\s+(\w+)\s*=')
        
        for i, line in enumerate(lines):
            # Handle interface declaration
            interface_match = interface_pattern.search(line)
            if interface_match:
                interface_name = interface_match.group(1)
                tsdoc = self._extract_js_jsdoc(lines, i)  # Reuse JSDoc extractor
                
                # Extract properties and methods from interface
                properties = []
                methods = []
                in_interface = True
                
                for j in range(i + 1, len(lines)):
                    if in_interface:
                        iface_line = lines[j].strip()
                        if iface_line.startswith("}"):
                            in_interface = False
                            break
                        
                        # Check for property
                        if ":" in iface_line and not iface_line.endswith("():"):
                            prop_name = iface_line.split(":")[0].strip()
                            properties.append(prop_name)
                        
                        # Check for method
                        if "():" in iface_line or "(...)" in iface_line:
                            method_name = iface_line.split("(")[0].strip()
                            methods.append(method_name)
                
                structure["language_specific"]["interfaces"].append({
                    "name": interface_name,
                    "properties": properties,
                    "methods": methods,
                    "documentation": tsdoc
                })
                continue
            
            # Handle type declaration
            type_match = type_pattern.search(line)
            if type_match:
                type_name = type_match.group(1)
                tsdoc = self._extract_js_jsdoc(lines, i)
                
                # Extract type definition
                type_def = line.split("=")[1].strip().rstrip(";")
                
                structure["language_specific"]["types"].append({
                    "name": type_name,
                    "definition": type_def,
                    "documentation": tsdoc
                })
                continue
            
            # Enhance existing class and function definitions with type information
            # Extract type from function parameters and return values
            for func in structure["functions"]:
                func_line_idx = self._find_function_line_index(lines, func["name"])
                if func_line_idx != -1:
                    func_line = lines[func_line_idx]
                    # Extract return type
                    if '):' in func_line and not func_line.endswith('):'):
                        return_type = func_line.split('):')[1].split('{')[0].strip()
                        func["return_type"] = return_type
            
            # Extract type annotations from variables
            for var in structure["variables"]:
                var_line_idx = self._find_variable_line_index(lines, var["name"])
                if var_line_idx != -1:
                    var_line = lines[var_line_idx]
                    if ":" in var_line and "=" in var_line:
                        type_annotation = var_line.split(":")[1].split("=")[0].strip()
                        var["type"] = type_annotation
        
        return {"structure": structure}
    
    def _find_function_line_index(self, lines: List[str], function_name: str) -> int:
        """Find the line index of a function definition."""
        function_pattern = re.compile(rf'function\s+{function_name}\s*\(|const\s+{function_name}\s*=\s*\(')
        
        for i, line in enumerate(lines):
            if function_pattern.search(line):
                return i
        
        return -1
    
    def _find_variable_line_index(self, lines: List[str], variable_name: str) -> int:
        """Find the line index of a variable declaration."""
        variable_pattern = re.compile(rf'(?:const|let|var)\s+{variable_name}\s*[=:]')
        
        for i, line in enumerate(lines):
            if variable_pattern.search(line):
                return i
        
        return -1