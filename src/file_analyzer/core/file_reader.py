"""
File reader component responsible for safely reading file content.
"""
from pathlib import Path
from typing import Union

from file_analyzer.utils.exceptions import FileReadError


class FileReader:
    """Responsible for reading file content safely."""
    
    def read_file(self, file_path: Union[str, Path], max_size: int = 4000) -> str:
        """
        Read file content with error handling and size limiting.
        
        Args:
            file_path: Path to the file to read
            max_size: Maximum number of characters to read
            
        Returns:
            File content as a string, truncated to max_size if necessary
            
        Raises:
            FileReadError: If the file cannot be read
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path
        
        try:
            content = path.read_text(errors='replace')
            return content[:max_size]  # Truncate to control costs
        except Exception as e:
            raise FileReadError(f"Failed to read file {path}: {str(e)}")