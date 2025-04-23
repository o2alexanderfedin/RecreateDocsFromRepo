"""
AI-powered documentation generator for files.

This module uses AI to generate rich, detailed documentation for files
based on their content and metadata from previous analysis steps.
"""
import logging
import os
from typing import Dict, Any, List, Optional, Union

from file_analyzer.ai_providers.provider_interface import AIModelProvider
from file_analyzer.ai_providers.mock_provider import MockAIProvider

logger = logging.getLogger("file_analyzer.doc_generator.ai_documentation_generator")

class AiDocumentationGenerator:
    """
    Generates AI-powered documentation for files.
    
    This class uses AI to analyze file content and metadata
    to generate detailed, insightful documentation that
    explains the purpose, components, and usage of files.
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
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive documentation for a file.
        
        Args:
            file_path: Path to the file
            content: Content of the file
            metadata: Metadata from previous analysis steps
            
        Returns:
            Dictionary with documentation components including:
            - description: Overall description of the file
            - purpose: Main purpose of the file in the codebase
            - usage_examples: Code examples demonstrating usage
            - key_components: Important classes, functions, etc.
            - main_concepts: Key concepts implemented in the file
            - architecture_notes: How the file fits into the overall architecture
        """
        logger.debug(f"Generating AI documentation for {file_path}")
        
        # Get file language from metadata if available
        language = metadata.get("language", "")
        file_type = metadata.get("file_type", "")
        
        # Check if the AI provider has a specific documentation generation method
        if hasattr(self.ai_provider, "generate_documentation"):
            logger.debug("Using provider's native documentation generation")
            return self.ai_provider.generate_documentation(file_path, content, metadata)
        
        # Otherwise, construct documentation from available information
        logger.debug("Constructing documentation from metadata")
        
        # Extract structure information
        code_structure = metadata.get("code_structure", {}).get("structure", {})
        classes = code_structure.get("classes", [])
        functions = code_structure.get("functions", [])
        imports = code_structure.get("imports", [])
        
        # Extract framework information
        frameworks = metadata.get("frameworks", [])
        
        # Default documentation structure
        documentation = {
            "description": self._generate_description(file_path, content, metadata),
            "purpose": self._generate_purpose(file_path, content, metadata),
            "usage_examples": self._generate_usage_examples(file_path, content, metadata),
            "key_components": self._extract_key_components(classes, functions),
            "main_concepts": self._extract_main_concepts(file_path, content, metadata),
            "architecture_notes": self._generate_architecture_notes(file_path, metadata)
        }
        
        return documentation
    
    def _generate_description(
        self, 
        file_path: str, 
        content: str, 
        metadata: Dict[str, Any]
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
        
        # Fallback to basic description
        return f"This is a {language} {file_type} file in the project."
    
    def _generate_purpose(
        self, 
        file_path: str, 
        content: str, 
        metadata: Dict[str, Any]
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
        metadata: Dict[str, Any]
    ) -> List[str]:
        """Generate usage examples for the file."""
        examples = []
        
        # Get language for code blocks
        language = metadata.get("language", "").lower()
        
        # Generate example based on file type
        code_structure = metadata.get("code_structure", {}).get("structure", {})
        classes = code_structure.get("classes", [])
        functions = code_structure.get("functions", [])
        
        if classes and language == "python":
            # Create example using the first class
            class_name = classes[0].get("name", "Class")
            example = f"```python\nfrom {os.path.basename(file_path).replace('.py', '')} import {class_name}\n\n"
            example += f"# Create an instance of {class_name}\ninstance = {class_name}()\n"
            
            # Add method call if available
            methods = classes[0].get("methods", [])
            if methods:
                method = next((m for m in methods if not m.startswith("__")), methods[0])
                example += f"result = instance.{method}()\n"
            
            example += "```"
            examples.append(example)
        
        elif functions and language == "python":
            # Create example using the first function
            func_name = functions[0].get("name", "function")
            example = f"```python\nfrom {os.path.basename(file_path).replace('.py', '')} import {func_name}\n\n"
            example += f"# Call the function\nresult = {func_name}()\n```"
            examples.append(example)
        
        # If we couldn't generate specific examples, add a generic one
        if not examples:
            if language:
                examples.append(f"```{language}\n# Example usage will depend on your specific use case\n```")
            else:
                examples.append("Usage examples will depend on the specific context of your project.")
        
        return examples
    
    def _extract_key_components(
        self, 
        classes: List[Dict[str, Any]], 
        functions: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Extract key components (classes, functions) from metadata."""
        components = []
        
        # Add classes
        for cls in classes:
            name = cls.get("name", "")
            doc = cls.get("documentation", "")
            
            if name:
                components.append({
                    "name": name,
                    "description": doc or f"A class defined in this file."
                })
        
        # Add functions
        for func in functions:
            name = func.get("name", "")
            doc = func.get("documentation", "")
            
            if name:
                components.append({
                    "name": name,
                    "description": doc or f"A function defined in this file."
                })
        
        return components
    
    def _extract_main_concepts(
        self, 
        file_path: str, 
        content: str, 
        metadata: Dict[str, Any]
    ) -> List[str]:
        """Extract main concepts implemented in the file."""
        concepts = []
        
        # Use file name as a concept
        base_name = os.path.basename(file_path)
        name_concept = self._convert_filename_to_concept(base_name)
        if name_concept:
            concepts.append(name_concept)
        
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
                concepts.append(f"{name.title()} Integration")
        
        # If we don't have enough concepts, add generic ones based on file type
        if len(concepts) < 2:
            file_type = metadata.get("file_type", "")
            if file_type == "code":
                concepts.append("Implementation")
            elif file_type == "configuration":
                concepts.append("Configuration Management")
            elif file_type == "documentation":
                concepts.append("Documentation")
            elif file_type == "test":
                concepts.append("Testing")
        
        return concepts
    
    def _generate_architecture_notes(
        self, 
        file_path: str, 
        metadata: Dict[str, Any]
    ) -> str:
        """Generate notes on how the file fits into the overall architecture."""
        # Look for imports as indicators of dependencies
        code_structure = metadata.get("code_structure", {}).get("structure", {})
        imports = code_structure.get("imports", [])
        
        if imports:
            return f"This file depends on {len(imports)} other modules and integrates with them to provide its functionality."
        
        return "This file is part of the application's architecture."
    
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
    ai_provider: Optional[AIModelProvider] = None
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
        
    Returns:
        Dictionary with documentation components
    """
    if not ai_provider:
        ai_provider = MockAIProvider()
    
    generator = AiDocumentationGenerator(ai_provider)
    return generator.generate_file_documentation(file_path, content, metadata)