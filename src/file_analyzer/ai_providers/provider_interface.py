"""
Interface for AI model providers.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class AIModelProvider(ABC):
    """Abstract base class for different AI model providers."""
    
    @abstractmethod
    def analyze_content(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Send content to AI model and get analysis result.
        
        Args:
            file_path: Path to the file being analyzed
            content: Content of the file to analyze
            
        Returns:
            Dictionary with analysis results
        """
        pass
    
    def analyze_code(self, file_path: str, content: str, language: str) -> Dict[str, Any]:
        """
        Send code content to AI model for structural analysis.
        
        This method is optional and can be implemented by providers
        that support specialized code analysis. If not implemented,
        the CodeAnalyzer will fall back to a mock implementation.
        
        Args:
            file_path: Path to the file being analyzed
            content: Content of the file to analyze
            language: Programming language of the code
            
        Returns:
            Dictionary with code structure analysis
        """
        # Default implementation delegates to analyze_content
        # Providers should override this for specialized code analysis
        return {
            "structure": {
                "imports": [],
                "classes": [],
                "functions": [],
                "variables": [],
                "language_specific": {},
                "confidence": 0.5
            }
        }