import pytest
from pathlib import Path
from src.agents.architecture_agent import ArchitectureAgent

@pytest.fixture
def architecture_agent():
    return ArchitectureAgent()

@pytest.fixture
def temp_repo(tmp_path):
    """Create a temporary repository structure for testing."""
    # Create some dummy files and directories
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('Hello world')")
    (tmp_path / "docs").mkdir()
    return tmp_path

def test_agent_initialization(architecture_agent):
    """Test that the agent initializes correctly."""
    assert architecture_agent.name == "Architecture"

def test_analyze(architecture_agent, temp_repo):
    """Test that the analyze method returns the expected structure."""
    results = architecture_agent.analyze(temp_repo)
    assert "components" in results
    assert "relationships" in results
    assert "diagrams" in results

def test_generate_documentation(architecture_agent, temp_repo, tmp_path):
    """Test that documentation is generated correctly."""
    results = architecture_agent.analyze(temp_repo)
    output_path = architecture_agent.generate_documentation(results, tmp_path)
    assert output_path.exists()
    assert output_path.name == "architecture.md"
