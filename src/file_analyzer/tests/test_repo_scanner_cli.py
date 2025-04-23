"""
Unit tests for the Repository Scanner CLI.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from file_analyzer.repo_scanner_cli import main, create_analyzer


class TestRepoScannerCLI:
    """Unit tests for the Repository Scanner CLI."""
    
    def test_create_analyzer_mock(self):
        """Test creating a analyzer with mock provider."""
        # Act
        analyzer = create_analyzer("mock")
        
        # Assert
        assert analyzer is not None
        assert analyzer.ai_provider.__class__.__name__ == "MockAIProvider"
    
    @patch("os.environ.get")
    def test_create_analyzer_mistral_missing_key(self, mock_env_get):
        """Test handling missing Mistral API key."""
        # Arrange
        mock_env_get.return_value = None
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            create_analyzer("mistral")
        
        assert "MISTRAL_API_KEY" in str(exc_info.value)
    
    @patch("os.environ.get")
    def test_create_analyzer_openai_missing_key(self, mock_env_get):
        """Test handling missing OpenAI API key."""
        # Arrange
        mock_env_get.return_value = None
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            create_analyzer("openai")
        
        assert "OPENAI_API_KEY" in str(exc_info.value)
    
    def test_create_analyzer_unknown_provider(self):
        """Test handling unknown provider."""
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            create_analyzer("unknown")
        
        assert "Unknown provider" in str(exc_info.value)
    
    @patch("file_analyzer.repo_scanner_cli.create_analyzer")
    @patch("file_analyzer.repo_scanner_cli.RepositoryScanner")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_success(self, mock_parse_args, mock_scanner_class, mock_create_analyzer):
        """Test successful execution of main."""
        # Arrange
        mock_args = mock_parse_args.return_value
        mock_args.repo_path = "/path/to/repo"
        mock_args.provider = "mock"
        mock_args.api_key = None
        mock_args.output = None
        mock_args.use_async = False
        mock_args.exclude = []
        mock_args.max_size = 10 * 1024 * 1024
        mock_args.concurrency = 5
        mock_args.batch_size = 10
        mock_args.no_progress = True
        mock_args.verbose = False
        
        # Mock analyzer and scanner
        mock_analyzer = MagicMock()
        mock_scanner = MagicMock()
        mock_create_analyzer.return_value = mock_analyzer
        mock_scanner_class.return_value = mock_scanner
        
        # Mock scanner result
        mock_result = {
            "repository": "/path/to/repo",
            "analysis_results": {"file1.py": {"language": "python"}},
            "statistics": {
                "total_files": 10,
                "analyzed_files": 8,
                "excluded_files": 2,
                "error_files": 0,
                "processing_time": 1.5,
                "languages": {"python": 5, "markdown": 3},
                "file_types": {"code": 5, "documentation": 3}
            }
        }
        mock_scanner.scan_repository.return_value = mock_result
        
        # Patch Path.exists to return True
        with patch("pathlib.Path.exists", return_value=True):
            # Patch print to capture output
            with patch("builtins.print") as mock_print:
                # Act
                exit_code = main()
                
                # Assert
                assert exit_code == 0
                mock_create_analyzer.assert_called_once_with("mock", None)
                mock_scanner_class.assert_called_once()
                mock_scanner.scan_repository.assert_called_once()
                
                # Verify result is printed
                mock_print.assert_any_call(json.dumps(mock_result, indent=2))
    
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_nonexistent_path(self, mock_parse_args):
        """Test handling nonexistent repository path."""
        # Arrange
        mock_args = mock_parse_args.return_value
        mock_args.repo_path = "/path/that/does/not/exist"
        mock_args.provider = "mock"
        mock_args.verbose = False
        
        # Act
        with patch("pathlib.Path.exists", return_value=False):
            exit_code = main()
        
        # Assert
        assert exit_code == 1
    
    @patch("file_analyzer.repo_scanner_cli.create_analyzer")
    @patch("file_analyzer.repo_scanner_cli.RepositoryScanner")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_with_output_file(self, mock_parse_args, mock_scanner_class, mock_create_analyzer):
        """Test writing results to output file."""
        # Arrange
        mock_args = mock_parse_args.return_value
        mock_args.repo_path = "/path/to/repo"
        mock_args.provider = "mock"
        mock_args.api_key = None
        mock_args.output = "results.json"
        mock_args.use_async = False
        mock_args.exclude = []
        mock_args.max_size = 10 * 1024 * 1024
        mock_args.concurrency = 5
        mock_args.batch_size = 10
        mock_args.no_progress = True
        mock_args.verbose = False
        
        # Mock analyzer and scanner
        mock_analyzer = MagicMock()
        mock_scanner = MagicMock()
        mock_create_analyzer.return_value = mock_analyzer
        mock_scanner_class.return_value = mock_scanner
        
        # Mock scanner result
        mock_result = {
            "repository": "/path/to/repo",
            "analysis_results": {"file1.py": {"language": "python"}},
            "statistics": {
                "total_files": 10,
                "analyzed_files": 8,
                "excluded_files": 2,
                "error_files": 0,
                "processing_time": 1.5,
                "languages": {"python": 5, "markdown": 3},
                "file_types": {"code": 5, "documentation": 3}
            }
        }
        mock_scanner.scan_repository.return_value = mock_result
        
        # Act
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.mkdir"), patch("builtins.open") as mock_open:
                with patch("json.dump") as mock_json_dump:
                    exit_code = main()
        
        # Assert
        assert exit_code == 0
        mock_json_dump.assert_called_once_with(mock_result, mock_open.return_value.__enter__.return_value, indent=2)
    
    @patch("file_analyzer.repo_scanner_cli.create_analyzer")
    @patch("file_analyzer.repo_scanner_cli.RepositoryScanner")
    @patch("argparse.ArgumentParser.parse_args")
    @patch("asyncio.get_event_loop")
    def test_main_with_async(self, mock_get_loop, mock_parse_args, mock_scanner_class, mock_create_analyzer):
        """Test using asynchronous processing."""
        # Arrange
        mock_args = mock_parse_args.return_value
        mock_args.repo_path = "/path/to/repo"
        mock_args.provider = "mock"
        mock_args.api_key = None
        mock_args.output = None
        mock_args.use_async = True
        mock_args.exclude = []
        mock_args.max_size = 10 * 1024 * 1024
        mock_args.concurrency = 5
        mock_args.batch_size = 10
        mock_args.no_progress = True
        mock_args.verbose = False
        
        # Mock analyzer and scanner
        mock_analyzer = MagicMock()
        mock_scanner = MagicMock()
        mock_create_analyzer.return_value = mock_analyzer
        mock_scanner_class.return_value = mock_scanner
        
        # Mock event loop
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop
        
        # Mock scanner result
        mock_result = {
            "repository": "/path/to/repo",
            "analysis_results": {"file1.py": {"language": "python"}},
            "statistics": {
                "total_files": 10,
                "analyzed_files": 8,
                "excluded_files": 2,
                "error_files": 0,
                "processing_time": 1.5,
                "languages": {"python": 5, "markdown": 3},
                "file_types": {"code": 5, "documentation": 3}
            }
        }
        mock_loop.run_until_complete.return_value = mock_result
        
        # Act
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.print") as mock_print:
                exit_code = main()
        
        # Assert
        assert exit_code == 0
        mock_scanner.scan_repository_async.assert_called_once()
        mock_loop.run_until_complete.assert_called_once()