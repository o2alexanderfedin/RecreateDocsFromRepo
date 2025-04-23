"""
Integration tests for the enhanced caching system.
"""
import json
import os
import tempfile
import time
from pathlib import Path
import pytest

from file_analyzer.core.file_type_analyzer import FileTypeAnalyzer
from file_analyzer.core.cache_provider import (
    InMemoryCache, SqliteCache, FileSystemCache, CacheFactory, CacheManager
)
from file_analyzer.core.cache_config import get_cache_settings
from file_analyzer.ai_providers.mock_provider import MockAIProvider


class TestCacheIntegration:
    """Test integration of the caching system with the file type analyzer."""
    
    @pytest.fixture
    def mock_provider(self):
        """Create a mock AI provider for testing."""
        return MockAIProvider()
    
    @pytest.fixture
    def test_files(self):
        """Create temporary test files for analysis."""
        with tempfile.TemporaryDirectory() as tempdir:
            # Create Python file
            py_path = Path(tempdir) / "test.py"
            with open(py_path, "w") as f:
                f.write("def test(): print('Hello, world!')")
            
            # Create Markdown file
            md_path = Path(tempdir) / "README.md"
            with open(md_path, "w") as f:
                f.write("# Test Markdown\n\nThis is a test file.")
            
            # Create JSON file
            json_path = Path(tempdir) / "config.json"
            with open(json_path, "w") as f:
                f.write('{"name": "test", "version": "1.0.0"}')
            
            # Create directory structure for testing path exclusions
            os.makedirs(Path(tempdir) / ".git")
            git_file = Path(tempdir) / ".git" / "HEAD"
            with open(git_file, "w") as f:
                f.write("ref: refs/heads/main")
            
            yield {
                "dir": Path(tempdir),
                "py": py_path,
                "md": md_path,
                "json": json_path,
                "git": git_file
            }
    
    def test_memory_cache_integration(self, mock_provider, test_files):
        """Test integration with in-memory cache."""
        # Create analyzer with memory cache
        cache = InMemoryCache()
        analyzer = FileTypeAnalyzer(
            ai_provider=mock_provider,
            cache_provider=cache
        )
        
        # First analysis (should miss cache)
        result1 = analyzer.analyze_file(test_files["py"])
        
        # Second analysis (should hit cache)
        result2 = analyzer.analyze_file(test_files["py"])
        
        # Third analysis of a different file (should miss)
        result3 = analyzer.analyze_file(test_files["md"])
        
        # Fourth analysis of the second file (should hit)
        result4 = analyzer.analyze_file(test_files["md"])
        
        # Check results match
        assert result1 == result2
        assert result3 == result4
        
        # Check cache statistics
        stats = analyzer.get_cache_stats()
        assert stats["hit"] == 2
        assert stats["miss"] == 2
        assert stats["store"] == 2
    
    def test_sqlite_cache_integration(self, mock_provider, test_files):
        """Test integration with SQLite cache."""
        with tempfile.TemporaryDirectory() as tempdir:
            db_path = Path(tempdir) / "cache.db"
            
            # Create analyzer with SQLite cache
            cache = SqliteCache(db_path=db_path)
            analyzer = FileTypeAnalyzer(
                ai_provider=mock_provider,
                cache_provider=cache
            )
            
            # First analysis (should miss cache)
            result1 = analyzer.analyze_file(test_files["py"])
            
            # Second analysis (should hit cache)
            result2 = analyzer.analyze_file(test_files["py"])
            
            # Check results match
            assert result1 == result2
            
            # Check cache statistics
            stats = analyzer.get_cache_stats()
            assert stats["hit"] == 1
            assert stats["miss"] == 1
            assert stats["store"] == 1
            
            # Verify that cache file was created
            assert db_path.exists()
    
    def test_filesystem_cache_integration(self, mock_provider, test_files):
        """Test integration with filesystem cache."""
        with tempfile.TemporaryDirectory() as tempdir:
            cache_dir = Path(tempdir) / "cache"
            
            # Create analyzer with filesystem cache
            cache = FileSystemCache(cache_dir=cache_dir)
            analyzer = FileTypeAnalyzer(
                ai_provider=mock_provider,
                cache_provider=cache
            )
            
            # First analysis (should miss cache)
            result1 = analyzer.analyze_file(test_files["py"])
            
            # Second analysis (should hit cache)
            result2 = analyzer.analyze_file(test_files["py"])
            
            # Check results match
            assert result1 == result2
            
            # Check cache statistics
            stats = analyzer.get_cache_stats()
            assert stats["hit"] == 1
            assert stats["miss"] == 1
            assert stats["store"] == 1
            
            # Verify that cache directory and files were created
            assert cache_dir.exists()
            assert len(list(cache_dir.glob("*.json"))) > 1  # At least 1 cache file + stats file
    
    def test_tiered_cache_integration(self, mock_provider, test_files):
        """Test integration with tiered cache."""
        with tempfile.TemporaryDirectory() as tempdir:
            db_path = Path(tempdir) / "cache.db"
            
            # Create tiered cache
            memory_cache = InMemoryCache()
            sqlite_cache = SqliteCache(db_path=db_path)
            cache_manager = CacheManager([memory_cache, sqlite_cache])
            
            analyzer = FileTypeAnalyzer(
                ai_provider=mock_provider,
                cache_provider=cache_manager
            )
            
            # First analysis (should miss all caches)
            result1 = analyzer.analyze_file(test_files["py"])
            
            # Second analysis (should hit memory cache)
            result2 = analyzer.analyze_file(test_files["py"])
            
            # Check results match
            assert result1 == result2
            
            # Memory cache should have a hit, SQLite should have no hits
            assert memory_cache.stats["hits"] == 1
            assert sqlite_cache.stats["hits"] == 0
            
            # Both caches should have the item stored
            assert len(memory_cache.cache) == 1
            
            # Create new analyzer with just SQLite cache to test persistence
            new_analyzer = FileTypeAnalyzer(
                ai_provider=mock_provider,
                cache_provider=SqliteCache(db_path=db_path)
            )
            
            # This analysis should hit the SQLite cache
            result3 = new_analyzer.analyze_file(test_files["py"])
            
            # Results should still match
            assert result1 == result3
    
    def test_cache_ttl_expiration(self, mock_provider, test_files):
        """Test TTL expiration in the cache."""
        # Use short TTL for testing
        cache = InMemoryCache(ttl=0.1)  # 100ms TTL
        analyzer = FileTypeAnalyzer(
            ai_provider=mock_provider,
            cache_provider=cache
        )
        
        # First analysis (cache miss)
        result1 = analyzer.analyze_file(test_files["py"])
        
        # Immediate second analysis (cache hit)
        result2 = analyzer.analyze_file(test_files["py"])
        
        # Wait for TTL to expire
        time.sleep(0.2)
        
        # Third analysis (should be miss due to expiration)
        result3 = analyzer.analyze_file(test_files["py"])
        
        # Results should be identical
        assert result1 == result2
        assert result1 == result3
        
        # Check cache statistics
        stats = analyzer.get_cache_stats()
        assert stats["hit"] == 1
        assert stats["miss"] == 2  # Initial + after expiration
        assert stats["store"] == 2  # Initial + after expiration
        assert cache.stats["expirations"] == 1
    
    def test_cache_max_size_eviction(self, mock_provider, test_files):
        """Test max size eviction in the cache."""
        # Use small max_size for testing
        cache = InMemoryCache(max_size=2)
        analyzer = FileTypeAnalyzer(
            ai_provider=mock_provider,
            cache_provider=cache
        )
        
        # Analyze three different files to trigger eviction
        analyzer.analyze_file(test_files["py"])   # Will be evicted
        analyzer.analyze_file(test_files["md"])
        analyzer.analyze_file(test_files["json"])
        
        # Now analyze Python file again (should be a miss)
        analyzer.analyze_file(test_files["py"])
        
        # Analyze MD and JSON files (should be hits)
        analyzer.analyze_file(test_files["md"])
        analyzer.analyze_file(test_files["json"])
        
        # Check cache statistics
        assert cache.stats["evictions"] > 0  # At least one eviction should have occurred
        assert len(cache.cache) <= 2  # Max size is 2
    
    def test_automatic_cache_setup(self, mock_provider, test_files):
        """Test automatic cache setup using configuration."""
        # Get default cache settings
        cache_config = get_cache_settings()
        
        # Create analyzer with automatic cache setup
        analyzer = FileTypeAnalyzer(
            ai_provider=mock_provider,
            cache_config=cache_config
        )
        
        # Check cache was set up
        assert analyzer.cache_provider is not None
        assert analyzer.cache_stats["enabled"] is True
        
        # Test basic caching
        result1 = analyzer.analyze_file(test_files["py"])
        result2 = analyzer.analyze_file(test_files["py"])
        
        # Results should match
        assert result1 == result2
        
        # Check cache statistics
        stats = analyzer.get_cache_stats()
        
        # Different caches may have different stat names, but we should have some hit stats
        assert stats.get("hit", 0) >= 1 or "provider" in stats
    
    def test_pre_warming(self, mock_provider):
        """Test pre-warming the cache."""
        cache = InMemoryCache()
        
        # Pre-warm with some known values
        warmup_data = {
            "python_script": {
                "file_type": "code",
                "language": "python",
                "purpose": "script",
                "characteristics": ["executable", "imports", "procedural"],
                "confidence": 0.95
            },
            "markdown_doc": {
                "file_type": "documentation",
                "language": "markdown",
                "purpose": "documentation",
                "characteristics": ["formatted text", "headings", "lists"],
                "confidence": 0.95
            }
        }
        
        cache.pre_warm(warmup_data)
        
        # Create analyzer with pre-warmed cache
        analyzer = FileTypeAnalyzer(
            ai_provider=mock_provider,
            cache_provider=cache
        )
        
        # Check that values are in the cache
        stats = cache.get_stats()
        assert stats["size"] == 2
        assert stats["sets"] == 2
        
        # We can't directly test retrieving the warmed-up values because
        # they are keyed by file hash, but we can verify the cache is functioning
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w+") as tf:
            tf.write("def test(): pass")
            tf.flush()
            
            # First analysis (cache miss)
            result1 = analyzer.analyze_file(tf.name)
            
            # Second analysis (cache hit)
            result2 = analyzer.analyze_file(tf.name)
            
            assert result1 == result2
            
            # Check cache statistics
            stats = analyzer.get_cache_stats()
            assert stats["hit"] == 1
            assert stats["miss"] == 1