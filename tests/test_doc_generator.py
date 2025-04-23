import pytest
from pathlib import Path
from src.utils.doc_generator import DocGenerator

@pytest.fixture
def doc_generator(tmp_path):
    # Create a test template
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    
    test_template = template_dir / "test.md.j2"
    test_template.write_text("# {{ title }}\n\n{{ content }}")
    
    return DocGenerator(template_dir)

def test_render_template(doc_generator, tmp_path):
    """Test that templates are rendered correctly."""
    output_dir = tmp_path / "output"
    output_path = output_dir / "test.md"
    
    context = {
        "title": "Test Document",
        "content": "This is a test document."
    }
    
    result = doc_generator.render_template("test.md.j2", context, output_path)
    
    assert result.exists()
    content = result.read_text()
    assert "# Test Document" in content
    assert "This is a test document." in content
