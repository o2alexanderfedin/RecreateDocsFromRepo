"""
File hasher component for generating file content hashes.
"""
import hashlib
from pathlib import Path
from typing import Union


class FileHasher:
    """Responsible for generating file hashes for caching."""
    
    def get_file_hash(self, file_path: Union[str, Path]) -> str:
        """
        Generate a hash for the file content.
        
        Args:
            file_path: Path to the file to hash
            
        Returns:
            MD5 hash of the file content, or of the file path if content can't be read
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path
        
        try:
            content = path.read_bytes()
            return hashlib.md5(content).hexdigest()
        except Exception:
            # Fallback to path-based hash if file can't be read
            return hashlib.md5(str(path).encode()).hexdigest()
    
    def get_string_hash(self, content: str) -> str:
        """
        Generate a hash for a string.
        
        Args:
            content: String content to hash
            
        Returns:
            MD5 hash of the string content
        """
        return hashlib.md5(content.encode()).hexdigest()