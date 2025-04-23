"""
Tests for the Markdown formatter module.

This module tests the functionality for formatting AI-generated
documentation into well-structured Markdown.
"""
import os
import unittest
from unittest.mock import MagicMock, patch

from file_analyzer.doc_generator.markdown_formatter import (
    MarkdownFormatter,
    format_documentation,
    create_toc,
    sanitize_markdown,
    create_anchor_link
)


class TestMarkdownFormatter(unittest.TestCase):
    """Test the MarkdownFormatter class and related functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.formatter = MarkdownFormatter()
        
        # Sample AI-generated documentation dictionary
        self.sample_doc = {
            "description": "This is a sample description with some *formatting*.",
            "purpose": "The purpose of this file is to demonstrate markdown formatting.",
            "usage_examples": [
                "```python\nfrom example import function\n\nresult = function()\n```",
                "Another example with `inline code`"
            ],
            "key_components": [
                {"name": "Component1", "description": "Description of component 1"},
                {"name": "Component2", "description": "Description of component 2"}
            ],
            "main_concepts": ["Concept 1", "Concept 2"],
            "architecture_notes": "Architecture notes with <script>alert('xss')</script>"
        }
        
    def test_format_documentation(self):
        """Test formatting complete documentation."""
        file_path = "/path/to/example.py"
        
        formatted = self.formatter.format_documentation(file_path, self.sample_doc)
        
        # Check that basic structure is present
        self.assertIn("# example.py", formatted)
        self.assertIn("## Description", formatted)
        self.assertIn("## Purpose", formatted)
        self.assertIn("## Usage Examples", formatted)
        self.assertIn("## Key Components", formatted)
        self.assertIn("## Main Concepts", formatted)
        self.assertIn("## Architecture Notes", formatted)
        
        # Check that code blocks are preserved
        self.assertIn("```python", formatted)
        self.assertIn("from example import function", formatted)
        
        # Check that TOC is generated
        self.assertIn("## Table of Contents", formatted)
        self.assertIn("- [Description](#description)", formatted)
        
    def test_create_toc(self):
        """Test table of contents generation."""
        sections = ["Description", "Purpose", "Usage Examples"]
        toc = create_toc(sections)
        
        # Check that TOC contains links to all sections
        for section in sections:
            anchor = create_anchor_link(section)
            self.assertIn(f"- [{section}](#{anchor})", toc)
    
    def test_sanitize_markdown(self):
        """Test markdown sanitization."""
        # Test HTML sanitization
        unsafe = "Text with <script>alert('xss')</script> and <img src=x onerror=alert('XSS')>"
        safe = sanitize_markdown(unsafe)
        self.assertNotIn("<script>", safe)
        self.assertNotIn("onerror=", safe)
        
        # Test that legitimate markdown is preserved
        markdown = "# Heading\n**Bold** and *italic* with `code`"
        sanitized = sanitize_markdown(markdown)
        self.assertEqual(markdown, sanitized)
        
        # Test code block preservation
        code_block = "```python\nprint('hello')\n```"
        sanitized_code = sanitize_markdown(code_block)
        self.assertEqual(code_block, sanitized_code)
    
    def test_create_anchor_link(self):
        """Test anchor link creation."""
        # Test regular text
        self.assertEqual("description", create_anchor_link("Description"))
        
        # Test text with spaces and punctuation
        self.assertEqual("usage-examples", create_anchor_link("Usage Examples"))
        self.assertEqual("why-how", create_anchor_link("Why & How?"))
        
        # Test with unicode characters
        self.assertEqual("section-", create_anchor_link("Section §"))


if __name__ == "__main__":
    unittest.main()