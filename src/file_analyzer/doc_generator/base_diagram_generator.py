"""
Base Diagram Generator abstract class.

This module provides the BaseDiagramGenerator abstract class that serves as the
foundation for all UML diagram generators (logical, process, development views).
"""
import abc
import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple, Union

from file_analyzer.ai_providers.provider_interface import AIModelProvider
from file_analyzer.core.file_reader import FileReader
from file_analyzer.core.file_hasher import FileHasher
from file_analyzer.core.cache_provider import CacheProvider
from file_analyzer.core.code_analyzer import CodeAnalyzer
from file_analyzer.utils.exceptions import FileAnalyzerError

logger = logging.getLogger("file_analyzer.base_diagram_generator")


class BaseDiagramGenerator(abc.ABC):
    """
    Abstract base class for UML diagram generators.
    
    This class defines the common structure and functionality for all diagram
    generators, including caching, stats tracking, and common helper methods.
    """
    
    def __init__(
        self,
        ai_provider: AIModelProvider,
        code_analyzer: Optional[CodeAnalyzer] = None,
        file_reader: Optional[FileReader] = None,
        file_hasher: Optional[FileHasher] = None,
        cache_provider: Optional[CacheProvider] = None,
    ):
        """
        Initialize the base diagram generator.
        
        Args:
            ai_provider: Provider for AI model access
            code_analyzer: CodeAnalyzer for analyzing code files (optional)
            file_reader: Component for reading files (optional)
            file_hasher: Component for hashing files (optional)
            cache_provider: Provider for caching results (optional)
        """
        self.ai_provider = ai_provider
        self.file_reader = file_reader or FileReader()
        self.file_hasher = file_hasher or FileHasher()
        self.cache_provider = cache_provider
        
        # Import at runtime to avoid circular imports
        if code_analyzer is None:
            from file_analyzer.core.code_analyzer import CodeAnalyzer as CA
            self.code_analyzer = CA(
                ai_provider=ai_provider,
                file_reader=self.file_reader,
                file_hasher=self.file_hasher,
                cache_provider=cache_provider
            )
        else:
            self.code_analyzer = code_analyzer
        
        # Initialize base statistics
        self.stats = {
            "diagrams_generated": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    @abc.abstractmethod
    def generate_diagram(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Abstract method for generating a diagram.
        
        Each subclass must implement this method to generate its specific diagram type.
        
        Returns:
            Dictionary containing diagram data with Mermaid or PlantUML syntax
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the diagram generation.
        
        Returns:
            Dictionary with generator statistics
        """
        return self.stats.copy()
    
    def _hash_paths(self, paths: List[Path]) -> str:
        """
        Calculate a hash for a list of file paths.
        
        Args:
            paths: List of file paths to hash
            
        Returns:
            A unique hash string for the combined paths
        """
        paths_str = "|".join(sorted([str(p) for p in paths]))
        return self.file_hasher.get_string_hash(paths_str)
    
    def _check_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Check if a diagram is already in the cache.
        
        Args:
            cache_key: The key to look up in the cache
            
        Returns:
            The cached diagram data or None if not found
        """
        if not self.cache_provider:
            return None
        
        cached_result = self.cache_provider.get(cache_key)
        if cached_result:
            logger.debug(f"Using cached diagram for {cache_key}")
            self.stats["cache_hits"] += 1
            return cached_result
        
        self.stats["cache_misses"] += 1
        return None
    
    def _save_to_cache(self, cache_key: str, result: Dict[str, Any]) -> None:
        """
        Save a diagram to the cache.
        
        Args:
            cache_key: The key to store the diagram under
            result: The diagram data to cache
        """
        if self.cache_provider:
            self.cache_provider.set(cache_key, result)
    
    def _find_code_files(self, repo_path: Path) -> List[Path]:
        """
        Find all code files in a repository.
        
        Args:
            repo_path: Path to the repository root
            
        Returns:
            List of file paths
        """
        code_extensions = [".py", ".java", ".js", ".jsx", ".ts", ".tsx", ".cs", ".cpp", ".c", ".go", ".rb"]
        
        exclude_dirs = {".git", "node_modules", "__pycache__", "venv", "env", ".venv", "build", "dist"}
        
        code_files = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in code_extensions):
                    code_files.append(Path(root) / file)
        
        return code_files