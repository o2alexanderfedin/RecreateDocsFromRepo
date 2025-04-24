"""
Unit tests for the process view generator.
"""
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import os
import tempfile

from file_analyzer.ai_providers.mock_provider import MockAIProvider
from file_analyzer.doc_generator.process_view_generator import ProcessViewGenerator
from file_analyzer.core.file_reader import FileReader
from file_analyzer.core.file_hasher import FileHasher
from file_analyzer.core.cache_provider import InMemoryCache

class TestProcessViewGenerator(unittest.TestCase):
    """Test case for the ProcessViewGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_provider = MockAIProvider()
        self.cache = InMemoryCache()
        self.file_reader = MagicMock(spec=FileReader)
        self.file_hasher = FileHasher()
        
        # Create mock code analyzer
        self.mock_code_analyzer = MagicMock()
        self.mock_code_analyzer.analyze_code.return_value = {
            "language": "python",
            "structure": {
                "classes": [
                    {
                        "name": "Controller",
                        "methods": [
                            {
                                "name": "process_request",
                                "body": "self.service.validate(request)\nself.service.execute(request)\nreturn response",
                                "parameters": [{"name": "request"}]
                            }
                        ]
                    },
                    {
                        "name": "Service",
                        "methods": [
                            {
                                "name": "validate",
                                "body": "if not request.is_valid():\n    raise ValidationError()\nreturn True",
                                "parameters": [{"name": "request"}]
                            },
                            {
                                "name": "execute",
                                "body": "result = self.repository.get_data()\nreturn process_result(result)",
                                "parameters": [{"name": "request"}]
                            }
                        ]
                    }
                ],
                "functions": [
                    {
                        "name": "process_result",
                        "body": "return result.transform()",
                        "parameters": [{"name": "result"}]
                    }
                ]
            }
        }
        
        # Create generator with mock code analyzer
        self.generator = ProcessViewGenerator(
            ai_provider=self.mock_provider,
            code_analyzer=self.mock_code_analyzer,
            file_reader=self.file_reader,
            file_hasher=self.file_hasher,
            cache_provider=self.cache
        )
        
        # Mock file paths
        self.controller_file = Path("/test/controller.py")
        self.service_file = Path("/test/service.py")
    
    def test_generate_sequence_diagram(self):
        """Test generation of sequence diagrams."""
        # Mock the trace_method_calls method to avoid complex implementation testing
        with patch.object(self.generator, '_trace_method_calls'):
            # Generate diagram
            result = self.generator.generate_sequence_diagram(
                [self.controller_file, self.service_file],
                entry_point="controller.Controller.process_request",
                title="Test Sequence Diagram"
            )
            
            # Verify result structure
            self.assertEqual(result["title"], "Test Sequence Diagram")
            self.assertEqual(result["diagram_type"], "sequence")
            self.assertEqual(result["syntax_type"], "mermaid")
            
            # Check diagram content
            self.assertIn("sequenceDiagram", result["content"])
            
            # Verify components and statistics
            self.assertTrue(len(result["components"]) > 0)
            self.assertEqual(self.generator.stats["sequence_diagrams_generated"], 1)
    
    @patch("file_analyzer.doc_generator.process_view_generator.ProcessViewGenerator._generate_activity_diagram_with_ai")
    def test_generate_activity_diagram(self, mock_ai_diagram):
        """Test generation of activity diagrams using AI."""
        # Setup mock AI response
        mock_ai_diagram.return_value = {
            "title": "Test Activity Diagram",
            "diagram_type": "activity",
            "syntax_type": "mermaid",
            "content": "flowchart TD\n    Start([Start]) --> Process[Process]\n    Process --> Condition{Condition?}\n    Condition -->|Yes| Yes[Process Yes]\n    Condition -->|No| No[Process No]\n    Yes --> End([End])\n    No --> End",
            "activities": ["Start", "Process", "Condition", "Yes", "No", "End"],
            "flows": [{"from": "Start", "to": "Process"}, {"from": "Process", "to": "Condition"}],
            "metadata": {"decision_points": 2, "code_length": 10}
        }
        
        # Mock file reading
        self.file_reader.read_file.return_value = """
        def process_data(data):
            if data.is_valid():
                result = transform(data)
                return result
            else:
                log_error("Invalid data")
                return None
        """
        
        # Generate diagram
        result = self.generator.generate_activity_diagram(
            self.controller_file,
            function_name="process_data",
            title="Test Activity Diagram"
        )
        
        # Verify result
        self.assertEqual(result["diagram_type"], "activity")
        self.assertEqual(result["syntax_type"], "mermaid")
        self.assertIn("flowchart TD", result["content"])
        
        # Verify AI was called correctly
        mock_ai_diagram.assert_called_once()
        
        # Verify stats
        self.assertEqual(self.generator.stats["activity_diagrams_generated"], 1)
    
    def test_generate_diagram(self):
        """Test the generate_diagram method."""
        # Mock the specific generator methods
        self.generator.generate_sequence_diagram = MagicMock(return_value={"diagram_type": "sequence"})
        self.generator.generate_activity_diagram = MagicMock(return_value={"diagram_type": "activity"})
        
        # Test sequence diagram
        result = self.generator.generate_diagram([self.controller_file], "sequence")
        self.assertEqual(result["diagram_type"], "sequence")
        self.generator.generate_sequence_diagram.assert_called_once()
        
        # Test activity diagram with single file
        result = self.generator.generate_diagram([self.controller_file], "activity")
        self.assertEqual(result["diagram_type"], "activity")
        self.generator.generate_activity_diagram.assert_called_once()
        
        # Test activity diagram with multiple files (should raise error)
        with self.assertRaises(ValueError):
            self.generator.generate_diagram([self.controller_file, self.service_file], "activity")
        
        # Test invalid diagram type
        with self.assertRaises(ValueError):
            self.generator.generate_diagram([self.controller_file], "invalid_type")
    
    def test_create_fallback_activity_diagram(self):
        """Test creation of fallback activity diagrams."""
        # Sample code with various control structures
        code = """
        def complex_function(data):
            if data.is_valid():
                for item in data.items:
                    try:
                        process_item(item)
                    except Exception as e:
                        log_error(e)
                return True
            else:
                return False
        """
        
        # Generate fallback diagram
        diagram = self.generator._create_fallback_activity_diagram(code, "complex_function")
        
        # Verify diagram structure
        self.assertIn("flowchart TD", diagram)
        self.assertIn("Start([Start])", diagram)
        self.assertIn("End([End])", diagram)
        
        # Check for detection of control structures
        self.assertIn("Condition", diagram)  # Should detect if statement
        self.assertIn("Loop", diagram)       # Should detect for loop
        self.assertIn("Try", diagram)        # Should detect try/except
    
    def test_get_stats(self):
        """Test retrieving statistics."""
        # Mock the methods to avoid actual execution
        self.generator.generate_sequence_diagram = MagicMock()
        self.generator.generate_activity_diagram = MagicMock()
        
        # Update stats manually to test retrieval
        self.generator.stats["sequence_diagrams_generated"] = 3
        self.generator.stats["activity_diagrams_generated"] = 2
        self.generator.stats["function_calls_traced"] = 15
        self.generator.stats["decision_points"] = 8
        
        # Get stats
        stats = self.generator.get_stats()
        
        # Verify stats
        self.assertEqual(stats["sequence_diagrams_generated"], 3)
        self.assertEqual(stats["activity_diagrams_generated"], 2)
        self.assertEqual(stats["function_calls_traced"], 15)
        self.assertEqual(stats["decision_points"], 8)

if __name__ == '__main__':
    unittest.main()