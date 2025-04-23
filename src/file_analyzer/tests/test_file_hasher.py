"""
Unit tests for FileHasher.
"""
import hashlib
import tempfile
from pathlib import Path

from file_analyzer.core.file_hasher import FileHasher


class TestFileHasher:
    """Unit tests for the FileHasher class."""
    
    def test_get_file_hash_success(self):
        """Test that a file hash can be generated successfully."""
        # Arrange
        hasher = FileHasher()
        content = "Test content"
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(content)
            filepath = f.name
        
        # Calculate expected hash
        expected_hash = hashlib.md5(content.encode()).hexdigest()
        
        # Act
        actual_hash = hasher.get_file_hash(Path(filepath))
        
        # Assert
        assert actual_hash == expected_hash
        
        # Cleanup
        Path(filepath).unlink()
    
    def test_get_file_hash_nonexistent_file(self):
        """Test that hashing a nonexistent file returns a hash of the path."""
        # Arrange
        hasher = FileHasher()
        path = Path("/nonexistent/file.txt")
        
        # Calculate expected hash
        expected_hash = hashlib.md5(str(path).encode()).hexdigest()
        
        # Act
        actual_hash = hasher.get_file_hash(path)
        
        # Assert
        assert actual_hash == expected_hash
        
    def test_get_file_hash_different_content(self):
        """Test that different file contents yield different hashes."""
        # Arrange
        hasher = FileHasher()
        
        # Create two files with different content
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
            f1.write("Content 1")
            filepath1 = f1.name
            
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
            f2.write("Content 2")
            filepath2 = f2.name
        
        # Act
        hash1 = hasher.get_file_hash(filepath1)
        hash2 = hasher.get_file_hash(filepath2)
        
        # Assert
        assert hash1 != hash2
        
        # Cleanup
        Path(filepath1).unlink()
        Path(filepath2).unlink()
        
    def test_get_file_hash_same_content(self):
        """Test that identical file contents yield identical hashes."""
        # Arrange
        hasher = FileHasher()
        content = "Same content"
        
        # Create two files with same content
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
            f1.write(content)
            filepath1 = f1.name
            
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
            f2.write(content)
            filepath2 = f2.name
        
        # Act
        hash1 = hasher.get_file_hash(filepath1)
        hash2 = hasher.get_file_hash(filepath2)
        
        # Assert
        assert hash1 == hash2
        
        # Cleanup
        Path(filepath1).unlink()
        Path(filepath2).unlink()