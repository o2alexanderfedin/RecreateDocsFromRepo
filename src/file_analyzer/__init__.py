"""File Analyzer Package.

A tool for automatically analyzing files to determine their type, language,
purpose, and key characteristics using AI models.
"""

from file_analyzer.core import (
    FileReader, FileHasher, CacheProvider, InMemoryCache, 
    FileTypeAnalyzer, CodeAnalyzer, FrameworkDetector, PRIMARY_LANGUAGES
)
from file_analyzer.ai_providers import (
    AIModelProvider, MistralProvider, OpenAIProvider, MockAIProvider
)
from file_analyzer.utils import (
    FileAnalyzerError, FileReadError, AIProviderError, CacheError
)

__version__ = '0.5.0'

__all__ = [
    'FileReader', 'FileHasher', 'CacheProvider', 'InMemoryCache', 'FileTypeAnalyzer',
    'CodeAnalyzer', 'FrameworkDetector', 'PRIMARY_LANGUAGES',
    'AIModelProvider', 'MistralProvider', 'OpenAIProvider', 'MockAIProvider',
    'FileAnalyzerError', 'FileReadError', 'AIProviderError', 'CacheError',
]
