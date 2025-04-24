"""
Mock AI provider for testing.
"""
import os
import re
import json
from typing import Dict, Any, List, Optional

from file_analyzer.ai_providers.provider_interface import AIModelProvider
# Import will be loaded at runtime to avoid circular imports
# from file_analyzer.core.framework_detector import FRAMEWORK_SIGNATURES


class MockAIProvider(AIModelProvider):
    """Mock AI provider implementation for testing."""
    
    # Common environment variable patterns
    ENV_VAR_PATTERNS = [
        r'\${[A-Za-z0-9_]+}',           # ${VAR_NAME}
        r'\$[A-Za-z0-9_]+',              # $VAR_NAME
        r'%[A-Za-z0-9_]+%',              # %VAR_NAME%
        r'{{[A-Za-z0-9_]+}}',            # {{VAR_NAME}}
        r'\b[A-Z0-9_]{3,}\b(?=\s*[=:])'  # VAR_NAME= or VAR_NAME:
    ]
    
    # Common security issue patterns
    SECURITY_PATTERNS = {
        "hardcoded_password": [
            r'password["\']\s*:\s*["\'][^"\']+["\']',
            r'password\s*=\s*["\'][^"\']+["\']',
            r'pwd\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']'
        ],
        "api_key": [
            r'key["\']\s*:\s*["\'][A-Za-z0-9+/]{32,}["\']',
            r'api[_-]?key\s*=\s*["\'][A-Za-z0-9+/]{16,}["\']',
            r'token\s*=\s*["\'][A-Za-z0-9+/]{16,}["\']'
        ],
        "connection_string": [
            r'(?i)(?:jdbc|odbc|mongodb|postgresql|mysql|sqlserver)://[^\s"\'>]+',
            r'(?i)Data Source=[^\s"\'>;]+'
        ],
        "insecure_protocol": [
            r'(?i)http://(?!localhost|127\.0\.0\.1)',
            r'(?i)ftp://'
        ]
    }
    
    # Framework detection patterns for configs
    CONFIG_FRAMEWORK_PATTERNS = {
        "django": [r'INSTALLED_APPS', r'MIDDLEWARE', r'DATABASES\s*=', r'DEBUG\s*='],
        "flask": [r'FLASK_APP', r'FLASK_ENV', r'SECRET_KEY'],
        "spring": [r'spring\.', r'logging\.level\.org\.springframework'],
        "react": [r'react', r'jsx', r'componentDidMount'],
        "angular": [r'angular', r'ng\w+'],
        "docker": [r'image:', r'container_name:', r'volumes:'],
        "kubernetes": [r'apiVersion:', r'kind:\s*(?:Pod|Deployment|Service)'],
        "aws": [r'aws_', r'region', r'availability_zone'],
        "terraform": [r'provider\s*"', r'resource\s*"'],
        "nginx": [r'server_name', r'listen\s+\d+', r'location\s+/']
    }
    
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
    
    def detect_frameworks(self, file_path: str, content: str, language: str) -> Dict[str, Any]:
        """
        Detect frameworks in code with a mock implementation.
        
        Args:
            file_path: Path to the file being analyzed
            content: Content of the file to analyze
            language: Programming language of the code
            
        Returns:
            Dictionary with framework detection results
        """
        language = language.lower()
        frameworks = []
        
        # Import at runtime to avoid circular imports
        from file_analyzer.core.framework_detector import FRAMEWORK_SIGNATURES
        
        # Use language-specific framework detection if available
        if language in FRAMEWORK_SIGNATURES:
            frameworks = self._detect_frameworks_for_language(file_path, content, language)
        
        return {
            "frameworks": frameworks,
            "confidence": 0.8 if frameworks else 0.0
        }
    
    def _detect_frameworks_for_language(self, file_path: str, content: str, language: str) -> List[Dict[str, Any]]:
        """
        Detect frameworks for a specific language.
        
        Args:
            file_path: Path to the file being analyzed
            content: Content of the file to analyze
            language: Programming language of the code
            
        Returns:
            List of detected frameworks
        """
        # Import at runtime to avoid circular imports
        from file_analyzer.core.framework_detector import FRAMEWORK_SIGNATURES
        
        frameworks = []
        
        # Get signatures for the language
        signatures = FRAMEWORK_SIGNATURES.get(language, {})
        
        for framework_name, signature in signatures.items():
            # Check if any import signatures are present in content
            imports_present = any(
                import_sig.lower() in content.lower() 
                for import_sig in signature.get("imports", [])
            )
            
            # Check if any pattern signatures are present in content
            patterns_present = any(
                pattern.lower() in content.lower() 
                for pattern in signature.get("patterns", [])
            )
            
            # For testing purposes, detect frameworks with simplified logic
            if imports_present or patterns_present:
                # Generate mock evidence
                evidence = []
                features = []
                
                # Add import evidence
                for import_sig in signature.get("imports", []):
                    if import_sig.lower() in content.lower():
                        evidence.append(f"Import: {import_sig}")
                        features.append(import_sig)
                
                # Add pattern evidence
                for pattern in signature.get("patterns", []):
                    if pattern.lower() in content.lower():
                        evidence.append(f"Pattern: {pattern}")
                        features.append(pattern)
                
                # Add framework to results
                frameworks.append({
                    "name": framework_name,
                    "confidence": 0.8,
                    "evidence": evidence,
                    "features": features
                })
        
        return frameworks
        
    def analyze_config(self, file_path: str, content: str, format_hint: str = None) -> Dict[str, Any]:
        """
        Analyze a configuration file to extract parameters, structure, and purpose.
        
        Args:
            file_path: Path to the file being analyzed
            content: Content of the file to analyze
            format_hint: Optional hint about the configuration format
            
        Returns:
            Dictionary with configuration analysis results
        """
        # Determine format based on file extension or hint
        config_format = format_hint
        if not config_format:
            if file_path.endswith(('.json')):
                config_format = 'json'
            elif file_path.endswith(('.yml', '.yaml')):
                config_format = 'yaml'  # Always use 'yaml' regardless of specific extension
            elif file_path.endswith(('.xml')):
                config_format = 'xml'
            elif file_path.endswith(('.properties', '.conf', '.ini', '.env')):
                config_format = 'properties'
            elif file_path.endswith(('.toml')):
                config_format = 'toml'
            else:
                # Try to determine format from content
                content_lower = content.lower()
                if content.strip().startswith('{') and content.strip().endswith('}'):
                    config_format = 'json'
                elif '<?xml' in content_lower or '<config' in content_lower:
                    config_format = 'xml'
                elif '=' in content and not content.strip().startswith('{'):
                    config_format = 'properties'
                elif ':' in content and '-' in content and not '{' in content:
                    config_format = 'yaml'
                else:
                    # Default to unknown
                    config_format = 'unknown'
        
        # Check if this is actually a config file
        is_config_file = True
        if file_path.endswith(('.py', '.js', '.ts', '.java', '.c', '.cpp', '.go')):
            # Code files with specific config patterns (like settings.py)
            if not any(re.search(pattern, content) for framework in self.CONFIG_FRAMEWORK_PATTERNS.values() 
                       for pattern in framework):
                is_config_file = False
                return {
                    "is_config_file": False,
                    "format": "unknown",
                    "error": "Not a configuration file",
                    "confidence": 0.8
                }
        
        # Extract parameters based on format
        parameters = []
        if config_format == 'json':
            try:
                # Parse JSON for parameters
                json_data = json.loads(content)
                parameters = self._extract_json_parameters(json_data)
            except json.JSONDecodeError:
                return {
                    "is_config_file": True,
                    "format": "json",
                    "error": "Invalid JSON format",
                    "parameters": [],
                    "environment_vars": [],
                    "security_issues": [],
                    "confidence": 0.5
                }
        elif config_format == 'yaml':
            # Simple YAML parameter extraction (mocked)
            parameters = self._extract_yaml_parameters(content)
        elif config_format == 'properties':
            # Extract key-value pairs from properties
            parameters = self._extract_properties_parameters(content)
        elif config_format == 'xml':
            # Extract XML elements (mocked)
            parameters = self._extract_xml_parameters(content)
        
        # Detect environment variables
        env_vars = []
        for pattern in self.ENV_VAR_PATTERNS:
            env_vars.extend(re.findall(pattern, content))
        
        # Detect security issues
        security_issues = []
        for issue_type, patterns in self.SECURITY_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    security_issues.append({
                        "type": issue_type,
                        "value": match,
                        "severity": "high" if issue_type in ["hardcoded_password", "api_key"] else "medium"
                    })
        
        # Detect framework
        framework = self._detect_config_framework(content)
        
        # Build result
        return {
            "is_config_file": is_config_file,
            "format": config_format,
            "parameters": parameters,
            "environment_vars": env_vars,
            "security_issues": security_issues,
            "framework": framework["name"] if framework else None,
            "framework_confidence": framework["confidence"] if framework else 0.0,
            "confidence": 0.9
        }
    
    def _extract_json_parameters(self, json_data, prefix=""):
        """Extract parameters from JSON data with dot notation paths."""
        parameters = []
        
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                path = f"{prefix}.{key}" if prefix else key
                
                if isinstance(value, (dict, list)):
                    # Recurse into nested structures
                    parameters.extend(self._extract_json_parameters(value, path))
                else:
                    # Add leaf node as parameter
                    parameter_type = self._determine_parameter_type(value)
                    parameters.append({
                        "path": path,
                        "value": str(value) if value is not None else None,
                        "type": parameter_type,
                        "description": f"Configuration parameter for {path}"
                    })
                    
        elif isinstance(json_data, list):
            for i, item in enumerate(json_data):
                path = f"{prefix}[{i}]"
                if isinstance(item, (dict, list)):
                    parameters.extend(self._extract_json_parameters(item, path))
                else:
                    parameter_type = self._determine_parameter_type(item)
                    parameters.append({
                        "path": path,
                        "value": str(item) if item is not None else None,
                        "type": parameter_type,
                        "description": f"List item at index {i}"
                    })
                    
        return parameters
    
    def _extract_yaml_parameters(self, content):
        """Simple extraction of parameters from YAML content (mocked)."""
        parameters = []
        lines = content.split('\n')
        current_prefix = []
        indentation_stack = [-1]  # Start with imaginary root level
        
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
                
            # Count indentation
            indentation = len(line) - len(line.lstrip())
            
            # Determine key and value
            if ':' in stripped:
                key, value = stripped.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Adjust prefix stack based on indentation
                while indentation <= indentation_stack[-1] and len(indentation_stack) > 1:
                    indentation_stack.pop()
                    current_prefix.pop()
                
                # If this is the first time we see this indentation level, add it
                if indentation > indentation_stack[-1]:
                    indentation_stack.append(indentation)
                    current_prefix.append(key)
                else:
                    # Replace the last prefix component
                    current_prefix[-1] = key
                
                # Skip if this is just a parent node with no value
                if not value or value == '-':
                    continue
                    
                # Build the full path
                path = '.'.join(current_prefix[:-1] + [key])
                
                # Determine type
                param_type = self._determine_parameter_type(value)
                
                # Add parameter
                parameters.append({
                    "path": path,
                    "value": value,
                    "type": param_type,
                    "description": f"Configuration parameter for {path}"
                })
        
        return parameters
    
    def _extract_properties_parameters(self, content):
        """Extract parameters from properties file format."""
        parameters = []
        lines = content.split('\n')
        
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
                
            if '=' in stripped:
                key, value = stripped.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Determine parameter type
                param_type = self._determine_parameter_type(value)
                
                # Add parameter
                parameters.append({
                    "path": key,
                    "value": value,
                    "type": param_type,
                    "description": f"Configuration parameter {key}"
                })
        
        return parameters
    
    def _extract_xml_parameters(self, content):
        """Extract parameters from XML content (mocked)."""
        parameters = []
        # Simple regex-based extraction for testing
        element_pattern = r'<([a-zA-Z0-9_.-]+)>(.*?)</\1>'
        nested_elements = {}
        
        for match in re.finditer(element_pattern, content, re.DOTALL):
            tag, value = match.groups()
            value = value.strip()
            
            # Skip nested elements
            if re.search(element_pattern, value):
                nested_elements[tag] = value
                continue
                
            # Determine parameter type
            param_type = self._determine_parameter_type(value)
            
            # Add parameter
            parameters.append({
                "path": tag,
                "value": value,
                "type": param_type,
                "description": f"XML element {tag}"
            })
            
        # Process nested elements
        for parent, nested_content in nested_elements.items():
            for match in re.finditer(element_pattern, nested_content):
                tag, value = match.groups()
                value = value.strip()
                
                # Skip doubly-nested elements
                if re.search(element_pattern, value):
                    continue
                    
                # Determine parameter type
                param_type = self._determine_parameter_type(value)
                
                # Add parameter with parent prefix
                parameters.append({
                    "path": f"{parent}.{tag}",
                    "value": value,
                    "type": param_type,
                    "description": f"Nested XML element {parent}.{tag}"
                })
        
        return parameters
    
    def _determine_parameter_type(self, value):
        """Determine the type of a parameter value."""
        if value is None:
            return "null"
        
        # Try to determine if it's a boolean
        if isinstance(value, str):
            if value.lower() in ('true', 'false', 'yes', 'no', 'on', 'off'):
                return "boolean"
            
            # Check if it's a number
            try:
                if '.' in value:
                    float(value)
                    return "float"
                else:
                    int(value)
                    return "integer"
            except (ValueError, TypeError):
                pass
                
            # Check if it's a connection string
            if 'jdbc:' in value or 'mongodb://' in value or 'postgresql://' in value:
                return "connection_string"
                
            # Check if it's a path/file
            if value.startswith('/') or value.startswith('./') or ':\\' in value:
                return "file_path"
                
            # Check if it's a URL
            if value.startswith(('http://', 'https://', 'ftp://')):
                return "url"
                
            # Check if it's an environment variable
            if any(re.search(pattern, value) for pattern in self.ENV_VAR_PATTERNS):
                return "environment_variable"
                
            # Default to string
            return "string"
        
        # Handle non-string types
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return "unknown"
    
    def _detect_config_framework(self, content):
        """Detect framework based on configuration content."""
        for framework, patterns in self.CONFIG_FRAMEWORK_PATTERNS.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                    matches += 1
            
            # If more than half of the patterns match, consider it a match
            if matches >= max(1, len(patterns) // 2):
                return {
                    "name": framework.capitalize(),
                    "confidence": min(0.5 + (matches / len(patterns) * 0.5), 0.95)
                }
        
        return None