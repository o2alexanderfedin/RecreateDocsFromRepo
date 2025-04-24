import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from file_analyzer.doc_generator.config_documentation_generator import (
    ConfigDocumentationGenerator,
    generate_config_file_documentation
)
from file_analyzer.core.config_relationship_mapper import ConfigRelationshipMapper


class TestConfigDocumentationGenerator:
    """Test suite for ConfigDocumentationGenerator."""
    
    @pytest.fixture
    def mock_ai_provider(self):
        """Create a mock AI provider."""
        mock_provider = MagicMock()
        mock_provider.simple_completion.return_value = "Mock documentation description"
        return mock_provider
    
    @pytest.fixture
    def mock_relationship_mapper(self):
        """Create a mock relationship mapper with test data."""
        mock_mapper = MagicMock(spec=ConfigRelationshipMapper)
        
        # Sample relationship data for a config file
        mock_mapper.map_config_to_code_relationships.return_value = {
            "file_path": "/mock/config.json",
            "format": "json",
            "is_config_file": True,
            "framework": None,
            "parameters": [
                {
                    "path": "app.name", 
                    "value": "TestApp",
                    "type": "string",
                    "referenced": True
                },
                {
                    "path": "database.host", 
                    "value": "localhost",
                    "type": "string",
                    "referenced": True
                },
                {
                    "path": "database.password", 
                    "value": "${DB_PASSWORD}",
                    "type": "environment_variable",
                    "referenced": True
                },
                {
                    "path": "logging.level", 
                    "value": "info",
                    "type": "string",
                    "referenced": False
                }
            ],
            "environment_vars": ["${DB_PASSWORD}"],
            "env_var_usages": [
                {
                    "file_path": "/mock/database.py",
                    "var_name": "DB_PASSWORD",
                    "line": 12
                }
            ],
            "direct_references": [
                {
                    "file_path": "/mock/app.py",
                    "language": "python",
                    "reference_type": "direct_load",
                    "references": [
                        {
                            "file_path": "/mock/app.py",
                            "reference_type": "direct_load",
                            "language": "python",
                            "line": 5
                        }
                    ]
                }
            ],
            "indirect_references": [
                {
                    "file_path": "/mock/utils.py",
                    "language": "python",
                    "reference_type": "indirect_reference",
                    "references": [
                        {
                            "file_path": "/mock/utils.py",
                            "reference_type": "indirect_reference",
                            "language": "python",
                            "line": 2
                        }
                    ]
                }
            ]
        }
        
        return mock_mapper
    
    @pytest.fixture
    def mock_file_reader(self):
        """Create a mock file reader."""
        mock_reader = MagicMock()
        mock_reader.read_file.return_value = '{"app": {"name": "TestApp"}, "database": {"host": "localhost"}}'
        return mock_reader
    
    @pytest.fixture
    def config_generator(self, mock_ai_provider, mock_relationship_mapper, mock_file_reader):
        """Create a ConfigDocumentationGenerator instance for testing."""
        return ConfigDocumentationGenerator(
            ai_provider=mock_ai_provider,
            relationship_mapper=mock_relationship_mapper,
            file_reader=mock_file_reader
        )
    
    def test_initialization(self, config_generator, mock_ai_provider, mock_relationship_mapper):
        """Test that the generator initializes correctly."""
        assert config_generator.ai_provider == mock_ai_provider
        assert config_generator.relationship_mapper == mock_relationship_mapper
        assert config_generator.file_reader is not None
    
    def test_generate_config_documentation(self, config_generator, mock_relationship_mapper):
        """Test generating documentation for a config file."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            temp_file.write(b'{"app": {"name": "TestApp"}, "database": {"host": "localhost"}}')
            temp_path = temp_file.name
        
        try:
            # Generate documentation
            result = config_generator.generate_config_documentation(temp_path)
            
            # Check that relationship mapper was called
            mock_relationship_mapper.map_config_to_code_relationships.assert_called_once()
            
            # Check that the result contains expected sections
            assert "variables" in result
            assert "environment_vars" in result
            assert "env_var_descriptions" in result
            assert "param_usage" in result
            
            # Check variables are formatted correctly
            assert len(result["variables"]) == 4
            assert any(var["name"] == "app.name" for var in result["variables"])
            assert any(var["name"] == "database.host" for var in result["variables"])
            
            # Check environment variables
            assert "${DB_PASSWORD}" in result["environment_vars"]
            assert "${DB_PASSWORD}" in result["env_var_descriptions"]
            
            # Check parameter usage mapping
            assert "param_usage" in result
            assert isinstance(result["param_usage"], dict)
            
            # Check AI documentation
            assert "ai_documentation" in result
        finally:
            # Clean up temp file
            os.unlink(temp_path)
    
    def test_generate_parameter_documentation(self, config_generator):
        """Test generating documentation for parameters."""
        # Test with different parameter types
        string_param = {"path": "app.name", "value": "TestApp", "type": "string"}
        int_param = {"path": "database.port", "value": "5432", "type": "integer"}
        bool_param = {"path": "debug", "value": "true", "type": "boolean"}
        env_param = {"path": "password", "value": "${DB_PASSWORD}", "type": "environment_variable"}
        
        # Generate documentation for each parameter
        string_doc = config_generator._generate_parameter_documentation(string_param)
        int_doc = config_generator._generate_parameter_documentation(int_param)
        bool_doc = config_generator._generate_parameter_documentation(bool_param)
        env_doc = config_generator._generate_parameter_documentation(env_param)
        
        # Since we're using a mock AI provider that always returns "Mock documentation description",
        # we just need to assert that we get back some documentation for each parameter
        assert string_doc
        assert isinstance(string_doc, str)
        assert int_doc
        assert isinstance(int_doc, str)
        assert bool_doc
        assert isinstance(bool_doc, str)
        assert env_doc
        assert isinstance(env_doc, str)
    
    def test_generate_env_var_documentation(self, config_generator):
        """Test generating documentation for environment variables."""
        # Test with different environment variables
        env_var_usages = [
            {"file_path": "/mock/app.py", "var_name": "DB_PASSWORD", "line": 5},
            {"file_path": "/mock/database.py", "var_name": "API_KEY", "line": 10}
        ]
        
        # Generate documentation for different environment variables
        password_doc = config_generator._generate_env_var_documentation("DB_PASSWORD", env_var_usages)
        api_key_doc = config_generator._generate_env_var_documentation("API_KEY", env_var_usages)
        host_doc = config_generator._generate_env_var_documentation("DB_HOST", env_var_usages)
        
        # Since we're using a mock AI provider that always returns "Mock documentation description",
        # we just need to verify that we get documentation strings for each variable
        assert password_doc
        assert isinstance(password_doc, str)
        assert api_key_doc
        assert isinstance(api_key_doc, str)
        assert host_doc
        assert isinstance(host_doc, str)
    
    def test_convenience_function(self, mock_ai_provider, mock_relationship_mapper):
        """Test the convenience function for generating config documentation."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            temp_file.write(b'{"app": {"name": "TestApp"}}')
            temp_path = temp_file.name
        
        try:
            # Use the convenience function
            with patch('file_analyzer.doc_generator.config_documentation_generator.ConfigDocumentationGenerator') as MockGenerator:
                # Setup the mock to return a simple result
                mock_instance = MockGenerator.return_value
                mock_instance.generate_config_documentation.return_value = {"variables": [{"name": "app.name"}]}
                
                # Call the convenience function
                result = generate_config_file_documentation(
                    config_file_path=temp_path,
                    relationship_mapper=mock_relationship_mapper,
                    ai_provider=mock_ai_provider
                )
                
                # Verify the generator was initialized correctly
                MockGenerator.assert_called_once_with(
                    ai_provider=mock_ai_provider,
                    relationship_mapper=mock_relationship_mapper
                )
                
                # Verify generate_config_documentation was called
                mock_instance.generate_config_documentation.assert_called_once_with(temp_path)
                
                # Check the result
                assert "variables" in result
        finally:
            # Clean up temp file
            os.unlink(temp_path)