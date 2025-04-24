"""
Tests for the DocumentationAssembler class.

This module tests the functionality for assembling all documentation
components into a complete, cohesive documentation package.
"""
import os
import shutil
import tempfile
import pytest
from unittest.mock import MagicMock, patch

from file_analyzer.doc_generator.documentation_assembler import (
    DocumentationAssembler,
    AssemblyConfig,
    DocumentationValidator,
    DocumentationCompressor
)


class TestAssemblyConfig:
    """Test suite for AssemblyConfig."""
    
    def test_init_with_defaults(self):
        """Test initialization with default values."""
        config = AssemblyConfig(output_dir="/tmp/docs")
        
        assert config.output_dir == "/tmp/docs"
        assert config.input_dirs == []
        assert config.self_contained is True
        assert config.validate_output is True
        assert config.optimize_output is True
        assert config.include_readme is True
        assert config.output_format == "markdown"
    
    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        config = AssemblyConfig(
            output_dir="/tmp/docs",
            input_dirs=["/tmp/input1", "/tmp/input2"],
            self_contained=False,
            validate_output=False,
            optimize_output=False,
            include_readme=False,
            output_format="html",
            template_dir="/custom/templates"
        )
        
        assert config.output_dir == "/tmp/docs"
        assert config.input_dirs == ["/tmp/input1", "/tmp/input2"]
        assert config.self_contained is False
        assert config.validate_output is False
        assert config.optimize_output is False
        assert config.include_readme is False
        assert config.output_format == "html"
        assert config.template_dir == "/custom/templates"


class TestDocumentationAssembler:
    """Test suite for DocumentationAssembler."""
    
    @pytest.fixture
    def sample_input_structure(self):
        """Create a sample input structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create structure directories
            os.makedirs(os.path.join(tmpdir, "files"), exist_ok=True)
            os.makedirs(os.path.join(tmpdir, "architecture"), exist_ok=True)
            os.makedirs(os.path.join(tmpdir, "components"), exist_ok=True)
            os.makedirs(os.path.join(tmpdir, "modules"), exist_ok=True)
            
            # Create sample index files
            with open(os.path.join(tmpdir, "index.md"), "w") as f:
                f.write("# Main Index\n\nMain documentation index.\n")
            
            with open(os.path.join(tmpdir, "architecture/index.md"), "w") as f:
                f.write("# Architecture\n\nArchitecture documentation.\n")
            
            with open(os.path.join(tmpdir, "components/index.md"), "w") as f:
                f.write("# Components\n\nComponent documentation.\n")
            
            with open(os.path.join(tmpdir, "modules/index.md"), "w") as f:
                f.write("# Modules\n\nModule documentation.\n")
            
            # Create sample file documentation
            os.makedirs(os.path.join(tmpdir, "files/src"), exist_ok=True)
            with open(os.path.join(tmpdir, "files/src/main.md"), "w") as f:
                f.write("# main.py\n\nMain entry point.\n")
            
            yield tmpdir
    
    def test_init(self):
        """Test initialization of DocumentationAssembler."""
        config = AssemblyConfig(output_dir="/tmp/docs")
        assembler = DocumentationAssembler(config)
        
        assert assembler.config.output_dir == "/tmp/docs"
    
    def test_assemble_documentation(self, sample_input_structure):
        """Test the main assembly process."""
        with tempfile.TemporaryDirectory() as output_dir:
            # Create configuration
            config = AssemblyConfig(
                output_dir=output_dir,
                input_dirs=[sample_input_structure]
            )
            
            # Create assembler
            assembler = DocumentationAssembler(config)
            
            # Run assembly
            result = assembler.assemble_documentation()
            
            # Check results
            assert result["success"] is True
            assert result["files_processed"] > 0
            assert os.path.exists(os.path.join(output_dir, "index.md"))
            assert os.path.exists(os.path.join(output_dir, "architecture", "index.md"))
            assert os.path.exists(os.path.join(output_dir, "components", "index.md"))
            assert os.path.exists(os.path.join(output_dir, "modules", "index.md"))
            assert os.path.exists(os.path.join(output_dir, "files", "src", "main.md"))
    
    def test_generate_readme(self):
        """Test generation of README file."""
        with tempfile.TemporaryDirectory() as output_dir:
            # Create configuration
            config = AssemblyConfig(
                output_dir=output_dir,
                include_readme=True
            )
            
            # Create assembler
            assembler = DocumentationAssembler(config)
            
            # Generate README
            readme_path = assembler.generate_readme(
                project_name="Test Project",
                repo_url="https://github.com/test/project"
            )
            
            # Check README exists and contains expected content
            assert os.path.exists(readme_path)
            
            with open(readme_path, "r") as f:
                content = f.read()
                assert "# Test Project Documentation" in content
                assert "https://github.com/test/project" in content
                assert "Navigation" in content
    
    def test_integrate_file_docs(self, sample_input_structure):
        """Test integration of file documentation."""
        with tempfile.TemporaryDirectory() as output_dir:
            # Create configuration
            config = AssemblyConfig(
                output_dir=output_dir,
                input_dirs=[sample_input_structure]
            )
            
            # Create assembler
            assembler = DocumentationAssembler(config)
            
            # Integrate file docs
            result = assembler.integrate_file_docs(os.path.join(sample_input_structure, "files"))
            
            # Check results
            assert result["success"] is True
            assert result["files_integrated"] > 0
            assert os.path.exists(os.path.join(output_dir, "files", "src", "main.md"))
    
    def test_integrate_diagrams(self, sample_input_structure):
        """Test integration of diagrams."""
        with tempfile.TemporaryDirectory() as output_dir:
            # Create a sample diagram
            os.makedirs(os.path.join(sample_input_structure, "architecture/diagrams"), exist_ok=True)
            with open(os.path.join(sample_input_structure, "architecture/diagrams/class_diagram.md"), "w") as f:
                f.write("# Class Diagram\n\n```mermaid\nclassDiagram\nClass1 --> Class2\n```\n")
            
            # Create configuration
            config = AssemblyConfig(
                output_dir=output_dir,
                input_dirs=[sample_input_structure]
            )
            
            # Create assembler
            assembler = DocumentationAssembler(config)
            
            # Integrate diagrams
            result = assembler.integrate_diagrams(os.path.join(sample_input_structure, "architecture"))
            
            # Check results
            assert result["success"] is True
            assert result["diagrams_integrated"] > 0
            assert os.path.exists(os.path.join(output_dir, "architecture", "diagrams", "class_diagram.md"))
    
    def test_integrate_navigation(self, sample_input_structure):
        """Test integration of navigation elements."""
        with tempfile.TemporaryDirectory() as output_dir:
            # Create configuration
            config = AssemblyConfig(
                output_dir=output_dir,
                input_dirs=[sample_input_structure]
            )
            
            # Create assembler
            assembler = DocumentationAssembler(config)
            
            # Copy files to output directory first
            assembler.integrate_file_docs(os.path.join(sample_input_structure, "files"))
            
            # Mock navigation update
            def mock_update_navigation(doc_path):
                with open(doc_path, "r") as f:
                    content = f.read()
                
                content = content + "\n\n## Navigation\n\n- [Home](../../index.md)\n"
                
                with open(doc_path, "w") as f:
                    f.write(content)
                
                return True
            
            # Patch the update_navigation method
            with patch.object(assembler, "_update_navigation", side_effect=mock_update_navigation):
                # Integrate navigation
                result = assembler.integrate_navigation()
                
                # Check results
                assert result["success"] is True
                assert result["files_updated"] > 0
                
                # Check if navigation was added
                with open(os.path.join(output_dir, "files", "src", "main.md"), "r") as f:
                    content = f.read()
                    assert "## Navigation" in content
                    assert "[Home]" in content
    
    def test_resolve_cross_references(self, sample_input_structure):
        """Test resolution of cross-references."""
        with tempfile.TemporaryDirectory() as output_dir:
            # Create a file with references - use a reference format that will be fixed
            os.makedirs(os.path.join(sample_input_structure, "files/src"), exist_ok=True)
            
            # Create a file with a broken reference that needs fixing
            with open(os.path.join(sample_input_structure, "files/src/main.md"), "w") as f:
                f.write("# main.py\n\nSee [helper.py](helper) for utilities.\n")
            
            # Create the referenced file
            with open(os.path.join(sample_input_structure, "files/helper.md"), "w") as f:
                f.write("# helper.py\n\nUtility functions.\n")
            
            # Create configuration
            config = AssemblyConfig(
                output_dir=output_dir,
                input_dirs=[sample_input_structure]
            )
            
            # Create assembler
            assembler = DocumentationAssembler(config)
            
            # Copy files to output directory first
            assembler.integrate_file_docs(os.path.join(sample_input_structure, "files"))
            
            # Copy the referenced file manually to ensure it's in the output directory
            os.makedirs(os.path.join(output_dir, "files"), exist_ok=True)
            shutil.copy2(
                os.path.join(sample_input_structure, "files/helper.md"),
                os.path.join(output_dir, "files/helper.md")
            )
            
            # Resolve cross-references
            result = assembler.resolve_cross_references()
            
            # Check results
            assert result["success"] is True
            assert result["references_resolved"] > 0
            
            # Check if references were resolved
            with open(os.path.join(output_dir, "files", "src", "main.md"), "r") as f:
                content = f.read()
                assert "helper.py" in content  # Reference exists
    
    def test_disabled_features(self):
        """Test assembly with disabled features."""
        with tempfile.TemporaryDirectory() as output_dir:
            # Create configuration with features disabled
            config = AssemblyConfig(
                output_dir=output_dir,
                self_contained=False,
                validate_output=False,
                optimize_output=False,
                include_readme=False
            )
            
            # Create assembler
            assembler = DocumentationAssembler(config)
            
            # Patch methods to track calls
            with patch.object(assembler, "generate_readme") as mock_readme, \
                 patch.object(DocumentationValidator, "validate_documentation") as mock_validate, \
                 patch.object(DocumentationCompressor, "optimize_documentation") as mock_optimize:
                
                # Run assembly (with empty input)
                assembler.assemble_documentation()
                
                # Check if disabled features were not called
                mock_readme.assert_not_called()
                mock_validate.assert_not_called()
                mock_optimize.assert_not_called()


class TestDocumentationValidator:
    """Test suite for DocumentationValidator."""
    
    def test_validate_documentation(self):
        """Test validation of documentation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple documentation structure
            with open(os.path.join(tmpdir, "index.md"), "w") as f:
                f.write("# Index\n\nSee [file.md](file.md).\n")
            
            with open(os.path.join(tmpdir, "file.md"), "w") as f:
                f.write("# File\n\nContent.\n")
            
            # Create a broken link
            with open(os.path.join(tmpdir, "broken.md"), "w") as f:
                f.write("# Broken\n\nSee [missing.md](missing.md).\n")
            
            # Create validator
            validator = DocumentationValidator(tmpdir)
            
            # Validate documentation
            result = validator.validate_documentation()
            
            # Check results
            assert result["valid"] is False  # False because of broken link
            assert result["broken_links"] > 0
            assert result["files_checked"] == 3
    
    def test_validate_links(self):
        """Test validation of links."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files with links
            with open(os.path.join(tmpdir, "valid.md"), "w") as f:
                f.write("# Valid\n\nSee [index.md](index.md).\n")
            
            with open(os.path.join(tmpdir, "index.md"), "w") as f:
                f.write("# Index\n\nContent.\n")
            
            with open(os.path.join(tmpdir, "broken.md"), "w") as f:
                f.write("# Broken\n\nSee [missing.md](missing.md).\n")
            
            # Create validator
            validator = DocumentationValidator(tmpdir)
            
            # Validate links
            valid_links = validator.validate_links(os.path.join(tmpdir, "valid.md"))
            broken_links = validator.validate_links(os.path.join(tmpdir, "broken.md"))
            
            # Check results
            assert valid_links["valid"] is True
            assert valid_links["broken_links"] == 0
            
            assert broken_links["valid"] is False
            assert broken_links["broken_links"] > 0


class TestDocumentationCompressor:
    """Test suite for DocumentationCompressor."""
    
    def test_optimize_documentation(self):
        """Test optimization of documentation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple documentation structure with an image
            with open(os.path.join(tmpdir, "index.md"), "w") as f:
                f.write("# Index\n\nSee [image](img.png).\n")
            
            # Create a dummy image file
            with open(os.path.join(tmpdir, "img.png"), "wb") as f:
                f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")
            
            # Create compressor
            compressor = DocumentationCompressor(tmpdir)
            
            # Mock the actual optimization to avoid dependency on image libraries
            with patch.object(compressor, "_compress_image", return_value=True):
                # Optimize documentation
                result = compressor.optimize_documentation()
                
                # Check results
                assert result["success"] is True
                assert result["files_optimized"] > 0
                assert result["size_reduction"] > 0
    
    def test_compress_images(self):
        """Test compression of images."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dummy image files
            with open(os.path.join(tmpdir, "img1.png"), "wb") as f:
                f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")
            
            with open(os.path.join(tmpdir, "img2.jpg"), "wb") as f:
                f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342")
            
            # Create compressor
            compressor = DocumentationCompressor(tmpdir)
            
            # Mock the actual compression to avoid dependency on image libraries
            with patch.object(compressor, "_compress_image", return_value=True):
                # Compress images
                result = compressor.compress_images()
                
                # Check results
                assert result["success"] is True
                assert result["images_compressed"] == 2