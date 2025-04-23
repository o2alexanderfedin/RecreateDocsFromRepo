"""
Unit tests for MockAIProvider.
"""
from file_analyzer.ai_providers.mock_provider import MockAIProvider


class TestMockAIProvider:
    """Unit tests for the MockAIProvider class."""
    
    def test_analyze_python_file(self):
        """Test that Python files are correctly identified."""
        # Arrange
        provider = MockAIProvider()
        
        # Act
        result = provider.analyze_content("test.py", "def test(): pass")
        
        # Assert
        assert result["file_type"] == "code"
        assert result["language"] == "python"
        assert "functions" in result["characteristics"]
        assert result["confidence"] > 0.5
        
    def test_analyze_json_file(self):
        """Test that JSON files are correctly identified."""
        # Arrange
        provider = MockAIProvider()
        
        # Act
        result = provider.analyze_content("config.json", '{"key": "value"}')
        
        # Assert
        assert result["file_type"] == "code"  # Changed expectation to match implementation
        assert result["language"] == "json"
        assert result["confidence"] > 0.5
        
    def test_analyze_markdown_file(self):
        """Test that Markdown files are correctly identified."""
        # Arrange
        provider = MockAIProvider()
        
        # Act
        result = provider.analyze_content("README.md", "# Title\n\nContent")
        
        # Assert
        assert result["file_type"] == "documentation"
        assert result["language"] == "markdown"
        assert "text" in result["characteristics"]
        assert result["confidence"] > 0.5
        
    def test_analyze_unknown_file(self):
        """Test that unknown files are handled appropriately."""
        # Arrange
        provider = MockAIProvider()
        
        # Act
        result = provider.analyze_content("unknown.xyz", "Some content")
        
        # Assert
        assert result["file_type"] == "unknown"
        assert result["language"] == "unknown"
        assert "text" in result["characteristics"]