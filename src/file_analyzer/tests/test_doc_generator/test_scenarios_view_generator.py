"""
Unit tests for the scenarios view generator.
"""
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import os
import tempfile

from file_analyzer.ai_providers.mock_provider import MockAIProvider
from file_analyzer.doc_generator.scenarios_view_generator import ScenariosViewGenerator
from file_analyzer.core.file_reader import FileReader
from file_analyzer.core.file_hasher import FileHasher
from file_analyzer.core.cache_provider import InMemoryCache

class TestScenariosViewGenerator(unittest.TestCase):
    """Test case for the ScenariosViewGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_provider = MockAIProvider()
        self.cache = InMemoryCache()
        self.file_reader = MagicMock(spec=FileReader)
        self.file_hasher = FileHasher()
        
        # Create mock code analyzer
        self.mock_code_analyzer = MagicMock()
        
        # Create generator with mock code analyzer
        self.generator = ScenariosViewGenerator(
            ai_provider=self.mock_provider,
            code_analyzer=self.mock_code_analyzer,
            file_reader=self.file_reader,
            file_hasher=self.file_hasher,
            cache_provider=self.cache
        )
        
        # Repository path for testing
        self.repo_path = Path("/test/repo")
        
        # Setup common mocks
        self.generator._find_documentation_files = MagicMock(return_value=[
            Path("/test/repo/README.md"),
            Path("/test/repo/docs/usage.md")
        ])
        
        self.generator._find_test_files = MagicMock(return_value=[
            Path("/test/repo/tests/test_user_login.py"),
            Path("/test/repo/tests/test_search.py")
        ])
        
        self.generator._find_route_files = MagicMock(return_value=[
            Path("/test/repo/src/routes.py"),
            Path("/test/repo/src/api/endpoints.py")
        ])
    
    def test_generate_use_case_diagram(self):
        """Test generation of use case diagrams."""
        # Mock file reading
        def mock_read_file(file_path):
            if "README.md" in str(file_path):
                return """# Test Project
                
This application allows users to:
- Log in to the system
- Search for items
- Upload files
- Download files

Administrators can:
- Manage user accounts
- View system statistics"""
            elif "usage.md" in str(file_path):
                return """## User Guide
                
Regular users can perform the following actions:
1. Login with email and password
2. Search the database for items
3. Upload new files to the system
4. Download existing files"""
            elif "routes.py" in str(file_path):
                return """
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Login implementation
    pass

@app.route('/search', methods=['GET'])
def search():
    # Search implementation
    pass

@app.route('/upload', methods=['POST'])
def upload_file():
    # Upload implementation
    pass

@app.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    # Download implementation
    pass
"""
            elif "endpoints.py" in str(file_path):
                return """
@api.route('/users')
class UserManagement(Resource):
    @admin_required
    def get(self):
        # List users implementation
        pass
    
    @admin_required
    def post(self):
        # Create user implementation
        pass
    
    @admin_required
    def delete(self):
        # Delete user implementation
        pass

@api.route('/stats')
class SystemStats(Resource):
    @admin_required
    def get(self):
        # System stats implementation
        pass
"""
            return ""
        
        self.file_reader.read_file.side_effect = mock_read_file
        
        # Mock AI provider response
        self.mock_provider.analyze_content = MagicMock(return_value={
            "actors": [
                {"id": "user", "name": "User", "type": "human"},
                {"id": "admin", "name": "Administrator", "type": "human"},
                {"id": "system", "name": "System", "type": "system"}
            ],
            "use_cases": [
                {"id": "login", "name": "Log in", "description": "Authenticate to the system"},
                {"id": "search", "name": "Search items", "description": "Search database for items"},
                {"id": "upload", "name": "Upload file", "description": "Upload new file to the system"},
                {"id": "download", "name": "Download file", "description": "Download existing file"},
                {"id": "manage_users", "name": "Manage users", "description": "CRUD operations on users"},
                {"id": "view_stats", "name": "View statistics", "description": "View system statistics"}
            ],
            "relationships": [
                {"actor": "user", "use_case": "login"},
                {"actor": "user", "use_case": "search"},
                {"actor": "user", "use_case": "upload"},
                {"actor": "user", "use_case": "download"},
                {"actor": "admin", "use_case": "login"},
                {"actor": "admin", "use_case": "manage_users"},
                {"actor": "admin", "use_case": "view_stats"},
                {"actor": "system", "use_case": "view_stats", "type": "include"}
            ]
        })
        
        # Generate diagram
        result = self.generator.generate_use_case_diagram(
            self.repo_path,
            title="Test Use Case Diagram"
        )
        
        # Verify result structure
        self.assertEqual(result["title"], "Test Use Case Diagram")
        self.assertEqual(result["diagram_type"], "use_case")
        self.assertEqual(result["syntax_type"], "mermaid")
        
        # Check diagram content
        self.assertIn("graph TD", result["content"])
        
        # Check actors and use cases
        self.assertTrue(len(result["actors"]) >= 2)  # At least 2 actors
        self.assertTrue(len(result["use_cases"]) >= 4)  # At least 4 use cases
        
        # Verify stats
        self.assertEqual(self.generator.stats["use_case_diagrams_generated"], 1)
    
    def test_generate_user_flow_diagram(self):
        """Test generation of user flow diagrams."""
        # Mock file reading
        def mock_read_file(file_path):
            if "test_user_login.py" in str(file_path):
                return """def test_user_login():
    # Test user login flow
    client = create_client()
    
    # 1. User visits login page
    response = client.get('/login')
    assert response.status_code == 200
    
    # 2. User submits credentials
    response = client.post('/login', data={'username': 'test', 'password': 'password'})
    assert response.status_code == 302  # Redirect
    
    # 3. User is redirected to dashboard
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert 'Welcome, test' in response.text"""
            elif "test_search.py" in str(file_path):
                return """def test_search_flow():
    client = create_client()
    login(client)  # Login first
    
    # 1. User visits search page
    response = client.get('/search')
    assert response.status_code == 200
    
    # 2. User submits search query
    response = client.get('/search?q=test')
    assert response.status_code == 200
    assert 'Results for: test' in response.text
    
    # 3. User clicks on a result
    response = client.get('/items/1')
    assert response.status_code == 200
    assert 'Item details' in response.text"""
            return ""
        
        self.file_reader.read_file.side_effect = mock_read_file
        
        # Mock AI provider response
        self.mock_provider.analyze_content = MagicMock(return_value={
            "title": "User Login Flow",
            "actor": "User",
            "steps": [
                {"id": "start", "name": "Start", "type": "start"},
                {"id": "visit_login", "name": "Visit Login Page", "type": "action"},
                {"id": "enter_credentials", "name": "Enter Credentials", "type": "action"},
                {"id": "submit_form", "name": "Submit Login Form", "type": "action"},
                {"id": "valid_credentials", "name": "Valid Credentials?", "type": "decision"},
                {"id": "show_error", "name": "Show Error Message", "type": "action"},
                {"id": "redirect_dashboard", "name": "Redirect to Dashboard", "type": "action"},
                {"id": "end", "name": "End", "type": "end"}
            ],
            "flows": [
                {"source": "start", "target": "visit_login"},
                {"source": "visit_login", "target": "enter_credentials"},
                {"source": "enter_credentials", "target": "submit_form"},
                {"source": "submit_form", "target": "valid_credentials"},
                {"source": "valid_credentials", "target": "redirect_dashboard", "label": "Yes"},
                {"source": "valid_credentials", "target": "show_error", "label": "No"},
                {"source": "show_error", "target": "enter_credentials"},
                {"source": "redirect_dashboard", "target": "end"}
            ]
        })
        
        # Generate diagram
        result = self.generator.generate_user_flow_diagram(
            self.repo_path,
            use_case="login",
            title="Test User Flow Diagram"
        )
        
        # Verify result structure
        self.assertEqual(result["title"], "Test User Flow Diagram")
        self.assertEqual(result["diagram_type"], "user_flow")
        self.assertEqual(result["syntax_type"], "mermaid")
        
        # Check diagram content
        self.assertIn("flowchart TD", result["content"])
        
        # Check steps and flows
        self.assertTrue(len(result["steps"]) >= 5)  # At least 5 steps
        self.assertTrue(len(result["flows"]) >= 4)  # At least 4 flows
        
        # Verify stats
        self.assertEqual(self.generator.stats["user_flow_diagrams_generated"], 1)
    
    def test_generate_diagram(self):
        """Test the generate_diagram method."""
        # Mock the specific generator methods
        self.generator.generate_use_case_diagram = MagicMock(return_value={"diagram_type": "use_case"})
        self.generator.generate_user_flow_diagram = MagicMock(return_value={"diagram_type": "user_flow"})
        
        # Test use case diagram
        result = self.generator.generate_diagram(self.repo_path, "use_case")
        self.assertEqual(result["diagram_type"], "use_case")
        self.generator.generate_use_case_diagram.assert_called_once()
        
        # Test user flow diagram
        result = self.generator.generate_diagram(self.repo_path, "user_flow", use_case="login")
        self.assertEqual(result["diagram_type"], "user_flow")
        self.generator.generate_user_flow_diagram.assert_called_once_with(self.repo_path, use_case="login", title=None)
        
        # Test invalid diagram type
        with self.assertRaises(ValueError):
            self.generator.generate_diagram(self.repo_path, "invalid_type")
    
    def test_get_stats(self):
        """Test retrieving statistics."""
        # Update stats manually to test retrieval
        self.generator.stats["use_case_diagrams_generated"] = 3
        self.generator.stats["user_flow_diagrams_generated"] = 2
        self.generator.stats["actors_identified"] = 5
        self.generator.stats["use_cases_identified"] = 12
        
        # Get stats
        stats = self.generator.get_stats()
        
        # Verify stats
        self.assertEqual(stats["use_case_diagrams_generated"], 3)
        self.assertEqual(stats["user_flow_diagrams_generated"], 2)
        self.assertEqual(stats["actors_identified"], 5)
        self.assertEqual(stats["use_cases_identified"], 12)

if __name__ == '__main__':
    unittest.main()