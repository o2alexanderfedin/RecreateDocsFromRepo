"""
Metadata standardization system for normalizing output from different language analyzers.

This module provides functionality to standardize and normalize metadata extracted from
different programming languages and frameworks into a consistent format for
documentation generation.
"""
import logging
from typing import Dict, Any
import copy

logger = logging.getLogger("file_analyzer.core.metadata_standardization")

# Standard schema for code metadata
CODE_METADATA_SCHEMA = {
    "components": [],  # Classes, functions, interfaces, etc.
    "relationships": [],  # Inheritance, implementation, dependencies, etc.
    "metadata": {
        "language": "",
        "frameworks": [],
        "confidence": 0.0,
        "description": "",
        "file_path": ""
    }
}

# Standard schema for a componen
COMPONENT_SCHEMA = {
    "type": "",  # class, function, interface, variable
    "name": "",
    "description": "",
    "methods": [],
    "properties": [],
    "parameters": [],
    "return_type": None,
    "visibility": "public",  # public, private, protected
    "language_specific": {}
}

# Standard schema for a relationship
RELATIONSHIP_SCHEMA = {
    "type": "",  # inheritance, implements, dependency, etc.
    "source": "",
    "target": "",
    "description": "",
    "confidence": 1.0
}


class MetadataStandardizer:
    """
    Standardizes metadata from different languages into a consistent format.

    This class provides methods to normalize and standardize metadata extracted
    from different programming languages and frameworks to ensure consisten
    documentation generation regardless of the source language.
    """

    def __init__(self):
        """Initialize the metadata standardizer."""
        self.schema = CODE_METADATA_SCHEMA
        self.language_handlers = {
            "python": self._standardize_python,
            "javascript": self._standardize_javascript,
            "typescript": self._standardize_javascript,  # Share same handler
            "java": self._standardize_java
        }

    def get_schema(self) -> Dict[str, Any]:
        """
        Get the standard code metadata schema.

        Returns:
            The standard schema for code metadata.
        """
        return copy.deepcopy(self.schema)

    def standardize(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardize metadata from any language into the consistent format.

        Args:
            metadata: The metadata output from an AI analyzer.

        Returns:
            Standardized metadata in a consistent format.
        """
        language = metadata.get("language", "unknown").lower()

        # Create standardized result structure
        result = self.get_schema()

        # Set metadata
        result["metadata"]["language"] = language
        result["metadata"]["frameworks"] = metadata.get("frameworks", [])
        result["metadata"]["confidence"] = metadata.get("confidence", 0.0)

        if "file_path" in metadata:
            result["metadata"]["file_path"] = metadata["file_path"]

        if "structure" in metadata and "docstring" in metadata["structure"]:
            result["metadata"]["description"] = metadata["structure"]["docstring"]

        # Use language-specific handler if available, otherwise use generic handler
        if language in self.language_handlers:
            handler = self.language_handlers[language]
        else:
            handler = self._standardize_generic

        # Process components and relationships
        handler(metadata, result)

        return result

    def _standardize_python(self, metadata: Dict[str, Any], result: Dict[str, Any]) -> None:
        """
        Standardize Python-specific metadata.

        Args:
            metadata: The Python metadata to standardize.
            result: The result dictionary to populate.
        """
        if "structure" not in metadata:
            return

        structure = metadata["structure"]

        # Process classes
        for cls in structure.get("classes", []):
            component = copy.deepcopy(COMPONENT_SCHEMA)
            component["type"] = "class"
            component["name"] = cls["name"]
            component["methods"] = cls.get("methods", [])
            component["properties"] = cls.get("properties", [])

            # Handle language-specific features
            if "language_specific" in structure:
                component["language_specific"] = copy.deepcopy(structure["language_specific"])

            result["components"].append(component)

            # Handle inheritance relationships
            for parent in cls.get("inheritance", []):
                relationship = copy.deepcopy(RELATIONSHIP_SCHEMA)
                relationship["type"] = "inheritance"
                relationship["source"] = cls["name"]
                relationship["target"] = parent
                relationship["description"] = f"{cls['name']} inherits from {parent}"
                result["relationships"].append(relationship)

        # Process functions
        for func in structure.get("functions", []):
            component = copy.deepcopy(COMPONENT_SCHEMA)
            component["type"] = "function"
            component["name"] = func["name"]
            component["parameters"] = func.get("parameters", [])

            # Handle return type if available
            if "return_type" in func:
                component["return_type"] = func["return_type"]

            result["components"].append(component)

        # Process variables
        for var in structure.get("variables", []):
            component = copy.deepcopy(COMPONENT_SCHEMA)
            component["type"] = "variable"
            component["name"] = var
            result["components"].append(component)

    def _standardize_javascript(self, metadata: Dict[str, Any], result: Dict[str, Any]) -> None:
        """
        Standardize JavaScript/TypeScript-specific metadata.

        Args:
            metadata: The JavaScript/TypeScript metadata to standardize.
            result: The result dictionary to populate.
        """
        if "structure" not in metadata:
            return

        structure = metadata["structure"]

        # Process classes
        for cls in structure.get("classes", []):
            component = copy.deepcopy(COMPONENT_SCHEMA)
            component["type"] = "class"
            component["name"] = cls["name"]
            component["methods"] = cls.get("methods", [])
            component["properties"] = cls.get("properties", [])

            # Handle language-specific features like JSX, hooks, etc.
            if "language_specific" in structure:
                component["language_specific"] = copy.deepcopy(structure["language_specific"])

            result["components"].append(component)

            # Handle inheritance relationships
            for parent in cls.get("inheritance", []):
                relationship = copy.deepcopy(RELATIONSHIP_SCHEMA)
                relationship["type"] = "inheritance"
                relationship["source"] = cls["name"]
                relationship["target"] = parent
                relationship["description"] = f"{cls['name']} extends {parent}"
                result["relationships"].append(relationship)

        # Process functions (including React hooks, etc.)
        for func in structure.get("functions", []):
            component = copy.deepcopy(COMPONENT_SCHEMA)
            component["type"] = "function"
            component["name"] = func["name"]
            component["parameters"] = func.get("parameters", [])

            # Detect if this is a React hook
            if "language_specific" in structure and "hooks" in structure["language_specific"]:
                if any(func["name"].startswith(hook) for hook in structure["language_specific"]["hooks"]):
                    component["language_specific"]["is_hook"] = True

            result["components"].append(component)

        # Process variables and constants
        for var in structure.get("variables", []):
            component = copy.deepcopy(COMPONENT_SCHEMA)
            component["type"] = "variable"
            component["name"] = var
            result["components"].append(component)

        # Handle import relationships
        for imp in structure.get("imports", []):
            # Simplified parsing for demonstration
            if "from" in imp and "import" in imp:
                try:
                    # Extract module and imported items
                    parts = imp.split("from")
                    if len(parts) == 2:
                        imported = parts[0].replace("import", "").strip()
                        module = parts[1].strip().strip("'").strip('"')

                        relationship = copy.deepcopy(RELATIONSHIP_SCHEMA)
                        relationship["type"] = "dependency"
                        relationship["source"] = "current_file"
                        relationship["target"] = module
                        relationship["description"] = f"Imports {imported} from {module}"
                        result["relationships"].append(relationship)
                except Exception as e:
                    logger.debug(f"Error parsing import statement {imp}: {str(e)}")

    def _standardize_java(self, metadata: Dict[str, Any], result: Dict[str, Any]) -> None:
        """
        Standardize Java-specific metadata.

        Args:
            metadata: The Java metadata to standardize.
            result: The result dictionary to populate.
        """
        if "structure" not in metadata:
            return

        structure = metadata["structure"]

        # Process classes
        for cls in structure.get("classes", []):
            component = copy.deepcopy(COMPONENT_SCHEMA)
            component["type"] = "class"
            component["name"] = cls["name"]
            component["methods"] = cls.get("methods", [])
            component["properties"] = cls.get("properties", [])

            # Handle Java-specific features like annotations
            if "annotations" in cls:
                if "language_specific" not in component:
                    component["language_specific"] = {}
                component["language_specific"]["annotations"] = cls["annotations"]

            if "language_specific" in structure:
                for key, value in structure["language_specific"].items():
                    if "language_specific" not in component:
                        component["language_specific"] = {}
                    component["language_specific"][key] = value

            result["components"].append(component)

            # Handle inheritance relationships
            for parent in cls.get("inheritance", []):
                relationship = copy.deepcopy(RELATIONSHIP_SCHEMA)
                relationship["type"] = "inheritance"
                relationship["source"] = cls["name"]
                relationship["target"] = parent
                relationship["description"] = f"{cls['name']} extends {parent}"
                result["relationships"].append(relationship)

            # Handle implementation relationships
            for interface in cls.get("implements", []):
                relationship = copy.deepcopy(RELATIONSHIP_SCHEMA)
                relationship["type"] = "implements"
                relationship["source"] = cls["name"]
                relationship["target"] = interface
                relationship["description"] = f"{cls['name']} implements {interface}"
                result["relationships"].append(relationship)

        # Process interfaces
        for interface in structure.get("interfaces", []):
            component = copy.deepcopy(COMPONENT_SCHEMA)
            component["type"] = "interface"
            component["name"] = interface["name"]
            component["methods"] = interface.get("methods", [])

            if "language_specific" in structure:
                component["language_specific"] = copy.deepcopy(structure["language_specific"])

            result["components"].append(component)

    def _standardize_generic(self, metadata: Dict[str, Any], result: Dict[str, Any]) -> None:
        """
        Standardize metadata from unknown or unsupported languages.

        Args:
            metadata: The metadata to standardize.
            result: The result dictionary to populate.
        """
        if "structure" not in metadata:
            return

        structure = metadata["structure"]

        # Process classes if presen
        for cls in structure.get("classes", []):
            component = copy.deepcopy(COMPONENT_SCHEMA)
            component["type"] = "class"
            component["name"] = cls["name"]
            component["methods"] = cls.get("methods", [])
            component["properties"] = cls.get("properties", [])

            result["components"].append(component)

        # Process functions if presen
        for func in structure.get("functions", []):
            component = copy.deepcopy(COMPONENT_SCHEMA)
            component["type"] = "function"
            component["name"] = func["name"]
            component["parameters"] = func.get("parameters", [])

            result["components"].append(component)

        # Process variables if presen
        for var in structure.get("variables", []):
            component = copy.deepcopy(COMPONENT_SCHEMA)
            component["type"] = "variable"
            component["name"] = var

            result["components"].append(component)


def standardize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to standardize metadata.

    Args:
        metadata: The metadata to standardize.

    Returns:
        Standardized metadata in a consistent format.
    """
    standardizer = MetadataStandardizer()
    return standardizer.standardize(metadata)
