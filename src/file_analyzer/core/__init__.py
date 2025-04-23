"""Core components for file analyzer."""

from file_analyzer.core.file_reader import FileReader
from file_analyzer.core.file_hasher import FileHasher
from file_analyzer.core.cache_provider import CacheProvider, InMemoryCache
from file_analyzer.core.file_type_analyzer import FileTypeAnalyzer
from file_analyzer.core.code_analyzer import CodeAnalyzer, PRIMARY_LANGUAGES
from file_analyzer.core.framework_detector import FrameworkDetector

__all__ = [
    'FileReader', 'FileHasher', 'CacheProvider', 'InMemoryCache', 
    'FileTypeAnalyzer', 'CodeAnalyzer', 'FrameworkDetector', 'PRIMARY_LANGUAGES'
]
