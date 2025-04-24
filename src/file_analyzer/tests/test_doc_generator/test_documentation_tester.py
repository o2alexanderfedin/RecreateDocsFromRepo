"""
Tests for the documentation testing system.

This module tests functionality for verifying documentation quality and correctness.
"""
import os
import unittest
from unittest.mock import MagicMock, patch, mock_open

from file_analyzer.doc_generator.documentation_tester import (
    DocumentationTester,
    run_documentation_test,
    DocumentationTestResult,
    DocumentationQualityCheck,
)


class TestDocumentationTester(unittest.TestCase):
    """Test case for the documentation testing system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tester = DocumentationTester()
        
        # Sample documentation content
        self.good_doc = """# example.py

## Table of Contents

- [Description](#description)
- [Purpose](#purpose)
- [Usage Examples](#usage-examples)
- [Key Components](#key-components)

## Description

This is a sample description with proper formatting.

## Purpose

This file provides utility functions for testing.

## Usage Examples

```python
from example import test_function

result = test_function()
```

## Key Components

| Component | Description |
|-----------|-------------|
| test_function | A function that does testing |
| TestClass | A class for advanced testing |
"""

        self.poor_doc = """# example.py

Some text without proper sections.

## Usage

No code examples provided.
"""

        self.broken_doc = """# example.py

## Table of Contents

- [Description](#description)
- [Broken Link](#nonexistent)

## Description

This has a broken link: [Missing](#nowhere)
"""

    def test_check_required_sections(self):
        """Test checking for required documentation sections."""
        # Test with good documentation
        result = self.tester.check_required_sections(self.good_doc)
        self.assertTrue(result.passed)
        self.assertEqual(len(result.issues), 0)
        
        # Test with missing sections
        result = self.tester.check_required_sections(self.poor_doc)
        self.assertFalse(result.passed)
        self.assertGreater(len(result.issues), 0)
        
    def test_check_broken_links(self):
        """Test checking for broken internal links."""
        # Test with good documentation
        result = self.tester.check_broken_links(self.good_doc)
        self.assertTrue(result.passed)
        
        # Test with broken links
        result = self.tester.check_broken_links(self.broken_doc)
        self.assertFalse(result.passed)
        self.assertGreater(len(result.issues), 0)
        
    def test_check_code_blocks(self):
        """Test checking for proper code blocks."""
        # Test with proper code blocks
        result = self.tester.check_code_blocks(self.good_doc)
        self.assertTrue(result.passed)
        
        # Test with missing code blocks
        result = self.tester.check_code_blocks(self.poor_doc)
        self.assertFalse(result.passed)
    
    def test_check_table_formatting(self):
        """Test checking for proper table formatting."""
        # Test with proper tables
        result = self.tester.check_table_formatting(self.good_doc)
        self.assertTrue(result.passed)
        
        # Test with missing tables
        result = self.tester.check_table_formatting(self.poor_doc)
        self.assertFalse(result.passed)
    
    def test_measure_documentation_quality(self):
        """Test measuring overall documentation quality."""
        # Test with good documentation
        result = self.tester.measure_documentation_quality(self.good_doc)
        self.assertGreaterEqual(result.quality_score, 8.0)  # Good score (out of 10)
        
        # Test with poor documentation
        result = self.tester.measure_documentation_quality(self.poor_doc)
        self.assertLess(result.quality_score, 5.0)  # Poor score
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_test_documentation_file(self, mock_file, mock_exists):
        """Test testing a documentation file."""
        # Setup mocks
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = self.good_doc
        
        # Test good documentation file
        file_path = "/path/to/docs/example.py.md"
        result = self.tester.test_documentation_file(file_path)
        self.assertTrue(result.passed)
        
        # Test with poor documentation
        mock_file.return_value.read.return_value = self.poor_doc
        result = self.tester.test_documentation_file(file_path)
        self.assertFalse(result.passed)
    
    @patch('os.walk')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_test_documentation_directory(self, mock_file, mock_exists, mock_walk):
        """Test testing a directory of documentation."""
        # Setup mocks
        mock_exists.return_value = True
        mock_walk.return_value = [
            ("/path/to/docs", [], ["file1.md", "file2.md"])
        ]
        mock_file.return_value.read.side_effect = [self.good_doc, self.poor_doc]
        
        # Test directory
        dir_path = "/path/to/docs"
        results = self.tester.test_documentation_directory(dir_path)
        
        # Should have two files
        self.assertEqual(len(results), 2)
        # First should pass, second should fail
        self.assertTrue(results[0].passed)
        self.assertFalse(results[1].passed)
    
    def test_generate_test_report(self):
        """Test generating a test report."""
        # Create some test results
        results = [
            DocumentationTestResult(
                file_path="/path/to/docs/good.md",
                passed=True,
                quality_score=9.5,
                issues=[]
            ),
            DocumentationTestResult(
                file_path="/path/to/docs/poor.md",
                passed=False,
                quality_score=4.0,
                issues=["Missing required sections", "No code examples"]
            )
        ]
        
        report = self.tester.generate_test_report(results)
        
        # Check if report contains expected content
        self.assertIn("Documentation Test Report", report)
        self.assertIn("good.md", report)
        self.assertIn("poor.md", report)
        self.assertIn("Missing required sections", report)
        
    def test_convenience_function(self):
        """Test the convenience function for documentation testing."""
        with patch('file_analyzer.doc_generator.documentation_tester.DocumentationTester.test_documentation_directory') as mock_test:
            # Setup mock
            mock_test.return_value = [
                DocumentationTestResult(
                    file_path="/path/to/docs/file.md",
                    passed=True,
                    quality_score=9.0,
                    issues=[]
                )
            ]
            
            # Call convenience function
            results = run_documentation_test("/path/to/docs")
            
            # Verify results
            self.assertEqual(len(results), 1)
            self.assertTrue(results[0].passed)


if __name__ == '__main__':
    unittest.main()