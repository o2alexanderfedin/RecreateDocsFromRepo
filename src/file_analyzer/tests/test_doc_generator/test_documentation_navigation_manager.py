"""
Tests for the DocumentationNavigationManager class.

This module tests the functionality for creating navigation elements within
documentation including table of contents, breadcrumbs, cross-references,
and section navigation.
"""
import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch

from file_analyzer.doc_generator.documentation_navigation_manager import (
    DocumentationNavigationManager,
    NavigationConfig
)

class TestNavigationConfig:
    """Test suite for NavigationConfig."""
    
    def test_init_with_defaults(self):
        """Test initialization with default values."""
        config = NavigationConfig(output_dir="/tmp/docs")
        
        assert config.output_dir == "/tmp/docs"
        assert config.include_breadcrumbs is True
        assert config.include_toc is True
        assert config.include_section_nav is True
        assert config.include_cross_references is True
        assert config.include_footer_nav is True
        assert config.max_toc_depth == 3
        assert config.max_breadcrumb_segments == 5
    
    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        config = NavigationConfig(
            output_dir="/tmp/docs",
            include_breadcrumbs=False,
            include_toc=False,
            include_section_nav=False,
            include_cross_references=False,
            include_footer_nav=False,
            max_toc_depth=2,
            max_breadcrumb_segments=3,
            navigation_templates_dir="/custom/templates"
        )
        
        assert config.output_dir == "/tmp/docs"
        assert config.include_breadcrumbs is False
        assert config.include_toc is False
        assert config.include_section_nav is False
        assert config.include_cross_references is False
        assert config.include_footer_nav is False
        assert config.max_toc_depth == 2
        assert config.max_breadcrumb_segments == 3
        assert config.navigation_templates_dir == "/custom/templates"


class TestDocumentationNavigationManager:
    """Test suite for DocumentationNavigationManager."""
    
    @pytest.fixture
    def sample_doc_structure(self):
        """Sample documentation structure for testing."""
        return {
            "index.md": {
                "title": "Repository Documentation",
                "path": "index.md",
                "headings": [
                    {"level": 1, "text": "Repository Documentation"},
                    {"level": 2, "text": "Overview"},
                    {"level": 2, "text": "Modules"},
                    {"level": 2, "text": "Key Files"}
                ],
                "children": ["src/index.md", "config/index.md"]
            },
            "src/index.md": {
                "title": "Source Code",
                "path": "src/index.md",
                "headings": [
                    {"level": 1, "text": "Source Code"},
                    {"level": 2, "text": "Overview"},
                    {"level": 2, "text": "Files"}
                ],
                "children": ["src/main.md", "src/utils.md"],
                "parent": "index.md"
            },
            "src/main.md": {
                "title": "main.py",
                "path": "src/main.md",
                "headings": [
                    {"level": 1, "text": "main.py"},
                    {"level": 2, "text": "Description"},
                    {"level": 2, "text": "Usage"},
                    {"level": 2, "text": "Functions"}
                ],
                "parent": "src/index.md",
                "related_files": ["src/utils.md"]
            },
            "src/utils.md": {
                "title": "utils.py",
                "path": "src/utils.md",
                "headings": [
                    {"level": 1, "text": "utils.py"},
                    {"level": 2, "text": "Description"},
                    {"level": 2, "text": "Classes"},
                    {"level": 2, "text": "Functions"}
                ],
                "parent": "src/index.md",
                "related_files": ["src/main.md"]
            },
            "config/index.md": {
                "title": "Configuration",
                "path": "config/index.md",
                "headings": [
                    {"level": 1, "text": "Configuration"},
                    {"level": 2, "text": "Overview"},
                    {"level": 2, "text": "Files"}
                ],
                "children": ["config/settings.md"],
                "parent": "index.md"
            },
            "config/settings.md": {
                "title": "settings.json",
                "path": "config/settings.md",
                "headings": [
                    {"level": 1, "text": "settings.json"},
                    {"level": 2, "text": "Description"},
                    {"level": 2, "text": "Configuration Options"}
                ],
                "parent": "config/index.md"
            }
        }
    
    @pytest.fixture
    def sample_doc_content(self):
        """Sample document content for testing."""
        return {
            "src/main.md": "# main.py\n\n## Description\n\nMain entry point for the application.\n\n## Usage\n\n```python\npython main.py --config settings.json\n```\n\n## Functions\n\n- `main()`: Entry point function\n- `parse_args()`: Parse command line arguments\n"
        }
    
    def test_init(self):
        """Test initialization of DocumentationNavigationManager."""
        config = NavigationConfig(output_dir="/tmp/docs")
        manager = DocumentationNavigationManager(config)
        
        assert manager.config.output_dir == "/tmp/docs"
        assert manager.config.include_breadcrumbs is True
    
    def test_generate_toc(self, sample_doc_structure):
        """Test generation of table of contents."""
        config = NavigationConfig(output_dir="/tmp/docs")
        manager = DocumentationNavigationManager(config)
        
        document = sample_doc_structure["src/main.md"]
        toc = manager.generate_toc(document)
        
        assert "## Table of Contents" in toc
        assert "- [Description](#description)" in toc
        assert "- [Usage](#usage)" in toc
        assert "- [Functions](#functions)" in toc
    
    def test_generate_breadcrumbs(self, sample_doc_structure):
        """Test generation of breadcrumb navigation."""
        config = NavigationConfig(output_dir="/tmp/docs")
        manager = DocumentationNavigationManager(config)
        
        document = sample_doc_structure["src/main.md"]
        breadcrumbs = manager.generate_breadcrumbs(document, sample_doc_structure)
        
        assert "Repository Documentation" in breadcrumbs
        assert "Source Code" in breadcrumbs
        assert "main.py" in breadcrumbs
        assert "Repository Documentation" in breadcrumbs
        assert "Source Code" in breadcrumbs
    
    def test_generate_section_navigation(self, sample_doc_structure):
        """Test generation of section navigation."""
        config = NavigationConfig(output_dir="/tmp/docs")
        manager = DocumentationNavigationManager(config)
        
        document = sample_doc_structure["src/main.md"]
        section_nav = manager.generate_section_navigation(document)
        
        assert "Description" in section_nav
        assert "Usage" in section_nav
        assert "Functions" in section_nav
    
    def test_generate_cross_references(self, sample_doc_structure):
        """Test generation of cross-references."""
        config = NavigationConfig(output_dir="/tmp/docs")
        manager = DocumentationNavigationManager(config)
        
        document = sample_doc_structure["src/main.md"]
        cross_references = manager.generate_cross_references(document, sample_doc_structure)
        
        assert "Related Files" in cross_references
        assert "utils.py" in cross_references
        assert "[utils.py](utils.md)" in cross_references
    
    def test_generate_header_footer(self, sample_doc_structure):
        """Test generation of header and footer navigation."""
        config = NavigationConfig(output_dir="/tmp/docs")
        manager = DocumentationNavigationManager(config)
        
        document = sample_doc_structure["src/main.md"]
        header, footer = manager.generate_header_footer(document, sample_doc_structure)
        
        assert "Navigation" in header or "Navigation" in footer
        assert "Home" in footer
    
    def test_add_navigation_to_document(self, sample_doc_content, sample_doc_structure):
        """Test adding navigation elements to a document."""
        config = NavigationConfig(output_dir="/tmp/docs")
        manager = DocumentationNavigationManager(config)
        
        doc_path = "src/main.md"
        content = sample_doc_content[doc_path]
        document = sample_doc_structure[doc_path]
        
        result = manager.add_navigation_to_document(content, document, sample_doc_structure)
        
        assert "Table of Contents" in result
        assert "Description" in result
        assert "Usage" in result
        assert "Functions" in result
        assert "Navigation" in result or "Breadcrumbs" in result
    
    def test_disabled_navigation_elements(self, sample_doc_content, sample_doc_structure):
        """Test disabling specific navigation elements."""
        config = NavigationConfig(
            output_dir="/tmp/docs",
            include_breadcrumbs=False,
            include_toc=False
        )
        manager = DocumentationNavigationManager(config)
        
        doc_path = "src/main.md"
        content = sample_doc_content[doc_path]
        document = sample_doc_structure[doc_path]
        
        result = manager.add_navigation_to_document(content, document, sample_doc_structure)
        
        assert "Table of Contents" not in result
        assert "Breadcrumbs" not in result
        assert "Description" in result  # Original content still there
    
    def test_process_documentation_structure(self, sample_doc_structure, sample_doc_content):
        """Test processing full documentation structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = NavigationConfig(output_dir=tmpdir)
            manager = DocumentationNavigationManager(config)
            
            # Create a test document file
            doc_path = os.path.join(tmpdir, "src/main.md")
            os.makedirs(os.path.dirname(doc_path), exist_ok=True)
            with open(doc_path, "w") as f:
                f.write(sample_doc_content["src/main.md"])
            
            # Process the document
            mock_structure = {
                "file_path": doc_path,
                "metadata": sample_doc_structure["src/main.md"]
            }
            
            result = manager.process_documentation_structure([mock_structure], sample_doc_structure)
            
            assert result["total_files"] == 1
            assert result["processed_files"] == 1
            assert os.path.exists(doc_path)
            
            # Check the content of the processed file
            with open(doc_path, "r") as f:
                content = f.read()
                assert "Table of Contents" in content
                assert "Navigation" in content or "Breadcrumbs" in content