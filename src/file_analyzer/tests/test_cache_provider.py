"""
Unit tests for CacheProvider implementations.
"""
from file_analyzer.core.cache_provider import InMemoryCache


class TestInMemoryCache:
    """Unit tests for the InMemoryCache class."""
    
    def test_get_nonexistent_key(self):
        """Test that getting a nonexistent key returns None."""
        # Arrange
        cache = InMemoryCache()
        
        # Act
        result = cache.get("nonexistent")
        
        # Assert
        assert result is None
    
    def test_set_and_get(self):
        """Test that a value can be set and retrieved."""
        # Arrange
        cache = InMemoryCache()
        key = "test_key"
        value = {"key": "value", "nested": {"foo": "bar"}}
        
        # Act
        cache.set(key, value)
        result = cache.get(key)
        
        # Assert
        assert result == value
        
    def test_set_overwrites_existing(self):
        """Test that setting an existing key overwrites the previous value."""
        # Arrange
        cache = InMemoryCache()
        key = "test_key"
        value1 = {"version": 1}
        value2 = {"version": 2}
        
        # Act
        cache.set(key, value1)
        cache.set(key, value2)
        result = cache.get(key)
        
        # Assert
        assert result == value2
        
    def test_multiple_keys(self):
        """Test that multiple keys can be stored and retrieved."""
        # Arrange
        cache = InMemoryCache()
        
        # Act
        cache.set("key1", {"id": 1})
        cache.set("key2", {"id": 2})
        
        # Assert
        assert cache.get("key1") == {"id": 1}
        assert cache.get("key2") == {"id": 2}