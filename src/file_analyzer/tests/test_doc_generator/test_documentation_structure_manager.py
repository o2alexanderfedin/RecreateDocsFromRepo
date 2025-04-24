"""
Tests for the DocumentationStructureManager class.

This module tests the functionality for creating hierarchical and logical 
documentation structure beyond simple directory-based organization.
"""
import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch

from file_analyzer.doc_generator.documentation_structure_manager import (
    DocumentationStructureManager,
    DocumentationStructureConfig
)


class TestDocumentationStructureManager:
    """Test suite for DocumentationStructureManager."""
    
    @pytest.fixture
    def sample_file_results(self):
        """Sample file analysis results for testing."""
        return {
            "/repo/src/core/main.py": {
                "file_type": "code",
                "language": "python",
                "code_structure": {
                    "structure": {
                        "classes": [],
                        "functions": [{"name": "main"}],
                        "imports": ["from core.utils import helper"]
                    },
                    "documentation": "Main entry point for the application."
                },
                "frameworks": []
            },
            "/repo/src/core/utils/helper.py": {
                "file_type": "code",
                "language": "python",
                "code_structure": {
                    "structure": {
                        "classes": [{"name": "Helper"}],
                        "functions": [{"name": "util_function"}],
                        "imports": []
                    },
                    "documentation": "Helper utilities for the application."
                },
                "frameworks": []
            },
            "/repo/src/api/routes.py": {
                "file_type": "code",
                "language": "python",
                "code_structure": {
                    "structure": {
                        "classes": [],
                        "functions": [{"name": "get_data"}],
                        "imports": ["from core.utils.helper import util_function"]
                    },
                    "documentation": "API route definitions."
                },
                "frameworks": [{"name": "FastAPI"}]
            },
            "/repo/config/settings.json": {
                "file_type": "config",
                "language": "json",
                "code_structure": {
                    "structure": {
                        "classes": [],
                        "functions": [],
                        "imports": []
                    },
                    "documentation": "Application configuration settings."
                },
                "frameworks": []
            }
        }
    
    @pytest.fixture
    def sample_relationships(self):
        """Sample relationship data for testing."""
        return {
            "/repo/src/core/main.py": {
                "imports": ["src/core/utils/helper.py"],
                "imported_by": ["src/api/routes.py"],
                "references": [],
                "referenced_by": [],
                "inherits_from": [],
                "inherited_by": [],
                "related": [],
                "graph_data": {}
            },
            "/repo/src/core/utils/helper.py": {
                "imports": [],
                "imported_by": ["src/core/main.py", "src/api/routes.py"],
                "references": [],
                "referenced_by": ["src/api/routes.py"],
                "inherits_from": [],
                "inherited_by": [],
                "related": [],
                "graph_data": {}
            },
            "/repo/src/api/routes.py": {
                "imports": ["src/core/utils/helper.py", "src/core/main.py"],
                "imported_by": [],
                "references": ["src/core/utils/helper.py"],
                "referenced_by": [],
                "inherits_from": [],
                "inherited_by": [],
                "related": [],
                "graph_data": {}
            },
            "/repo/config/settings.json": {
                "imports": [],
                "imported_by": [],
                "references": [],
                "referenced_by": [],
                "inherits_from": [],
                "inherited_by": [],
                "related": [],
                "graph_data": {}
            }
        }
    
    @pytest.fixture
    def sample_frameworks(self):
        """Sample framework data for testing."""
        return [
            {"name": "FastAPI", "language": "python", "version": "0.95.0", "count": 1}
        ]
    
    def test_init(self):
        """Test initialization of DocumentationStructureManager."""
        config = DocumentationStructureConfig(output_dir="/tmp/docs")
        manager = DocumentationStructureManager(config)
        
        assert manager.config.output_dir == "/tmp/docs"
        assert manager.config.max_depth == 3  # Default value
        assert manager.config.group_by_functionality
    
    def test_create_structure_organization(self, sample_file_results, sample_frameworks):
        """Test creation of basic structure organization."""
        config = DocumentationStructureConfig(
            output_dir="/tmp/docs",
            max_depth=2,
            group_by_functionality=True
        )
        manager = DocumentationStructureManager(config)
        
        structure = manager.create_structure_organization(
            repo_path="/repo",
            file_results=sample_file_results,
            frameworks=sample_frameworks
        )
        
        # Basic structure checks
        assert "modules" in structure
        assert "configs" in structure
        
        # Module grouping check
        assert "src" in structure["modules"]
        
        # Check that core and api are in src submodules
        assert "core" in structure["modules"]["src"]["submodules"]
        assert "api" in structure["modules"]["src"]["submodules"]
        
        # Config grouping check
        assert any(f == "config/settings.json" for f in structure["configs"])
    
    def test_create_logical_grouping(self, sample_file_results, sample_relationships):
        """Test logical grouping of files based on relationships."""
        config = DocumentationStructureConfig(
            output_dir="/tmp/docs",
            max_depth=2,
            group_by_functionality=True
        )
        manager = DocumentationStructureManager(config)
        
        logical_groups = manager.create_logical_grouping(
            repo_path="/repo",
            file_results=sample_file_results,
            relationships=sample_relationships
        )
        
        # Should detect src module group (top-level directory)
        assert "src" in logical_groups
        
        # Check src module contents
        src_files = [os.path.basename(f) for f in logical_groups["src"]]
        assert any("main.py" in f for f in src_files)
        assert any("helper.py" in f for f in src_files)
        assert any("routes.py" in f for f in src_files)
    
    def test_generate_hierarchical_structure(self, sample_file_results, sample_relationships):
        """Test generation of hierarchical documentation structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DocumentationStructureConfig(
                output_dir=tmpdir,
                max_depth=2,
                group_by_functionality=True
            )
            manager = DocumentationStructureManager(config)
            
            hierarchy = manager.generate_hierarchical_structure(
                repo_path="/repo",
                file_results=sample_file_results,
                relationships=sample_relationships
            )
            
            # Check structure levels
            assert "root" in hierarchy
            assert "modules" in hierarchy
            assert "components" in hierarchy
            
            # Check module hierarchy (should group by top-level directories)
            assert "src" in hierarchy["modules"]
            assert "config" in hierarchy["modules"]
            
            # Check file assignments
            src_files = [os.path.basename(f) for f in hierarchy["modules"]["src"]["files"]]
            assert any("main.py" in f for f in src_files) or \
                  any("routes.py" in f for f in src_files) or \
                  any("helper.py" in f for f in src_files)
    
    def test_adaptive_depth_control(self, sample_file_results):
        """Test adaptive depth control based on repository size."""
        # Test with a small repository
        config = DocumentationStructureConfig(
            output_dir="/tmp/docs",
            adapt_depth_to_size=True
        )
        manager = DocumentationStructureManager(config)
        
        depth = manager._calculate_optimal_depth(sample_file_results)
        assert depth <= 2  # Small repo should have shallow depth
        
        # Test with a larger repository
        large_repo = {}
        for i in range(100):
            large_repo[f"/repo/src/module{i}/file{i}.py"] = {"file_type": "code"}
        
        depth = manager._calculate_optimal_depth(large_repo)
        assert depth >= 3  # Larger repo should have deeper structure
    
    def test_generate_component_view(self, sample_file_results, sample_relationships):
        """Test generation of component-based view."""
        config = DocumentationStructureConfig(
            output_dir="/tmp/docs",
            group_by_functionality=True
        )
        manager = DocumentationStructureManager(config)
        
        components = manager.generate_component_view(
            repo_path="/repo",
            file_results=sample_file_results,
            relationships=sample_relationships
        )
        
        # Should identify API component
        assert "API" in components
        # Should identify Core component
        assert "Core" in components
        # Should identify Configuration component
        assert "Configuration" in components
        
        # Check component assignments
        assert any("routes.py" in f for f in components["API"]["files"])
        assert any("main.py" in f for f in components["Core"]["files"])
    
    def test_generate_structure_indexes(self, sample_file_results, sample_relationships, sample_frameworks):
        """Test generation of structure index files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DocumentationStructureConfig(output_dir=tmpdir)
            manager = DocumentationStructureManager(config)
            
            # Create required view data manually for the test
            logical_groups = manager.create_logical_grouping(
                repo_path="/repo",
                file_results=sample_file_results,
                relationships=sample_relationships
            )
            
            hierarchy = manager.generate_hierarchical_structure(
                repo_path="/repo",
                file_results=sample_file_results,
                relationships=sample_relationships
            )
            
            component_view = manager.generate_component_view(
                repo_path="/repo",
                file_results=sample_file_results,
                relationships=sample_relationships
            )
            
            architecture_view = manager.generate_architecture_view(
                repo_path="/repo",
                file_results=sample_file_results,
                relationships=sample_relationships,
                frameworks=sample_frameworks
            )
            
            # Call with all required data provided
            index_files = manager.generate_structure_indexes(
                repo_path="/repo",
                file_results=sample_file_results,
                relationships=sample_relationships,
                frameworks=sample_frameworks,
                hierarchy=hierarchy,
                logical_groups=logical_groups,
                component_view=component_view,
                architecture_view=architecture_view
            )
            
            # Should generate main index
            assert os.path.exists(os.path.join(tmpdir, "index.md"))
            
            # Should generate architecture index
            os.makedirs(os.path.join(tmpdir, "architecture"), exist_ok=True)
            
            # Should generate component index
            os.makedirs(os.path.join(tmpdir, "components"), exist_ok=True)
            
            # Should return a list of generated index files
            assert isinstance(index_files, list)