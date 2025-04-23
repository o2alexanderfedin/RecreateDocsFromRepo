import os
from pathlib import Path
from loguru import logger
import re

class RepoAnalyzer:
    """Utility class for analyzing repository structure."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        logger.info(f"Initializing repository analyzer for {repo_path}")
    
    def get_file_list(self, extensions: list[str] = None) -> list[Path]:
        """Get list of files in the repository, optionally filtered by extension.
        
        Args:
            extensions: List of file extensions to include (e.g., [".py", ".js"])
            
        Returns:
            List of file paths
        """
        files = []
        for root, _, filenames in os.walk(self.repo_path):
            for filename in filenames:
                file_path = Path(root) / filename
                # Skip .git directory
                if '.git' in file_path.parts:
                    continue
                    
                if extensions and not any(file_path.name.endswith(ext) for ext in extensions):
                    continue
                    
                files.append(file_path)
        
        return files
    
    def find_files_by_pattern(self, pattern: str) -> list[Path]:
        """Find files whose content matches the given regex pattern.
        
        Args:
            pattern: Regular expression pattern to search for
            
        Returns:
            List of file paths containing the pattern
        """
        matching_files = []
        for file_path in self.get_file_list():
            try:
                if file_path.is_file() and file_path.stat().st_size < 1_000_000:  # Skip large files
                    content = file_path.read_text(errors='ignore')
                    if re.search(pattern, content):
                        matching_files.append(file_path)
            except Exception as e:
                logger.warning(f"Error reading {file_path}: {e}")
        
        return matching_files
