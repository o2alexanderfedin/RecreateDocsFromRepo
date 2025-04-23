"""
Cache provider for storing analysis results.

This module provides different cache implementations for storing and retrieving
file analysis results. It supports various storage backends, cache expiration,
statistics tracking, and other cache management features.
"""
import time
import json
import logging
import os
import sqlite3
from abc import ABC, abstractmethod
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union

logger = logging.getLogger("file_analyzer.cache")


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
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary of cache statistics
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all items from the cache."""
        pass
    
    @abstractmethod
    def invalidate(self, keys: List[str]) -> int:
        """
        Invalidate specific keys from the cache.
        
        Args:
            keys: List of keys to invalidate
            
        Returns:
            Number of keys invalidated
        """
        pass
    
    @abstractmethod
    def pre_warm(self, items: Dict[str, Dict[str, Any]]) -> None:
        """
        Pre-warm the cache with known values.
        
        Args:
            items: Dictionary mapping keys to values
        """
        pass


class InMemoryCache(CacheProvider):
    """
    Simple in-memory cache implementation.
    
    This is a basic cache that stores all items in memory. It supports
    optional expiration times and tracks basic cache statistics.
    """
    
    def __init__(self, max_size: Optional[int] = None, ttl: Optional[int] = None):
        """
        Initialize in-memory cache.
        
        Args:
            max_size: Maximum number of items to store (None for unlimited)
            ttl: Time-to-live in seconds (None for no expiration)
        """
        self.max_size = max_size
        self.ttl = ttl
        # Use OrderedDict to support LRU eviction when max_size is set
        self.cache: OrderedDict[str, Tuple[Dict[str, Any], float]] = OrderedDict()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0,
            "expirations": 0
        }
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a value from the in-memory cache.
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            Cached value, or None if not found
        """
        if key not in self.cache:
            self.stats["misses"] += 1
            return None
        
        # Check for expiration
        value, timestamp = self.cache[key]
        if self.ttl is not None and time.time() - timestamp > self.ttl:
            # Item has expired
            del self.cache[key]
            self.stats["expirations"] += 1
            self.stats["misses"] += 1
            return None
        
        # Move to end of OrderedDict to mark as recently used
        if self.max_size is not None:
            self.cache.move_to_end(key)
        
        self.stats["hits"] += 1
        return value
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """
        Set a value in the in-memory cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        # Evict least recently used item if max size reached
        if self.max_size is not None and len(self.cache) >= self.max_size and key not in self.cache:
            # Remove the first item (least recently used)
            self.cache.popitem(last=False)
            self.stats["evictions"] += 1
        
        # Store value with timestamp
        self.cache[key] = (value, time.time())
        
        if self.max_size is not None:
            # Move to end to mark as recently used
            self.cache.move_to_end(key)
        
        self.stats["sets"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary of cache statistics
        """
        stats = self.stats.copy()
        stats["size"] = len(self.cache)
        stats["max_size"] = self.max_size
        stats["ttl"] = self.ttl
        
        # Calculate hit rate (0 if no requests)
        total_requests = stats["hits"] + stats["misses"]
        stats["hit_rate"] = stats["hits"] / total_requests if total_requests > 0 else 0
        
        return stats
    
    def clear(self) -> None:
        """Clear all items from the cache."""
        self.cache.clear()
    
    def invalidate(self, keys: List[str]) -> int:
        """
        Invalidate specific keys from the cache.
        
        Args:
            keys: List of keys to invalidate
            
        Returns:
            Number of keys invalidated
        """
        invalidated = 0
        for key in keys:
            if key in self.cache:
                del self.cache[key]
                invalidated += 1
        return invalidated
    
    def pre_warm(self, items: Dict[str, Dict[str, Any]]) -> None:
        """
        Pre-warm the cache with known values.
        
        Args:
            items: Dictionary mapping keys to values
        """
        for key, value in items.items():
            self.set(key, value)


class SqliteCache(CacheProvider):
    """
    SQLite-based persistent cache implementation.
    
    This cache stores items in a SQLite database, allowing for persistence
    across application restarts. It supports expiration times and maintains
    cache statistics.
    """
    
    # SQL statements
    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS cache (
        key TEXT PRIMARY KEY,
        value TEXT,
        timestamp REAL
    )
    """
    
    CREATE_STATS_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS cache_stats (
        name TEXT PRIMARY KEY,
        value INTEGER
    )
    """
    
    def __init__(self, db_path: Union[str, Path], ttl: Optional[int] = None):
        """
        Initialize SQLite cache.
        
        Args:
            db_path: Path to SQLite database file
            ttl: Time-to-live in seconds (None for no expiration)
        """
        self.db_path = Path(db_path).resolve()
        self.ttl = ttl
        
        # Create directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_db()
        
        # Initialize stats
        self.stats = {
            "hits": self._get_stat("hits"),
            "misses": self._get_stat("misses"),
            "sets": self._get_stat("sets"),
            "evictions": self._get_stat("evictions"),
            "expirations": self._get_stat("expirations")
        }
    
    def _init_db(self) -> None:
        """Initialize the SQLite database."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            cursor.execute(self.CREATE_TABLE_SQL)
            cursor.execute(self.CREATE_STATS_TABLE_SQL)
            
            # Initialize stats if not exist
            for stat in ["hits", "misses", "sets", "evictions", "expirations"]:
                cursor.execute(
                    "INSERT OR IGNORE INTO cache_stats (name, value) VALUES (?, 0)",
                    (stat,)
                )
            
            conn.commit()
        finally:
            conn.close()
    
    def _increment_stat(self, name: str, value: int = 1) -> None:
        """
        Increment a statistics counter.
        
        Args:
            name: Name of the statistic
            value: Amount to increment by
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE cache_stats SET value = value + ? WHERE name = ?",
                (value, name)
            )
            conn.commit()
            self.stats[name] += value
        finally:
            conn.close()
    
    def _get_stat(self, name: str) -> int:
        """
        Get a statistics counter value.
        
        Args:
            name: Name of the statistic
            
        Returns:
            Current value of the statistic
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM cache_stats WHERE name = ?",
                (name,)
            )
            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            conn.close()
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a value from the SQLite cache.
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            Cached value, or None if not found
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT value, timestamp FROM cache WHERE key = ?",
                (key,)
            )
            
            result = cursor.fetchone()
            if not result:
                self._increment_stat("misses")
                return None
            
            value_str, timestamp = result
            
            # Check for expiration
            if self.ttl is not None and time.time() - timestamp > self.ttl:
                # Item has expired
                cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
                self._increment_stat("expirations")
                self._increment_stat("misses")
                return None
            
            # Update access time (optional, can improve LRU behavior)
            # cursor.execute(
            #     "UPDATE cache SET timestamp = ? WHERE key = ?",
            #     (time.time(), key)
            # )
            # conn.commit()
            
            self._increment_stat("hits")
            return json.loads(value_str)
        
        except (sqlite3.Error, json.JSONDecodeError) as e:
            logger.error(f"Error retrieving from SQLite cache: {str(e)}")
            self._increment_stat("misses")
            return None
        
        finally:
            conn.close()
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """
        Set a value in the SQLite cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            
            # Serialize value to JSON
            value_str = json.dumps(value)
            timestamp = time.time()
            
            cursor.execute(
                "INSERT OR REPLACE INTO cache (key, value, timestamp) VALUES (?, ?, ?)",
                (key, value_str, timestamp)
            )
            
            conn.commit()
            self._increment_stat("sets")
            
        except (sqlite3.Error, TypeError) as e:
            logger.error(f"Error storing in SQLite cache: {str(e)}")
            conn.rollback()
        
        finally:
            conn.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary of cache statistics
        """
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            
            # Get current size
            cursor.execute("SELECT COUNT(*) FROM cache")
            size = cursor.fetchone()[0]
            
            stats = self.stats.copy()
            stats["size"] = size
            stats["db_path"] = str(self.db_path)
            stats["ttl"] = self.ttl
            
            # Calculate hit rate
            total_requests = stats["hits"] + stats["misses"]
            stats["hit_rate"] = stats["hits"] / total_requests if total_requests > 0 else 0
            
            return stats
        
        finally:
            conn.close()
    
    def clear(self) -> None:
        """Clear all items from the cache."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cache")
            conn.commit()
        finally:
            conn.close()
    
    def invalidate(self, keys: List[str]) -> int:
        """
        Invalidate specific keys from the cache.
        
        Args:
            keys: List of keys to invalidate
            
        Returns:
            Number of keys invalidated
        """
        if not keys:
            return 0
        
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            
            # Use parameterized query with placeholders
            placeholders = ",".join("?" for _ in keys)
            query = f"DELETE FROM cache WHERE key IN ({placeholders})"
            
            cursor.execute(query, keys)
            invalidated = cursor.rowcount
            conn.commit()
            
            return invalidated
        
        finally:
            conn.close()
    
    def pre_warm(self, items: Dict[str, Dict[str, Any]]) -> None:
        """
        Pre-warm the cache with known values.
        
        Args:
            items: Dictionary mapping keys to values
        """
        if not items:
            return
        
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            timestamp = time.time()
            
            for key, value in items.items():
                try:
                    value_str = json.dumps(value)
                    cursor.execute(
                        "INSERT OR REPLACE INTO cache (key, value, timestamp) VALUES (?, ?, ?)",
                        (key, value_str, timestamp)
                    )
                except (TypeError, json.JSONDecodeError) as e:
                    logger.error(f"Error pre-warming cache for key {key}: {str(e)}")
            
            conn.commit()
            self._increment_stat("sets", len(items))
            
        finally:
            conn.close()


class FileSystemCache(CacheProvider):
    """
    File system based cache implementation.
    
    This cache stores each item as a separate file in a cache directory.
    It's useful for caching large items that might impact memory usage.
    """
    
    def __init__(self, cache_dir: Union[str, Path], ttl: Optional[int] = None):
        """
        Initialize file system cache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl: Time-to-live in seconds (None for no expiration)
        """
        self.cache_dir = Path(cache_dir).resolve()
        self.ttl = ttl
        self.stats_file = self.cache_dir / "cache_stats.json"
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize stats
        self.stats = self._load_stats()
    
    def _get_cache_path(self, key: str) -> Path:
        """
        Get the file path for a cache key.
        
        Args:
            key: Cache key
            
        Returns:
            Path to the cache file
        """
        # Create a safe filename from the key
        safe_key = "".join(c if c.isalnum() else "_" for c in key)
        return self.cache_dir / f"{safe_key}.json"
    
    def _load_stats(self) -> Dict[str, int]:
        """
        Load cache statistics from the stats file.
        
        Returns:
            Dictionary of cache statistics
        """
        default_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0,
            "expirations": 0
        }
        
        if not self.stats_file.exists():
            self._save_stats(default_stats)
            return default_stats
        
        try:
            with open(self.stats_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading cache stats: {str(e)}")
            self._save_stats(default_stats)
            return default_stats
    
    def _save_stats(self, stats: Dict[str, int]) -> None:
        """
        Save cache statistics to the stats file.
        
        Args:
            stats: Dictionary of cache statistics
        """
        try:
            with open(self.stats_file, "w") as f:
                json.dump(stats, f)
        except IOError as e:
            logger.error(f"Error saving cache stats: {str(e)}")
    
    def _update_stat(self, name: str, increment: int = 1) -> None:
        """
        Update a statistic and save to disk.
        
        Args:
            name: Name of the statistic
            increment: Amount to increment by
        """
        self.stats[name] = self.stats.get(name, 0) + increment
        self._save_stats(self.stats)
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a value from the file system cache.
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            Cached value, or None if not found
        """
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            self._update_stat("misses")
            return None
        
        try:
            with open(cache_path, "r") as f:
                cache_data = json.load(f)
            
            # Check for expiration
            if self.ttl is not None:
                timestamp = cache_data.get("timestamp", 0)
                if time.time() - timestamp > self.ttl:
                    # Item has expired
                    cache_path.unlink(missing_ok=True)
                    self._update_stat("expirations")
                    self._update_stat("misses")
                    return None
            
            self._update_stat("hits")
            return cache_data.get("value")
            
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading from cache file {cache_path}: {str(e)}")
            self._update_stat("misses")
            return None
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """
        Set a value in the file system cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        cache_path = self._get_cache_path(key)
        
        try:
            cache_data = {
                "key": key,
                "value": value,
                "timestamp": time.time()
            }
            
            with open(cache_path, "w") as f:
                json.dump(cache_data, f)
            
            self._update_stat("sets")
            
        except IOError as e:
            logger.error(f"Error writing to cache file {cache_path}: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary of cache statistics
        """
        # Count cache files (excluding stats file)
        size = sum(1 for f in self.cache_dir.iterdir() 
                  if f.is_file() and f.name != self.stats_file.name)
        
        stats = self.stats.copy()
        stats["size"] = size
        stats["cache_dir"] = str(self.cache_dir)
        stats["ttl"] = self.ttl
        
        # Calculate hit rate
        total_requests = stats["hits"] + stats["misses"]
        stats["hit_rate"] = stats["hits"] / total_requests if total_requests > 0 else 0
        
        return stats
    
    def clear(self) -> None:
        """Clear all items from the cache."""
        for cache_file in self.cache_dir.iterdir():
            if cache_file.is_file() and cache_file != self.stats_file:
                try:
                    cache_file.unlink()
                except IOError as e:
                    logger.error(f"Error deleting cache file {cache_file}: {str(e)}")
    
    def invalidate(self, keys: List[str]) -> int:
        """
        Invalidate specific keys from the cache.
        
        Args:
            keys: List of keys to invalidate
            
        Returns:
            Number of keys invalidated
        """
        invalidated = 0
        for key in keys:
            cache_path = self._get_cache_path(key)
            if cache_path.exists():
                try:
                    cache_path.unlink()
                    invalidated += 1
                except IOError as e:
                    logger.error(f"Error deleting cache file {cache_path}: {str(e)}")
        
        return invalidated
    
    def pre_warm(self, items: Dict[str, Dict[str, Any]]) -> None:
        """
        Pre-warm the cache with known values.
        
        Args:
            items: Dictionary mapping keys to values
        """
        for key, value in items.items():
            self.set(key, value)


class CacheFactory:
    """Factory for creating cache providers."""
    
    @staticmethod
    def create_cache(cache_type: str, **kwargs) -> CacheProvider:
        """
        Create a cache provider instance.
        
        Args:
            cache_type: Type of cache to create ('memory', 'sqlite', 'filesystem')
            **kwargs: Additional arguments for the specific cache type
        
        Returns:
            CacheProvider instance
            
        Raises:
            ValueError: If cache_type is not supported
        """
        if cache_type == "memory":
            max_size = kwargs.get("max_size")
            ttl = kwargs.get("ttl")
            return InMemoryCache(max_size=max_size, ttl=ttl)
        
        elif cache_type == "sqlite":
            db_path = kwargs.get("db_path")
            if not db_path:
                raise ValueError("db_path is required for SQLite cache")
            ttl = kwargs.get("ttl")
            return SqliteCache(db_path=db_path, ttl=ttl)
        
        elif cache_type == "filesystem":
            cache_dir = kwargs.get("cache_dir")
            if not cache_dir:
                raise ValueError("cache_dir is required for filesystem cache")
            ttl = kwargs.get("ttl")
            return FileSystemCache(cache_dir=cache_dir, ttl=ttl)
        
        else:
            raise ValueError(f"Unsupported cache type: {cache_type}")


class CacheManager:
    """
    Manages multiple cache providers in a tiered arrangement.
    
    This class implements a multi-level cache system, where faster caches
    (like in-memory) are checked first before slower but more persistent
    caches (like SQLite or filesystem).
    """
    
    def __init__(self, caches: List[CacheProvider]):
        """
        Initialize cache manager with a list of cache providers.
        
        Args:
            caches: List of cache providers, in order of access priority
        """
        if not caches:
            raise ValueError("At least one cache provider is required")
        
        self.caches = caches
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a value from cache, checking providers in priority order.
        
        If the value is found in a lower-priority cache but not in a 
        higher-priority one, it will be propagated to the higher-priority
        caches.
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            Cached value, or None if not found in any cache
        """
        # Check caches in order
        for i, cache in enumerate(self.caches):
            value = cache.get(key)
            if value is not None:
                # Found in this cache, propagate to higher-priority caches
                for j in range(i):
                    self.caches[j].set(key, value)
                return value
        
        # Not found in any cache
        return None
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """
        Set a value in all cache providers.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        for cache in self.caches:
            cache.set(key, value)
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics from all cache providers.
        
        Returns:
            Dictionary mapping cache names to their statistics
        """
        return {
            f"cache_{i}": cache.get_stats()
            for i, cache in enumerate(self.caches)
        }
    
    def clear(self) -> None:
        """Clear all items from all cache providers."""
        for cache in self.caches:
            cache.clear()
    
    def invalidate(self, keys: List[str]) -> Dict[int, int]:
        """
        Invalidate specific keys from all cache providers.
        
        Args:
            keys: List of keys to invalidate
            
        Returns:
            Dictionary mapping cache indices to number of keys invalidated
        """
        return {
            i: cache.invalidate(keys)
            for i, cache in enumerate(self.caches)
        }
    
    def pre_warm(self, items: Dict[str, Dict[str, Any]]) -> None:
        """
        Pre-warm all cache providers with known values.
        
        Args:
            items: Dictionary mapping keys to values
        """
        for cache in self.caches:
            cache.pre_warm(items)