"""
Interface for AI model providers.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


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