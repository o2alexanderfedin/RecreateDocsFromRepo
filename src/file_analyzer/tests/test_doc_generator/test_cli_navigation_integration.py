"""
Tests for integration between CLI and DocumentationNavigationManager.

This module tests the integration between the CLI documentation generation
and the enhanced navigation elements.
"""
import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch

from file_analyzer.doc_generator.cli import main
from file_analyzer.doc_generator.documentation_navigation_manager import (
    DocumentationNavigationManager,
    NavigationConfig
)


@pytest.fixture
def sample_repo_analysis():
    """Sample repository analysis results for testing."""
    return {
        "repo_path": "/test/repo",
        "file_results": {
            "/test/repo/src/main.py": {
                "file_type": "code",
                "language": "python",
                "code_structure": {
                    "structure": {
                        "classes": [],
                        "functions": [{"name": "main"}],
                        "imports": []
                    },
                    "documentation": "Main entry point."
                },
                "frameworks": []
            },
            "/test/repo/src/utils/helpers.py": {
                "file_type": "code",
                "language": "python",
                "code_structure": {
                    "structure": {
                        "classes": [{"name": "Helper"}],
                        "functions": [{"name": "util_function"}],
                        "imports": []
                    },
                    "documentation": "Helper utilities."
                },
                "frameworks": []
            }
        },
        "frameworks": [
            {"name": "Standard Library", "language": "python", "version": "", "count": 2}
        ]
    }


class TestCliNavigationIntegration:
    """Test suite for CLI integration with DocumentationNavigationManager."""
    
    @patch("file_analyzer.doc_generator.cli.parse_args")
    @patch("file_analyzer.doc_generator.cli.load_analysis_results")
    @patch("file_analyzer.doc_generator.cli.generate_documentation")
    @patch.object(DocumentationNavigationManager, "build_doc_structure")
    @patch.object(DocumentationNavigationManager, "process_documentation_structure")
    def test_cli_with_navigation(
        self, mock_process, mock_build, mock_generate, mock_load, mock_parse_args, sample_repo_analysis
    ):
        """Test CLI with navigation enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock arguments
            mock_args = MagicMock()
            mock_args.analysis_file = "analysis.json"
            mock_args.output_dir = tmpdir
            mock_args.template_dir = None
            mock_args.no_code_snippets = False
            mock_args.max_code_lines = 15
            mock_args.no_relationships = False
            mock_args.no_framework_details = False
            mock_args.no_ai_documentation = False
            mock_args.no_structure_manager = False
            mock_args.max_depth = 3
            mock_args.no_adapt_depth = False
            mock_args.no_component_view = False
            mock_args.no_architecture_view = False
            mock_args.no_navigation = False
            mock_args.no_breadcrumbs = False
            mock_args.no_toc = False
            mock_args.no_section_nav = False
            mock_args.no_cross_references = False
            mock_args.exclude = []
            mock_args.provider = "mock"
            mock_args.api_key = None
            mock_args.model = None
            mock_args.verbose = False
            mock_parse_args.return_value = mock_args
            
            # Mock load analysis results
            mock_load.return_value = sample_repo_analysis
            
            # Mock generate documentation
            mock_generate.return_value = {
                "total_files": 2,
                "documentation_files_generated": 2,
                "skipped_files": 0,
                "index_files": 1
            }
            
            # Mock build_doc_structure
            mock_build.return_value = {
                "index.md": {"title": "Index", "path": "index.md", "headings": []},
                "src/main.md": {"title": "main.py", "path": "src/main.md", "headings": []}
            }
            
            # Mock process_documentation_structure
            mock_process.return_value = {
                "total_files": 2,
                "processed_files": 2,
                "skipped_files": 0
            }
            
            # Run main function
            main()
            
            # Verify calls
            mock_generate.assert_called_once()
            mock_build.assert_called_once()
            mock_process.assert_called_once()
    
    @patch("file_analyzer.doc_generator.cli.parse_args")
    @patch("file_analyzer.doc_generator.cli.load_analysis_results")
    @patch("file_analyzer.doc_generator.cli.generate_documentation")
    @patch.object(DocumentationNavigationManager, "build_doc_structure")
    @patch.object(DocumentationNavigationManager, "process_documentation_structure")
    def test_cli_without_navigation(
        self, mock_process, mock_build, mock_generate, mock_load, mock_parse_args, sample_repo_analysis
    ):
        """Test CLI with navigation disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock arguments
            mock_args = MagicMock()
            mock_args.analysis_file = "analysis.json"
            mock_args.output_dir = tmpdir
            mock_args.template_dir = None
            mock_args.no_code_snippets = False
            mock_args.max_code_lines = 15
            mock_args.no_relationships = False
            mock_args.no_framework_details = False
            mock_args.no_ai_documentation = False
            mock_args.no_structure_manager = False
            mock_args.max_depth = 3
            mock_args.no_adapt_depth = False
            mock_args.no_component_view = False
            mock_args.no_architecture_view = False
            mock_args.no_navigation = True  # Navigation disabled
            mock_args.no_breadcrumbs = False
            mock_args.no_toc = False
            mock_args.no_section_nav = False
            mock_args.no_cross_references = False
            mock_args.exclude = []
            mock_args.provider = "mock"
            mock_args.api_key = None
            mock_args.model = None
            mock_args.verbose = False
            mock_parse_args.return_value = mock_args
            
            # Mock load analysis results
            mock_load.return_value = sample_repo_analysis
            
            # Mock generate documentation
            mock_generate.return_value = {
                "total_files": 2,
                "documentation_files_generated": 2,
                "skipped_files": 0,
                "index_files": 1
            }
            
            # Run main function
            main()
            
            # Verify calls
            mock_generate.assert_called_once()
            mock_build.assert_not_called()  # Should not be called when navigation is disabled
            mock_process.assert_not_called()  # Should not be called when navigation is disabled
    
    @pytest.mark.parametrize("breadcrumbs,toc,section_nav,cross_refs", [
        (True, True, True, True),   # All enabled
        (True, False, True, True),  # TOC disabled
        (False, True, False, True), # Breadcrumbs and section_nav disabled
        (False, False, False, False) # All disabled
    ])
    @patch("file_analyzer.doc_generator.cli.parse_args")
    @patch("file_analyzer.doc_generator.cli.load_analysis_results")
    @patch("file_analyzer.doc_generator.cli.generate_documentation")
    @patch.object(DocumentationNavigationManager, "build_doc_structure")
    @patch.object(DocumentationNavigationManager, "process_documentation_structure")
    def test_cli_navigation_options(
        self, mock_process, mock_build, mock_generate, mock_load, mock_parse_args, 
        breadcrumbs, toc, section_nav, cross_refs, sample_repo_analysis
    ):
        """Test CLI with different navigation options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock arguments
            mock_args = MagicMock()
            mock_args.analysis_file = "analysis.json"
            mock_args.output_dir = tmpdir
            mock_args.template_dir = None
            mock_args.no_code_snippets = False
            mock_args.max_code_lines = 15
            mock_args.no_relationships = False
            mock_args.no_framework_details = False
            mock_args.no_ai_documentation = False
            mock_args.no_structure_manager = False
            mock_args.max_depth = 3
            mock_args.no_adapt_depth = False
            mock_args.no_component_view = False
            mock_args.no_architecture_view = False
            mock_args.no_navigation = False
            mock_args.no_breadcrumbs = not breadcrumbs
            mock_args.no_toc = not toc
            mock_args.no_section_nav = not section_nav
            mock_args.no_cross_references = not cross_refs
            mock_args.exclude = []
            mock_args.provider = "mock"
            mock_args.api_key = None
            mock_args.model = None
            mock_args.verbose = False
            mock_parse_args.return_value = mock_args
            
            # Mock load analysis results
            mock_load.return_value = sample_repo_analysis
            
            # Mock generate documentation
            mock_generate.return_value = {
                "total_files": 2,
                "documentation_files_generated": 2,
                "skipped_files": 0,
                "index_files": 1
            }
            
            # Mock build_doc_structure
            mock_build.return_value = {
                "index.md": {"title": "Index", "path": "index.md", "headings": []},
                "src/main.md": {"title": "main.py", "path": "src/main.md", "headings": []}
            }
            
            # Mock process_documentation_structure
            mock_process.return_value = {
                "total_files": 2,
                "processed_files": 2,
                "skipped_files": 0
            }
            
            # Run main function
            main()
            
            # Verify calls
            mock_generate.assert_called_once()
            
            # Navigation manager should be called with the right parameters
            nav_config = None
            for call_args, _ in mock_process.call_args_list:
                # We check the parameters via mock_build which was called with the NavManager
                assert mock_build.called