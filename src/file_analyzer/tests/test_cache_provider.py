"""
Unit tests for the cache_provider module.
"""
import json
import os
import sqlite3
import tempfile
import time
from pathlib import Path
import pytest

from file_analyzer.core.cache_provider import (
    InMemoryCache, SqliteCache, FileSystemCache, CacheFactory, CacheManager
)


class TestInMemoryCache:
    """Test cases for the InMemoryCache implementation."""
    
    def test_get_nonexistent_key(self):
        """Test retrieving a key that doesn't exist."""
        # Arrange
        cache = InMemoryCache()
        
        # Act
        result = cache.get("nonexistent")
        
        # Assert
        assert result is None
        assert cache.stats["misses"] == 1
        assert cache.stats["hits"] == 0
    
    def test_set_and_get(self):
        """Test setting and retrieving a value."""
        # Arrange
        cache = InMemoryCache()
        key = "test_key"
        value = {"file_type": "code", "language": "python"}
        
        # Act
        cache.set(key, value)
        result = cache.get(key)
        
        # Assert
        assert result == value
        assert cache.stats["sets"] == 1
        assert cache.stats["hits"] == 1
        assert cache.stats["misses"] == 0
    
    def test_set_overwrites_existing(self):
        """Test that setting a key overwrites any existing value."""
        # Arrange
        cache = InMemoryCache()
        key = "test_key"
        value1 = {"file_type": "code", "language": "python"}
        value2 = {"file_type": "documentation", "language": "markdown"}
        
        # Act
        cache.set(key, value1)
        cache.set(key, value2)
        result = cache.get(key)
        
        # Assert
        assert result == value2
        assert cache.stats["sets"] == 2
        assert cache.stats["hits"] == 1
    
    def test_multiple_keys(self):
        """Test handling multiple keys in the cache."""
        # Arrange
        cache = InMemoryCache()
        items = {
            "key1": {"file_type": "code", "language": "python"},
            "key2": {"file_type": "documentation", "language": "markdown"},
            "key3": {"file_type": "config", "language": "json"}
        }
        
        # Act
        for key, value in items.items():
            cache.set(key, value)
        
        results = {key: cache.get(key) for key in items.keys()}
        
        # Assert
        assert results == items
        assert cache.stats["sets"] == 3
        assert cache.stats["hits"] == 3
    
    def test_ttl_expiration(self):
        """Test that items expire after the TTL."""
        # Arrange
        cache = InMemoryCache(ttl=0.1)  # 100ms TTL
        key = "test_key"
        value = {"file_type": "code", "language": "python"}
        
        # Act
        cache.set(key, value)
        result1 = cache.get(key)
        
        # Wait for the item to expire
        time.sleep(0.2)
        result2 = cache.get(key)
        
        # Assert
        assert result1 == value
        assert result2 is None
        assert cache.stats["hits"] == 1
        assert cache.stats["misses"] == 1
        assert cache.stats["expirations"] == 1
    
    def test_max_size_eviction(self):
        """Test that items are evicted when max size is reached."""
        # Arrange
        cache = InMemoryCache(max_size=2)
        keys = ["key1", "key2", "key3"]
        values = [
            {"file_type": "code", "language": "python"},
            {"file_type": "documentation", "language": "markdown"},
            {"file_type": "config", "language": "json"}
        ]
        
        # Act
        for key, value in zip(keys, values):
            cache.set(key, value)
        
        # The first item should be evicted when the third is added
        results = [cache.get(key) for key in keys]
        
        # Assert
        assert results == [None, values[1], values[2]]
        assert cache.stats["evictions"] == 1
        assert cache.stats["hits"] == 2
        assert cache.stats["misses"] == 1
    
    def test_get_stats(self):
        """Test getting cache statistics."""
        # Arrange
        cache = InMemoryCache(max_size=100, ttl=3600)
        key = "test_key"
        value = {"file_type": "code", "language": "python"}
        
        # Act
        cache.set(key, value)
        cache.get(key)
        cache.get("nonexistent")
        stats = cache.get_stats()
        
        # Assert
        assert stats["size"] == 1
        assert stats["max_size"] == 100
        assert stats["ttl"] == 3600
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["sets"] == 1
        assert stats["hit_rate"] == 0.5  # 1 hit out of 2 requests
    
    def test_clear(self):
        """Test clearing the cache."""
        # Arrange
        cache = InMemoryCache()
        cache.set("key1", {"value": 1})
        cache.set("key2", {"value": 2})
        
        # Act
        cache.clear()
        result1 = cache.get("key1")
        result2 = cache.get("key2")
        
        # Assert
        assert result1 is None
        assert result2 is None
        assert len(cache.cache) == 0
    
    def test_invalidate(self):
        """Test invalidating specific keys."""
        # Arrange
        cache = InMemoryCache()
        cache.set("key1", {"value": 1})
        cache.set("key2", {"value": 2})
        cache.set("key3", {"value": 3})
        
        # Act
        invalidated = cache.invalidate(["key1", "key3", "nonexistent"])
        
        # Assert
        assert invalidated == 2
        assert cache.get("key1") is None
        assert cache.get("key2") is not None
        assert cache.get("key3") is None
    
    def test_pre_warm(self):
        """Test pre-warming the cache."""
        # Arrange
        cache = InMemoryCache()
        items = {
            "key1": {"file_type": "code", "language": "python"},
            "key2": {"file_type": "documentation", "language": "markdown"}
        }
        
        # Act
        cache.pre_warm(items)
        
        # Assert
        assert cache.get("key1") == items["key1"]
        assert cache.get("key2") == items["key2"]
        assert cache.stats["sets"] == 2
        assert cache.stats["hits"] == 2


class TestSqliteCache:
    """Test cases for the SqliteCache implementation."""
    
    @pytest.fixture
    def db_path(self):
        """Create a temporary database path for tests."""
        with tempfile.TemporaryDirectory() as tempdir:
            yield Path(tempdir) / "test_cache.db"
    
    def test_init_creates_tables(self, db_path):
        """Test that initialization creates the necessary tables."""
        # Arrange & Act
        cache = SqliteCache(db_path)
        
        # Assert - Verify tables exist
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check cache table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cache'")
        assert cursor.fetchone() is not None
        
        # Check stats table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cache_stats'")
        assert cursor.fetchone() is not None
        
        conn.close()
    
    def test_set_and_get(self, db_path):
        """Test setting and retrieving a value."""
        # Arrange
        cache = SqliteCache(db_path)
        key = "test_key"
        value = {"file_type": "code", "language": "python"}
        
        # Act
        cache.set(key, value)
        result = cache.get(key)
        
        # Assert
        assert result == value
    
    def test_get_nonexistent(self, db_path):
        """Test retrieving a nonexistent key."""
        # Arrange
        cache = SqliteCache(db_path)
        
        # Act
        result = cache.get("nonexistent")
        
        # Assert
        assert result is None
    
    def test_ttl_expiration(self, db_path):
        """Test that items expire after the TTL."""
        # Arrange
        cache = SqliteCache(db_path, ttl=0.1)  # 100ms TTL
        key = "test_key"
        value = {"file_type": "code", "language": "python"}
        
        # Act
        cache.set(key, value)
        result1 = cache.get(key)
        
        # Wait for the item to expire
        time.sleep(0.2)
        result2 = cache.get(key)
        
        # Assert
        assert result1 == value
        assert result2 is None
    
    def test_get_stats(self, db_path):
        """Test getting statistics."""
        # Arrange
        cache = SqliteCache(db_path)
        cache.set("key1", {"value": 1})
        cache.get("key1")
        cache.get("nonexistent")
        
        # Act
        stats = cache.get_stats()
        
        # Assert
        assert stats["size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["sets"] == 1
        assert stats["hit_rate"] == 0.5
        assert stats["db_path"].replace('/private', '') == str(db_path).replace('/private', '')
    
    def test_clear(self, db_path):
        """Test clearing the cache."""
        # Arrange
        cache = SqliteCache(db_path)
        cache.set("key1", {"value": 1})
        cache.set("key2", {"value": 2})
        
        # Act
        cache.clear()
        result1 = cache.get("key1")
        result2 = cache.get("key2")
        
        # Assert
        assert result1 is None
        assert result2 is None
        assert cache.get_stats()["size"] == 0
    
    def test_invalidate(self, db_path):
        """Test invalidating specific keys."""
        # Arrange
        cache = SqliteCache(db_path)
        cache.set("key1", {"value": 1})
        cache.set("key2", {"value": 2})
        cache.set("key3", {"value": 3})
        
        # Act
        invalidated = cache.invalidate(["key1", "key3", "nonexistent"])
        
        # Assert
        assert invalidated == 2
        assert cache.get("key1") is None
        assert cache.get("key2") is not None
        assert cache.get("key3") is None
    
    def test_pre_warm(self, db_path):
        """Test pre-warming the cache."""
        # Arrange
        cache = SqliteCache(db_path)
        items = {
            "key1": {"file_type": "code", "language": "python"},
            "key2": {"file_type": "documentation", "language": "markdown"}
        }
        
        # Act
        cache.pre_warm(items)
        
        # Assert
        assert cache.get("key1") == items["key1"]
        assert cache.get("key2") == items["key2"]
        assert cache.get_stats()["size"] == 2


class TestFileSystemCache:
    """Test cases for the FileSystemCache implementation."""
    
    @pytest.fixture
    def cache_dir(self):
        """Create a temporary directory for cache files."""
        with tempfile.TemporaryDirectory() as tempdir:
            yield Path(tempdir) / "cache"
    
    def test_init_creates_directory(self, cache_dir):
        """Test that initialization creates the cache directory."""
        # Arrange & Act
        cache = FileSystemCache(cache_dir)
        
        # Assert
        assert cache_dir.exists()
        assert cache_dir.is_dir()
        
        # Should also create stats file
        assert (cache_dir / "cache_stats.json").exists()
    
    def test_set_and_get(self, cache_dir):
        """Test setting and retrieving a value."""
        # Arrange
        cache = FileSystemCache(cache_dir)
        key = "test_key"
        value = {"file_type": "code", "language": "python"}
        
        # Act
        cache.set(key, value)
        result = cache.get(key)
        
        # Assert
        assert result == value
        
        # Check file was created
        cache_files = list(cache_dir.glob("*.json"))
        assert len(cache_files) == 2  # 1 cache file + 1 stats file
    
    def test_get_nonexistent(self, cache_dir):
        """Test retrieving a nonexistent key."""
        # Arrange
        cache = FileSystemCache(cache_dir)
        
        # Act
        result = cache.get("nonexistent")
        
        # Assert
        assert result is None
    
    def test_ttl_expiration(self, cache_dir):
        """Test that items expire after the TTL."""
        # Arrange
        cache = FileSystemCache(cache_dir, ttl=0.1)  # 100ms TTL
        key = "test_key"
        value = {"file_type": "code", "language": "python"}
        
        # Act
        cache.set(key, value)
        result1 = cache.get(key)
        
        # Wait for the item to expire
        time.sleep(0.2)
        result2 = cache.get(key)
        
        # Assert
        assert result1 == value
        assert result2 is None
    
    def test_get_stats(self, cache_dir):
        """Test getting statistics."""
        # Arrange
        cache = FileSystemCache(cache_dir)
        cache.set("key1", {"value": 1})
        cache.get("key1")
        cache.get("nonexistent")
        
        # Act
        stats = cache.get_stats()
        
        # Assert
        assert stats["size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["sets"] == 1
        assert stats["hit_rate"] == 0.5
        assert stats["cache_dir"].replace('/private', '') == str(cache_dir).replace('/private', '')
    
    def test_clear(self, cache_dir):
        """Test clearing the cache."""
        # Arrange
        cache = FileSystemCache(cache_dir)
        cache.set("key1", {"value": 1})
        cache.set("key2", {"value": 2})
        
        # Act
        cache.clear()
        result1 = cache.get("key1")
        result2 = cache.get("key2")
        
        # Assert
        assert result1 is None
        assert result2 is None
        # Stats file should still exist
        assert (cache_dir / "cache_stats.json").exists()
        # Only stats file should remain
        assert len(list(cache_dir.glob("*.json"))) == 1
    
    def test_invalidate(self, cache_dir):
        """Test invalidating specific keys."""
        # Arrange
        cache = FileSystemCache(cache_dir)
        cache.set("key1", {"value": 1})
        cache.set("key2", {"value": 2})
        cache.set("key3", {"value": 3})
        
        # Act
        invalidated = cache.invalidate(["key1", "key3", "nonexistent"])
        
        # Assert
        assert invalidated == 2
        assert cache.get("key1") is None
        assert cache.get("key2") is not None
        assert cache.get("key3") is None
    
    def test_pre_warm(self, cache_dir):
        """Test pre-warming the cache."""
        # Arrange
        cache = FileSystemCache(cache_dir)
        items = {
            "key1": {"file_type": "code", "language": "python"},
            "key2": {"file_type": "documentation", "language": "markdown"}
        }
        
        # Act
        cache.pre_warm(items)
        
        # Assert
        assert cache.get("key1") == items["key1"]
        assert cache.get("key2") == items["key2"]
        # 2 cache files + 1 stats file
        assert len(list(cache_dir.glob("*.json"))) == 3


class TestCacheFactory:
    """Test cases for the CacheFactory."""
    
    def test_create_memory_cache(self):
        """Test creating an in-memory cache."""
        # Act
        cache = CacheFactory.create_cache("memory", max_size=100, ttl=3600)
        
        # Assert
        assert isinstance(cache, InMemoryCache)
        assert cache.max_size == 100
        assert cache.ttl == 3600
    
    def test_create_sqlite_cache(self):
        """Test creating a SQLite cache."""
        # Arrange
        with tempfile.TemporaryDirectory() as tempdir:
            db_path = Path(tempdir) / "test.db"
            
            # Act
            cache = CacheFactory.create_cache("sqlite", db_path=db_path, ttl=3600)
            
            # Assert
            assert isinstance(cache, SqliteCache)
            assert str(cache.db_path).replace('/private', '') == str(db_path).replace('/private', '')
            assert cache.ttl == 3600
    
    def test_create_filesystem_cache(self):
        """Test creating a filesystem cache."""
        # Arrange
        with tempfile.TemporaryDirectory() as tempdir:
            cache_dir = Path(tempdir) / "cache"
            
            # Act
            cache = CacheFactory.create_cache("filesystem", cache_dir=cache_dir, ttl=3600)
            
            # Assert
            assert isinstance(cache, FileSystemCache)
            assert str(cache.cache_dir).replace('/private', '') == str(cache_dir).replace('/private', '')
            assert cache.ttl == 3600
    
    def test_create_invalid_cache_type(self):
        """Test creating an invalid cache type raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError):
            CacheFactory.create_cache("invalid")
    
    def test_create_sqlite_without_path(self):
        """Test creating a SQLite cache without a path raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError):
            CacheFactory.create_cache("sqlite")
    
    def test_create_filesystem_without_dir(self):
        """Test creating a filesystem cache without a directory raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError):
            CacheFactory.create_cache("filesystem")


class TestCacheManager:
    """Test cases for the CacheManager."""
    
    def test_init_requires_caches(self):
        """Test initialization requires at least one cache."""
        # Act & Assert
        with pytest.raises(ValueError):
            CacheManager([])
    
    def test_get_from_first_cache(self):
        """Test retrieving from the first cache."""
        # Arrange
        cache1 = InMemoryCache()
        cache2 = InMemoryCache()
        cache1.set("key", {"value": 1})
        
        manager = CacheManager([cache1, cache2])
        
        # Act
        result = manager.get("key")
        
        # Assert
        assert result == {"value": 1}
        assert cache1.stats["hits"] == 1
        assert cache2.stats["hits"] == 0
    
    def test_get_from_second_cache_propagates(self):
        """Test retrieving from the second cache propagates to the first."""
        # Arrange
        cache1 = InMemoryCache()
        cache2 = InMemoryCache()
        cache2.set("key", {"value": 2})
        
        manager = CacheManager([cache1, cache2])
        
        # Act
        result = manager.get("key")
        
        # Assert
        assert result == {"value": 2}
        assert cache1.stats["hits"] == 0
        assert cache2.stats["hits"] == 1
        
        # Value should be propagated to the first cache
        assert cache1.get("key") == {"value": 2}
    
    def test_get_nonexistent(self):
        """Test retrieving a nonexistent key from all caches."""
        # Arrange
        cache1 = InMemoryCache()
        cache2 = InMemoryCache()
        
        manager = CacheManager([cache1, cache2])
        
        # Act
        result = manager.get("nonexistent")
        
        # Assert
        assert result is None
        assert cache1.stats["misses"] == 1
        assert cache2.stats["misses"] == 1
    
    def test_set_all_caches(self):
        """Test setting a value in all caches."""
        # Arrange
        cache1 = InMemoryCache()
        cache2 = InMemoryCache()
        
        manager = CacheManager([cache1, cache2])
        
        # Act
        manager.set("key", {"value": 3})
        
        # Assert
        assert cache1.get("key") == {"value": 3}
        assert cache2.get("key") == {"value": 3}
        assert cache1.stats["sets"] == 1
        assert cache2.stats["sets"] == 1
    
    def test_get_stats(self):
        """Test getting statistics from all caches."""
        # Arrange
        cache1 = InMemoryCache()
        cache2 = InMemoryCache()
        
        manager = CacheManager([cache1, cache2])
        manager.set("key1", {"value": 1})
        manager.get("key1")
        manager.get("nonexistent")
        
        # Act
        stats = manager.get_stats()
        
        # Assert
        assert "cache_0" in stats
        assert "cache_1" in stats
        assert stats["cache_0"]["hits"] == 1
        assert stats["cache_0"]["misses"] == 1
        assert stats["cache_1"]["hits"] == 0
        assert stats["cache_1"]["misses"] == 1
    
    def test_clear(self):
        """Test clearing all caches."""
        # Arrange
        cache1 = InMemoryCache()
        cache2 = InMemoryCache()
        cache1.set("key1", {"value": 1})
        cache2.set("key2", {"value": 2})
        
        manager = CacheManager([cache1, cache2])
        
        # Act
        manager.clear()
        
        # Assert
        assert cache1.get("key1") is None
        assert cache2.get("key2") is None
        assert len(cache1.cache) == 0
        assert len(cache2.cache) == 0
    
    def test_invalidate(self):
        """Test invalidating keys in all caches."""
        # Arrange
        cache1 = InMemoryCache()
        cache2 = InMemoryCache()
        cache1.set("key1", {"value": 1})
        cache1.set("key2", {"value": 2})
        cache2.set("key1", {"value": 1})
        
        manager = CacheManager([cache1, cache2])
        
        # Act
        result = manager.invalidate(["key1"])
        
        # Assert
        assert result == {0: 1, 1: 1}
        assert cache1.get("key1") is None
        assert cache1.get("key2") is not None
        assert cache2.get("key1") is None
    
    def test_pre_warm(self):
        """Test pre-warming all caches."""
        # Arrange
        cache1 = InMemoryCache()
        cache2 = InMemoryCache()
        
        manager = CacheManager([cache1, cache2])
        items = {
            "key1": {"value": 1},
            "key2": {"value": 2}
        }
        
        # Act
        manager.pre_warm(items)
        
        # Assert
        assert cache1.get("key1") == {"value": 1}
        assert cache1.get("key2") == {"value": 2}
        assert cache2.get("key1") == {"value": 1}
        assert cache2.get("key2") == {"value": 2}