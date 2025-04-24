"""
Configuration file analyzer for analyzing configuration files.

This module provides the ConfigAnalyzer class, which extracts parameters,
structure, and purpose from various configuration file formats.
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

from file_analyzer.ai_providers.provider_interface import AIModelProvider
from file_analyzer.core.file_reader import FileReader
from file_analyzer.core.file_hasher import FileHasher
from file_analyzer.core.cache_provider import (
    CacheProvider, CacheFactory, CacheManager, InMemoryCache
)
from file_analyzer.utils.exceptions import FileAnalyzerError, FileReadError

logger = logging.getLogger("file_analyzer.config_analyzer")


class ConfigAnalyzer:
    """
    Analyzes configuration files to extract parameters, structure, and purpose.
    
    This class uses AI models to parse configuration files of various formats
    and extract structured information about their parameters and purpose.
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
        Initialize the config file analyzer.
        
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
        
        # Set up cache if not provided but config is
        if self.cache_provider is None and cache_config is not None:
            self.cache_provider = self._setup_cache(cache_config)
        
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
            # Set up single or tiered cache
            if cache_type == "tiered":
                # For tiered cache, set up multiple providers
                default_types = config.get("default_types", ["memory", "sqlite"])
                caches = []
                
                for cache_type in default_types:
                    cache = CacheFactory.create_cache(
                        cache_type,
                        max_size=config.get("max_size"),
                        ttl=config.get("ttl"),
                        db_path=config.get("db_path"),
                        cache_dir=config.get("cache_dir")
                    )
                    if cache:
                        caches.append(cache)
                
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
    
    def analyze_config_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Analyze a configuration file to extract parameters and structure.
        
        Args:
            file_path: Path to the configuration file to analyze
            
        Returns:
            Dictionary with configuration analysis results
        """
        # Ensure file_path is a Path object
        path = Path(file_path) if isinstance(file_path, str) else file_path
        
        # For result caching, use the file path and hash
        try:
            # Read file content
            file_content = self.file_reader.read_file(path)
            file_hash = self.file_hasher.get_file_hash(path)
        except FileReadError as e:
            logger.error(f"Error reading file {path}: {str(e)}")
            return {
                "format": "unknown",
                "error": f"Failed to read file: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error processing file {path}: {str(e)}")
            return {
                "format": "unknown",
                "error": f"Unexpected error: {str(e)}"
            }
        
        # Try to get cached result
        cache_key = f"config_analysis:{path}:{file_hash}"
        if self.cache_provider:
            cached_result = self.cache_provider.get(cache_key)
            if cached_result:
                logger.debug(f"Using cached result for {path}")
                self.cache_stats["hits"] = self.cache_stats.get("hits", 0) + 1
                return cached_result
            else:
                self.cache_stats["misses"] = self.cache_stats.get("misses", 0) + 1
        
        # No cached result, perform analysis
        try:
            # Get file extension as a hint for format
            format_hint = path.suffix.lstrip('.').lower() if path.suffix else None
            
            # Analyze with AI provider
            result = self.ai_provider.analyze_config(
                str(path),
                file_content,
                format_hint=format_hint
            )
            
            # Add file path to result
            result["file_path"] = str(path)
            
            # Normalize format values
            if result.get("format") == "yml":
                result["format"] = "yaml"
            
            # Cache the result
            if self.cache_provider:
                self.cache_provider.set(cache_key, result)
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing configuration file {path}: {str(e)}")
            return {
                "format": "unknown",
                "error": f"Analysis error: {str(e)}",
                "file_path": str(path)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the configuration analyzer.
        
        Returns:
            Dictionary with analyzer statistics
        """
        stats = {
            "cache_enabled": self.cache_provider is not None
        }
        
        if self.cache_provider:
            stats.update(self.cache_stats)
            stats.update(self.cache_provider.get_stats())
        
        return stats