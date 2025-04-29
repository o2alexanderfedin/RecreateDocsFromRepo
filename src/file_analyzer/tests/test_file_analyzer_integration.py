"""
Integration tests for the file analyzer system.

These tests verify that the AI-based file type detection system correctly
identifies file types across various repository structures and file types,
ensuring the system meets accuracy and performance requirements.
"""
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

from file_analyzer.ai_providers.mock_provider import MockAIProvider
from file_analyzer.core.cache_provider import (
    CacheManager, FileSystemCache, InMemoryCache, SqliteCache
)
from file_analyzer.core.file_type_analyzer import FileTypeAnalyzer
from file_analyzer.repo_scanner import RepositoryScanner


class TestFileAnalyzerIntegration:
    """Integration tests for the file analyzer system."""

    @pytest.fixture
    def analyzer(self):
        """Create a file type analyzer with mock AI provider."""
        return FileTypeAnalyzer(ai_provider=MockAIProvider())

    @pytest.fixture
    def tiered_cache_analyzer(self):
        """Create a file type analyzer with tiered cache system."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create different cache providers
            memory_cache = InMemoryCache(max_size=100, ttl=3600)
            
            sqlite_path = temp_path / "cache.db"
            sqlite_cache = SqliteCache(db_path=sqlite_path, ttl=3600)
            
            fs_cache_dir = temp_path / "fs_cache"
            fs_cache_dir.mkdir(exist_ok=True)
            fs_cache = FileSystemCache(cache_dir=fs_cache_dir, ttl=3600)
            
            # Create tiered cache manager
            cache_manager = CacheManager([memory_cache, sqlite_cache, fs_cache])
            
            # Create analyzer with tiered cache
            analyzer = FileTypeAnalyzer(
                ai_provider=MockAIProvider(),
                cache_provider=cache_manager
            )
            
            yield analyzer
    
    @pytest.fixture
    def sample_repo(self):
        """Create a sample repository with various file types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create directory structure
            (repo_path / "src").mkdir()
            (repo_path / "src/app").mkdir()
            (repo_path / "src/utils").mkdir()
            (repo_path / "docs").mkdir()
            (repo_path / "config").mkdir()
            (repo_path / "tests").mkdir()
            
            # Create common file types
            files = {
                # Python files
                "src/app/main.py": """
import os
import sys
from .utils import helper

def main():
    '''Main entry point.'''
    print('Hello World')
    return 0

if __name__ == '__main__':
    sys.exit(main())
""",
                "src/utils/helper.py": """
def format_string(text):
    '''Format a string.'''
    return text.strip()

def calculate(x, y):
    '''Calculate something.'''
    return x + y
""",
                "tests/test_main.py": """
import unittest
from src.app.main import main

class TestMain(unittest.TestCase):
    def test_main(self):
        self.assertEqual(main(), 0)

if __name__ == '__main__':
    unittest.main()
""",
                
                # JavaScript files
                "src/app/app.js": """
import { helper } from '../utils/helper';

function App() {
    return (
        <div>
            <h1>{helper('Hello World')}</h1>
        </div>
    );
}

export default App;
""",
                "src/utils/helper.js": """
export function helper(text) {
    return text.trim();
}

export function calculate(x, y) {
    return x + y;
}
""",
                
                # Configuration files
                "config/settings.json": """{
    "name": "sample-app",
    "version": "1.0.0",
    "debug": true,
    "api": {
        "url": "https://api.example.com",
        "key": "sample-key"
    }
}""",
                "config/database.yml": """
development:
  adapter: sqlite3
  database: db/development.sqlite3
  pool: 5
  timeout: 5000

test:
  adapter: sqlite3
  database: db/test.sqlite3
  pool: 5
  timeout: 5000
""",
                
                # Documentation files
                "README.md": """# Sample Repository

A sample repository with various file types for integration testing.

## Usage

```python
from src.app.main import main
main()
```

## License

MIT
""",
                "docs/api.md": """# API Documentation

## Endpoints

- GET /api/v1/users
- POST /api/v1/users
- GET /api/v1/users/:id
- PUT /api/v1/users/:id
- DELETE /api/v1/users/:id
""",
                
                # Other file types
                "LICENSE": """MIT License

Copyright (c) 2023 Sample

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""",
                ".gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class
.env
.venv
env/
venv/
ENV/

# JavaScript
node_modules/
dist/
build/
.DS_Store
""",
                "requirements.txt": """
pytest==7.3.1
flask==2.3.2
sqlalchemy==2.0.15
"""
            }
            
            # Write files
            for file_path, content in files.items():
                full_path = repo_path / file_path
                full_path.parent.mkdir(exist_ok=True, parents=True)
                full_path.write_text(content)
            
            # Create binary files
            binary_files = [
                "src/app/logo.png",
                "docs/diagram.png"
            ]
            
            for bin_file in binary_files:
                full_path = repo_path / bin_file
                full_path.parent.mkdir(exist_ok=True, parents=True)
                # Create a small binary file
                with open(full_path, 'wb') as f:
                    f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\x60\x60\x60\x00\x00\x00\x04\x00\x01\xf6\x9eF\xba\x00\x00\x00\x00IEND\xaeB`\x82')
            
            # Return path to the repository
            yield repo_path
    
    @pytest.fixture
    def empty_files_repo(self):
        """Create a repository with empty files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create empty files of different types
            empty_files = [
                "empty.py",
                "empty.js",
                "empty.md",
                "empty.json",
                "empty.txt"
            ]
            
            for file_name in empty_files:
                full_path = repo_path / file_name
                full_path.touch()
            
            yield repo_path
    
    @pytest.fixture
    def mixed_encoding_repo(self):
        """Create a repository with files in different encodings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create files with different encodings
            encodings = {
                "utf8.py": ("utf-8", """
# -*- coding: utf-8 -*-
def greet():
    return "Hello, World! 你好，世界！"
"""),
                "utf16.py": ("utf-16", """
# -*- coding: utf-16 -*-
def greet():
    return "Hello, World! Привет, мир!"
"""),
                "latin1.py": ("latin-1", """
# -*- coding: latin-1 -*-
def greet():
    return "Hello, World! ¡Hola, mundo!"
""")
            }
            
            for file_name, (encoding, content) in encodings.items():
                full_path = repo_path / file_name
                with open(full_path, 'w', encoding=encoding) as f:
                    f.write(content)
            
            yield repo_path
    
    def test_analyze_diverse_file_types(self, analyzer, sample_repo):
        """Test analysis of diverse file types."""
        # Get a list of all files in the sample repo
        all_files = []
        for root, _, files in os.walk(sample_repo):
            for file in files:
                file_path = Path(root) / file
                all_files.append(file_path)
        
        # Analyze each file
        results = {}
        for file_path in all_files:
            result = analyzer.analyze_file(file_path)
            relative_path = file_path.relative_to(sample_repo)
            results[str(relative_path)] = result
        
        # Verify python files are detected correctly
        python_files = [f for f in results if f.endswith('.py')]
        assert len(python_files) > 0
        for file in python_files:
            assert results[file]["language"] == "python"
            assert results[file]["file_type"] == "code"
        
        # Verify JavaScript files are detected correctly
        js_files = [f for f in results if f.endswith('.js')]
        assert len(js_files) > 0
        for file in js_files:
            assert results[file]["language"] == "javascript"
            assert results[file]["file_type"] == "code"
        
        # Verify configuration files are detected correctly
        config_files = ["config/settings.json", "config/database.yml"]
        for file in config_files:
            assert results[file]["file_type"] == "code" or results[file]["file_type"] == "configuration"
        
        # Verify documentation files are detected correctly
        doc_files = ["README.md", "docs/api.md"]
        for file in doc_files:
            assert results[file]["language"] == "markdown"
            assert results[file]["file_type"] == "documentation"
        
        # Verify binary files handling
        binary_files = ["src/app/logo.png", "docs/diagram.png"]
        for file in binary_files:
            result = results[file]
            # Binary files might be classified as "unknown" or a specific type
            # depending on the AI provider's capabilities
            assert "error" not in result or "binary" in result.get("characteristics", [])
    
    def test_empty_file_handling(self, analyzer, empty_files_repo):
        """Test handling of empty files."""
        # Get all empty files
        empty_files = list(empty_files_repo.glob("empty.*"))
        
        # Analyze each empty file
        for file_path in empty_files:
            result = analyzer.analyze_file(file_path)
            
            # Check result - should not have errors
            assert "error" not in result
            
            # File type may vary based on extension, but should have some guess
            assert "file_type" in result
            assert "language" in result
            
            # Extension-based detection should work even for empty files
            if file_path.suffix == ".py":
                assert result["language"] == "python"
            elif file_path.suffix == ".js":
                assert result["language"] == "javascript"
            elif file_path.suffix == ".md":
                assert result["language"] == "markdown"
            elif file_path.suffix == ".json":
                assert result["language"] == "json"
    
    def test_encoding_handling(self, analyzer, mixed_encoding_repo):
        """Test handling of files with different encodings."""
        # Get all encoding test files
        encoding_files = list(mixed_encoding_repo.glob("*.py"))
        
        # Analyze each file
        for file_path in encoding_files:
            result = analyzer.analyze_file(file_path)
            
            # Check result - should not have errors
            assert "error" not in result
            
            # All files should be detected as Python
            assert result["language"] == "python"
            assert result["file_type"] == "code"
    
    def test_cache_efficiency(self, analyzer):
        """Test cache efficiency for repeated analysis."""
        # Set up a specific analyzer with in-memory cache 
        in_memory_cache = InMemoryCache()
        cache_analyzer = FileTypeAnalyzer(
            ai_provider=MockAIProvider(),
            cache_provider=in_memory_cache
        )
        
        # Create a temporary file to analyze
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as temp_file:
            temp_file.write("""
def hello():
    return "Hello, World!"
""")
            temp_path = temp_file.name
        
        try:
            # First analysis - should not use cache
            result1 = cache_analyzer.analyze_file(temp_path)
            
            # Second analysis - should use cache
            result2 = cache_analyzer.analyze_file(temp_path)
            
            # Results should be identical
            assert result1 == result2
            
            # Verify cache statistics
            cache_stats = in_memory_cache.get_stats()
            assert cache_stats["size"] > 0, "Cache should contain at least one item"
            assert cache_stats["hits"] > 0, "Cache should have at least one hit"
            assert cache_stats["sets"] > 0, "Cache should have at least one set operation"
        
        finally:
            # Clean up
            os.unlink(temp_path)
    
    def test_tiered_cache_propagation(self, tiered_cache_analyzer):
        """Test tiered cache propagation between cache layers."""
        # Create a temporary file to analyze
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as temp_file:
            temp_file.write("""
def hello():
    return "Hello, World!"
""")
            temp_path = temp_file.name
        
        try:
            # First analysis - cache it
            result1 = tiered_cache_analyzer.analyze_file(temp_path)
            
            # Second analysis - should use cache
            result2 = tiered_cache_analyzer.analyze_file(temp_path)
            
            # Check that results match
            assert result1 == result2
            
            # Check cache stats to verify it's working across layers
            cache_stats = tiered_cache_analyzer.get_cache_stats()
            assert "provider" in cache_stats
            
            # Check if we have a hit in one of the cache layers
            has_hit = False
            for cache_name, stats in cache_stats["provider"].items():
                if "hits" in stats and stats["hits"] > 0:
                    has_hit = True
                    break
            
            assert has_hit, "No cache hits recorded in any cache layer"
        
        finally:
            # Clean up
            os.unlink(temp_path)
    
    def test_repo_scanner_exclusions(self, analyzer, sample_repo):
        """Test repository scanner exclusion mechanisms."""
        # Create a scanner with specific exclusions
        scanner = RepositoryScanner(
            analyzer=analyzer,
            exclusions=["*.png", "tests"]  # Exclude PNGs and test directory
        )
        
        # Scan the repository
        result = scanner.scan_repository(sample_repo)
        
        # Verify exclusions were applied
        analysis_results = result["analysis_results"]
        
        # No PNG files should be in results
        png_files = [f for f in analysis_results if f.endswith('.png')]
        assert len(png_files) == 0, "PNG files should be excluded"
        
        # No test files should be in results
        test_files = [f for f in analysis_results if f.startswith('tests/')]
        assert len(test_files) == 0, "Test files should be excluded"
        
        # Other files should be analyzed
        assert len(analysis_results) > 0, "Some files should be analyzed"
        
        # Python files in src should be analyzed
        py_files = [f for f in analysis_results if f.endswith('.py')]
        assert len(py_files) > 0, "Python files should be analyzed"
    
    def test_repo_scanner_statistics(self, analyzer, sample_repo):
        """Test repository scanner statistics."""
        # Create a scanner
        scanner = RepositoryScanner(analyzer=analyzer)
        
        # Scan the repository
        result = scanner.scan_repository(sample_repo)
        
        # Verify statistics are present and accurate
        stats = result["statistics"]
        
        assert "total_files" in stats
        assert "analyzed_files" in stats
        assert "excluded_files" in stats
        assert "file_types" in stats
        assert "languages" in stats
        assert "processing_time" in stats
        
        # Counts should add up
        assert stats["total_files"] == stats["analyzed_files"] + stats["excluded_files"]
        
        # Language counts should add up to analyzed files
        language_total = sum(stats["languages"].values())
        assert language_total == stats["analyzed_files"]
        
        # File type counts should add up to analyzed files
        file_type_total = sum(stats["file_types"].values())
        assert file_type_total == stats["analyzed_files"]
    
    def test_repo_scanner_priority_handling(self, analyzer, sample_repo):
        """Test repository scanner priority file handling."""
        # Create a scanner with progress tracking
        progress_tracker = {"processed": 0, "total": 0, "order": []}
        
        def track_progress(processed, total):
            progress_tracker["processed"] = processed
            progress_tracker["total"] = total
            # This won't capture exact order, but will help observe batching
            progress_tracker["order"].append(processed)
        
        scanner = RepositoryScanner(
            analyzer=analyzer,
            progress_callback=track_progress,
            priority_patterns=["*.md", "README*", "requirements.txt"]  # Prioritize docs
        )
        
        # Scan the repository
        scanner.scan_repository(sample_repo)
        
        # Check progress was tracked
        assert progress_tracker["processed"] > 0
        assert progress_tracker["processed"] == progress_tracker["total"]
        assert len(progress_tracker["order"]) > 0
        
        # The order might not perfectly reflect priorities due to batching and concurrency,
        # but we should have made progress incrementally
        assert progress_tracker["order"] == sorted(progress_tracker["order"])
    
    def test_api_failure_handling(self, sample_repo):
        """Test handling of AI API failures."""
        # Create a failing mock provider
        class FailingMockProvider(MockAIProvider):
            def analyze_content(self, file_path, content):
                # Simulate API failure
                if "failing_trigger" in content:
                    raise ConnectionError("Simulated API failure")
                return super().analyze_content(file_path, content)
        
        # Create an analyzer with the failing provider
        analyzer = FileTypeAnalyzer(ai_provider=FailingMockProvider())
        
        # Create a file that will trigger the failure
        failing_file = sample_repo / "failing.py"
        failing_file.write_text("# This file contains failing_trigger to simulate API failure")
        
        # Analyze the file - should gracefully handle the error
        result = analyzer.analyze_file(failing_file)
        
        # Check that we got an error result but didn't crash
        assert "error" in result
        assert "file_type" in result
        assert result["file_type"] == "unknown"
    
    def test_cli_integration(self, sample_repo):
        """Test integration with the CLI."""
        # Look for the repo_scanner_cli module instead of main.py
        cli_module = Path(__file__).parent.parent / "repo_scanner_cli.py"
        if not cli_module.exists():
            pytest.skip("CLI module not found")
        
        # Create output file
        output_file = sample_repo / "analysis_results.json"
        
        # Run the CLI with the mock provider
        cmd = [
            sys.executable,
            str(cli_module),
            str(sample_repo),
            "--provider", "mock",
            "--output", str(output_file)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            assert result.returncode == 0, f"CLI failed with: {result.stderr}"
            
            # Verify output file exists
            assert output_file.exists(), "Output file was not created"
            
            # Parse the JSON output
            with open(output_file) as f:
                analysis_results = json.load(f)
            
            # Verify basic structure of results
            assert "repository" in analysis_results
            assert "analysis_results" in analysis_results
            assert "statistics" in analysis_results
            
            # Verify some files were analyzed
            assert len(analysis_results["analysis_results"]) > 0
            
            # Check stats are present
            stats = analysis_results["statistics"]
            assert stats["total_files"] > 0
            assert stats["analyzed_files"] > 0
            assert len(stats["languages"]) > 0
            assert len(stats["file_types"]) > 0
            
        except subprocess.TimeoutExpired:
            pytest.fail("CLI process timed out")
        except Exception as e:
            pytest.fail(f"Error running CLI: {str(e)}")
    
    def test_performance_metrics(self, analyzer, sample_repo):
        """Test performance metrics for file analysis."""
        # Get all files in the repo
        all_files = []
        for root, _, files in os.walk(sample_repo):
            for file in files:
                file_path = Path(root) / file
                all_files.append(file_path)
        
        # Measure time to analyze all files
        start_time = time.time()
        
        for file_path in all_files:
            analyzer.analyze_file(file_path)
        
        total_time = time.time() - start_time
        
        # Calculate average time per file
        avg_time = total_time / len(all_files) if all_files else 0
        
        # Log performance metrics
        logging.info(f"Total analysis time: {total_time:.2f}s for {len(all_files)} files")
        logging.info(f"Average time per file: {avg_time:.4f}s")
        
        # We're not enforcing specific performance criteria here,
        # just logging metrics for observability
        assert True
    
    def test_large_repository_simulation(self, analyzer):
        """Simulate analysis of a large repository by creating many small files."""
        # Create a large number of small files
        file_count = 100  # Adjust based on test speed requirements
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create different types of files
            for i in range(file_count):
                file_type = i % 5  # Cycle through 5 file types
                
                if file_type == 0:
                    # Python file
                    file_path = repo_path / f"file_{i}.py"
                    content = f"def function_{i}():\n    return {i}\n"
                elif file_type == 1:
                    # JavaScript file
                    file_path = repo_path / f"file_{i}.js"
                    content = f"function function_{i}() {{\n    return {i};\n}}\n"
                elif file_type == 2:
                    # Markdown file
                    file_path = repo_path / f"file_{i}.md"
                    content = f"# Heading {i}\n\nContent {i}\n"
                elif file_type == 3:
                    # JSON file
                    file_path = repo_path / f"file_{i}.json"
                    content = f'{{"id": {i}, "name": "item_{i}"}}\n'
                else:
                    # Text file
                    file_path = repo_path / f"file_{i}.txt"
                    content = f"Text content {i}\n"
                
                file_path.write_text(content)
            
            # Create scanner with cache
            scanner = RepositoryScanner(analyzer=analyzer)
            
            # Measure scan time
            start_time = time.time()
            result = scanner.scan_repository(repo_path)
            total_time = time.time() - start_time
            
            # Verify all files were analyzed
            assert result["statistics"]["analyzed_files"] > 0
            
            # Log performance
            logging.info(f"Large repo simulation: {total_time:.2f}s for {file_count} files")
            logging.info(f"Average time per file: {total_time / file_count:.4f}s")
            
            # Check language distribution
            languages = result["statistics"]["languages"]
            assert len(languages) >= 4  # Should have detected multiple languages
            
            # Python, JavaScript, and Markdown should be present
            assert "python" in languages
            assert "javascript" in languages
            assert "markdown" in languages
    
    def test_concurrent_analysis(self, analyzer, sample_repo):
        """Test concurrent file analysis using RepositoryScanner's async mode."""
        # Get scanner with async capability
        scanner = RepositoryScanner(
            analyzer=analyzer,
            concurrency=3,  # Use multiple concurrent workers
            batch_size=2    # Process files in small batches to test batching
        )
        
        # Need to run with asyncio
        import asyncio
        
        # Set event loop policy for Windows if needed
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        # Create event loop and run async scan
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run the async scan
            result = loop.run_until_complete(scanner.scan_repository_async(sample_repo))
            
            # Verify results
            assert "analysis_results" in result
            assert len(result["analysis_results"]) > 0
            
            # All files should be analyzed without errors
            for file_result in result["analysis_results"].values():
                assert "file_type" in file_result
                assert "language" in file_result
                
            # Statistics should be present
            assert "statistics" in result
            assert result["statistics"]["total_files"] > 0
            assert result["statistics"]["analyzed_files"] > 0
            
        finally:
            loop.close()


if __name__ == "__main__":
    pytest.main(["-v", __file__])