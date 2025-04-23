"""
Unit tests for the RepositoryScanner class.
"""
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

from file_analyzer.core.file_type_analyzer import FileTypeAnalyzer
from file_analyzer.ai_providers.mock_provider import MockAIProvider
from file_analyzer.core.cache_provider import InMemoryCache
from file_analyzer.repo_scanner import RepositoryScanner
from file_analyzer.utils.exceptions import FileAnalyzerError


class TestRepositoryScanner:
    """Unit tests for the RepositoryScanner class."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a file type analyzer with a mock provider."""
        return FileTypeAnalyzer(
            ai_provider=MockAIProvider(),
            cache_provider=InMemoryCache()
        )
    
    @pytest.fixture
    def scanner(self, analyzer):
        """Create a repository scanner with a mock analyzer."""
        return RepositoryScanner(analyzer=analyzer)
    
    def test_init_with_defaults(self, analyzer):
        """Test initialization with default values."""
        # Act
        scanner = RepositoryScanner(analyzer=analyzer)
        
        # Assert
        assert scanner.analyzer == analyzer
        assert scanner.exclusions == RepositoryScanner.DEFAULT_EXCLUSIONS
        assert scanner.max_file_size == RepositoryScanner.DEFAULT_MAX_FILE_SIZE
        assert scanner.concurrency == 5
        assert scanner.batch_size == 10
        assert scanner.priority_patterns == RepositoryScanner.PRIORITY_PATTERNS
        assert scanner.progress_callback is None
        
    def test_init_with_custom_values(self, analyzer):
        """Test initialization with custom values."""
        # Arrange
        exclusions = ["*.log", "tmp/"]
        max_file_size = 5 * 1024 * 1024
        concurrency = 10
        batch_size = 20
        priority_patterns = ["*.py", "*.ts"]
        progress_callback = lambda x, y: None
        
        # Act
        scanner = RepositoryScanner(
            analyzer=analyzer,
            exclusions=exclusions,
            max_file_size=max_file_size,
            concurrency=concurrency,
            batch_size=batch_size,
            priority_patterns=priority_patterns,
            progress_callback=progress_callback
        )
        
        # Assert
        assert scanner.analyzer == analyzer
        assert len(scanner.exclusions) > len(RepositoryScanner.DEFAULT_EXCLUSIONS)
        assert all(exc in scanner.exclusions for exc in exclusions)
        assert scanner.max_file_size == max_file_size
        assert scanner.concurrency == concurrency
        assert scanner.batch_size == batch_size
        assert scanner.priority_patterns == priority_patterns
        assert scanner.progress_callback == progress_callback
    
    def test_discover_files(self, scanner):
        """Test file discovery in a repository."""
        # Arrange - Create a temp directory with nested structure
        with tempfile.TemporaryDirectory() as tempdir:
            # Create directories including excluded ones
            os.makedirs(os.path.join(tempdir, "src"))
            os.makedirs(os.path.join(tempdir, "docs"))
            os.makedirs(os.path.join(tempdir, ".git"))
            os.makedirs(os.path.join(tempdir, "node_modules"))
            
            # Create files in src/
            with open(os.path.join(tempdir, "src", "main.py"), "w") as f:
                f.write("print('hello')")
            with open(os.path.join(tempdir, "src", "util.py"), "w") as f:
                f.write("def util(): pass")
                
            # Create files in docs/
            with open(os.path.join(tempdir, "docs", "index.md"), "w") as f:
                f.write("# Documentation")
                
            # Create files in root
            with open(os.path.join(tempdir, "README.md"), "w") as f:
                f.write("# Project")
            with open(os.path.join(tempdir, ".gitignore"), "w") as f:
                f.write("*.pyc\n__pycache__/")
                
            # Create file in excluded directory (should be skipped)
            with open(os.path.join(tempdir, ".git", "HEAD"), "w") as f:
                f.write("ref: refs/heads/main")
            with open(os.path.join(tempdir, "node_modules", "package.json"), "w") as f:
                f.write('{"name": "test"}')
            
            # Act
            discovered_files = scanner._discover_files(Path(tempdir))
            
            # Assert
            # Should find 5 files (excluding .git and node_modules dirs)
            assert len(discovered_files) == 5
            
            # Check individual files
            paths = [str(f) for f in discovered_files]
            assert any(p.endswith("src/main.py") for p in paths)
            assert any(p.endswith("src/util.py") for p in paths)
            assert any(p.endswith("docs/index.md") for p in paths)
            assert any(p.endswith("README.md") for p in paths)
            assert any(p.endswith(".gitignore") for p in paths)
            
            # Should NOT find files in excluded directories
            assert not any(".git/" in p or "/.git/" in p for p in paths)
            assert not any("node_modules/" in p or "/node_modules/" in p for p in paths)
    
    def test_filter_files(self, scanner):
        """Test file filtering and prioritization."""
        # Arrange
        with tempfile.TemporaryDirectory() as tempdir:
            repo_path = Path(tempdir)
            
            # Create files of different types/sizes
            files = [
                # Priority files
                repo_path / "README.md",
                repo_path / "setup.py",
                repo_path / "src" / "main.py",
                # Regular files
                repo_path / "LICENSE",
                repo_path / "requirements.txt",
                # Files to exclude
                repo_path / "large_file.bin",  # Will be made large
                repo_path / "image.jpg",  # Excluded by extension
            ]
            
            # Create parent directories
            (repo_path / "src").mkdir(exist_ok=True)
            
            # Write content to files
            for file_path in files:
                file_path.parent.mkdir(exist_ok=True)
                file_path.write_text("test content")
            
            # Make one file exceed the size limit
            with open(repo_path / "large_file.bin", "wb") as f:
                f.seek(scanner.max_file_size + 1)
                f.write(b"\0")
            
            # Act
            filtered_files = scanner._filter_files(files, repo_path)
            
            # Assert
            assert len(filtered_files) == 5  # Should exclude 2 files
            
            # Extract paths and priorities
            paths_and_priorities = [(str(path), priority) for path, priority in filtered_files]
            paths = [p[0] for p in paths_and_priorities]
            priorities = [p[1] for p in paths_and_priorities]
            
            # Check if excluded files are not in the result
            assert not any("large_file.bin" in p for p in paths)
            assert not any("image.jpg" in p for p in paths)
            
            # Check priorities - README, setup.py and main.py should be prioritized
            high_priority_files = [p for p, prio in paths_and_priorities if prio]
            assert len(high_priority_files) == 3
            assert any("README.md" in p for p in high_priority_files)
            assert any("setup.py" in p for p in high_priority_files)
            assert any("main.py" in p for p in high_priority_files)
            
            # Check that priorities come first in the list
            assert all(priorities[:3])
            assert not any(priorities[3:])
    
    def test_analyze_files(self, scanner):
        """Test file analysis logic."""
        # Arrange
        with tempfile.TemporaryDirectory() as tempdir:
            repo_path = Path(tempdir)
            
            # Create a few files
            py_file = repo_path / "test.py"
            py_file.write_text("def test(): pass")
            
            md_file = repo_path / "README.md"
            md_file.write_text("# Test")
            
            # Create files list with priorities
            files = [
                (py_file, True),
                (md_file, False)
            ]
            
            # Create a mock progress callback
            mock_callback = MagicMock()
            scanner.progress_callback = mock_callback
            
            # Act
            results = scanner._analyze_files(files, repo_path)
            
            # Assert
            assert len(results) == 2
            
            # Check that both files were analyzed
            assert "test.py" in results
            assert "README.md" in results
            
            # Verify Python file analysis
            assert results["test.py"]["language"].lower() == "python"
            assert results["test.py"]["file_type"].lower() == "code"
            
            # Verify Markdown file analysis
            assert results["README.md"]["language"].lower() == "markdown"
            assert results["README.md"]["file_type"].lower() == "documentation"
            
            # Verify progress callback was called
            assert mock_callback.call_count == 2
            mock_callback.assert_any_call(1, 2)
            mock_callback.assert_any_call(2, 2)
    
    def test_scan_repository(self, scanner):
        """Test the complete repository scanning flow."""
        # Arrange - Create a simple repository
        with tempfile.TemporaryDirectory() as tempdir:
            repo_path = Path(tempdir)
            
            # Create directories
            (repo_path / "src").mkdir()
            (repo_path / "docs").mkdir()
            
            # Create files
            (repo_path / "src" / "main.py").write_text("def main(): pass")
            (repo_path / "docs" / "index.md").write_text("# Documentation")
            (repo_path / "README.md").write_text("# Project")
            (repo_path / ".gitignore").write_text("*.pyc")
            
            # Act
            result = scanner.scan_repository(repo_path)
            
            # Assert
            assert "repository" in result
            assert "analysis_results" in result
            assert "statistics" in result
            
            # Check analysis results
            analysis = result["analysis_results"]
            assert len(analysis) == 4
            
            # Verify specific files
            assert "src/main.py" in analysis
            assert "docs/index.md" in analysis
            assert "README.md" in analysis
            assert ".gitignore" in analysis
            
            # Check stats
            stats = result["statistics"]
            assert stats["total_files"] >= 4
            assert stats["analyzed_files"] == 4
            assert stats["error_files"] == 0
            assert "python" in stats["languages"] or "Python" in stats["languages"]
            assert "markdown" in stats["languages"] or "Markdown" in stats["languages"]
            
    def test_scan_repository_nonexistent_path(self, scanner):
        """Test scanning a nonexistent repository path."""
        # Arrange
        nonexistent_path = "/path/that/does/not/exist"
        
        # Act & Assert
        with pytest.raises(FileAnalyzerError):
            scanner.scan_repository(nonexistent_path)
    
    @pytest.mark.asyncio
    async def test_analyze_files_async(self, scanner):
        """Test asynchronous file analysis."""
        # Arrange
        with tempfile.TemporaryDirectory() as tempdir:
            repo_path = Path(tempdir)
            
            # Create test files
            files = []
            for i in range(5):
                file_path = repo_path / f"file{i}.py"
                file_path.write_text(f"# Test file {i}")
                files.append((file_path, i % 2 == 0))  # Every even file is priority
            
            # Configure scanner for testing
            scanner.batch_size = 2
            scanner.concurrency = 2
            
            # Act
            results = await scanner._analyze_files_async(files, repo_path)
            
            # Assert
            assert len(results) == 5
            for i in range(5):
                assert f"file{i}.py" in results
                assert results[f"file{i}.py"]["language"].lower() == "python"
    
    @pytest.mark.asyncio
    async def test_scan_repository_async(self, scanner):
        """Test the complete asynchronous repository scanning flow."""
        # Arrange - Create a simple repository
        with tempfile.TemporaryDirectory() as tempdir:
            repo_path = Path(tempdir)
            
            # Create directories
            (repo_path / "src").mkdir()
            (repo_path / "docs").mkdir()
            
            # Create files
            (repo_path / "src" / "main.py").write_text("def main(): pass")
            (repo_path / "docs" / "index.md").write_text("# Documentation")
            (repo_path / "README.md").write_text("# Project")
            (repo_path / ".gitignore").write_text("*.pyc")
            
            # Act
            result = await scanner.scan_repository_async(repo_path)
            
            # Assert
            assert "repository" in result
            assert "analysis_results" in result
            assert "statistics" in result
            
            # Check analysis results
            analysis = result["analysis_results"]
            assert len(analysis) == 4
            
            # Verify specific files
            assert "src/main.py" in analysis
            assert "docs/index.md" in analysis
            assert "README.md" in analysis
            assert ".gitignore" in analysis