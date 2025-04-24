"""
Unit tests for the diagram factory.
"""
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

from file_analyzer.ai_providers.mock_provider import MockAIProvider
from file_analyzer.doc_generator.diagram_factory import DiagramFactory
from file_analyzer.doc_generator.logical_view_generator import LogicalViewGenerator
from file_analyzer.doc_generator.process_view_generator import ProcessViewGenerator
from file_analyzer.doc_generator.development_view_generator import DevelopmentViewGenerator
from file_analyzer.doc_generator.physical_view_generator import PhysicalViewGenerator
from file_analyzer.doc_generator.scenarios_view_generator import ScenariosViewGenerator
from file_analyzer.core.file_reader import FileReader
from file_analyzer.core.file_hasher import FileHasher
from file_analyzer.core.cache_provider import InMemoryCache

class TestDiagramFactory(unittest.TestCase):
    """Test case for the DiagramFactory class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_provider = MockAIProvider()
        self.cache = InMemoryCache()
        self.file_reader = MagicMock(spec=FileReader)
        self.file_hasher = FileHasher()
        self.mock_code_analyzer = MagicMock()
        
        # Create factory with dependencies
        self.factory = DiagramFactory(
            ai_provider=self.mock_provider,
            code_analyzer=self.mock_code_analyzer,
            file_reader=self.file_reader,
            file_hasher=self.file_hasher,
            cache_provider=self.cache
        )
    
    def test_create_generator_logical(self):
        """Test creating logical view generator."""
        generator = self.factory.create_generator("logical")
        
        # Verify generator type
        self.assertIsInstance(generator, LogicalViewGenerator)
        
        # Verify dependencies were passed
        self.assertEqual(generator.ai_provider, self.mock_provider)
        self.assertEqual(generator.code_analyzer, self.mock_code_analyzer)
        self.assertEqual(generator.file_reader, self.file_reader)
        self.assertEqual(generator.file_hasher, self.file_hasher)
        self.assertEqual(generator.cache_provider, self.cache)
        
        # Verify instance is cached (second request returns the same instance)
        generator2 = self.factory.create_generator("logical")
        self.assertIs(generator, generator2)
    
    def test_create_generator_process(self):
        """Test creating process view generator."""
        generator = self.factory.create_generator("process")
        self.assertIsInstance(generator, ProcessViewGenerator)
    
    def test_create_generator_development(self):
        """Test creating development view generator."""
        generator = self.factory.create_generator("development")
        self.assertIsInstance(generator, DevelopmentViewGenerator)
    
    def test_create_generator_physical(self):
        """Test creating physical view generator."""
        generator = self.factory.create_generator("physical")
        self.assertIsInstance(generator, PhysicalViewGenerator)
    
    def test_create_generator_scenarios(self):
        """Test creating scenarios view generator."""
        generator = self.factory.create_generator("scenarios")
        self.assertIsInstance(generator, ScenariosViewGenerator)
    
    def test_create_generator_invalid(self):
        """Test creating generator with invalid view type."""
        with self.assertRaises(ValueError):
            self.factory.create_generator("invalid_type")
    
    def test_get_supported_views(self):
        """Test retrieving supported views."""
        views = self.factory.get_supported_views()
        
        # Verify all view types are included
        self.assertIn("logical", views)
        self.assertIn("process", views)
        self.assertIn("development", views)
        self.assertIn("physical", views)
        self.assertIn("scenarios", views)
        
        # Verify each view has diagram types
        self.assertIn("class", views["logical"])
        self.assertIn("sequence", views["process"])
        self.assertIn("package", views["development"])
        self.assertIn("deployment", views["physical"])
        self.assertIn("use_case", views["scenarios"])
    
    def test_generate_diagram(self):
        """Test generating diagram through factory."""
        # Mock generators
        mock_physical_generator = MagicMock()
        mock_physical_generator.generate_diagram.return_value = {"diagram_type": "deployment"}
        
        mock_scenarios_generator = MagicMock()
        mock_scenarios_generator.generate_diagram.return_value = {"diagram_type": "use_case"}
        
        # Replace create_generator to return mocks
        original_method = self.factory.create_generator
        
        def mock_create_generator(view_type):
            if view_type == "physical":
                return mock_physical_generator
            elif view_type == "scenarios":
                return mock_scenarios_generator
            else:
                return original_method(view_type)
        
        self.factory.create_generator = mock_create_generator
        
        # Test physical view diagram generation
        result = self.factory.generate_diagram("physical", "deployment", "/test/repo")
        self.assertEqual(result["diagram_type"], "deployment")
        mock_physical_generator.generate_diagram.assert_called_once_with("/test/repo", "deployment")
        
        # Test scenarios view diagram generation with kwargs
        result = self.factory.generate_diagram("scenarios", "use_case", "/test/repo", title="Test")
        self.assertEqual(result["diagram_type"], "use_case")
        mock_scenarios_generator.generate_diagram.assert_called_once_with("/test/repo", "use_case", title="Test")
        
        # Test invalid view type
        with self.assertRaises(ValueError):
            self.factory.generate_diagram("invalid_view", "diagram_type", "/test/repo")
        
        # Test valid view type but invalid diagram type
        with self.assertRaises(ValueError):
            self.factory.generate_diagram("physical", "invalid_diagram", "/test/repo")

if __name__ == '__main__':
    unittest.main()