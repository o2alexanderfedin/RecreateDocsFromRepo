"""
Unit tests for the metadata standardization component.
"""
import pytest
from unittest.mock import MagicMock, patch
import json
from pathlib import Path

from file_analyzer.core.metadata_standardization import (
    MetadataStandardizer,
    standardize_metadata,
    CODE_METADATA_SCHEMA
)


class TestMetadataStandardizer:
    """Tests for the MetadataStandardizer class."""
    
    @pytest.fixture
    def standardizer(self):
        """Create a metadata standardizer."""
        return MetadataStandardizer()
    
    def test_init(self, standardizer):
        """Test initialization of standardizer."""
        assert standardizer is not None
        # Check that the schema is loaded
        assert hasattr(standardizer, 'schema')
    
    def test_get_schema(self, standardizer):
        """Test getting the code metadata schema."""
        schema = standardizer.get_schema()
        assert schema is not None
        assert isinstance(schema, dict)
        # Check for key schema elements
        assert 'components' in schema
        assert 'relationships' in schema
        assert 'metadata' in schema
    
    def test_standardize_python_metadata(self, standardizer):
        """Test standardizing Python metadata."""
        # Sample AI analyzer output for Python
        python_metadata = {
            "language": "python",
            "structure": {
                "imports": ["import os", "from pathlib import Path"],
                "classes": [
                    {
                        "name": "ExampleClass",
                        "methods": [
                            {"name": "__init__", "parameters": ["self", "arg1"]},
                            {"name": "process", "parameters": ["self", "data"]}
                        ],
                        "properties": ["prop1", "prop2"],
                        "inheritance": ["BaseClass"]
                    }
                ],
                "functions": [
                    {"name": "example_function", "parameters": ["arg1", "arg2"]}
                ],
                "variables": ["CONST_VALUE"],
                "docstring": "Example Python module.",
                "language_specific": {
                    "decorators": ["@classmethod", "@property"],
                    "type_hints": {"arg1": "str", "arg2": "int"}
                }
            },
            "frameworks": [
                {"name": "django", "confidence": 0.9}
            ],
            "confidence": 0.95
        }
        
        result = standardizer.standardize(python_metadata)
        
        # Check standardized output structure
        assert 'components' in result
        assert 'relationships' in result
        assert 'metadata' in result
        
        # Check component standardization
        components = result['components']
        classes = [c for c in components if c['type'] == 'class']
        assert len(classes) == 1
        assert classes[0]['name'] == 'ExampleClass'
        assert len(classes[0]['methods']) == 2
        
        functions = [c for c in components if c['type'] == 'function']
        assert len(functions) == 1
        assert functions[0]['name'] == 'example_function'
        
        # Check relationship standardization
        relationships = result['relationships']
        inheritance = [r for r in relationships if r['type'] == 'inheritance']
        assert len(inheritance) == 1
        assert inheritance[0]['source'] == 'ExampleClass'
        assert inheritance[0]['target'] == 'BaseClass'
        
        # Check metadata
        assert result['metadata']['language'] == 'python'
        assert 'django' in [f['name'] for f in result['metadata']['frameworks']]
    
    def test_standardize_javascript_metadata(self, standardizer):
        """Test standardizing JavaScript metadata."""
        # Sample AI analyzer output for JavaScript
        js_metadata = {
            "language": "javascript",
            "structure": {
                "imports": ["import React from 'react'", "import { useState } from 'react'"],
                "classes": [
                    {
                        "name": "Component",
                        "methods": [
                            {"name": "constructor", "parameters": ["props"]},
                            {"name": "render", "parameters": []}
                        ],
                        "properties": ["state", "props"],
                        "inheritance": ["React.Component"]
                    }
                ],
                "functions": [
                    {"name": "useExample", "parameters": ["value"]}
                ],
                "variables": ["DEFAULT_STATE"],
                "docstring": "Example React component.",
                "language_specific": {
                    "jsx": True,
                    "hooks": ["useState", "useEffect"]
                }
            },
            "frameworks": [
                {"name": "react", "confidence": 0.95}
            ],
            "confidence": 0.9
        }
        
        result = standardizer.standardize(js_metadata)
        
        # Check component standardization
        components = result['components']
        classes = [c for c in components if c['type'] == 'class']
        assert len(classes) == 1
        assert classes[0]['name'] == 'Component'
        assert classes[0]['language_specific']['jsx'] is True
        
        functions = [c for c in components if c['type'] == 'function']
        assert len(functions) == 1
        assert functions[0]['name'] == 'useExample'
        
        # Check relationship standardization
        relationships = result['relationships']
        inheritance = [r for r in relationships if r['type'] == 'inheritance']
        assert len(inheritance) == 1
        assert inheritance[0]['source'] == 'Component'
        assert inheritance[0]['target'] == 'React.Component'
        
        # Check framework metadata is standardized
        assert result['metadata']['language'] == 'javascript'
        assert 'react' in [f['name'] for f in result['metadata']['frameworks']]
    
    def test_standardize_java_metadata(self, standardizer):
        """Test standardizing Java metadata."""
        # Sample AI analyzer output for Java
        java_metadata = {
            "language": "java",
            "structure": {
                "imports": ["import java.util.List", "import java.util.ArrayList"],
                "classes": [
                    {
                        "name": "ExampleService",
                        "methods": [
                            {"name": "process", "parameters": ["String data"], "return_type": "void"},
                            {"name": "getData", "parameters": [], "return_type": "List<String>"}
                        ],
                        "properties": ["private List<String> items"],
                        "annotations": ["@Service", "@Autowired"],
                        "inheritance": [],
                        "implements": ["DataProcessor"]
                    }
                ],
                "interfaces": [
                    {
                        "name": "DataProcessor",
                        "methods": [
                            {"name": "process", "parameters": ["String data"], "return_type": "void"}
                        ]
                    }
                ],
                "docstring": "Example Spring service.",
                "language_specific": {
                    "annotations": ["@Service", "@Autowired"],
                    "generics": ["List<String>"]
                }
            },
            "frameworks": [
                {"name": "spring", "confidence": 0.9}
            ],
            "confidence": 0.85
        }
        
        result = standardizer.standardize(java_metadata)
        
        # Check component standardization
        components = result['components']
        classes = [c for c in components if c['type'] == 'class']
        assert len(classes) == 1
        assert classes[0]['name'] == 'ExampleService'
        
        interfaces = [c for c in components if c['type'] == 'interface']
        assert len(interfaces) == 1
        assert interfaces[0]['name'] == 'DataProcessor'
        
        # Check relationship standardization
        relationships = result['relationships']
        implements = [r for r in relationships if r['type'] == 'implements']
        assert len(implements) == 1
        assert implements[0]['source'] == 'ExampleService'
        assert implements[0]['target'] == 'DataProcessor'
        
        # Check Java-specific metadata is standardized
        assert result['metadata']['language'] == 'java'
        assert 'spring' in [f['name'] for f in result['metadata']['frameworks']]
        # Check annotations are preserved
        assert '@Service' in result['components'][0]['language_specific']['annotations']
    
    def test_consistency_across_languages(self, standardizer):
        """Test that standardization provides consistent output format across languages."""
        languages = ['python', 'javascript', 'java']
        results = []
        
        for lang in languages:
            # Create minimal metadata for each language
            metadata = {
                "language": lang,
                "structure": {
                    "imports": [],
                    "classes": [{"name": f"Test{lang.capitalize()}", "methods": [], "properties": []}],
                    "functions": [],
                    "variables": [],
                    "docstring": f"Test {lang} file."
                },
                "frameworks": [],
                "confidence": 0.8
            }
            results.append(standardizer.standardize(metadata))
        
        # Check that all results have the same structure
        for result in results:
            assert set(result.keys()) == {'components', 'relationships', 'metadata'}
            assert set(result['metadata'].keys()) >= {'language', 'frameworks', 'confidence'}
    
    def test_handle_unknown_language(self, standardizer):
        """Test handling of unknown language."""
        unknown_metadata = {
            "language": "unknown",
            "structure": {
                "imports": [],
                "classes": [],
                "functions": [{"name": "main", "parameters": []}],
                "variables": [],
                "docstring": "Unknown language file."
            },
            "confidence": 0.5
        }
        
        result = standardizer.standardize(unknown_metadata)
        
        # Should still standardize with generic approach
        assert result['metadata']['language'] == 'unknown'
        assert len(result['components']) == 1
        assert result['components'][0]['name'] == 'main'
    
    def test_convenience_function(self):
        """Test the convenience function for standardization."""
        # Test the module-level convenience function
        test_metadata = {
            "language": "python",
            "structure": {
                "imports": ["import os"],
                "classes": [],
                "functions": [{"name": "test", "parameters": []}],
                "variables": [],
                "docstring": "Test file."
            },
            "confidence": 0.8
        }
        
        result = standardize_metadata(test_metadata)
        
        # Check the standardized result
        assert 'components' in result
        assert 'relationships' in result
        assert 'metadata' in result
        assert result['metadata']['language'] == 'python'
    
    def test_schema_conformance(self, standardizer):
        """Test that standardized metadata conforms to the defined schema."""
        test_metadata = {
            "language": "python",
            "structure": {
                "imports": ["import os"],
                "classes": [{"name": "Test", "methods": [], "properties": []}],
                "functions": [],
                "variables": [],
                "docstring": "Test file."
            },
            "confidence": 0.8
        }
        
        result = standardizer.standardize(test_metadata)
        
        # Check against schema structure
        assert set(result.keys()) == set(CODE_METADATA_SCHEMA.keys())
        
        # Check components structure
        for component in result['components']:
            assert 'type' in component
            assert 'name' in component
            assert component['type'] in ['class', 'function', 'interface', 'variable']
    
    def test_preserve_language_specific_features(self, standardizer):
        """Test that language-specific features are preserved."""
        # Python with decorators
        python_metadata = {
            "language": "python",
            "structure": {
                "imports": [],
                "classes": [{"name": "Test", "methods": [], "properties": []}],
                "functions": [],
                "variables": [],
                "docstring": "",
                "language_specific": {
                    "decorators": ["@staticmethod", "@property"],
                    "type_hints": {"return": "str"}
                }
            },
            "confidence": 0.8
        }
        
        result = standardizer.standardize(python_metadata)
        
        # Check language-specific features are preserved
        cls = [c for c in result['components'] if c['type'] == 'class'][0]
        assert 'language_specific' in cls
        assert 'decorators' in cls['language_specific']
        assert '@staticmethod' in cls['language_specific']['decorators']