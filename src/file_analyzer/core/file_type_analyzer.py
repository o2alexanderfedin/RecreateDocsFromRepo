"""
Main file type analyzer implementation.
"""
from pathlib import Path
from typing import Dict, Any, Optional, Union

from file_analyzer.ai_providers.provider_interface import AIModelProvider
from file_analyzer.core.file_reader import FileReader
from file_analyzer.core.file_hasher import FileHasher
from file_analyzer.core.cache_provider import CacheProvider
from file_analyzer.utils.exceptions import FileAnalyzerError


class FileTypeAnalyzer:
    """
    Analyzes files to determine their type, language, and purpose.
    
    This class coordinates the file reading, AI analysis, and caching components
    to provide comprehensive file metadata.
    """
    
    def __init__(
        self, 
        ai_provider: AIModelProvider,
        file_reader: Optional[FileReader] = None,
        file_hasher: Optional[FileHasher] = None,
        cache_provider: Optional[CacheProvider] = None
    ):
        """
        Initialize the file type analyzer.
        
        Args:
            ai_provider: Provider for AI model access
            file_reader: Component for reading files (optional)
            file_hasher: Component for hashing files (optional)
            cache_provider: Provider for caching results (optional)
        """
        self.ai_provider = ai_provider
        self.file_reader = file_reader or FileReader()
        self.file_hasher = file_hasher or FileHasher()
        self.cache_provider = cache_provider
    
    def analyze_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Analyze a file to determine its metadata.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Dictionary with file analysis results
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path
        
        # Check cache if available
        if self.cache_provider:
            file_hash = self.file_hasher.get_file_hash(path)
            cached_result = self.cache_provider.get(file_hash)
            if cached_result:
                return cached_result
        
        try:
            # Read file content
            content = self.file_reader.read_file(path)
            
            # Analyze with AI provider
            result = self.ai_provider.analyze_content(str(path), content)
            
            # Cache result if caching is enabled
            if self.cache_provider and 'error' not in result:
                file_hash = self.file_hasher.get_file_hash(path)
                self.cache_provider.set(file_hash, result)
            
            return result
            
        except FileAnalyzerError as e:
            # Known errors from our components
            return {
                "error": str(e),
                "file_type": "unknown",
                "language": "unknown",
                "purpose": "unknown",
                "characteristics": [],
                "confidence": 0.0
            }
        except Exception as e:
            # Unexpected errors
            return {
                "error": f"Unexpected error: {str(e)}",
                "file_type": "unknown",
                "language": "unknown",
                "purpose": "unknown",
                "characteristics": [],
                "confidence": 0.0
            }