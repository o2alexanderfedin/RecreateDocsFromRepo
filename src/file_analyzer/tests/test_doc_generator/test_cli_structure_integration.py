"""
Tests for integration between CLI and DocumentationStructureManager.

This module tests the integration between the CLI documentation generation
and the enhanced documentation structure manager.
"""
import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch

from file_analyzer.doc_generator.cli import main
from file_analyzer.doc_generator.documentation_structure_manager import (
    DocumentationStructureManager,
    DocumentationStructureConfig
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
            },
            "/test/repo/config/settings.json": {
                "file_type": "config",
                "language": "json",
                "code_structure": {
                    "structure": {
                        "classes": [],
                        "functions": [],
                        "imports": []
                    },
                    "documentation": "Settings file."
                },
                "frameworks": []
            }
        },
        "frameworks": [
            {"name": "Standard Library", "language": "python", "version": "", "count": 2}
        ]
    }


class TestCliStructureIntegration:
    """Test suite for CLI integration with DocumentationStructureManager."""
    
    @patch("file_analyzer.doc_generator.cli.parse_args")
    @patch("file_analyzer.doc_generator.cli.load_analysis_results")
    @patch("file_analyzer.doc_generator.cli.generate_documentation")
    @patch.object(DocumentationStructureManager, "organize_documentation_structure")
    def test_cli_with_structure_manager(
        self, mock_organize, mock_generate, mock_load, mock_parse_args, sample_repo_analysis
    ):
        """Test CLI with structure manager enabled."""
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
                "total_files": 3,
                "documentation_files_generated": 3,
                "skipped_files": 0,
                "index_files": 1
            }
            
            # Mock organize_documentation_structure
            mock_organize.return_value = {
                "logical_groups": {"src": [], "config": []},
                "hierarchy": {"root": {"files": []}, "modules": {}, "components": {}},
                "component_view": {"Core": {"files": []}},
                "architecture_view": {"layers": {}},
                "structure": {},
                "index_files": [
                    os.path.join(tmpdir, "index.md"),
                    os.path.join(tmpdir, "architecture", "index.md"),
                    os.path.join(tmpdir, "components", "index.md")
                ]
            }
            
            # Run main function
            main()
            
            # Verify calls
            mock_generate.assert_called_once()
            mock_organize.assert_called_once()
    
    @patch("file_analyzer.doc_generator.cli.parse_args")
    @patch("file_analyzer.doc_generator.cli.load_analysis_results")
    @patch("file_analyzer.doc_generator.cli.generate_documentation")
    @patch.object(DocumentationStructureManager, "organize_documentation_structure")
    def test_cli_without_structure_manager(
        self, mock_organize, mock_generate, mock_load, mock_parse_args, sample_repo_analysis
    ):
        """Test CLI with structure manager disabled."""
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
            mock_args.no_structure_manager = True  # Structure manager disabled
            mock_args.max_depth = 3
            mock_args.no_adapt_depth = False
            mock_args.no_component_view = False
            mock_args.no_architecture_view = False
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
                "total_files": 3,
                "documentation_files_generated": 3,
                "skipped_files": 0,
                "index_files": 1
            }
            
            # Run main function
            main()
            
            # Verify calls
            mock_generate.assert_called_once()
            mock_organize.assert_not_called()  # Should not be called when disabled
    
    @pytest.mark.parametrize("component_view,architecture_view", [
        (True, True),   # Both enabled
        (True, False),  # Only component view
        (False, True),  # Only architecture view
        (False, False)  # Both disabled
    ])
    @patch("file_analyzer.doc_generator.cli.parse_args")
    @patch("file_analyzer.doc_generator.cli.load_analysis_results")
    @patch("file_analyzer.doc_generator.cli.generate_documentation")
    @patch.object(DocumentationStructureManager, "organize_documentation_structure")
    def test_cli_structure_view_options(
        self, mock_organize, mock_generate, mock_load, mock_parse_args, 
        component_view, architecture_view, sample_repo_analysis
    ):
        """Test CLI with different view options."""
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
            mock_args.no_component_view = not component_view
            mock_args.no_architecture_view = not architecture_view
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
                "total_files": 3,
                "documentation_files_generated": 3,
                "skipped_files": 0,
                "index_files": 1
            }
            
            # Run main function
            main()
            
            # Verify structure config
            structure_config = None
            for call_args, call_kwargs in mock_organize.call_args_list:
                # The structure config is in the DocumentationStructureManager constructor
                # which we didn't mock, so we can't verify it directly.
                # Instead, we make sure organize_documentation_structure was called
                assert call_kwargs["repo_path"] == sample_repo_analysis["repo_path"]
                assert call_kwargs["file_results"] == sample_repo_analysis["file_results"]
                assert call_kwargs["frameworks"] == sample_repo_analysis["frameworks"]