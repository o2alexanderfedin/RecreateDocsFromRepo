"""
Integration tests for real API providers.

These tests use the actual API services and require API keys.
They are only run if the appropriate environment variables are set.
"""
import os
import pytest
import tempfile
from pathlib import Path

from file_analyzer.core.file_type_analyzer import FileTypeAnalyzer
from file_analyzer.ai_providers.mistral_provider import MistralProvider
from file_analyzer.core.cache_provider import InMemoryCache


@pytest.mark.skipif(not os.environ.get('MISTRAL_API_KEY'), 
                    reason="MISTRAL_API_KEY environment variable not set")
class TestMistralAPIIntegration:
    """Integration tests for Mistral API."""
    
    def test_analyze_python_file(self):
        """Test real API call with a Python file."""
        # Get the API key from environment variable
        api_key = os.environ.get('MISTRAL_API_KEY')
        
        # Arrange
        analyzer = FileTypeAnalyzer(
            ai_provider=MistralProvider(api_key=api_key),
            cache_provider=InMemoryCache()
        )
        
        # Create a Python test file
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
            f.write("""
            def hello_world():
                \"\"\"Say hello to the world.\"\"\"
                return "Hello, World!"
                
            class Greeter:
                def __init__(self, name):
                    self.name = name
                    
                def greet(self):
                    return f"Hello, {self.name}!"
            """)
            filepath = f.name
        
        try:
            # Act
            result = analyzer.analyze_file(filepath)
            
            # Assert
            assert result["file_type"].lower() in ["code", "source", "source code"]
            assert result["language"].lower() == "python"
            assert "confidence" in result
            # Important characteristics that should be detected
            characteristics = [c.lower() for c in result.get("characteristics", [])]
            assert any("class" in c for c in characteristics) or any("function" in c for c in characteristics)
            
            # Print the result for inspection 
            print("\nMistral API Result for Python file:")
            for key, value in result.items():
                print(f"{key}: {value}")
                
        finally:
            # Clean up
            Path(filepath).unlink(missing_ok=True)
    
    def test_analyze_json_file(self):
        """Test real API call with a JSON file."""
        # Get the API key from environment variable
        api_key = os.environ.get('MISTRAL_API_KEY')
        
        # Arrange
        analyzer = FileTypeAnalyzer(
            ai_provider=MistralProvider(api_key=api_key),
            cache_provider=InMemoryCache()
        )
        
        # Create a JSON test file
        with tempfile.NamedTemporaryFile(suffix='.json', mode='w', delete=False) as f:
            f.write("""
            {
                "name": "test-project",
                "version": "1.0.0",
                "description": "Test project for API integration",
                "dependencies": {
                    "pytest": "^7.0.0",
                    "mistralai": "^1.7.0"
                },
                "settings": {
                    "debug": true,
                    "api_url": "https://example.com/api"
                }
            }
            """)
            filepath = f.name
        
        try:
            # Act
            result = analyzer.analyze_file(filepath)
            
            # Assert
            assert result["language"].lower() == "json"
            assert "confidence" in result
            
            # Print the result for inspection
            print("\nMistral API Result for JSON file:")
            for key, value in result.items():
                print(f"{key}: {value}")
                
        finally:
            # Clean up
            Path(filepath).unlink(missing_ok=True)
            
    def test_analyze_markdown_file(self):
        """Test real API call with a Markdown file."""
        # Get the API key from environment variable
        api_key = os.environ.get('MISTRAL_API_KEY')
        
        # Arrange
        analyzer = FileTypeAnalyzer(
            ai_provider=MistralProvider(api_key=api_key),
            cache_provider=InMemoryCache()
        )
        
        # Create a Markdown test file
        with tempfile.NamedTemporaryFile(suffix='.md', mode='w', delete=False) as f:
            f.write("""
            # Project Documentation
            
            ## Overview
            
            This is a test documentation file for API integration testing.
            
            ## Features
            
            - Feature 1: Something cool
            - Feature 2: Something cooler
            
            ## Code Example
            
            ```python
            def example():
                return "This is an example"
            ```
            
            ## Links
            
            - [Link 1](https://example.com)
            - [Link 2](https://test.com)
            """)
            filepath = f.name
        
        try:
            # Act
            result = analyzer.analyze_file(filepath)
            
            # Assert
            assert result["language"].lower() in ["markdown", "md"]
            assert "file_type" in result
            assert "confidence" in result
            
            # Print the result for inspection
            print("\nMistral API Result for Markdown file:")
            for key, value in result.items():
                print(f"{key}: {value}")
                
        finally:
            # Clean up
            Path(filepath).unlink(missing_ok=True)
            
    def test_cli_with_real_api(self):
        """Test the CLI interface with real API."""
        import subprocess
        import json
        import sys
        
        # Skip if no API key
        if not os.environ.get('MISTRAL_API_KEY'):
            pytest.skip("MISTRAL_API_KEY environment variable not set")
            
        # Create a temporary directory with test files
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_path = Path(tempdir)
            
            # Create test files
            files = {
                "test.py": "def test(): pass",
                "config.json": '{"name": "test", "version": "1.0.0"}',
                "README.md": "# Test Project\n\nThis is a test project."
            }
            
            for filename, content in files.items():
                file_path = tempdir_path / filename
                file_path.write_text(content)
            
            # Generate output file path
            output_file = tempdir_path / "results.json"
            
            # Run the CLI with real Mistral API
            cmd = [
                sys.executable, 
                "-m", 
                "file_analyzer.main",
                str(tempdir_path / "test.py"),  # Analyze just one file to keep it quick
                "--provider", "mistral",
                "--api-key", os.environ.get('MISTRAL_API_KEY'),
                "--output", str(output_file)
            ]
            
            try:
                # Act
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                # Assert command executed successfully
                assert result.returncode == 0, f"CLI failed with: {result.stderr}"
                
                # Verify output file exists and contains valid results
                assert output_file.exists(), "Output file was not created"
                
                # Parse the JSON output
                with open(output_file) as f:
                    results = json.load(f)
                
                # Verify the analysis looks reasonable
                file_path = str(tempdir_path / "test.py")
                assert file_path in results
                assert "language" in results[file_path]
                assert results[file_path]["language"].lower() == "python"
                
                # Print the result for inspection
                print("\nCLI with Mistral API Result:")
                print(json.dumps(results, indent=2))
                
            except subprocess.SubprocessError as e:
                pytest.fail(f"CLI execution failed: {str(e)}")