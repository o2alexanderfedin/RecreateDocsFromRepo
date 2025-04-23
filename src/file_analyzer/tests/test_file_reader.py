"""
Unit tests for FileReader.
"""
import pytest
from pathlib import Path
import tempfile

from file_analyzer.core.file_reader import FileReader
from file_analyzer.utils.exceptions import FileReadError


class TestFileReader:
    """Unit tests for the FileReader class."""
    
    def test_read_file_success(self):
        """Test that a file can be read successfully."""
        # Arrange
        reader = FileReader()
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test content")
            filepath = f.name
        
        # Act
        content = reader.read_file(Path(filepath))
        
        # Assert
        assert content == "Test content"
        
        # Cleanup
        Path(filepath).unlink()
    
    def test_read_file_truncates_large_files(self):
        """Test that large files are truncated to max_size."""
        # Arrange
        reader = FileReader()
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("A" * 10000)  # Write 10KB of content
            filepath = f.name
        
        # Act
        content = reader.read_file(Path(filepath), max_size=100)
        
        # Assert
        assert len(content) == 100
        assert content == "A" * 100
        
        # Cleanup
        Path(filepath).unlink()
    
    def test_read_file_handles_nonexistent_file(self):
        """Test that attempting to read a nonexistent file raises FileReadError."""
        # Arrange
        reader = FileReader()
        filepath = Path("/nonexistent/file.txt")
        
        # Act & Assert
        with pytest.raises(FileReadError):
            reader.read_file(filepath)
            
    def test_read_file_supports_string_path(self):
        """Test that the file reader accepts string paths."""
        # Arrange
        reader = FileReader()
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("String path test")
            filepath = f.name
        
        # Act
        content = reader.read_file(filepath)  # Pass string instead of Path
        
        # Assert
        assert content == "String path test"
        
        # Cleanup
        Path(filepath).unlink()