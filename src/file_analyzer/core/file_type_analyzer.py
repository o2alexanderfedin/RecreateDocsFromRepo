"""
Main file type analyzer implementation.

This module provides the core implementation of the file type analyzer,
which coordinates file reading, AI analysis, and caching to determine
file metadata.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

from file_analyzer.ai_providers.provider_interface import AIModelProvider
from file_analyzer.core.file_reader import FileReader
from file_analyzer.core.file_hasher import FileHasher
from file_analyzer.core.cache_provider import (
    CacheProvider, CacheFactory, CacheManager, InMemoryCache
)
from file_analyzer.core.cache_config import get_cache_settings
from file_analyzer.utils.exceptions import FileAnalyzerError

logger = logging.getLogger("file_analyzer.analyzer")


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
        cache_provider: Optional[CacheProvider] = None,
        cache_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the file type analyzer.
        
        Args:
            ai_provider: Provider for AI model access
            file_reader: Component for reading files (optional)
            file_hasher: Component for hashing files (optional)
            cache_provider: Provider for caching results (optional)
            cache_config: Configuration for cache when no provider is specified
        """
        self.ai_provider = ai_provider
        self.file_reader = file_reader or FileReader()
        self.file_hasher = file_hasher or FileHasher()
        
        # If cache_provider is specified, use it; otherwise, set up the cache
        # based on the configuration if caching is enabled
        self.cache_provider = cache_provider
        
        # Set up cache if not provided
        if self.cache_provider is None and cache_config is not None:
            self.cache_provider = self._setup_cache(cache_config)
            if self.cache_provider:
                self._pre_warm_cache(self.cache_provider, cache_config.get('warmup_data', {}))
        
        self.cache_stats = {"enabled": self.cache_provider is not None}
    
    @staticmethod
    def _setup_cache(config: Dict[str, Any]) -> Optional[CacheProvider]:
        """
        Set up a cache provider based on the configuration.
        
        Args:
            config: Cache configuration dictionary
            
        Returns:
            Cache provider instance
        """
        cache_type = config.get("cache_type", "memory")
        
        try:
            # For tiered cache, set up multiple providers
            if cache_type == "tiered":
                default_types = config.get("default_types", ["memory", "sqlite"])
                caches = []
                
                for cache_type in default_types:
                    if cache_type == "memory":
                        caches.append(CacheFactory.create_cache(
                            "memory",
                            max_size=config.get("max_size"),
                            ttl=config.get("ttl")
                        ))
                    elif cache_type == "sqlite":
                        caches.append(CacheFactory.create_cache(
                            "sqlite",
                            db_path=config.get("db_path"),
                            ttl=config.get("ttl")
                        ))
                    elif cache_type == "filesystem":
                        caches.append(CacheFactory.create_cache(
                            "filesystem",
                            cache_dir=config.get("cache_dir"),
                            ttl=config.get("ttl")
                        ))
                
                if caches:
                    return CacheManager(caches)
                return None
                
            # For single cache type
            return CacheFactory.create_cache(
                cache_type,
                max_size=config.get("max_size"),
                ttl=config.get("ttl"),
                db_path=config.get("db_path"),
                cache_dir=config.get("cache_dir")
            )
        except Exception as e:
            logger.warning(f"Failed to initialize cache: {str(e)}")
            # Fallback to in-memory cache if something goes wrong
            return InMemoryCache()
    
    @staticmethod
    def _pre_warm_cache(cache: CacheProvider, warmup_data: Dict[str, Dict[str, Any]]) -> None:
        """
        Pre-warm the cache with common file types.
        
        Args:
            cache: Cache provider instance
            warmup_data: Dictionary mapping keys to cache values
        """
        if not warmup_data:
            return
            
        try:
            cache.pre_warm(warmup_data)
            logger.info(f"Pre-warmed cache with {len(warmup_data)} entries")
        except Exception as e:
            logger.warning(f"Failed to pre-warm cache: {str(e)}")
    
    def analyze_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Analyze a file to determine its metadata.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Dictionary with file analysis results
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path
        cache_hit = False
        
        # Check cache if available
        if self.cache_provider:
            file_hash = self.file_hasher.get_file_hash(path)
            cached_result = self.cache_provider.get(file_hash)
            if cached_result:
                logger.debug(f"Cache hit for {path}")
                if self.cache_stats:
                    self.cache_stats["hit"] = self.cache_stats.get("hit", 0) + 1
                cache_hit = True
                return cached_result
            else:
                if self.cache_stats:
                    self.cache_stats["miss"] = self.cache_stats.get("miss", 0) + 1
        
        try:
            # Read file content
            content = self.file_reader.read_file(path)
            
            # Analyze with AI provider
            result = self.ai_provider.analyze_content(str(path), content)
            
            # Cache result if caching is enabled and analysis succeeded
            if self.cache_provider and 'error' not in result:
                file_hash = self.file_hasher.get_file_hash(path)
                self.cache_provider.set(file_hash, result)
                if self.cache_stats:
                    self.cache_stats["store"] = self.cache_stats.get("store", 0) + 1
                logger.debug(f"Stored in cache: {path}")
            
            return result
            
        except FileAnalyzerError as e:
            # Known errors from our components
            logger.warning(f"Error analyzing file {path}: {str(e)}")
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
            logger.error(f"Unexpected error analyzing file {path}: {str(e)}", exc_info=True)
            return {
                "error": f"Unexpected error: {str(e)}",
                "file_type": "unknown",
                "language": "unknown",
                "purpose": "unknown",
                "characteristics": [],
                "confidence": 0.0
            }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics or None if caching is disabled
        """
        if not self.cache_provider:
            return {"enabled": False}
        
        # Get stats from the cache provider
        provider_stats = {}
        try:
            if hasattr(self.cache_provider, "get_stats"):
                provider_stats = self.cache_provider.get_stats()
            elif isinstance(self.cache_provider, CacheManager):
                provider_stats = self.cache_provider.get_stats()
        except Exception as e:
            logger.warning(f"Error getting cache stats: {str(e)}")
        
        # Combine with our own tracker stats
        stats = {"enabled": True}
        stats.update(self.cache_stats)
        
        # Add provider stats under their own key
        if provider_stats:
            stats["provider"] = provider_stats
        
        return stats