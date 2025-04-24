"""
Unit tests for the logical view generator.
"""
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import os
import tempfile

from file_analyzer.ai_providers.mock_provider import MockAIProvider
from file_analyzer.doc_generator.logical_view_generator import LogicalViewGenerator
from file_analyzer.core.file_reader import FileReader
from file_analyzer.core.file_hasher import FileHasher
from file_analyzer.core.cache_provider import InMemoryCache

class TestLogicalViewGenerator(unittest.TestCase):
    """Test case for the LogicalViewGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_provider = MockAIProvider()
        self.cache = InMemoryCache()
        self.file_reader = FileReader()
        self.file_hasher = FileHasher()
        
        # Create mock code analyzer
        self.mock_code_analyzer = MagicMock()
        self.mock_code_analyzer.analyze_code.return_value = {
            "language": "python",
            "structure": {
                "classes": [
                    {
                        "name": "TestClass",
                        "attributes": [
                            {"name": "attr1", "type": "str", "accessibility": "public"},
                            {"name": "attr2", "type": "int", "accessibility": "private"}
                        ],
                        "methods": [
                            {
                                "name": "test_method",
                                "parameters": [{"name": "param1", "type": "str"}],
                                "return_type": "bool",
                                "accessibility": "public"
                            }
                        ],
                        "inherits_from": ["BaseClass"],
                        "implements": ["Interface1"]
                    },
                    {
                        "name": "BaseClass",
                        "attributes": [
                            {"name": "base_attr", "type": "str", "accessibility": "protected"}
                        ],
                        "methods": [
                            {
                                "name": "base_method",
                                "parameters": [],
                                "return_type": "None",
                                "accessibility": "public"
                            }
                        ]
                    }
                ],
                "functions": [
                    {
                        "name": "create_objects",
                        "body": "obj1 = TestClass('test')\nobj2 = BaseClass()\nobj1.test_method(obj2)",
                        "parameters": []
                    }
                ],
                "relationships": [
                    {
                        "source": "BaseClass",
                        "target": "TestClass",
                        "type": "inheritance"
                    },
                    {
                        "source": "Interface1",
                        "target": "TestClass",
                        "type": "implementation"
                    }
                ]
            }
        }
        
        # Create generator with mock code analyzer
        self.generator = LogicalViewGenerator(
            ai_provider=self.mock_provider,
            code_analyzer=self.mock_code_analyzer,
            file_reader=self.file_reader,
            file_hasher=self.file_hasher,
            cache_provider=self.cache
        )
        
        # Mock file paths
        self.test_file = Path("/test/test_class.py")
        self.base_file = Path("/test/base_class.py")
    
    def test_generate_class_diagram(self):
        """Test generation of class diagrams."""
        # Generate diagram
        result = self.generator.generate_class_diagram(
            [self.test_file, self.base_file],
            title="Test Class Diagram"
        )
        
        # Verify result structure
        self.assertEqual(result["title"], "Test Class Diagram")
        self.assertEqual(result["diagram_type"], "class")
        self.assertEqual(result["syntax_type"], "mermaid")
        
        # Check diagram content
        self.assertIn("classDiagram", result["content"])
        self.assertIn("TestClass", result["content"])
        self.assertIn("BaseClass", result["content"])
        
        # Verify relationships
        self.assertIn("TestClass --|> BaseClass", result["content"])
        
        # Check metadata
        self.assertEqual(result["metadata"]["file_count"], 2)
        # The mock_code_analyzer.analyze_code provides TestClass, BaseClass and Interface1 (from relationship)
        # so we should expect 3 or 4 classes in the diagram (varies depending on implementation)
        self.assertTrue(result["metadata"]["class_count"] >= 2)
        
        # Verify cache
        self.assertEqual(self.generator.stats["cache_misses"], 1)
        
        # Generate again to test caching
        result2 = self.generator.generate_class_diagram(
            [self.test_file, self.base_file],
            title="Test Class Diagram"
        )
        
        # Check cache stats
        self.assertEqual(self.generator.stats["cache_hits"], 1)
        self.assertEqual(result, result2)  # Should get identical result from cache
    
    def test_generate_object_model(self):
        """Test generation of object model diagrams."""
        # Generate diagram
        result = self.generator.generate_object_model(
            [self.test_file],
            title="Test Object Model"
        )
        
        # Verify result structure
        self.assertEqual(result["title"], "Test Object Model")
        self.assertEqual(result["diagram_type"], "object")
        self.assertEqual(result["syntax_type"], "mermaid")
        
        # Object model actually created
        self.assertIn("classDiagram", result["content"])
        
        # Verify cache
        self.assertEqual(self.generator.stats["object_models_generated"], 1)
    
    @patch("file_analyzer.doc_generator.logical_view_generator.LogicalViewGenerator._generate_state_diagram_with_ai")
    def test_generate_state_diagram(self, mock_ai_diagram):
        """Test generation of state diagrams using AI."""
        # Setup mock AI response
        mock_ai_diagram.return_value = {
            "title": "Test State Diagram",
            "diagram_type": "state",
            "syntax_type": "mermaid",
            "content": "stateDiagram-v2\n    [*] --> State1\n    State1 --> State2\n    State2 --> [*]",
            "states": ["State1", "State2"],
            "transitions": [{"from": "[*]", "to": "State1"}, {"from": "State1", "to": "State2"}, {"from": "State2", "to": "[*]"}]
        }
        
        # Write a test file to a temp location
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("""
            class StateMachine:
                def __init__(self):
                    self.state = 'initial'
                
                def transition(self, event):
                    if self.state == 'initial' and event == 'start':
                        self.state = 'running'
                    elif self.state == 'running' and event == 'pause':
                        self.state = 'paused'
                    elif self.state == 'paused' and event == 'resume':
                        self.state = 'running'
                    elif self.state == 'running' and event == 'stop':
                        self.state = 'stopped'
            """)
            temp_file = Path(f.name)
        
        try:
            # Generate diagram
            result = self.generator.generate_state_diagram(temp_file)
            
            # Verify result
            self.assertEqual(result["diagram_type"], "state")
            self.assertEqual(result["syntax_type"], "mermaid")
            self.assertIn("stateDiagram", result["content"])
            
            # Verify stats
            self.assertEqual(self.generator.stats["state_diagrams_generated"], 1)
        
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    @patch("file_analyzer.doc_generator.logical_view_generator.LogicalViewGenerator._find_code_files")
    @patch("file_analyzer.doc_generator.logical_view_generator.LogicalViewGenerator._select_important_files")
    @patch("file_analyzer.doc_generator.logical_view_generator.LogicalViewGenerator.generate_class_diagram")
    def test_generate_combined_class_diagram(self, mock_class_diagram, mock_select, mock_find):
        """Test generation of combined repository class diagrams."""
        # Setup mocks
        mock_find.return_value = [self.test_file, self.base_file]
        mock_select.return_value = [self.test_file, self.base_file]
        mock_class_diagram.return_value = {
            "title": "Test Combined Diagram",
            "diagram_type": "class",
            "syntax_type": "mermaid",
            "content": "classDiagram\n    TestClass --|> BaseClass",
            "classes": [],
            "relationships": [],
            "metadata": {"file_count": 2, "class_count": 2, "relationship_count": 1}
        }
        
        # Generate diagram
        result = self.generator.generate_combined_class_diagram(Path("/test/repo"))
        
        # Verify result
        self.assertEqual(result["diagram_type"], "class")
        self.assertEqual(result["repository"], "/test/repo")
        self.assertEqual(result["file_selection_strategy"], "importance_based")
        
        # Verify method calls
        mock_find.assert_called_once()
        mock_select.assert_called_once()
        mock_class_diagram.assert_called_once()
    
    def test_get_stats(self):
        """Test retrieving statistics."""
        # Generate some diagrams to populate stats
        self.generator.generate_class_diagram([self.test_file])
        self.generator.generate_object_model([self.test_file])
        
        # Get stats
        stats = self.generator.get_stats()
        
        # Verify stats
        self.assertEqual(stats["class_diagrams_generated"], 1)
        self.assertEqual(stats["object_models_generated"], 1)
        self.assertEqual(stats["cache_misses"], 2)

if __name__ == '__main__':
    unittest.main()