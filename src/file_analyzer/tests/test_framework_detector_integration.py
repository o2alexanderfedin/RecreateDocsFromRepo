"""
Integration tests for the framework detector component.

These tests use real files and real dependencies (no mocks).
"""
import os
import tempfile
from pathlib import Path
import pytest

from file_analyzer.core.framework_detector import FrameworkDetector
from file_analyzer.core.file_type_analyzer import FileTypeAnalyzer
from file_analyzer.core.code_analyzer import CodeAnalyzer
from file_analyzer.ai_providers.mock_provider import MockAIProvider
from file_analyzer.core.cache_provider import InMemoryCache


class TestFrameworkDetectorIntegration:
    """Integration tests for the FrameworkDetector class with real files."""
    
    @pytest.fixture
    def detector(self):
        """Create a framework detector with real dependencies."""
        ai_provider = MockAIProvider()  # Real MockAIProvider, not a mock of a mock
        
        # Use real implementations, not mocks
        file_type_analyzer = FileTypeAnalyzer(ai_provider=ai_provider)
        code_analyzer = CodeAnalyzer(ai_provider=ai_provider, file_type_analyzer=file_type_analyzer)
        
        return FrameworkDetector(
            ai_provider=ai_provider,
            code_analyzer=code_analyzer,
            file_type_analyzer=file_type_analyzer,
            cache_provider=InMemoryCache()
        )
    
    @pytest.fixture
    def test_files(self):
        """Create real test files for different languages with framework usage."""
        with tempfile.TemporaryDirectory() as tempdir:
            # Python file with Django
            django_file = Path(tempdir) / "django_app.py"
            with open(django_file, "w") as f:
                f.write("""
                from django.db import models
                from django.http import HttpResponse
                
                class MyModel(models.Model):
                    name = models.CharField(max_length=100)
                    
                def my_view(request):
                    return HttpResponse("Hello, Django!")
                """)
            
            # Python file with Flask
            flask_file = Path(tempdir) / "flask_app.py"
            with open(flask_file, "w") as f:
                f.write("""
                from flask import Flask, render_template
                
                app = Flask(__name__)
                
                @app.route('/')
                def index():
                    return render_template('index.html')
                """)
            
            # JavaScript file with React
            react_file = Path(tempdir) / "react_app.js"
            with open(react_file, "w") as f:
                f.write("""
                import React, { useState } from 'react';
                
                function App() {
                    const [count, setCount] = useState(0);
                    
                    return (
                        <div>
                            <h1>Hello, React!</h1>
                            <button onClick={() => setCount(count + 1)}>
                                Count: {count}
                            </button>
                        </div>
                    );
                }
                
                export default App;
                """)
            
            # Java file with Spring Boot
            spring_file = Path(tempdir) / "SpringController.java"
            with open(spring_file, "w") as f:
                f.write("""
                package com.example.demo;
                
                import org.springframework.boot.SpringApplication;
                import org.springframework.boot.autoconfigure.SpringBootApplication;
                import org.springframework.web.bind.annotation.GetMapping;
                import org.springframework.web.bind.annotation.RestController;
                
                @SpringBootApplication
                public class DemoApplication {
                    public static void main(String[] args) {
                        SpringApplication.run(DemoApplication.class, args);
                    }
                }
                
                @RestController
                class HelloController {
                    @GetMapping("/")
                    public String hello() {
                        return "Hello, Spring Boot!";
                    }
                }
                """)
            
            # Requirements file with versions
            requirements_file = Path(tempdir) / "requirements.txt"
            with open(requirements_file, "w") as f:
                f.write("""
                django==3.2.4
                flask==2.0.1
                pandas==1.3.0
                numpy==1.20.3
                """)
            
            # Package.json file with versions
            package_file = Path(tempdir) / "package.json"
            with open(package_file, "w") as f:
                f.write("""
                {
                    "name": "my-app",
                    "version": "1.0.0",
                    "dependencies": {
                        "react": "^17.0.2",
                        "react-dom": "^17.0.2",
                        "axios": "^0.21.1"
                    }
                }
                """)
            
            yield tempdir
    
    def test_detect_frameworks_django(self, detector, test_files):
        """Integration test for Django framework detection with real files."""
        django_file = Path(test_files) / "django_app.py"
        
        result = detector.detect_frameworks(django_file)
        
        # Check result structure
        assert "file_path" in result
        assert "language" in result
        assert "frameworks" in result
        assert isinstance(result["frameworks"], list)
        
        # Check for Django detection
        django_found = False
        for framework in result["frameworks"]:
            if framework["name"].lower() == "django":
                django_found = True
                assert framework["confidence"] > 0.5
                assert len(framework["evidence"]) > 0
        
        assert django_found, "Django framework not detected"
    
    def test_detect_frameworks_flask(self, detector, test_files):
        """Integration test for Flask framework detection with real files."""
        flask_file = Path(test_files) / "flask_app.py"
        
        result = detector.detect_frameworks(flask_file)
        
        # Check for Flask detection
        flask_found = False
        for framework in result["frameworks"]:
            if framework["name"].lower() == "flask":
                flask_found = True
                assert framework["confidence"] > 0.5
                assert len(framework["evidence"]) > 0
        
        assert flask_found, "Flask framework not detected"
    
    def test_detect_frameworks_react(self, detector, test_files):
        """Integration test for React framework detection with real files."""
        react_file = Path(test_files) / "react_app.js"
        
        result = detector.detect_frameworks(react_file)
        
        # Check for React detection
        react_found = False
        for framework in result["frameworks"]:
            if framework["name"].lower() == "react":
                react_found = True
                assert framework["confidence"] > 0.5
                assert len(framework["evidence"]) > 0
        
        assert react_found, "React framework not detected"
    
    def test_detect_frameworks_spring(self, detector, test_files):
        """Integration test for Spring Boot framework detection with real files."""
        spring_file = Path(test_files) / "SpringController.java"
        
        result = detector.detect_frameworks(spring_file)
        
        # Check for Spring detection
        spring_found = False
        for framework in result["frameworks"]:
            if framework["name"].lower() == "spring":
                spring_found = True
                assert framework["confidence"] > 0.5
                assert len(framework["evidence"]) > 0
        
        assert spring_found, "Spring framework not detected"
    
    def test_extract_version_info(self, detector, test_files):
        """Integration test for version extraction from real requirements.txt."""
        requirements_file = Path(test_files) / "requirements.txt"
        
        # Get versions using the internal method
        versions = detector._extract_version_info(requirements_file, "python")
        
        assert "django" in versions
        assert versions["django"] == "3.2.4"
        
        assert "flask" in versions
        assert versions["flask"] == "2.0.1"
    
    def test_repository_analysis(self, detector, test_files):
        """Integration test for full repository analysis with real files."""
        result = detector.analyze_repository(test_files)
        
        # Check result structure
        assert "repo_path" in result
        assert "frameworks" in result
        assert "file_results" in result
        assert "statistics" in result
        
        # Check framework results
        frameworks = {fw["name"].lower(): fw for fw in result["frameworks"]}
        
        # Common frameworks should be detected
        for framework in ["django", "flask", "react"]:
            assert framework in frameworks
            
        # Check statistics
        assert result["statistics"]["total_files_analyzed"] > 0
        assert result["statistics"]["frameworks_detected"] > 0
        assert len(result["statistics"]["languages"]) > 0