from abc import ABC, abstractmethod
from pathlib import Path
from loguru import logger

class BaseAgent(ABC):
    """Base class for all documentation agents."""
    
    def __init__(self, name: str):
        self.name = name
        logger.info(f"Initializing {name} agent")
    
    @abstractmethod
    def analyze(self, repo_path: Path) -> dict:
        """Analyze the repository and extract relevant information.
        
        Args:
            repo_path: Path to the repository to analyze
            
        Returns:
            Dictionary containing extracted information
        """
        pass
    
    @abstractmethod
    def generate_documentation(self, analysis_results: dict, output_dir: Path) -> Path:
        """Generate documentation based on analysis results.
        
        Args:
            analysis_results: Results from the analyze method
            output_dir: Directory to save generated documentation
            
        Returns:
            Path to the generated documentation
        """
        pass
