"""
Unit tests for FileTypeAnalyzer.
"""
from unittest.mock import MagicMock, patch
import tempfile
from pathlib import Path

from file_analyzer.core.file_type_analyzer import FileTypeAnalyzer
from file_analyzer.core.file_reader import FileReader
from file_analyzer.core.file_hasher import FileHasher
from file_analyzer.core.cache_provider import InMemoryCache
from file_analyzer.ai_providers.mock_provider import MockAIProvider
from file_analyzer.utils.exceptions import FileReadError


class TestFileTypeAnalyzer:
    """Unit tests for the FileTypeAnalyzer class."""
    
    def test_analyze_file_success(self):
        """Test successful file analysis."""
        # Arrange
        mock_provider = MockAIProvider()
        analyzer = FileTypeAnalyzer(ai_provider=mock_provider)
        
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
            f.write("def test(): pass")
            filepath = f.name
        
        # Act
        result = analyzer.analyze_file(filepath)
        
        # Assert
        assert result["file_type"] == "code"
        assert result["language"] == "python"
        
        # Cleanup
        Path(filepath).unlink()
        
    def test_analyze_file_with_cache(self):
        """Test that results are cached and reused."""
        # Arrange
        mock_provider = MockAIProvider()
        analyze_spy = MagicMock(wraps=mock_provider.analyze_content)
        mock_provider.analyze_content = analyze_spy
        
        cache = InMemoryCache()
        analyzer = FileTypeAnalyzer(
            ai_provider=mock_provider,
            cache_provider=cache
        )
        
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
            f.write("def test(): pass")
            filepath = f.name
        
        # Act - First call
        result1 = analyzer.analyze_file(filepath)
        
        # Should have called the AI provider
        assert analyze_spy.call_count == 1
        
        # Act - Second call
        result2 = analyzer.analyze_file(filepath)
        
        # Assert - Should have used the cache
        assert analyze_spy.call_count == 1  # Still just one call
        assert result1 == result2
        
        # Cleanup
        Path(filepath).unlink()
        
    def test_analyze_file_read_error(self):
        """Test handling of file read errors."""
        # Arrange
        mock_provider = MockAIProvider()
        
        # Mock reader that raises an error
        mock_reader = MagicMock(spec=FileReader)
        mock_reader.read_file.side_effect = FileReadError("Failed to read file")
        
        analyzer = FileTypeAnalyzer(
            ai_provider=mock_provider,
            file_reader=mock_reader
        )
        
        # Act
        result = analyzer.analyze_file("/path/to/nonexistent/file.txt")
        
        # Assert
        assert "error" in result
        assert result["file_type"] == "unknown"
        
    def test_analyze_file_general_exception(self):
        """Test handling of unexpected exceptions."""
        # Arrange
        mock_provider = MagicMock()
        mock_provider.analyze_content.side_effect = Exception("Unexpected error")
        
        analyzer = FileTypeAnalyzer(ai_provider=mock_provider)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            filepath = f.name
        
        # Act
        result = analyzer.analyze_file(filepath)
        
        # Assert
        assert "error" in result
        assert "Unexpected error" in result["error"]
        assert result["file_type"] == "unknown"
        
        # Cleanup
        Path(filepath).unlink()
        
    def test_file_path_types(self):
        """Test that both string and Path objects are accepted for file_path."""
        # Arrange
        mock_provider = MockAIProvider()
        analyzer = FileTypeAnalyzer(ai_provider=mock_provider)
        
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
            f.write("def test(): pass")
            filepath = f.name
        
        # Act - Test with string path
        result1 = analyzer.analyze_file(filepath)
        
        # Act - Test with Path object
        result2 = analyzer.analyze_file(Path(filepath))
        
        # Assert
        assert result1["file_type"] == "code"
        assert result1["language"] == "python"
        assert result2["file_type"] == "code"
        assert result2["language"] == "python"
        
        # Cleanup
        Path(filepath).unlink()