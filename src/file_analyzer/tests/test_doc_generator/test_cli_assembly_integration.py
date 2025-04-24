"""
Tests for CLI integration with DocumentationAssembler.

This module tests the integration of the CLI with DocumentationAssembler
for final documentation assembly.
"""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from file_analyzer.doc_generator.cli import main


class TestCliAssemblyIntegration:
    """Test suite for CLI integration with DocumentationAssembler."""
    
    @pytest.fixture
    def mock_repo_scanner(self):
        """Mock repository scanner for testing."""
        with patch("file_analyzer.doc_generator.cli.RepositoryScanner") as mock_scanner:
            scanner_instance = MagicMock()
            scanner_instance.scan.return_value = {
                "repo_path": "/test/repo",
                "file_results": {
                    "/test/repo/file1.py": {
                        "path": "/test/repo/file1.py",
                        "type": "python",
                        "metadata": {
                            "imports": [],
                            "functions": []
                        }
                    }
                },
                "frameworks": []
            }
            mock_scanner.return_value = scanner_instance
            yield mock_scanner
    
    @pytest.fixture
    def mock_generate_documentation(self):
        """Mock documentation generator."""
        with patch("file_analyzer.doc_generator.cli.generate_documentation") as mock_generate:
            mock_generate.return_value = {
                "total_files": 1,
                "documentation_files_generated": 1,
                "skipped_files": 0,
                "index_files": 1
            }
            yield mock_generate
    
    def test_cli_with_assembly(self, mock_repo_scanner, mock_generate_documentation, monkeypatch):
        """Test CLI with documentation assembly enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "docs")
            
            # Mock command-line arguments
            test_args = [
                "file_analyzer.doc_generator.cli",
                "/test/repo",
                "--output-dir", output_dir,
                "--final-assembly"
            ]
            monkeypatch.setattr("sys.argv", test_args)
            
            # Mock the DocumentationAssembler classes
            mock_assembler = MagicMock()
            mock_assembler.assemble_documentation.return_value = {
                "success": True,
                "files_processed": 5,
                "errors": []
            }
            mock_assembler.generate_readme.return_value = "/test/output/assembled/README.md"
            
            mock_assembler_class = MagicMock()
            mock_assembler_class.return_value = mock_assembler
            
            # Run the CLI
            with patch("file_analyzer.doc_generator.cli.DocumentationStructureManager"), \
                 patch("file_analyzer.doc_generator.cli.DocumentationNavigationManager"), \
                 patch("file_analyzer.doc_generator.documentation_assembler.DocumentationAssembler", mock_assembler_class), \
                 patch("file_analyzer.doc_generator.documentation_assembler.AssemblyConfig"):
                main()
            
            # Check that the assembler was called
            mock_assembler_class.assert_called_once()
            mock_assembler.assemble_documentation.assert_called_once()
            mock_assembler.generate_readme.assert_called_once()
    
    def test_cli_assembly_options(self, mock_repo_scanner, mock_generate_documentation, monkeypatch):
        """Test CLI with various assembly options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "docs")
            custom_assembly_dir = os.path.join(tmpdir, "custom_assembled")
            
            # Mock command-line arguments with assembly options
            test_args = [
                "file_analyzer.doc_generator.cli",
                "/test/repo",
                "--output-dir", output_dir,
                "--final-assembly",
                "--assembly-output-dir", custom_assembly_dir,
                "--no-self-contained",
                "--no-validate",
                "--no-optimize",
                "--no-readme",
                "--assembly-format", "html"
            ]
            monkeypatch.setattr("sys.argv", test_args)
            
            # Mock the DocumentationAssembler class
            with patch("file_analyzer.doc_generator.cli.DocumentationStructureManager"), \
                 patch("file_analyzer.doc_generator.cli.DocumentationNavigationManager"), \
                 patch("file_analyzer.doc_generator.documentation_assembler.DocumentationAssembler") as mock_assembler_class:
                
                # Run the CLI
                main()
                
                # Check that the assembler was called
                mock_assembler_class.assert_called_once()
                
                # Get the AssemblyConfig that was used
                config = mock_assembler_class.call_args[0][0]
                
                # Verify the config values reflect the CLI arguments
                assert config.output_dir == custom_assembly_dir
                assert config.self_contained is False
                assert config.validate_output is False
                assert config.optimize_output is False
                assert config.include_readme is False
                assert config.output_format == "html"
    
    def test_cli_without_assembly(self, mock_repo_scanner, mock_generate_documentation, monkeypatch):
        """Test CLI without documentation assembly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "docs")
            
            # Mock command-line arguments without assembly option
            test_args = [
                "file_analyzer.doc_generator.cli",
                "/test/repo",
                "--output-dir", output_dir
            ]
            monkeypatch.setattr("sys.argv", test_args)
            
            # Mock the DocumentationAssembler class
            mock_assembler_class = MagicMock()
            
            # Run the CLI
            with patch("file_analyzer.doc_generator.cli.DocumentationStructureManager"), \
                 patch("file_analyzer.doc_generator.cli.DocumentationNavigationManager"), \
                 patch("file_analyzer.doc_generator.documentation_assembler.DocumentationAssembler", mock_assembler_class):
                main()
            
            # Verify that DocumentationAssembler was not called
            mock_assembler_class.assert_not_called()