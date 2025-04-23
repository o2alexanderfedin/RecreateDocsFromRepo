"""
Cache provider for storing analysis results.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class CacheProvider(ABC):
    """Abstract base class for different cache implementations."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            Cached value, or None if not found
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        pass


class InMemoryCache(CacheProvider):
    """Simple in-memory cache implementation."""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a value from the in-memory cache.
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            Cached value, or None if not found
        """
        return self.cache.get(key)
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """
        Set a value in the in-memory cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self.cache[key] = value