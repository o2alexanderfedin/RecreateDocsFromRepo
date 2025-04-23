#!/usr/bin/env python3
"""
Cache management utility script.

This script provides a command-line interface for managing the file analyzer caches,
including viewing cache statistics, clearing caches, and pre-warming with common file types.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

from file_analyzer.core.cache_provider import CacheFactory, CacheManager
from file_analyzer.core.cache_config import get_cache_settings, DEFAULT_CACHE_WARMUP

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("file_analyzer.cache_manager")


def setup_cache(args):
    """
    Set up the cache provider based on command line arguments.
    
    Args:
        args: Command line arguments
        
    Returns:
        Configured cache provider
    """
    cache_config = get_cache_settings(
        cache_type=args.cache_type,
        ttl=args.ttl,
        max_size=args.max_size,
        cache_dir=args.cache_dir,
        db_path=args.db_path
    )
    
    if args.cache_type == "tiered":
        # Set up tiered cache
        caches = []
        for cache_type in cache_config["default_types"]:
            if cache_type == "memory":
                caches.append(CacheFactory.create_cache(
                    "memory",
                    max_size=cache_config.get("max_size"),
                    ttl=cache_config.get("ttl")
                ))
            elif cache_type == "sqlite":
                caches.append(CacheFactory.create_cache(
                    "sqlite",
                    db_path=cache_config.get("db_path"),
                    ttl=cache_config.get("ttl")
                ))
            elif cache_type == "filesystem":
                caches.append(CacheFactory.create_cache(
                    "filesystem",
                    cache_dir=cache_config.get("cache_dir"),
                    ttl=cache_config.get("ttl")
                ))
        
        if caches:
            return CacheManager(caches)
        return None
    
    # For single cache type
    return CacheFactory.create_cache(
        args.cache_type,
        max_size=cache_config.get("max_size"),
        ttl=cache_config.get("ttl"),
        db_path=cache_config.get("db_path"),
        cache_dir=cache_config.get("cache_dir")
    )


def show_stats(cache, args):
    """
    Show cache statistics.
    
    Args:
        cache: Cache provider
        args: Command line arguments
    """
    stats = cache.get_stats()
    
    print(f"\nCache Type: {args.cache_type}")
    
    if isinstance(cache, CacheManager):
        # Show stats for each managed cache
        for key, value in stats.items():
            print(f"\n{key.upper()} Statistics:")
            for k, v in value.items():
                print(f"  {k}: {v}")
    else:
        # Show stats for a single cache
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"\n{key.upper()}:")
                for k, v in value.items():
                    print(f"  {k}: {v}")
            else:
                print(f"{key}: {value}")
                
    # Show hit rate
    hits = stats.get("hits", 0)
    if isinstance(hits, int):
        misses = stats.get("misses", 0)
        total = hits + misses
        hit_rate = 0
        if total > 0:
            hit_rate = hits / total * 100
        print(f"\nHit Rate: {hit_rate:.1f}% ({hits}/{total})")


def clear_cache(cache, args):
    """
    Clear the cache.
    
    Args:
        cache: Cache provider
        args: Command line arguments
    """
    try:
        cache.clear()
        print(f"Cache cleared: {args.cache_type}")
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return 1
    return 0


def pre_warm_cache(cache, args):
    """
    Pre-warm the cache with common file types.
    
    Args:
        cache: Cache provider
        args: Command line arguments
    """
    # Get warmup data
    warmup_data = DEFAULT_CACHE_WARMUP
    
    # Add custom data if provided
    if args.warmup_file:
        try:
            with open(args.warmup_file, 'r') as f:
                custom_data = json.load(f)
                warmup_data.update(custom_data)
        except Exception as e:
            logger.error(f"Error loading warmup file: {str(e)}")
            return 1
    
    # Pre-warm the cache
    try:
        cache.pre_warm(warmup_data)
        print(f"Cache pre-warmed with {len(warmup_data)} entries")
        
        # Show example entries if verbose
        if args.verbose:
            print("\nExample cache entries:")
            for key, value in list(warmup_data.items())[:3]:
                print(f"  {key}: {json.dumps(value, indent=2)}")
    except Exception as e:
        logger.error(f"Error pre-warming cache: {str(e)}")
        return 1
    
    return 0


def export_cache_data(cache, args):
    """
    Export cache data to a JSON file.
    
    Args:
        cache: Cache provider
        args: Command line arguments
    """
    if not args.export_file:
        logger.error("No export file specified")
        return 1
    
    # Get all data (this is a bit of a hack since we don't have a direct way to do this)
    data = {}
    
    # For SQLite cache, we need to export data differently
    if args.cache_type == "sqlite":
        try:
            import sqlite3
            conn = sqlite3.connect(args.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM cache")
            
            for key, value_str in cursor.fetchall():
                data[key] = json.loads(value_str)
            
            conn.close()
        except Exception as e:
            logger.error(f"Error exporting SQLite cache: {str(e)}")
            return 1
    else:
        logger.error(f"Export not supported for cache type: {args.cache_type}")
        return 1
    
    # Write to file
    try:
        with open(args.export_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Cache data exported to {args.export_file} ({len(data)} entries)")
    except Exception as e:
        logger.error(f"Error writing export file: {str(e)}")
        return 1
    
    return 0


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description='Manage file analyzer caches.')
    
    # Cache configuration options
    parser.add_argument('--cache-type', choices=['memory', 'sqlite', 'filesystem', 'tiered'],
                      default='tiered', help='Type of cache to manage')
    parser.add_argument('--ttl', type=int, help='Time-to-live for cache entries in seconds')
    parser.add_argument('--max-size', type=int, help='Maximum items for in-memory cache')
    parser.add_argument('--cache-dir', help='Directory for filesystem cache')
    parser.add_argument('--db-path', help='Path to SQLite database file')
    
    # Actions
    parser.add_argument('--stats', action='store_true', help='Show cache statistics')
    parser.add_argument('--clear', action='store_true', help='Clear the cache')
    parser.add_argument('--pre-warm', action='store_true', help='Pre-warm the cache with common file types')
    parser.add_argument('--warmup-file', help='JSON file with additional warmup data')
    parser.add_argument('--export', action='store_true', help='Export cache data')
    parser.add_argument('--export-file', help='File to export cache data to')
    
    # Other options
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        # Make sure at least one action is specified
        if not any([args.stats, args.clear, args.pre_warm, args.export]):
            logger.error("No action specified. Use --stats, --clear, --pre-warm or --export")
            return 1
        
        # Set up cache provider
        cache = setup_cache(args)
        if not cache:
            logger.error("Failed to set up cache")
            return 1
        
        result = 0
        
        # Perform actions
        if args.stats:
            show_stats(cache, args)
        
        if args.clear:
            result = clear_cache(cache, args)
            if result != 0:
                return result
        
        if args.pre_warm:
            result = pre_warm_cache(cache, args)
            if result != 0:
                return result
        
        if args.export:
            result = export_cache_data(cache, args)
            if result != 0:
                return result
        
        return result
        
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())