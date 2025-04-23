"""
Mock AI provider for testing.
"""
from typing import Dict, Any

from file_analyzer.ai_providers.provider_interface import AIModelProvider


class MockAIProvider(AIModelProvider):
    """Mock AI provider implementation for testing."""
    
    def analyze_content(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Return mock analysis results based on file path.
        
        Args:
            file_path: Path to the file being analyzed
            content: Content of the file to analyze
            
        Returns:
            Dictionary with mock analysis results
        """
        if ".py" in file_path.lower():
            return {
                "file_type": "code",
                "language": "python",
                "purpose": "implementation",
                "characteristics": ["functions", "classes", "module"],
                "confidence": 0.9
            }
        elif ".js" in file_path.lower() and not ".json" in file_path.lower():
            return {
                "file_type": "code",
                "language": "javascript",
                "purpose": "implementation",
                "characteristics": ["functions", "module"],
                "confidence": 0.9
            }
        elif ".json" in file_path.lower():
            return {
                "file_type": "code",
                "language": "json",
                "purpose": "configuration",
                "characteristics": ["settings", "data"],
                "confidence": 0.9
            }
        elif ".md" in file_path.lower():
            return {
                "file_type": "documentation",
                "language": "markdown",
                "purpose": "documentation",
                "characteristics": ["text", "formatting"],
                "confidence": 0.9
            }
        elif ".yml" in file_path.lower() or ".yaml" in file_path.lower():
            return {
                "file_type": "configuration",
                "language": "yaml",
                "purpose": "configuration",
                "characteristics": ["settings", "environment"],
                "confidence": 0.9
            }
        elif ".html" in file_path.lower():
            return {
                "file_type": "markup",
                "language": "html",
                "purpose": "user interface",
                "characteristics": ["markup", "structure"],
                "confidence": 0.9
            }
        elif ".css" in file_path.lower():
            return {
                "file_type": "code",
                "language": "css",
                "purpose": "styling",
                "characteristics": ["styles", "presentation"],
                "confidence": 0.9
            }
        elif ".sh" in file_path.lower():
            return {
                "file_type": "code",
                "language": "shell",
                "purpose": "automation",
                "characteristics": ["commands", "script"],
                "confidence": 0.9
            }
        else:
            # Default for unknown files
            # Handle special cases for common files
            if "requirements.txt" in file_path.lower():
                return {
                    "file_type": "configuration",
                    "language": "text",
                    "purpose": "dependencies",
                    "characteristics": ["packages", "dependencies"],
                    "confidence": 0.9
                }
            elif ".toml" in file_path.lower():
                return {
                    "file_type": "configuration",
                    "language": "toml",
                    "purpose": "project configuration",
                    "characteristics": ["settings", "metadata"],
                    "confidence": 0.9
                }
            else:
                # Default for other unknown files
                return {
                    "file_type": "unknown",
                    "language": "unknown",
                    "purpose": "unknown",
                    "characteristics": ["binary" if b"\0" in content.encode() else "text"],
                    "confidence": 0.5
                }