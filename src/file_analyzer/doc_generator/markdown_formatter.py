"""
Markdown formatter for AI-generated documentation.

This module provides functionality to format AI-generated documentation
into well-structured, consistent Markdown files with proper styling and
cross-references.
"""
import os
import re
import logging
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger("file_analyzer.doc_generator.markdown_formatter")

class MarkdownFormatter:
    """
    Formats AI-generated documentation into well-structured Markdown.
    
    This class ensures consistent formatting, proper headings, code blocks,
    tables, and cross-references according to GitHub Flavored Markdown specs.
    """
    
    def __init__(self):
        """Initialize the Markdown formatter."""
        self.default_sections = [
            "Description",
            "Purpose",
            "Usage Examples",
            "Key Components",
            "Main Concepts",
            "Architecture Notes"
        ]
    
    def format_documentation(
        self, 
        file_path: str, 
        doc_data: Dict[str, Any]
    ) -> str:
        """
        Format AI-generated documentation into a Markdown string.
        
        Args:
            file_path: Path to the file being documented
            doc_data: AI-generated documentation dictionary
            
        Returns:
            Formatted Markdown string
        """
        # Extract file name for title
        file_name = os.path.basename(file_path)
        
        # Start with the title
        markdown = f"# {file_name}\n\n"
        
        # Create table of contents with available sections
        available_sections = []
        for section in self.default_sections:
            section_key = section.lower().replace(" ", "_")
            if section_key in doc_data or section == "Key Components" and "key_components" in doc_data:
                available_sections.append(section)
                
        # Add table of contents
        markdown += "## Table of Contents\n\n"
        markdown += create_toc(available_sections)
        markdown += "\n\n"
        
        # Add each section
        for section in self.default_sections:
            section_key = section.lower().replace(" ", "_")
            
            # Skip sections that don't have content
            if section_key not in doc_data and not (section == "Key Components" and "key_components" in doc_data):
                continue
                
            # Create section heading with anchor
            markdown += f"## {section}\n\n"
            
            # Format section content based on type
            if section == "Usage Examples":
                # Format code examples
                examples = doc_data.get("usage_examples", [])
                for example in examples:
                    markdown += f"{example}\n\n"
            
            elif section == "Key Components":
                # Format components as a list or table
                components = doc_data.get("key_components", [])
                if components:
                    # Create a table for components
                    markdown += "| Component | Description |\n"
                    markdown += "|-----------|-------------|\n"
                    
                    for component in components:
                        name = component.get("name", "")
                        description = component.get("description", "")
                        
                        # Sanitize table cell content (remove newlines, pipes)
                        name = name.replace("\n", " ").replace("|", "\\|")
                        description = description.replace("\n", " ").replace("|", "\\|")
                        
                        markdown += f"| {name} | {description} |\n"
                    
                    markdown += "\n"
            
            elif section == "Main Concepts":
                # Format concepts as a list
                concepts = doc_data.get("main_concepts", [])
                for concept in concepts:
                    markdown += f"- {concept}\n"
                markdown += "\n"
            
            else:
                # Regular text content
                content = doc_data.get(section_key, "")
                if content:
                    # Sanitize content
                    content = sanitize_markdown(content)
                    markdown += f"{content}\n\n"
        
        return markdown


def format_documentation(
    file_path: str,
    doc_data: Dict[str, Any]
) -> str:
    """
    Format AI-generated documentation into a Markdown string.
    
    This is a convenience function that creates a MarkdownFormatter
    and formats documentation in one step.
    
    Args:
        file_path: Path to the file being documented
        doc_data: AI-generated documentation dictionary
        
    Returns:
        Formatted Markdown string
    """
    formatter = MarkdownFormatter()
    return formatter.format_documentation(file_path, doc_data)


def create_toc(sections: List[str]) -> str:
    """
    Create a table of contents with links to sections.
    
    Args:
        sections: List of section names
        
    Returns:
        Markdown table of contents
    """
    toc = ""
    for section in sections:
        anchor = create_anchor_link(section)
        toc += f"- [{section}](#{anchor})\n"
    return toc


def sanitize_markdown(content: str) -> str:
    """
    Sanitize Markdown content for security and consistency.
    
    Args:
        content: Markdown content to sanitize
        
    Returns:
        Sanitized Markdown
    """
    # Remove potentially dangerous HTML tags
    content = re.sub(r'<script.*?>.*?</script>', '', content, flags=re.DOTALL)
    content = re.sub(r'<iframe.*?>.*?</iframe>', '', content, flags=re.DOTALL)
    content = re.sub(r'<style.*?>.*?</style>', '', content, flags=re.DOTALL)
    
    # Remove all on* event handlers - more comprehensive pattern
    content = re.sub(r'\s(on\w+)(\s*=\s*["\'][^"\']*["\'])', ' ', content, flags=re.IGNORECASE)
    content = re.sub(r'\s(on\w+)(\s*=\s*[^\s>]*)', ' ', content, flags=re.IGNORECASE)
    
    # Remove potentially dangerous HTML tags completely
    dangerous_tags = ['script', 'iframe', 'object', 'embed', 'svg']
    for tag in dangerous_tags:
        content = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(f'<{tag}[^>]*/?>', '', content, flags=re.IGNORECASE)
    
    # More comprehensive approach to remove dangerous HTML attributes
    dangerous_attrs = ['onerror', 'onload', 'onclick', 'onmouseover', 'onblur', 'onchange',
                      'onfocus', 'onscroll', 'onsubmit']
    
    # Use more aggressive pattern to remove event handlers
    for attr in dangerous_attrs:
        content = re.sub(f'\\s{attr}\\s*=\\s*["\'][^"\']*["\']', ' ', content, flags=re.IGNORECASE)
        content = re.sub(f'\\s{attr}\\s*=\\s*[^\\s>]*', ' ', content, flags=re.IGNORECASE)
    
    # Remove entire img tags with onerror attributes as a last resort
    content = re.sub(r'<img\s+[^>]*onerror\s*=\s*[^>]*>', '', content, flags=re.IGNORECASE)
    
    # Fix common Markdown issues
    
    # Ensure blank line before headings for proper parsing
    content = re.sub(r'(\S)(\n#+\s+)', r'\1\n\n\2', content)
    
    # Ensure proper spacing for list items
    content = re.sub(r'(\n)([*+-])\s+', r'\1\2 ', content)
    
    return content


def create_anchor_link(text: str) -> str:
    """
    Create an anchor link from text.
    
    Follows GitHub Flavored Markdown format:
    - Lowercase all letters
    - Replace spaces with hyphens
    - Remove characters that are not alphanumeric, hyphen, or underscore
    
    Args:
        text: Text to create anchor from
        
    Returns:
        Anchor link string
    """
    # Convert to lowercase
    anchor = text.lower()
    
    # Replace spaces with hyphens
    anchor = anchor.replace(" ", "-")
    
    # Remove non-alphanumeric characters (except hyphens and underscores)
    anchor = re.sub(r'[^\w-]', '', anchor)
    
    # Fix duplicate hyphens (caused by replacing special chars with nothing)
    anchor = re.sub(r'-+', '-', anchor)
    
    return anchor