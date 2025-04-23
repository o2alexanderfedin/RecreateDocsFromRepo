"""
Unit tests for the code analyzer component.
"""
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import MagicMock

from file_analyzer.core.code_analyzer import CodeAnalyzer
from file_analyzer.core.file_type_analyzer import FileTypeAnalyzer
from file_analyzer.ai_providers.mock_provider import MockAIProvider
from file_analyzer.core.cache_provider import InMemoryCache
from file_analyzer.utils.exceptions import FileAnalyzerError


class TestCodeAnalyzer:
    """Tests for the CodeAnalyzer class."""
    
    @pytest.fixture
    def mock_provider(self):
        """Create a mock AI provider."""
        provider = MockAIProvider()
        
        # Mock the analyze_content method to return expected values
        provider.analyze_content = MagicMock(side_effect=provider.analyze_content)
        
        # Mock the analyze_code method to return expected values for tests
        # Note: We're not completely overriding the method, just mocking it for assertions
        original_analyze_code = provider.analyze_code
        provider.analyze_code = MagicMock(side_effect=original_analyze_code)
        
        return provider
    
    @pytest.fixture
    def analyzer(self, mock_provider):
        """Create a code analyzer with mock provider."""
        return CodeAnalyzer(
            ai_provider=mock_provider,
            cache_provider=InMemoryCache()
        )
    
    @pytest.fixture
    def test_files(self):
        """Create test files for different languages."""
        with tempfile.TemporaryDirectory() as tempdir:
            # Python file
            py_file = Path(tempdir) / "test.py"
            with open(py_file, "w") as f:
                f.write("""import os
import pathlib

TEST_VAR = "test"

class TestClass:
    \"\"\"Test class docstring.\"\"\"
    
    def __init__(self):
        self.prop1 = "test"
    
    def method1(self):
        \"\"\"Method 1 docstring.\"\"\"
        return True
    
    def method2(self, param):
        return param

def test_func(param1, param2):
    \"\"\"Test function docstring.\"\"\"
    return param1 + param2
""")
            
            # Java file
            java_file = Path(tempdir) / "Test.java"
            with open(java_file, "w") as f:
                f.write("""package com.example.test;

import java.util.List;
import java.util.ArrayList;

/**
 * Test class javadoc.
 */
public class Test {
    private String prop1;
    
    public Test() {
        this.prop1 = "test";
    }
    
    /**
     * Method 1 javadoc.
     */
    public boolean method1() {
        return true;
    }
    
    public String method2(String param) {
        return param;
    }
}
""")
            
            # JavaScript file
            js_file = Path(tempdir) / "test.js"
            with open(js_file, "w") as f:
                f.write("""import { something } from 'somewhere';
const fs = require('fs');

const TEST_VAR = 'test';

/**
 * Test class.
 */
class TestClass {
    constructor() {
        this.prop1 = 'test';
    }
    
    /**
     * Method 1.
     */
    method1() {
        return true;
    }
    
    method2(param) {
        return param;
    }
}

/**
 * Test function.
 */
function testFunc(param1, param2) {
    return param1 + param2;
}

// Arrow function
const arrowFunc = (x) => x * 2;

export { TestClass, testFunc };
""")
            
            # TypeScript file
            ts_file = Path(tempdir) / "test.ts"
            with open(ts_file, "w") as f:
                f.write("""import { Something } from 'somewhere';

interface TestInterface {
    prop1: string;
    method1(): boolean;
}

type TestType = string | number;

const TEST_VAR: string = 'test';

/**
 * Test class.
 */
class TestClass implements TestInterface {
    prop1: string;
    
    constructor() {
        this.prop1 = 'test';
    }
    
    /**
     * Method 1.
     */
    method1(): boolean {
        return true;
    }
    
    method2(param: string): string {
        return param;
    }
}

/**
 * Test function.
 */
function testFunc(param1: string, param2: string): string {
    return param1 + param2;
}

// Arrow function
const arrowFunc = (x: number): number => x * 2;

export { TestClass, testFunc };
""")
            
            # Non-code file (Markdown)
            md_file = Path(tempdir) / "README.md"
            with open(md_file, "w") as f:
                f.write("""# Test

This is a test file.
""")
            
            yield {
                "py": py_file,
                "java": java_file,
                "js": js_file,
                "ts": ts_file,
                "md": md_file
            }
    
    def test_init(self, mock_provider):
        """Test initialization of code analyzer."""
        # Arrange & Act
        analyzer = CodeAnalyzer(ai_provider=mock_provider)
        
        # Assert
        assert analyzer.ai_provider == mock_provider
        assert analyzer.file_type_analyzer is not None
        assert analyzer.file_reader is not None
        assert analyzer.file_hasher is not None
        assert analyzer.cache_provider is None
        assert analyzer.stats == {
            "analyzed_files": 0,
            "supported_files": 0,
            "unsupported_files": 0,
            "chunked_files": 0,
            "error_files": 0,
        }
    
    def test_init_with_file_type_analyzer(self, mock_provider):
        """Test initialization with provided file type analyzer."""
        # Arrange
        file_type_analyzer = FileTypeAnalyzer(ai_provider=mock_provider)
        
        # Act
        analyzer = CodeAnalyzer(
            ai_provider=mock_provider,
            file_type_analyzer=file_type_analyzer
        )
        
        # Assert
        assert analyzer.file_type_analyzer == file_type_analyzer
    
    def test_analyze_code_python(self, analyzer, test_files, mock_provider):
        """Test analyzing a Python file."""
        # Arrange
        file_path = test_files["py"]
        
        # Act
        result = analyzer.analyze_code(file_path)
        
        # Assert
        assert result["language"] == "python"
        assert result["supported"] is True
        assert "file_type_analysis" in result
        assert "code_structure" in result
        
        # Verify AI provider was called
        mock_provider.analyze_code.assert_called_once()
        args = mock_provider.analyze_code.call_args[0]
        assert args[0] == str(file_path)
        assert isinstance(args[1], str)  # content
        assert args[2] == "python"
    
    def test_analyze_code_java(self, analyzer, test_files, mock_provider):
        """Test analyzing a Java file."""
        # Arrange
        file_path = test_files["java"]
        
        # Act
        result = analyzer.analyze_code(file_path)
        
        # Assert
        assert result["language"] == "java"
        assert result["supported"] is True
        assert "file_type_analysis" in result
        assert "code_structure" in result
        
        # Verify AI provider was called
        mock_provider.analyze_code.assert_called()
    
    def test_analyze_code_javascript(self, analyzer, test_files, mock_provider):
        """Test analyzing a JavaScript file."""
        # Arrange
        file_path = test_files["js"]
        
        # Act
        result = analyzer.analyze_code(file_path)
        
        # Assert
        assert result["language"] == "javascript"
        assert result["supported"] is True
        assert "file_type_analysis" in result
        assert "code_structure" in result
        
        # Verify AI provider was called
        mock_provider.analyze_code.assert_called()
    
    def test_analyze_code_typescript(self, analyzer, test_files, mock_provider):
        """Test analyzing a TypeScript file."""
        # Arrange
        file_path = test_files["ts"]
        
        # Act
        result = analyzer.analyze_code(file_path)
        
        # Assert
        assert result["language"] == "typescript"
        assert result["supported"] is True
        assert "file_type_analysis" in result
        assert "code_structure" in result
        
        # Verify AI provider was called
        mock_provider.analyze_code.assert_called()
    
    def test_analyze_unsupported_file(self, analyzer, test_files):
        """Test analyzing an unsupported file (non-code file)."""
        # Arrange
        file_path = test_files["md"]
        
        # Act
        result = analyzer.analyze_code(file_path)
        
        # Assert
        assert result["language"] == "markdown"
        assert result["supported"] is False
        assert "file_type_analysis" in result
        assert result["code_structure"] is None
        assert "error" in result
    
    def test_analyze_with_cache(self, mock_provider, test_files):
        """Test that caching works for code analysis."""
        # Arrange
        cache = InMemoryCache()
        analyzer = CodeAnalyzer(
            ai_provider=mock_provider,
            cache_provider=cache
        )
        file_path = test_files["py"]
        
        # Act - First call (cache miss)
        result1 = analyzer.analyze_code(file_path)
        
        # Act - Second call (should be cache hit)
        result2 = analyzer.analyze_code(file_path)
        
        # Assert
        assert result1 == result2
        assert mock_provider.analyze_code.call_count == 1  # Called only once
    
    def test_chunk_file(self, analyzer):
        """Test file chunking for large files."""
        # Arrange
        content = "\n".join([f"line {i}" for i in range(1000)])
        
        # Act
        chunks = analyzer._chunk_file(content, "python")
        
        # Assert
        assert len(chunks) > 1
        assert all(isinstance(chunk, str) for chunk in chunks)
        
        # Reconstruct the content from chunks and compare
        reconstructed = "\n".join(chunk for chunk in chunks)
        assert set(reconstructed.split("\n")) == set(content.split("\n"))
    
    def test_analyze_large_file(self, analyzer, mock_provider):
        """Test analyzing a large file that requires chunking."""
        # Arrange
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w+") as temp_file:
            # Create a large Python file
            content = "import os\nimport sys\n\n"
            for i in range(100):
                content += f"def function_{i}(param):\n    return param * {i}\n\n"
            temp_file.write(content)
            temp_file.flush()
            
            file_path = Path(temp_file.name)
            
            # Override MAX_FILE_SIZE to force chunking
            original_max_size = analyzer.__class__.MAX_FILE_SIZE
            analyzer.__class__.MAX_FILE_SIZE = 100  # Small size to force chunking
            
            try:
                # Act
                result = analyzer.analyze_code(file_path)
                
                # Assert
                assert result["language"] == "python"
                assert result["supported"] is True
                assert analyzer.stats["chunked_files"] > 0
                assert "code_structure" in result
                
            finally:
                # Restore original MAX_FILE_SIZE
                analyzer.__class__.MAX_FILE_SIZE = original_max_size
    
    def test_get_stats(self, analyzer, test_files):
        """Test gathering statistics during analysis."""
        # Arrange - Analyze multiple files
        analyzer.analyze_code(test_files["py"])
        analyzer.analyze_code(test_files["java"])
        analyzer.analyze_code(test_files["md"])  # Unsupported
        
        # Act
        stats = analyzer.get_stats()
        
        # Assert
        assert stats["analyzed_files"] == 3  # All 3 files were analyzed (2 supported, 1 unsupported)
        assert stats["supported_files"] == 2
        assert stats["unsupported_files"] == 1
        assert "chunked_files" in stats
        assert "error_files" in stats
    
    def test_error_handling(self, mock_provider):
        """Test error handling during analysis."""
        # Arrange
        analyzer = CodeAnalyzer(ai_provider=mock_provider)
        
        # Mock the file type analyzer to return valid info, but then make
        # the file_reader raise an exception when reading the content for analysis
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w+") as temp_file:
            temp_file.write("# Sample Python file")
            temp_file.flush()
            file_path = temp_file.name
            
            # Mock the original analyze_file to not raise an error but let the code analyzer handle it
            original_file_type_analyzer_analyze = analyzer.file_type_analyzer.analyze_file
            
            def mocked_analyze_file(path):
                return {
                    "file_type": "code",
                    "language": "python",
                    "confidence": 0.9
                }
                
            analyzer.file_type_analyzer.analyze_file = MagicMock(side_effect=mocked_analyze_file)
            
            # Then make the file_reader raise an exception during content reading
            def raise_error(path):
                if str(path).endswith(".py"):
                    raise FileAnalyzerError("Test error")
                return "content"
                
            analyzer.file_reader.read_file = MagicMock(side_effect=raise_error)
            
            # Act
            result = analyzer.analyze_code(file_path)
            
            # Reset mocks
            analyzer.file_type_analyzer.analyze_file = original_file_type_analyzer_analyze
            
            # Assert
            assert "error" in result
            assert result["code_structure"] is None
            assert analyzer.stats["error_files"] > 0