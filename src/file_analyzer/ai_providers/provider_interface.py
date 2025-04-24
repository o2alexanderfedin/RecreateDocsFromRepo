"""
Interface for AI model providers.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


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
    
    def detect_frameworks(self, file_path: str, content: str, language: str) -> Dict[str, Any]:
        """
        Detect frameworks and libraries used in a code file.
        
        This method is optional and can be implemented by providers
        that support specialized framework detection. If not implemented,
        the FrameworkDetector will use a default implementation combining
        heuristics and general AI analysis.
        
        Args:
            file_path: Path to the file being analyzed
            content: Content of the file to analyze
            language: Programming language of the code
            
        Returns:
            Dictionary with detected frameworks and libraries
        """
        # Default implementation returns an empty result
        # Providers should override this for specialized framework detection
        return {
            "frameworks": [],
            "confidence": 0.0
        }
    
    def analyze_config(self, file_path: str, content: str, format_hint: str = None) -> Dict[str, Any]:
        """
        Analyze a configuration file to extract parameters, structure, and purpose.
        
        This method is optional and can be implemented by providers
        that support specialized configuration analysis. If not implemented,
        the ConfigAnalyzer will fallback to a default implementation.
        
        Args:
            file_path: Path to the file being analyzed
            content: Content of the file to analyze
            format_hint: Optional hint about the configuration format
            
        Returns:
            Dictionary with configuration analysis results
        """
        # Default implementation returns a basic result
        # Providers should override this for specialized config analysis
        return {
            "format": format_hint or "unknown",
            "is_config_file": True,
            "parameters": [],
            "environment_vars": [],
            "security_issues": [],
            "confidence": 0.5
        }