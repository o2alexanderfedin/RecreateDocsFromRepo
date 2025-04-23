"""
Documentation generator module.

This module provides functionality to generate Markdown documentation
from repository analysis results.
"""
from file_analyzer.doc_generator.markdown_generator import (
    MarkdownGenerator, DocumentationConfig, generate_documentation
)

__all__ = ['MarkdownGenerator', 'DocumentationConfig', 'generate_documentation']