"""
Diagram Factory implementation.

This module provides the DiagramFactory class that creates the appropriate diagram
generator based on the diagram type requested.
"""
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path

from file_analyzer.ai_providers.provider_interface import AIModelProvider
from file_analyzer.core.file_reader import FileReader
from file_analyzer.core.file_hasher import FileHasher
from file_analyzer.core.cache_provider import CacheProvider
from file_analyzer.core.code_analyzer import CodeAnalyzer
from file_analyzer.doc_generator.base_diagram_generator import BaseDiagramGenerator
from file_analyzer.doc_generator.logical_view_generator import LogicalViewGenerator
from file_analyzer.doc_generator.process_view_generator import ProcessViewGenerator
from file_analyzer.doc_generator.development_view_generator import DevelopmentViewGenerator
from file_analyzer.doc_generator.physical_view_generator import PhysicalViewGenerator
from file_analyzer.doc_generator.scenarios_view_generator import ScenariosViewGenerator

logger = logging.getLogger("file_analyzer.diagram_factory")


class DiagramFactory:
    """
    Factory class for creating UML diagram generators.
    
    This class creates the appropriate diagram generator based on the
    diagram type and view requested, following the 4+1 architectural view model.
    """
    
    def __init__(
        self,
        ai_provider: AIModelProvider,
        code_analyzer: Optional[CodeAnalyzer] = None,
        file_reader: Optional[FileReader] = None,
        file_hasher: Optional[FileHasher] = None,
        cache_provider: Optional[CacheProvider] = None,
    ):
        """
        Initialize the diagram factory.
        
        Args:
            ai_provider: Provider for AI model access
            code_analyzer: CodeAnalyzer for analyzing code files (optional)
            file_reader: Component for reading files (optional)
            file_hasher: Component for hashing files (optional)
            cache_provider: Provider for caching results (optional)
        """
        self.ai_provider = ai_provider
        self.code_analyzer = code_analyzer
        self.file_reader = file_reader
        self.file_hasher = file_hasher
        self.cache_provider = cache_provider
        
        # Cache instances for reuse
        self._instances = {}
    
    def create_generator(self, view_type: str) -> BaseDiagramGenerator:
        """
        Create a diagram generator for the specified view type.
        
        Args:
            view_type: Type of architectural view ('logical', 'process', 'development', 
                                                 'physical', 'scenarios')
            
        Returns:
            Appropriate diagram generator instance
            
        Raises:
            ValueError: If the view type is not supported
        """
        # Check if instance already exists
        if view_type in self._instances:
            return self._instances[view_type]
        
        # Create new instance based on view type
        if view_type == "logical":
            generator = LogicalViewGenerator(
                ai_provider=self.ai_provider,
                code_analyzer=self.code_analyzer,
                file_reader=self.file_reader,
                file_hasher=self.file_hasher,
                cache_provider=self.cache_provider
            )
        elif view_type == "process":
            generator = ProcessViewGenerator(
                ai_provider=self.ai_provider,
                code_analyzer=self.code_analyzer,
                file_reader=self.file_reader,
                file_hasher=self.file_hasher,
                cache_provider=self.cache_provider
            )
        elif view_type == "development":
            generator = DevelopmentViewGenerator(
                ai_provider=self.ai_provider,
                code_analyzer=self.code_analyzer,
                file_reader=self.file_reader,
                file_hasher=self.file_hasher,
                cache_provider=self.cache_provider
            )
        elif view_type == "physical":
            generator = PhysicalViewGenerator(
                ai_provider=self.ai_provider,
                code_analyzer=self.code_analyzer,
                file_reader=self.file_reader,
                file_hasher=self.file_hasher,
                cache_provider=self.cache_provider
            )
        elif view_type == "scenarios":
            generator = ScenariosViewGenerator(
                ai_provider=self.ai_provider,
                code_analyzer=self.code_analyzer,
                file_reader=self.file_reader,
                file_hasher=self.file_hasher,
                cache_provider=self.cache_provider
            )
        else:
            raise ValueError(f"Unsupported view type: {view_type}")
        
        # Cache the instance
        self._instances[view_type] = generator
        
        return generator
    
    def get_supported_views(self) -> Dict[str, Dict[str, str]]:
        """
        Get information about supported views and diagram types.
        
        Returns:
            Dictionary mapping view types to supported diagram types and descriptions
        """
        return {
            "logical": {
                "class": "Class relationship diagrams showing static structure",
                "object": "Object diagram showing instances and relationships",
                "state": "State diagram showing state transitions"
            },
            "process": {
                "sequence": "Sequence diagram showing object interactions over time",
                "activity": "Activity diagram showing control flow of a process"
            },
            "development": {
                "package": "Package diagram showing code organization",
                "component": "Component diagram showing logical components and interfaces"
            },
            "physical": {
                "deployment": "Deployment diagram showing hardware nodes and artifacts",
                "infrastructure": "Infrastructure diagram showing cloud resources and connections"
            },
            "scenarios": {
                "use_case": "Use case diagram showing actors and system functionality",
                "user_flow": "User flow diagram showing step-by-step user interactions"
            }
        }
    
    def generate_diagram(
        self, 
        view_type: str, 
        diagram_type: str, 
        target: Union[str, Path, list], 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a diagram directly through the factory.
        
        Args:
            view_type: Type of architectural view ('logical', 'process', 'development',
                                                 'physical', 'scenarios')
            diagram_type: Type of diagram within the view
            target: Target file(s) or directory for analysis
            **kwargs: Additional arguments for the specific diagram type
            
        Returns:
            Dictionary containing diagram data with Mermaid or PlantUML syntax
            
        Raises:
            ValueError: If the view type or diagram type is not supported
        """
        # Validate view and diagram type
        supported_views = self.get_supported_views()
        if view_type not in supported_views:
            raise ValueError(f"Unsupported view type: {view_type}")
        
        if diagram_type not in supported_views[view_type]:
            supported = ", ".join(supported_views[view_type].keys())
            raise ValueError(f"Unsupported diagram type '{diagram_type}' for view '{view_type}'. Supported: {supported}")
        
        # Create generator
        generator = self.create_generator(view_type)
        
        # Generate diagram
        return generator.generate_diagram(target, diagram_type, **kwargs)