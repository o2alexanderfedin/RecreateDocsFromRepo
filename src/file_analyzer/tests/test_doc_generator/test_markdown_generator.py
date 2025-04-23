"""
Unit tests for the Markdown documentation generator.
"""
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from file_analyzer.doc_generator.markdown_generator import (
    MarkdownGenerator, DocumentationConfig, generate_documentation
)


class TestDocumentationConfig:
    """Tests for DocumentationConfig class."""
    
    def test_documentation_config_defaults(self):
        """Test default configuration values."""
        config = DocumentationConfig(output_dir="/tmp/docs")
        
        assert config.output_dir == "/tmp/docs"
        assert config.template_dir is None
        assert config.include_code_snippets is True
        assert config.max_code_snippet_lines == 15
        assert config.include_relationships is True
        assert config.include_framework_details is True
        assert config.exclude_patterns == []
    
    def test_documentation_config_custom(self):
        """Test custom configuration values."""
        config = DocumentationConfig(
            output_dir="/tmp/docs",
            template_dir="/tmp/templates",
            include_code_snippets=False,
            max_code_snippet_lines=10,
            include_relationships=False,
            include_framework_details=False,
            exclude_patterns=["node_modules", ".git"]
        )
        
        assert config.output_dir == "/tmp/docs"
        assert config.template_dir == "/tmp/templates"
        assert config.include_code_snippets is False
        assert config.max_code_snippet_lines == 10
        assert config.include_relationships is False
        assert config.include_framework_details is False
        assert config.exclude_patterns == ["node_modules", ".git"]


class TestMarkdownGenerator:
    """Tests for MarkdownGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create a MarkdownGenerator with a temporary output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = DocumentationConfig(output_dir=temp_dir)
            yield MarkdownGenerator(config), temp_dir
    
    def test_initialization(self, generator):
        """Test that the generator initializes correctly."""
        markdown_generator, output_dir = generator
        
        assert markdown_generator.config.output_dir == output_dir
        assert markdown_generator.jinja_env is not None
        assert os.path.exists(output_dir)
    
    def test_relative_path_extraction(self, generator):
        """Test extracting relative paths."""
        markdown_generator, _ = generator
        
        # Test with repo root path prefix
        repo_path = "/path/to/repo"
        file_path = "/path/to/repo/src/file.py"
        rel_path = markdown_generator._get_relative_path(file_path, repo_path)
        assert rel_path == "src/file.py"
        
        # Test with file not under repo
        file_path = "/other/path/file.py"
        rel_path = markdown_generator._get_relative_path(file_path, repo_path)
        assert rel_path == file_path
    
    def test_exclusion(self, generator):
        """Test file exclusion logic."""
        markdown_generator, _ = generator
        
        # Add some exclude patterns
        markdown_generator.config.exclude_patterns = [
            "node_modules", ".git", "test_"
        ]
        
        # Test excluded files
        assert markdown_generator._should_exclude("/path/to/node_modules/file.js") is True
        assert markdown_generator._should_exclude("/path/to/.git/config") is True
        assert markdown_generator._should_exclude("/path/to/test_file.py") is True
        
        # Test included files
        assert markdown_generator._should_exclude("/path/to/src/file.py") is False
        assert markdown_generator._should_exclude("/path/to/app.js") is False
    
    def test_get_template_for_file(self, generator):
        """Test template selection based on file type and language."""
        markdown_generator, _ = generator
        
        # Test language-specific template
        assert markdown_generator._get_template_for_file("python", "code") == "python_file.md.j2"
        
        # Test web-related files
        assert markdown_generator._get_template_for_file("javascript", "code") == "web_file.md.j2"
        assert markdown_generator._get_template_for_file("html", "markup") == "web_file.md.j2"
        assert markdown_generator._get_template_for_file("css", "stylesheet") == "web_file.md.j2"
        
        # Test config files
        assert markdown_generator._get_template_for_file("json", "config") == "config_file.md.j2"
        assert markdown_generator._get_template_for_file("yaml", "data") == "config_file.md.j2"
        
        # Test markup files
        assert markdown_generator._get_template_for_file("markdown", "documentation") == "markup_file.md.j2"
        
        # Test fallback to generic template
        assert markdown_generator._get_template_for_file("unknown", "unknown") == "generic_file.md.j2"
    
    def test_get_language_import_patterns(self, generator):
        """Test generation of language-specific import patterns."""
        markdown_generator, _ = generator
        
        # Test Python import patterns
        python_patterns = markdown_generator._get_language_import_patterns(
            "/path/to/repo/module/test.py", "test"
        )
        assert "test" in python_patterns
        assert "from test" in python_patterns
        
        # Test JavaScript import patterns
        js_patterns = markdown_generator._get_language_import_patterns(
            "/path/to/repo/js/test.js", "test"
        )
        assert "test" in js_patterns
        assert "import test" in js_patterns
        assert "require('test" in js_patterns
        
        # Test C/C++ import patterns
        c_patterns = markdown_generator._get_language_import_patterns(
            "/path/to/repo/src/test.h", "test"
        )
        assert "test" in c_patterns
        assert '#include "test' in c_patterns
    
    @patch('builtins.open', new_callable=MagicMock)
    @patch('os.makedirs', new_callable=MagicMock)
    def test_generate_indexes(self, mock_makedirs, mock_open, generator):
        """Test generating index files."""
        markdown_generator, output_dir = generator
        
        # Mock template environment
        mock_template = MagicMock()
        mock_template.render.return_value = "# Test Index"
        markdown_generator.jinja_env.get_template = MagicMock(return_value=mock_template)
        
        # Test data
        repo_path = "/path/to/repo"
        file_results = {
            "/path/to/repo/src/module1/file1.py": {"file_type": "code", "language": "python"},
            "/path/to/repo/src/module1/file2.py": {"file_type": "code", "language": "python"},
            "/path/to/repo/src/module2/file3.py": {"file_type": "code", "language": "python"},
            "/path/to/repo/config.yaml": {"file_type": "config", "language": "yaml"}
        }
        frameworks = []
        
        # Call the method
        index_paths = markdown_generator._generate_indexes(repo_path, file_results, frameworks)
        
        # Check the results
        assert len(index_paths) >= 1  # At least the main index
        
        # Main index file should be created
        assert os.path.join(output_dir, "index.md") in index_paths
        
        # Directory indexes for src, src/module1, src/module2 should be created
        assert os.path.join(output_dir, "src", "index.md") in index_paths
        assert os.path.join(output_dir, "src/module1", "index.md") in index_paths
        assert os.path.join(output_dir, "src/module2", "index.md") in index_paths
        
        # Template should be called for each index
        assert mock_template.render.call_count >= 4  # Main + 3 directories
        
        # Directories should be created
        assert mock_makedirs.called
        
        # Index files should be written
        assert mock_open.call_count >= 4  # Main + 3 directories
    
    @patch('builtins.open', new_callable=MagicMock)
    def test_generate_file_documentation(self, mock_open, generator):
        """Test generating documentation for a single file."""
        markdown_generator, output_dir = generator
        
        # Mock methods
        markdown_generator._get_code_snippet = MagicMock(return_value="# Code snippet")
        markdown_generator._get_file_relationships = MagicMock(return_value={
            "imports": [],
            "imported_by": [],
            "related": []
        })
        
        # Mock template environment
        mock_template = MagicMock()
        mock_template.render.return_value = "# Test Documentation"
        markdown_generator.jinja_env.get_template = MagicMock(return_value=mock_template)
        markdown_generator._get_template_for_file = MagicMock(return_value="python_file.md.j2")
        
        # Test data
        file_path = "/path/to/repo/src/test.py"
        repo_path = "/path/to/repo"
        file_result = {
            "file_type": "code",
            "language": "python",
            "frameworks": [{"name": "django", "confidence": 0.9}],
            "code_structure": {
                "structure": {
                    "classes": [{"name": "TestClass", "methods": ["test_method"]}],
                    "functions": [{"name": "test_function", "parameters": ["param"]}],
                    "imports": ["import os", "import sys"],
                    "variables": [{"name": "TEST_VAR", "scope": "module"}]
                }
            }
        }
        frameworks = [
            {
                "name": "django",
                "language": "python",
                "version": "3.2.4",
                "confidence": 0.9,
                "count": 1,
                "usage": [
                    {
                        "file_path": file_path,
                        "features": ["models.Model"]
                    }
                ]
            }
        ]
        
        # Call the method
        doc_path = markdown_generator._generate_file_documentation(
            file_path, file_result, repo_path, frameworks
        )
        
        # Check the result
        expected_doc_path = os.path.join(output_dir, "src/test.py.md")
        assert doc_path == expected_doc_path
        
        # Check that the template was rendered with the expected context
        context = mock_template.render.call_args[1]
        assert context["file_path"] == file_path
        assert context["rel_path"] == "src/test.py"
        assert context["language"] == "python"
        assert len(context["frameworks"]) == 1
        assert context["frameworks"][0]["name"] == "django"
        
        # Check that the template selection was called with the right parameters
        markdown_generator._get_template_for_file.assert_called_once_with("python", "code")
        
        # Check that the file was written
        mock_open.assert_called_once()
        mock_open().__enter__().write.assert_called_once_with("# Test Documentation")


class TestGenerateDocumentation:
    """Tests for generate_documentation function."""
    
    def test_generate_documentation(self):
        """Test the generate_documentation convenience function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Simple test data
            repo_analysis = {
                "repo_path": "/test/repo",
                "file_results": {
                    "/test/repo/test.py": {
                        "file_type": "code",
                        "language": "python"
                    }
                },
                "frameworks": []
            }
            
            # Mock the MarkdownGenerator
            with patch('file_analyzer.doc_generator.markdown_generator.MarkdownGenerator') as MockGenerator:
                mock_instance = MockGenerator.return_value
                mock_instance.generate_documentation.return_value = {
                    "total_files": 1,
                    "documentation_files_generated": 1,
                    "skipped_files": 0,
                    "index_files": 1
                }
                
                # Call the function
                result = generate_documentation(
                    repo_analysis=repo_analysis,
                    output_dir=temp_dir
                )
                
                # Check that the generator was created with the right config
                MockGenerator.assert_called_once()
                config = MockGenerator.call_args[0][0]
                assert isinstance(config, DocumentationConfig)
                assert config.output_dir == temp_dir
                
                # Check that generate_documentation was called
                mock_instance.generate_documentation.assert_called_once_with(repo_analysis)
                
                # Check the result
                assert result["total_files"] == 1
                assert result["documentation_files_generated"] == 1