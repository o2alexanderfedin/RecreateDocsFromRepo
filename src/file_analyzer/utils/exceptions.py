"""
Exceptions for the file analyzer module.
"""

class FileAnalyzerError(Exception):
    """Base exception for the file analyzer module."""
    pass


class FileReadError(FileAnalyzerError):
    """Raised when a file cannot be read."""
    pass


class AIProviderError(FileAnalyzerError):
    """Raised when an AI provider encounters an error."""
    pass


class CacheError(FileAnalyzerError):
    """Raised when there is an error with the cache."""
    pass