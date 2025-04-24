"""
AI-powered documentation generator for files.

This module uses AI to generate rich, detailed documentation for files
based on their content and metadata from previous analysis steps.
It supports various file types and programming languages, providing
specialized documentation for each.
"""
import logging
import os
import re
from typing import Dict, Any, List, Optional, Union, Set
from pathlib import Path

from file_analyzer.ai_providers.provider_interface import AIModelProvider
from file_analyzer.ai_providers.mock_provider import MockAIProvider

logger = logging.getLogger("file_analyzer.doc_generator.ai_documentation_generator")

class AiDocumentationGenerator:
    """
    Generates AI-powered documentation for files.
    
    This class uses AI to analyze file content and metadata
    to generate detailed, insightful documentation that
    explains the purpose, components, and usage of files.
    
    It handles different file types with specialized approaches:
    - For code files: Documents classes, functions, and usage patterns
    - For config files: Documents parameters, environment variables, and examples
    - For build files: Documents build processes and requirements
    - For markup files: Summarizes content and structure
    """
    
    def __init__(self, ai_provider: AIModelProvider):
        """
        Initialize the AI documentation generator.
        
        Args:
            ai_provider: The AI provider to use for generating documentation
        """
        self.ai_provider = ai_provider
    
    def generate_file_documentation(
        self, 
        file_path: str, 
        content: str, 
        metadata: Dict[str, Any],
        relationship_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive documentation for a file.
        
        Args:
            file_path: Path to the file
            content: Content of the file
            metadata: Metadata from previous analysis steps
            relationship_data: File relationship data (optional)
            
        Returns:
            Dictionary with documentation components including:
            - description: Overall description of the file
            - purpose: Main purpose of the file in the codebase
            - usage_examples: Code examples demonstrating usage
            - key_components: Important classes, functions, etc.
            - main_concepts: Key concepts implemented in the file
            - architecture_notes: How the file fits into the overall architecture
            - compilation_instructions: How to build/run the file (if applicable)
            - dependencies: Key dependencies of the file
            - file_type_specific: Additional information specific to the file type
        """
        logger.debug(f"Generating AI documentation for {file_path}")
        
        # Get file language and type from metadata
        language = metadata.get("language", "").lower()
        file_type = metadata.get("file_type", "").lower()
        
        # Determine file category for specialized handling
        file_category = self._determine_file_category(file_path, language, file_type)
        
        # Check if the AI provider has a specific documentation generation method
        if hasattr(self.ai_provider, "generate_documentation"):
            logger.debug("Using provider's native documentation generation")
            ai_doc = self.ai_provider.generate_documentation(file_path, content, metadata)
            # If the provider only returns basic documentation, enhance it with our specialized methods
            if not ai_doc.get("file_type_specific"):
                ai_doc = self._enhance_provider_documentation(ai_doc, file_path, content, metadata, 
                                                              relationship_data, file_category)
            return ai_doc
        
        # Otherwise, construct documentation from available information
        logger.debug(f"Constructing documentation from metadata for {file_category} file")
        
        # Extract structure information
        code_structure = metadata.get("code_structure", {}).get("structure", {})
        classes = code_structure.get("classes", [])
        functions = code_structure.get("functions", [])
        imports = code_structure.get("imports", [])
        variables = code_structure.get("variables", [])
        
        # Extract framework information
        frameworks = metadata.get("frameworks", [])
        
        # Base documentation structure
        documentation = {
            "description": self._generate_description(file_path, content, metadata, file_category),
            "purpose": self._generate_purpose(file_path, content, metadata, file_category),
            "usage_examples": self._generate_usage_examples(file_path, content, metadata, file_category),
            "key_components": self._extract_key_components(classes, functions, variables),
            "main_concepts": self._extract_main_concepts(file_path, content, metadata, file_category),
            "architecture_notes": self._generate_architecture_notes(file_path, metadata, relationship_data),
            "compilation_instructions": self._generate_compilation_instructions(file_path, language, file_type, metadata),
            "dependencies": self._extract_dependencies(file_path, metadata, relationship_data)
        }
        
        # Add file type-specific documentation
        documentation["file_type_specific"] = self._generate_file_type_specific_docs(
            file_path, content, metadata, relationship_data, file_category)
        
        return documentation
    
    def _determine_file_category(self, file_path: str, language: str, file_type: str) -> str:
        """Determine the file category for specialized documentation handling."""
        # Extract file extension
        ext = os.path.splitext(file_path)[1].lower()
        
        # Check for configuration files
        if (file_type == "config" or 
            language in ["json", "yaml", "toml", "ini"] or
            ext in [".json", ".yaml", ".yml", ".toml", ".ini", ".conf", ".config", ".env"] or
            os.path.basename(file_path) == ".env"):
            return "config"
        
        # Check for build files
        if (file_type == "build" or
            any(name in file_path.lower() for name in ["makefile", "dockerfile", "jenkinsfile", "travis"]) or
            ext in [".gradle", ".maven", ".ant", ".bat", ".sh"] or
            os.path.basename(file_path).lower() in ["package.json", "setup.py", "requirements.txt"]):
            return "build"
        
        # Check for markup/documentation files
        if (file_type == "documentation" or
            language in ["markdown", "restructuredtext", "asciidoc", "html"] or
            ext in [".md", ".rst", ".adoc", ".txt", ".html"]):
            return "markup"
        
        # Check for test files
        if (file_type == "test" or 
            "test" in file_path.lower() or 
            os.path.basename(file_path).startswith("test_")):
            return "test"
        
        # Default to code
        return "code"
    
    def _enhance_provider_documentation(
        self, 
        provider_doc: Dict[str, Any],
        file_path: str,
        content: str,
        metadata: Dict[str, Any],
        relationship_data: Optional[Dict[str, Any]],
        file_category: str
    ) -> Dict[str, Any]:
        """Enhance the documentation provided by the AI provider with specialized information."""
        # Add any missing fields
        if "compilation_instructions" not in provider_doc:
            language = metadata.get("language", "").lower()
            file_type = metadata.get("file_type", "").lower()
            provider_doc["compilation_instructions"] = self._generate_compilation_instructions(
                file_path, language, file_type, metadata)
        
        if "dependencies" not in provider_doc:
            provider_doc["dependencies"] = self._extract_dependencies(file_path, metadata, relationship_data)
        
        if "file_type_specific" not in provider_doc:
            provider_doc["file_type_specific"] = self._generate_file_type_specific_docs(
                file_path, content, metadata, relationship_data, file_category)
        
        return provider_doc
    
    def _generate_description(
        self, 
        file_path: str, 
        content: str, 
        metadata: Dict[str, Any],
        file_category: str
    ) -> str:
        """Generate an overall description of the file."""
        # Extract docstring if available
        docstring = self._extract_module_docstring(content)
        if docstring:
            return docstring
        
        # Construct basic description from metadata
        file_type = metadata.get("file_type", "unknown")
        language = metadata.get("language", "unknown")
        purpose = metadata.get("purpose", "")
        
        if purpose:
            return f"This {language} {file_type} file is used for {purpose}."
        
        # Specialized descriptions by file category
        if file_category == "config":
            return f"This is a {language} configuration file that defines settings and parameters for the application."
        elif file_category == "build":
            return f"This is a build file used for compiling, packaging, or deploying the application."
        elif file_category == "markup":
            return f"This is a documentation file that provides information about the project."
        elif file_category == "test":
            return f"This is a test file that validates the functionality of the application."
        
        # Fallback to basic description
        return f"This is a {language} {file_type} file in the project."
    
    def _generate_purpose(
        self, 
        file_path: str, 
        content: str, 
        metadata: Dict[str, Any],
        file_category: str
    ) -> str:
        """Generate the main purpose of the file."""
        # Try to infer purpose from metadata
        purpose = metadata.get("purpose", "")
        if purpose:
            return f"The main purpose of this file is {purpose}."
        
        # Look at code structure for hints
        code_structure = metadata.get("code_structure", {}).get("structure", {})
        classes = code_structure.get("classes", [])
        functions = code_structure.get("functions", [])
        
        # Specialized purpose by file category
        if file_category == "config":
            return "This file centralizes configuration settings, making the application more flexible and environment-aware."
        elif file_category == "build":
            return "This file automates the build, test, or deployment process, ensuring consistent and repeatable operations."
        elif file_category == "markup":
            return "This file provides documentation to help developers understand the project structure, features, or usage."
        elif file_category == "test":
            return "This file verifies that the code works as expected, catching regressions and ensuring quality."
        
        # Generate purpose based on file contents
        if classes and functions:
            return f"This file defines {len(classes)} classes and {len(functions)} functions that implement core functionality."
        elif classes:
            return f"This file defines {len(classes)} classes for use in the project."
        elif functions:
            return f"This file provides {len(functions)} utility functions."
        
        # Fallback
        return "This file is part of the project's implementation."
    
    def _generate_usage_examples(
        self, 
        file_path: str, 
        content: str, 
        metadata: Dict[str, Any],
        file_category: str
    ) -> List[str]:
        """Generate usage examples for the file."""
        examples = []
        
        # Get language for code blocks
        language = metadata.get("language", "").lower()
        
        # Generate examples based on file category
        if file_category == "config":
            examples.append(self._generate_config_usage_example(file_path, content, metadata))
        elif file_category == "build":
            examples.append(self._generate_build_usage_example(file_path, content, metadata))
        elif file_category == "markup":
            examples.append("This documentation file can be referenced in your development workflow.")
        elif file_category == "test":
            examples.append(self._generate_test_usage_example(file_path, content, metadata))
        else:
            # Generate code examples based on file structure
            code_structure = metadata.get("code_structure", {}).get("structure", {})
            classes = code_structure.get("classes", [])
            functions = code_structure.get("functions", [])
            
            # Generate examples for classes and functions
            if classes and language == "python":
                examples.append(self._generate_python_class_example(file_path, classes))
            
            if functions and language == "python":
                examples.append(self._generate_python_function_example(file_path, functions))
            
            # Handle JavaScript/TypeScript modules
            if language in ["javascript", "typescript"] and (classes or functions):
                examples.append(self._generate_js_example(file_path, classes, functions))
        
        # If we couldn't generate specific examples, add a generic one
        if not examples:
            if language:
                examples.append(f"```{language}\n# Example usage will depend on your specific use case\n```")
            else:
                examples.append("Usage examples will depend on the specific context of your project.")
        
        return examples
    
    def _generate_python_class_example(self, file_path: str, classes: List[Dict[str, Any]]) -> str:
        """Generate an example for Python classes."""
        file_basename = os.path.basename(file_path)
        module_name = os.path.splitext(file_basename)[0]
        
        # Use the first class for the example
        class_name = classes[0].get("name", "Class")
        
        # Check for constructor parameters
        methods = classes[0].get("methods", [])
        init_params = []
        for method in methods:
            if isinstance(method, dict) and method.get("name") == "__init__":
                init_params = method.get("parameters", [])
                break
        
        # Generate example with constructor parameters
        example = f"```python\nfrom {module_name} import {class_name}\n\n"
        
        if init_params:
            example += f"# Create an instance of {class_name} with parameters\n"
            param_values = [self._get_default_value_for_param(p) for p in init_params]
            param_str = ", ".join(param_values)
            example += f"instance = {class_name}({param_str})\n"
        else:
            example += f"# Create an instance of {class_name}\n"
            example += f"instance = {class_name}()\n"
        
        # Add method call if available
        public_methods = [m for m in methods if isinstance(m, str) and not m.startswith("__")]
        if public_methods:
            method = public_methods[0]
            example += f"\n# Call a method\nresult = instance.{method}()\n"
        elif isinstance(methods, list) and methods:
            for method in methods:
                if isinstance(method, dict) and not method.get("name", "").startswith("__"):
                    method_name = method.get("name", "")
                    method_params = method.get("parameters", [])
                    if method_name:
                        param_values = [self._get_default_value_for_param(p) for p in method_params]
                        param_str = ", ".join(param_values)
                        example += f"\n# Call a method\nresult = instance.{method_name}({param_str})\n"
                        break
        
        example += "```"
        return example
    
    def _generate_python_function_example(self, file_path: str, functions: List[Dict[str, Any]]) -> str:
        """Generate an example for Python functions."""
        file_basename = os.path.basename(file_path)
        module_name = os.path.splitext(file_basename)[0]
        
        # Use the first function for the example
        function = functions[0]
        func_name = function.get("name", "function")
        
        # Check for parameters
        params = function.get("parameters", [])
        
        # Generate example with parameters
        example = f"```python\nfrom {module_name} import {func_name}\n\n"
        
        if params:
            example += f"# Call the function with parameters\n"
            param_values = [self._get_default_value_for_param(p) for p in params]
            param_str = ", ".join(param_values)
            example += f"result = {func_name}({param_str})\n"
        else:
            example += f"# Call the function\nresult = {func_name}()\n"
        
        example += "```"
        return example
    
    def _generate_js_example(
        self, 
        file_path: str, 
        classes: List[Dict[str, Any]], 
        functions: List[Dict[str, Any]]
    ) -> str:
        """Generate an example for JavaScript/TypeScript modules."""
        file_basename = os.path.basename(file_path)
        module_name = os.path.splitext(file_basename)[0]
        
        imports = []
        usage = []
        
        # Add classes to example
        for cls in classes[:2]:  # Limit to 2 classes for brevity
            class_name = cls.get("name", "Class")
            imports.append(class_name)
            
            # Add class usage
            usage.append(f"// Create an instance of {class_name}")
            usage.append(f"const instance = new {class_name}();")
            
            # Add method call if available
            methods = cls.get("methods", [])
            if methods and isinstance(methods, list):
                method = next((m for m in methods if isinstance(m, str) and not m.startswith("_")), None)
                if method:
                    usage.append(f"const result = instance.{method}();")
            
            usage.append("")  # Empty line between examples
        
        # Add functions to example
        for func in functions[:2]:  # Limit to 2 functions for brevity
            func_name = func.get("name", "function")
            if func_name.startswith("_"):
                continue  # Skip private functions
                
            imports.append(func_name)
            
            # Add function usage
            usage.append(f"// Call {func_name}")
            usage.append(f"const result = {func_name}();")
            usage.append("")  # Empty line between examples
        
        # Generate import statement
        if imports:
            import_list = ", ".join(imports)
            import_statement = f"import {{ {import_list} }} from './{module_name}';"
            
            example = f"```javascript\n{import_statement}\n\n"
            example += "\n".join(usage).rstrip() + "\n```"
            return example
        
        return "```javascript\n// Import and use the module based on your specific needs\n```"
    
    def _generate_config_usage_example(self, file_path: str, content: str, metadata: Dict[str, Any]) -> str:
        """Generate usage example for configuration files."""
        file_ext = os.path.splitext(file_path)[1].lower()
        language = metadata.get("language", "").lower()
        
        example = ""
        
        if file_ext in [".json", ".js"] or language == "json":
            example = """```javascript
// Example: Loading configuration in JavaScript
const fs = require('fs');
const config = JSON.parse(fs.readFileSync('config.json', 'utf8'));

// Access configuration values
console.log(`Database connection: ${config.database.url}`);
```"""
        elif file_ext in [".yaml", ".yml"] or language == "yaml":
            example = """```python
# Example: Loading configuration in Python
import yaml

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Access configuration values
print(f"Database connection: {config['database']['url']}")
```"""
        elif file_ext in [".toml"] or language == "toml":
            example = """```python
# Example: Loading configuration in Python
import toml

config = toml.load('config.toml')

# Access configuration values
print(f"Database connection: {config['database']['url']}")
```"""
        elif file_ext in [".ini", ".conf", ".cfg"] or language == "ini":
            example = """```python
# Example: Loading configuration in Python
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

# Access configuration values
print(f"Database connection: {config['database']['url']}")
```"""
        elif file_ext in [".env"]:
            example = """```javascript
// Example: Loading environment variables in Node.js
require('dotenv').config();

// Access environment variables
console.log(`Database URL: ${process.env.DATABASE_URL}`);
```"""
        else:
            example = """```python
# Example: Loading configuration (format-specific code would be used here)
config = load_configuration('config_file')

# Access configuration values
print(f"Setting value: {config['setting_name']}")
```"""
        
        return example
    
    def _generate_build_usage_example(self, file_path: str, content: str, metadata: Dict[str, Any]) -> str:
        """Generate usage example for build files."""
        file_basename = os.path.basename(file_path).lower()
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if "dockerfile" in file_basename:
            return """```bash
# Build the Docker image
docker build -t myapp:latest .

# Run the container
docker run -p 8080:8080 myapp:latest
```"""
        elif "makefile" in file_basename or file_basename == "makefile":
            return """```bash
# Run the default target
make

# Run a specific target
make build

# Clean the project
make clean
```"""
        elif file_ext in [".gradle"]:
            return """```bash
# Build the project
./gradlew build

# Run tests
./gradlew test

# Clean and rebuild
./gradlew clean build
```"""
        elif file_basename == "setup.py":
            return """```bash
# Install the package
pip install -e .

# Build a distribution
python setup.py sdist bdist_wheel
```"""
        elif file_basename == "package.json":
            return """```bash
# Install dependencies
npm install

# Run a script (e.g., start the application)
npm start

# Run tests
npm test
```"""
        elif file_basename == "requirements.txt":
            return """```bash
# Install dependencies
pip install -r requirements.txt
```"""
        else:
            return """```bash
# Execute the build script (specific commands depend on the build system)
./build.sh

# Or for compiled languages
./configure && make && make install
```"""
    
    def _generate_test_usage_example(self, file_path: str, content: str, metadata: Dict[str, Any]) -> str:
        """Generate usage example for test files."""
        file_basename = os.path.basename(file_path).lower()
        language = metadata.get("language", "").lower()
        
        if language == "python" and file_basename.startswith("test_"):
            return """```bash
# Run this specific test file
pytest path/to/test_file.py

# Run with verbose output
pytest -v path/to/test_file.py

# Run a specific test function
pytest path/to/test_file.py::test_function_name
```"""
        elif language in ["javascript", "typescript"]:
            if "jest" in content.lower():
                return """```bash
# Run tests with Jest
npm test

# Run with coverage report
npm test -- --coverage

# Run in watch mode
npm test -- --watch
```"""
            else:
                return """```bash
# Run tests with the configured test runner
npm test
```"""
        elif language in ["java", "kotlin"]:
            if "junit" in content.lower():
                return """```bash
# Run JUnit tests
./gradlew test

# Run a specific test class
./gradlew test --tests "com.example.TestClass"
```"""
            else:
                return """```bash
# Run tests with the configured build tool
./gradlew test
```"""
        else:
            return """```bash
# Run test suite (exact command depends on your testing framework)
run_tests

# Run this specific test
run_tests path/to/test_file
```"""
    
    def _get_default_value_for_param(self, param: str) -> str:
        """Get a sensible default value for a parameter based on its name."""
        param_name = param.strip().lower()
        
        # Handle common parameter names
        if any(name in param_name for name in ["path", "file", "dir", "directory"]):
            return "'path/to/file'"
        elif any(name in param_name for name in ["name", "title", "label", "key"]):
            return "'example_name'"
        elif any(name in param_name for name in ["id", "identifier"]):
            return "'id_123'"
        elif any(name in param_name for name in ["url", "uri", "link"]):
            return "'https://example.com'"
        elif any(name in param_name for name in ["count", "size", "length", "num", "limit"]):
            return "10"
        elif any(name in param_name for name in ["index", "position"]):
            return "0"
        elif any(name in param_name for name in ["enable", "disable", "flag", "is_", "has_"]):
            return "True"
        elif any(name in param_name for name in ["options", "config", "settings", "params"]):
            return "{}"
        elif any(name in param_name for name in ["data", "items", "elements", "values"]):
            return "[]"
        else:
            return "value"  # Generic fallback
    
    def _extract_key_components(
        self, 
        classes: List[Dict[str, Any]], 
        functions: List[Dict[str, Any]],
        variables: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Extract key components (classes, functions, variables) from metadata."""
        components = []
        
        # Add classes with enhanced descriptions
        for cls in classes:
            name = cls.get("name", "")
            doc = cls.get("documentation", "")
            methods = cls.get("methods", [])
            properties = cls.get("properties", [])
            
            if name:
                # Create more detailed description when documentation is missing
                if not doc:
                    if methods and properties:
                        method_count = len(methods) if isinstance(methods, list) else 0
                        prop_count = len(properties) if isinstance(properties, list) else 0
                        doc = f"A class with {method_count} methods and {prop_count} properties."
                    elif methods:
                        method_count = len(methods) if isinstance(methods, list) else 0
                        doc = f"A class with {method_count} methods."
                    elif properties:
                        prop_count = len(properties) if isinstance(properties, list) else 0
                        doc = f"A class with {prop_count} properties."
                    else:
                        doc = "A class defined in this file."
                
                components.append({
                    "name": name,
                    "description": doc,
                    "type": "class"
                })
        
        # Add functions with enhanced descriptions
        for func in functions:
            name = func.get("name", "")
            doc = func.get("documentation", "")
            parameters = func.get("parameters", [])
            
            if name:
                # Create more detailed description when documentation is missing
                if not doc:
                    if parameters:
                        param_count = len(parameters) if isinstance(parameters, list) else 0
                        if param_count > 0:
                            doc = f"A function that takes {param_count} parameters."
                        else:
                            doc = "A function defined in this file."
                    else:
                        doc = "A function defined in this file."
                
                components.append({
                    "name": name,
                    "description": doc,
                    "type": "function"
                })
        
        # Add important variables
        important_var_types = ["constant", "configuration", "global", "export"]
        for var in variables:
            name = var.get("name", "")
            doc = var.get("documentation", "")
            var_type = var.get("type", "").lower()
            
            if name and (doc or any(t in var_type for t in important_var_types)):
                components.append({
                    "name": name,
                    "description": doc or f"A {var_type} variable defined in this file.",
                    "type": "variable"
                })
        
        return components
    
    def _extract_main_concepts(
        self, 
        file_path: str, 
        content: str, 
        metadata: Dict[str, Any],
        file_category: str
    ) -> List[str]:
        """Extract main concepts implemented in the file."""
        concepts = []
        
        # Use file name as a concept
        base_name = os.path.basename(file_path)
        name_concept = self._convert_filename_to_concept(base_name)
        if name_concept:
            concepts.append(name_concept)
        
        # Use file category as a concept
        category_concept = file_category.capitalize()
        if category_concept and category_concept not in concepts:
            category_map = {
                "Code": "Implementation",
                "Config": "Configuration Management",
                "Build": "Build System",
                "Markup": "Documentation",
                "Test": "Testing"
            }
            concepts.append(category_map.get(category_concept, category_concept))
        
        # Use characteristics from metadata
        characteristics = metadata.get("characteristics", [])
        for char in characteristics:
            # Convert to title case and add
            concept = char.replace("_", " ").title()
            if concept and concept not in concepts:
                concepts.append(concept)
        
        # Use frameworks as concepts
        frameworks = metadata.get("frameworks", [])
        for framework in frameworks:
            name = framework.get("name", "")
            if name:
                framework_concept = f"{name.title()} Integration"
                if framework_concept not in concepts:
                    concepts.append(framework_concept)
        
        # Extract additional concepts based on file category
        if file_category == "code":
            # Look for design patterns in class and function names
            code_structure = metadata.get("code_structure", {}).get("structure", {})
            classes = code_structure.get("classes", [])
            
            pattern_indicators = {
                "Factory": "Factory Pattern",
                "Builder": "Builder Pattern",
                "Adapter": "Adapter Pattern",
                "Decorator": "Decorator Pattern",
                "Observer": "Observer Pattern",
                "Strategy": "Strategy Pattern",
                "Singleton": "Singleton Pattern",
                "Command": "Command Pattern",
                "Repository": "Repository Pattern",
                "Service": "Service Layer",
                "Controller": "MVC Pattern",
                "Model": "Data Modeling"
            }
            
            for cls in classes:
                name = cls.get("name", "")
                for indicator, pattern in pattern_indicators.items():
                    if indicator in name and pattern not in concepts:
                        concepts.append(pattern)
        
        elif file_category == "config":
            # Add concepts relevant to configuration
            config_concepts = [
                "Application Settings",
                "Environment Configuration"
            ]
            
            # Check content for specific configuration purposes
            if any(term in content.lower() for term in ["database", "db", "mongo", "postgres", "mysql"]):
                config_concepts.append("Database Configuration")
            
            if any(term in content.lower() for term in ["log", "debug", "trace", "error"]):
                config_concepts.append("Logging Configuration")
            
            if any(term in content.lower() for term in ["test", "dev", "stage", "prod"]):
                config_concepts.append("Environment-specific Settings")
            
            # Add concepts not already in the list
            for concept in config_concepts:
                if concept not in concepts:
                    concepts.append(concept)
        
        # If we don't have enough concepts, add generic ones based on file category
        if len(concepts) < 2:
            if file_category == "code":
                concepts.append("Software Implementation")
            elif file_category == "config":
                concepts.append("Application Configuration")
            elif file_category == "build":
                concepts.append("Build Automation")
            elif file_category == "markup":
                concepts.append("Project Documentation")
            elif file_category == "test":
                concepts.append("Quality Assurance")
        
        # Limit to most important concepts (max 5)
        return concepts[:5]
    
    def _generate_architecture_notes(
        self, 
        file_path: str, 
        metadata: Dict[str, Any],
        relationship_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate notes on how the file fits into the overall architecture."""
        # Use relationship data if available
        if relationship_data:
            imported_by_count = len(relationship_data.get("imported_by", []))
            imports_count = len(relationship_data.get("imports", []))
            inherits_count = len(relationship_data.get("inherits_from", []))
            inherited_by_count = len(relationship_data.get("inherited_by", []))
            
            notes = []
            
            if imported_by_count > 0:
                notes.append(f"This file is imported by {imported_by_count} other files, indicating it provides widely used functionality.")
            
            if imports_count > 0:
                notes.append(f"It imports {imports_count} other files to leverage existing functionality.")
            
            if inherits_count > 0:
                notes.append(f"It inherits from {inherits_count} other files, extending their functionality.")
            
            if inherited_by_count > 0:
                notes.append(f"It is inherited by {inherited_by_count} other files, serving as a base for derived implementations.")
            
            if notes:
                return " ".join(notes)
        
        # Look for imports as indicators of dependencies
        code_structure = metadata.get("code_structure", {}).get("structure", {})
        imports = code_structure.get("imports", [])
        
        if imports:
            return f"This file depends on {len(imports)} other modules and integrates with them to provide its functionality."
        
        return "This file is part of the application's architecture."
    
    def _generate_compilation_instructions(
        self, 
        file_path: str, 
        language: str, 
        file_type: str, 
        metadata: Dict[str, Any]
    ) -> str:
        """Generate compilation or execution instructions for the file."""
        file_basename = os.path.basename(file_path)
        
        # Handle different languages with appropriate instructions
        if language == "python":
            if file_basename.startswith("test_"):
                return "Run with pytest: `pytest path/to/this/file.py`"
            else:
                return "Import this module in other Python files or run directly with: `python path/to/this/file.py`"
        
        elif language in ["javascript", "typescript"]:
            if file_type == "test":
                return "Run with your configured test runner (jest, mocha, etc.): `npm test`"
            elif language == "javascript":
                return "For Node.js: `node path/to/this/file.js`\nFor browser: Import this file in your HTML with a script tag."
            else:
                return "Compile TypeScript to JavaScript: `tsc path/to/this/file.ts`\nThen run the compiled JavaScript file."
        
        elif language in ["java"]:
            if file_type == "test":
                return "Run with JUnit: `gradle test` or `mvn test`"
            else:
                return "Compile with javac: `javac path/to/this/file.java`\nRun with java: `java ClassName`"
        
        elif language in ["c", "cpp", "c++"]:
            return "Compile with gcc/g++: `g++ -o output_name path/to/this/file.cpp`\nRun the compiled executable: `./output_name`"
        
        elif language in ["go"]:
            return "Run with Go: `go run path/to/this/file.go`\nBuild executable: `go build path/to/this/file.go`"
        
        elif language in ["rust"]:
            return "Build with Cargo: `cargo build`\nRun with Cargo: `cargo run`"
        
        elif file_type == "config":
            return "This is a configuration file that is read by the application at runtime. It does not need to be compiled or executed directly."
        
        elif file_type == "markup" or language in ["markdown", "html"]:
            return "This is a documentation file. View it with a Markdown viewer, web browser, or text editor."
        
        # Generic fallback
        return "Compilation or execution instructions depend on how this file is used in your specific environment."
    
    def _extract_dependencies(
        self, 
        file_path: str, 
        metadata: Dict[str, Any],
        relationship_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """Extract dependencies of the file."""
        dependencies = []
        
        # Use relationship data if available
        if relationship_data:
            imports = relationship_data.get("imports", [])
            inherits_from = relationship_data.get("inherits_from", [])
            
            # Add imported files
            for imp in imports:
                dependencies.append({
                    "name": os.path.basename(imp),
                    "type": "import",
                    "path": imp
                })
            
            # Add inherited files
            for inh in inherits_from:
                dependencies.append({
                    "name": os.path.basename(inh),
                    "type": "inheritance",
                    "path": inh
                })
            
            # If we have dependencies from relationship data, return them
            if dependencies:
                return dependencies
        
        # Fall back to imports from code structure
        code_structure = metadata.get("code_structure", {}).get("structure", {})
        imports = code_structure.get("imports", [])
        
        for imp in imports:
            # Extract module name from import statement
            if isinstance(imp, str):
                # Handle different import formats
                module_name = ""
                
                # Python: from x import y or import x
                if "import" in imp:
                    if "from" in imp:
                        module_name = imp.split("from")[1].split("import")[0].strip()
                    else:
                        module_name = imp.split("import")[1].strip().split()[0]
                # JavaScript/TypeScript: import x from 'y'
                elif "from" in imp:
                    parts = imp.split("from")
                    if len(parts) > 1 and ("'" in parts[1] or '"' in parts[1]):
                        quoted = re.findall(r'[\'"]([^\'"]*)[\'"]', parts[1])
                        if quoted:
                            module_name = quoted[0]
                
                if module_name:
                    dependencies.append({
                        "name": module_name,
                        "type": "import",
                        "path": ""  # We don't have the actual path here
                    })
        
        return dependencies
    
    def _generate_file_type_specific_docs(
        self,
        file_path: str,
        content: str,
        metadata: Dict[str, Any],
        relationship_data: Optional[Dict[str, Any]],
        file_category: str
    ) -> Dict[str, Any]:
        """Generate documentation specific to the file type."""
        specific_docs = {}
        
        if file_category == "config":
            specific_docs = self._generate_config_specific_docs(file_path, content, metadata)
        elif file_category == "build":
            specific_docs = self._generate_build_specific_docs(file_path, content, metadata)
        elif file_category == "markup":
            specific_docs = self._generate_markup_specific_docs(file_path, content, metadata)
        elif file_category == "test":
            specific_docs = self._generate_test_specific_docs(file_path, content, metadata, relationship_data)
        
        return specific_docs
    
    def _generate_config_specific_docs(
        self, 
        file_path: str, 
        content: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate config file specific documentation."""
        # Extract config parameters from metadata if available
        config_docs = {
            "format": metadata.get("language", "unknown"),
            "parameters": [],
            "environment_vars": [],
            "default_values": [],
            "required_values": []
        }
        
        # Get parameters from config_structure if available
        config_structure = metadata.get("config_structure", {})
        parameters = config_structure.get("parameters", [])
        
        if parameters:
            for param in parameters:
                if isinstance(param, dict):
                    param_name = param.get("name", "")
                    param_value = param.get("value", "")
                    param_required = param.get("required", False)
                    param_description = param.get("description", "")
                    
                    if param_name:
                        config_docs["parameters"].append({
                            "name": param_name,
                            "value": param_value,
                            "required": param_required,
                            "description": param_description
                        })
                        
                        if param_value:
                            config_docs["default_values"].append({
                                "name": param_name,
                                "value": param_value
                            })
                        
                        if param_required:
                            config_docs["required_values"].append(param_name)
        
        # Extract environment variables
        env_vars = config_structure.get("environment_vars", [])
        if env_vars:
            for env_var in env_vars:
                if isinstance(env_var, dict):
                    var_name = env_var.get("name", "")
                    var_description = env_var.get("description", "")
                    
                    if var_name:
                        config_docs["environment_vars"].append({
                            "name": var_name,
                            "description": var_description
                        })
                elif isinstance(env_var, str):
                    config_docs["environment_vars"].append({
                        "name": env_var,
                        "description": ""
                    })
        
        return config_docs
    
    def _generate_build_specific_docs(
        self, 
        file_path: str, 
        content: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate build file specific documentation."""
        file_basename = os.path.basename(file_path).lower()
        
        build_docs = {
            "build_type": "",
            "targets": [],
            "dependencies": [],
            "environment_requirements": []
        }
        
        # Determine build type
        if "dockerfile" in file_basename:
            build_docs["build_type"] = "Docker"
            build_docs["targets"] = ["build", "run"]
            
            # Extract base image as dependency
            base_image_match = re.search(r'FROM\s+(\S+)', content)
            if base_image_match:
                build_docs["dependencies"].append({
                    "name": base_image_match.group(1),
                    "type": "base_image"
                })
            
            # Extract environment variables
            env_matches = re.findall(r'ENV\s+(\S+)\s+(\S+)', content)
            for env_match in env_matches:
                if len(env_match) >= 1:
                    build_docs["environment_requirements"].append({
                        "name": env_match[0],
                        "value": env_match[1] if len(env_match) > 1 else ""
                    })
        
        elif "makefile" in file_basename or file_basename == "makefile":
            build_docs["build_type"] = "Make"
            
            # Extract targets
            target_matches = re.findall(r'^([a-zA-Z0-9_-]+):', content, re.MULTILINE)
            for target in target_matches:
                build_docs["targets"].append(target)
            
            # Environment variables
            env_matches = re.findall(r'(\w+)\s*=\s*(\S+)', content)
            for env_match in env_matches:
                if len(env_match) >= 1:
                    build_docs["environment_requirements"].append({
                        "name": env_match[0],
                        "value": env_match[1] if len(env_match) > 1 else ""
                    })
        
        elif file_basename == "package.json":
            build_docs["build_type"] = "NPM/Yarn"
            
            # Try to extract scripts as targets
            try:
                import json
                package_data = json.loads(content)
                
                # Extract scripts
                if "scripts" in package_data:
                    for script_name in package_data["scripts"]:
                        build_docs["targets"].append(script_name)
                
                # Extract dependencies
                if "dependencies" in package_data:
                    for dep_name, dep_version in package_data["dependencies"].items():
                        build_docs["dependencies"].append({
                            "name": dep_name,
                            "version": dep_version,
                            "type": "runtime"
                        })
                
                # Extract dev dependencies
                if "devDependencies" in package_data:
                    for dep_name, dep_version in package_data["devDependencies"].items():
                        build_docs["dependencies"].append({
                            "name": dep_name,
                            "version": dep_version,
                            "type": "development"
                        })
            except:
                # Fallback if JSON parsing fails
                script_matches = re.findall(r'"scripts"\s*:\s*{\s*"([^"]+)"\s*:', content)
                for script in script_matches:
                    build_docs["targets"].append(script)
        
        elif file_basename == "setup.py":
            build_docs["build_type"] = "Python setuptools"
            build_docs["targets"] = ["install", "sdist", "bdist_wheel", "develop"]
            
            # Extract dependencies
            dep_matches = re.findall(r'install_requires\s*=\s*\[(.*?)\]', content, re.DOTALL)
            if dep_matches:
                deps_str = dep_matches[0]
                dep_list = re.findall(r'[\'"]([^\'"]+)[\'"]', deps_str)
                for dep in dep_list:
                    parts = dep.split(">=")
                    name = parts[0].strip()
                    version = parts[1].strip() if len(parts) > 1 else ""
                    build_docs["dependencies"].append({
                        "name": name,
                        "version": version,
                        "type": "runtime"
                    })
        
        elif file_basename == "requirements.txt":
            build_docs["build_type"] = "Python pip"
            build_docs["targets"] = ["install"]
            
            # Extract dependencies
            lines = content.split("\n")
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = re.split(r'[=><]', line)
                    name = parts[0].strip()
                    version = parts[1].strip() if len(parts) > 1 else ""
                    build_docs["dependencies"].append({
                        "name": name,
                        "version": version,
                        "type": "runtime"
                    })
        
        else:
            build_docs["build_type"] = "Unknown"
        
        return build_docs
    
    def _generate_markup_specific_docs(
        self, 
        file_path: str, 
        content: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate markup file specific documentation."""
        markup_docs = {
            "format": "",
            "sections": [],
            "structure": {}
        }
        
        # Determine format
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == ".md":
            markup_docs["format"] = "Markdown"
        elif file_ext == ".rst":
            markup_docs["format"] = "reStructuredText"
        elif file_ext == ".adoc":
            markup_docs["format"] = "AsciiDoc"
        elif file_ext == ".html":
            markup_docs["format"] = "HTML"
        elif file_ext == ".txt":
            markup_docs["format"] = "Plain Text"
        else:
            markup_docs["format"] = "Unknown"
        
        # Extract sections for Markdown
        if markup_docs["format"] == "Markdown":
            # Find headings
            heading_matches = re.findall(r'^(#+)\s+(.+)$', content, re.MULTILINE)
            toc = {}
            
            for heading in heading_matches:
                level = len(heading[0])
                title = heading[1].strip()
                
                markup_docs["sections"].append({
                    "level": level,
                    "title": title
                })
                
                # Build table of contents structure
                if level == 1:
                    if title not in toc:
                        toc[title] = []
                elif level == 2:
                    # Find the closest h1 heading
                    h1_title = None
                    for h in reversed(markup_docs["sections"]):
                        if h["level"] == 1:
                            h1_title = h["title"]
                            break
                    
                    if h1_title and h1_title in toc:
                        toc[h1_title].append(title)
            
            markup_docs["structure"] = toc
        
        return markup_docs
    
    def _generate_test_specific_docs(
        self, 
        file_path: str, 
        content: str, 
        metadata: Dict[str, Any],
        relationship_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate test file specific documentation."""
        test_docs = {
            "test_framework": "",
            "test_types": [],
            "tested_components": [],
            "test_cases": []
        }
        
        # Determine test framework
        if "pytest" in content.lower():
            test_docs["test_framework"] = "pytest"
        elif "unittest" in content.lower():
            test_docs["test_framework"] = "unittest"
        elif "jest" in content.lower():
            test_docs["test_framework"] = "Jest"
        elif "mocha" in content.lower():
            test_docs["test_framework"] = "Mocha"
        elif "junit" in content.lower():
            test_docs["test_framework"] = "JUnit"
        elif "testng" in content.lower():
            test_docs["test_framework"] = "TestNG"
        else:
            test_docs["test_framework"] = "Unknown"
        
        # Determine test types
        if "mock" in content.lower() or "patch" in content.lower():
            test_docs["test_types"].append("Unit Tests")
        if "integration" in content.lower():
            test_docs["test_types"].append("Integration Tests")
        if "fixture" in content.lower():
            test_docs["test_types"].append("Fixture Tests")
        if "e2e" in content.lower() or "end-to-end" in content.lower():
            test_docs["test_types"].append("End-to-End Tests")
        if "performance" in content.lower() or "benchmark" in content.lower():
            test_docs["test_types"].append("Performance Tests")
        
        # Default to Unit Tests if no specific type is found
        if not test_docs["test_types"]:
            test_docs["test_types"].append("Unit Tests")
        
        # Find tested components from imports or relationship data
        code_structure = metadata.get("code_structure", {}).get("structure", {})
        imports = code_structure.get("imports", [])
        
        for imp in imports:
            if isinstance(imp, str) and "test" not in imp.lower() and "fixture" not in imp.lower():
                # Extract module name from import
                module_name = ""
                
                # Handle different import formats
                if "import" in imp:
                    if "from" in imp:
                        module_name = imp.split("from")[1].split("import")[0].strip()
                    else:
                        module_name = imp.split("import")[1].strip().split()[0]
                
                if module_name and not module_name.startswith("unittest") and not module_name.startswith("pytest"):
                    test_docs["tested_components"].append({
                        "name": module_name,
                        "type": "module"
                    })
        
        # Use relationship data if available and no components found
        if relationship_data and not test_docs["tested_components"]:
            imports = relationship_data.get("imports", [])
            for imp in imports:
                if "test" not in imp.lower():
                    test_docs["tested_components"].append({
                        "name": os.path.basename(imp),
                        "path": imp,
                        "type": "file"
                    })
        
        # Extract test cases (functions that start with 'test_')
        functions = code_structure.get("functions", [])
        for func in functions:
            name = ""
            doc = ""
            
            if isinstance(func, dict):
                name = func.get("name", "")
                doc = func.get("documentation", "")
            elif isinstance(func, str):
                name = func
            
            if name.startswith("test_"):
                test_case = {
                    "name": name,
                    "description": doc or f"Test case for {name.replace('test_', '')}"
                }
                test_docs["test_cases"].append(test_case)
        
        return test_docs
    
    def _extract_module_docstring(self, content: str) -> str:
        """Extract the module-level docstring from the file content."""
        # Very simple docstring extraction - could be more sophisticated
        if '"""' in content:
            # Try to extract text between first pair of triple quotes
            start = content.find('"""')
            if start >= 0:
                end = content.find('"""', start + 3)
                if end >= 0:
                    docstring = content[start + 3:end].strip()
                    return docstring
        
        # Try single quotes style
        if "'''" in content:
            start = content.find("'''")
            if start >= 0:
                end = content.find("'''", start + 3)
                if end >= 0:
                    docstring = content[start + 3:end].strip()
                    return docstring
        
        # Try JavaDoc style
        if "/**" in content:
            start = content.find("/**")
            if start >= 0:
                end = content.find("*/", start + 3)
                if end >= 0:
                    docstring = content[start + 3:end].strip()
                    # Remove * at the beginning of lines
                    docstring = re.sub(r'^\s*\*\s?', '', docstring, flags=re.MULTILINE)
                    return docstring
        
        return ""
    
    def _convert_filename_to_concept(self, filename: str) -> str:
        """Convert a filename to a concept."""
        # Remove extension
        base_name = os.path.splitext(filename)[0]
        
        # Convert snake_case or kebab-case to space-separated
        name = base_name.replace("_", " ").replace("-", " ")
        
        # Title case and return
        return name.title()


def generate_file_documentation(
    file_path: str,
    content: str,
    metadata: Dict[str, Any],
    ai_provider: Optional[AIModelProvider] = None,
    relationship_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate AI documentation for a file.
    
    This is a convenience function that creates an AiDocumentationGenerator
    and generates documentation in one step.
    
    Args:
        file_path: Path to the file
        content: Content of the file
        metadata: Metadata from previous analysis steps
        ai_provider: AI provider to use (optional, defaults to MockAIProvider)
        relationship_data: Optional relationship data for the file
        
    Returns:
        Dictionary with documentation components
    """
    if not ai_provider:
        ai_provider = MockAIProvider()
    
    generator = AiDocumentationGenerator(ai_provider)
    return generator.generate_file_documentation(file_path, content, metadata, relationship_data)