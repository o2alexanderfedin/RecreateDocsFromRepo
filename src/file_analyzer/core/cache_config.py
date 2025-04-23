"""
Cache configuration module.

This module provides default configuration settings for the caching system.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Default cache directory - in user home directory
DEFAULT_CACHE_DIR = Path.home() / ".file_analyzer" / "cache"

# Default SQLite database path
DEFAULT_DB_PATH = DEFAULT_CACHE_DIR / "cache.db"

# Default TTL (time-to-live) for cache entries (24 hours)
DEFAULT_TTL = 24 * 60 * 60  # in seconds

# Default maximum size for in-memory cache (items)
DEFAULT_MAX_SIZE = 1000

# Default cache types to use
DEFAULT_CACHE_TYPES = ["memory", "sqlite"]

# Cache warm-up data for common file types
DEFAULT_CACHE_WARMUP = {
    # Python
    "python_script": {
        "file_type": "code",
        "language": "python",
        "purpose": "script",
        "characteristics": ["executable", "imports", "procedural"],
        "confidence": 0.95
    },
    # Markdown
    "markdown_doc": {
        "file_type": "documentation",
        "language": "markdown",
        "purpose": "documentation",
        "characteristics": ["formatted text", "headings", "lists"],
        "confidence": 0.95
    },
    # JSON
    "json_config": {
        "file_type": "configuration",
        "language": "json",
        "purpose": "settings",
        "characteristics": ["structured data", "key-value pairs"],
        "confidence": 0.95
    },
    # Simple text
    "text_file": {
        "file_type": "text",
        "language": "plaintext",
        "purpose": "documentation",
        "characteristics": ["unformatted text"],
        "confidence": 0.90
    },
    # JavaScript
    "javascript_module": {
        "file_type": "code",
        "language": "javascript",
        "purpose": "module",
        "characteristics": ["imports", "exports", "functions"],
        "confidence": 0.95
    }
}


def get_cache_settings(
    cache_type: Optional[str] = None,
    ttl: Optional[int] = None,
    max_size: Optional[int] = None,
    cache_dir: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get cache settings with defaults for any unspecified parameters.
    
    Args:
        cache_type: Type of cache to use (memory, sqlite, filesystem, tiered)
        ttl: Time-to-live for cache entries in seconds
        max_size: Maximum items for in-memory cache
        cache_dir: Directory for filesystem cache
        db_path: Path to SQLite database file
        
    Returns:
        Dictionary of cache settings
    """
    # Create cache directory if it doesn't exist
    cache_directory = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
    cache_directory.mkdir(parents=True, exist_ok=True)
    
    # Use default values if not specified
    settings = {
        "cache_type": cache_type or "tiered",
        "ttl": ttl or DEFAULT_TTL,
        "max_size": max_size or DEFAULT_MAX_SIZE,
        "cache_dir": str(cache_directory),
        "db_path": db_path or str(DEFAULT_DB_PATH),
        "warmup_data": DEFAULT_CACHE_WARMUP,
        "default_types": DEFAULT_CACHE_TYPES
    }
    
    return settings