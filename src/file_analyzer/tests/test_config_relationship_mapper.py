"""
Tests for the config relationship mapper.

This module contains tests for the ConfigRelationshipMapper class, which is responsible
for mapping relationships between configuration files and code.
"""
import os
import tempfile
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from file_analyzer.ai_providers.mock_provider import MockAIProvider
from file_analyzer.core.config_analyzer import ConfigAnalyzer
from file_analyzer.core.code_analyzer import CodeAnalyzer
from file_analyzer.core.config_relationship_mapper import ConfigRelationshipMapper
from file_analyzer.core.file_reader import FileReader
from file_analyzer.core.file_hasher import FileHasher
from file_analyzer.core.cache_provider import InMemoryCache


class TestConfigRelationshipMapper:
    """Tests for the ConfigRelationshipMapper class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.mock_provider = MockAIProvider()
        self.file_reader = FileReader()
        self.file_hasher = FileHasher()
        self.cache = InMemoryCache()
        
        # Set up the analyzers that the relationship mapper depends on
        self.config_analyzer = ConfigAnalyzer(
            ai_provider=self.mock_provider,
            file_reader=self.file_reader,
            file_hasher=self.file_hasher,
            cache_provider=self.cache
        )
        self.code_analyzer = CodeAnalyzer(
            ai_provider=self.mock_provider,
            file_reader=self.file_reader,
            file_hasher=self.file_hasher,
            cache_provider=self.cache
        )
        
        # Set up the relationship mapper
        self.mapper = ConfigRelationshipMapper(
            ai_provider=self.mock_provider,
            config_analyzer=self.config_analyzer,
            code_analyzer=self.code_analyzer,
            file_reader=self.file_reader,
            file_hasher=self.file_hasher,
            cache_provider=self.cache
        )
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
    
    def teardown_method(self):
        """Clean up after each test method."""
        self.temp_dir.cleanup()
    
    def create_test_files(self):
        """Create test configuration and code files for testing."""
        # Create config files
        config_dir = self.test_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        # Create a JSON configuration file
        db_config = config_dir / "database.json"
        db_config.write_text('''
        {
            "database": {
                "host": "localhost",
                "port": 5432,
                "username": "user",
                "password": "${DB_PASSWORD}"
            },
            "pool": {
                "max_size": 20,
                "timeout": 30
            }
        }
        ''')
        
        # Create a YAML configuration file
        app_config = config_dir / "app.yaml"
        app_config.write_text('''
        app:
          name: MyTestApp
          version: 1.0.0
          debug: true
          
        logging:
          level: info
          file: /var/log/app.log
          
        api:
          url: https://api.example.com
          timeout: 30
        ''')
        
        # Create code files that reference the configs
        src_dir = self.test_dir / "src"
        src_dir.mkdir(exist_ok=True)
        
        # Python file that loads database config
        db_module = src_dir / "database.py"
        db_module.write_text('''
        import json
        import os
        
        def load_config():
            """Load database configuration from JSON file."""
            with open("config/database.json", "r") as f:
                config = json.load(f)
            
            # Replace environment variables
            if "${DB_PASSWORD}" in config["database"]["password"]:
                config["database"]["password"] = os.getenv("DB_PASSWORD", "")
            
            return config
        
        def get_connection_string():
            """Get database connection string from config."""
            config = load_config()
            db = config["database"]
            return f"postgresql://{db['username']}:{db['password']}@{db['host']}:{db['port']}/mydb"
        
        def get_pool_config():
            """Get connection pool configuration."""
            config = load_config()
            return config["pool"]
        ''')
        
        # Python file that loads app config
        app_module = src_dir / "app.py"
        app_module.write_text('''
        import yaml
        import requests
        
        def load_config():
            """Load application configuration from YAML file."""
            with open("config/app.yaml", "r") as f:
                return yaml.safe_load(f)
        
        def get_app_name():
            """Get application name from config."""
            config = load_config()
            return config["app"]["name"]
        
        def setup_logging():
            """Configure logging based on configuration."""
            config = load_config()
            level = config["logging"]["level"]
            log_file = config["logging"]["file"]
            # Setup logging code would go here
            return level, log_file
        
        def call_api(endpoint):
            """Call API with configured settings."""
            config = load_config()
            api_config = config["api"]
            url = f"{api_config['url']}/{endpoint}"
            timeout = api_config["timeout"]
            
            return requests.get(url, timeout=timeout)
        ''')
        
        # Another file with indirect config reference
        utils_module = src_dir / "utils.py"
        utils_module.write_text('''
        from database import get_connection_string, get_pool_config
        from app import get_app_name, setup_logging
        
        def initialize_app():
            """Initialize application components."""
            conn_string = get_connection_string()
            pool_config = get_pool_config()
            app_name = get_app_name()
            log_level, log_file = setup_logging()
            
            print(f"Initializing {app_name} with connection {conn_string}")
            print(f"Pool config: {pool_config}")
            print(f"Logging to {log_file} at level {log_level}")
        ''')
        
        return {
            "db_config": str(db_config),
            "app_config": str(app_config),
            "db_module": str(db_module),
            "app_module": str(app_module),
            "utils_module": str(utils_module)
        }
    
    def test_map_config_to_code_relationships(self):
        """Test mapping relationships from config files to code files."""
        test_files = self.create_test_files()
        
        # Map relationships starting from config file
        db_config_relationships = self.mapper.map_config_to_code_relationships(test_files["db_config"])
        
        # Verify relationships for database config
        assert db_config_relationships is not None
        assert "direct_references" in db_config_relationships
        assert len(db_config_relationships["direct_references"]) >= 1
        assert test_files["db_module"] in [ref["file_path"] for ref in db_config_relationships["direct_references"]]
        
        # Verify that the relationship includes parameter path information
        db_params = db_config_relationships.get("parameters", [])
        assert any(param["path"] == "database.host" for param in db_params)
        assert any(param["path"] == "pool.max_size" for param in db_params)
        
        # Verify indirect relationships
        assert "indirect_references" in db_config_relationships
        assert len(db_config_relationships["indirect_references"]) >= 1
        assert test_files["utils_module"] in [ref["file_path"] for ref in db_config_relationships["indirect_references"]]
    
    def test_map_code_to_config_relationships(self):
        """Test mapping relationships from code files to config files."""
        test_files = self.create_test_files()
        
        # Map relationships starting from code file
        app_module_relationships = self.mapper.map_code_to_config_relationships(test_files["app_module"])
        
        # Verify relationships for app module
        assert app_module_relationships is not None
        assert "config_files" in app_module_relationships
        assert len(app_module_relationships["config_files"]) >= 1
        assert test_files["app_config"] in [config["file_path"] for config in app_module_relationships["config_files"]]
        
        # Verify referenced parameters
        assert "referenced_parameters" in app_module_relationships
        refs = app_module_relationships["referenced_parameters"]
        assert any(param["path"] == "app.name" for param in refs)
        assert any(param["path"] == "api.url" for param in refs)
        assert any(param["path"] == "api.timeout" for param in refs)
    
    def test_map_repository_config_relationships(self):
        """Test mapping all config relationships in a repository."""
        test_files = self.create_test_files()
        
        # Map all relationships in the test directory
        relationship_map = self.mapper.map_repository_config_relationships(str(self.test_dir))
        
        # Verify the map contains all config files
        assert len(relationship_map["config_files"]) == 2
        config_paths = [config["file_path"] for config in relationship_map["config_files"]]
        assert test_files["db_config"] in config_paths
        assert test_files["app_config"] in config_paths
        
        # Verify the map contains config-to-code relationships
        assert len(relationship_map["config_to_code"]) == 2
        
        # Verify the map contains code-to-config relationships
        assert len(relationship_map["code_to_config"]) == 3
        
        # Verify that relationships are bidirectional
        db_config_entry = next(c for c in relationship_map["config_to_code"] 
                              if c["config_file"] == test_files["db_config"])
        assert test_files["db_module"] in [r["file_path"] for r in db_config_entry["direct_references"]]
        
        db_module_entry = next(c for c in relationship_map["code_to_config"] 
                              if c["code_file"] == test_files["db_module"])
        assert test_files["db_config"] in [r["file_path"] for r in db_module_entry["config_files"]]
    
    def test_detect_environment_variable_usage(self):
        """Test detection of environment variable usage in config relationships."""
        test_files = self.create_test_files()
        
        # Map relationships for database config
        db_config_relationships = self.mapper.map_config_to_code_relationships(test_files["db_config"])
        
        # Verify environment variable detection
        assert "environment_vars" in db_config_relationships
        assert "${DB_PASSWORD}" in db_config_relationships["environment_vars"]
        
        # Check if the environment variable is linked to code usage
        env_var_usages = db_config_relationships.get("env_var_usages", [])
        assert len(env_var_usages) >= 1
        assert any(usage["var_name"] == "DB_PASSWORD" for usage in env_var_usages)
        assert any(usage["file_path"] == test_files["db_module"] for usage in env_var_usages)
    
    def test_caching(self):
        """Test that relationship mapping results are cached."""
        test_files = self.create_test_files()
        
        # First mapping should populate the cache
        self.mapper.map_config_to_code_relationships(test_files["db_config"])
        
        # Mock the AI provider to verify it's not called on second mapping
        self.mock_provider.analyze_content = Mock(return_value={"error": "Should not be called"})
        
        # Second mapping should use cache
        db_config_relationships = self.mapper.map_config_to_code_relationships(test_files["db_config"])
        
        # Verify we got a valid result despite mocking the provider
        assert db_config_relationships is not None
        assert "direct_references" in db_config_relationships
        
        # Verify the mock wasn't called (or wasn't used for the main result)
        assert "error" not in db_config_relationships
    
    def test_error_handling(self):
        """Test error handling for invalid files."""
        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            self.mapper.map_config_to_code_relationships("/path/to/nonexistent/file.json")
        
        # Test with invalid content (create an empty file)
        empty_file = self.test_dir / "empty.json"
        empty_file.touch()
        
        result = self.mapper.map_config_to_code_relationships(str(empty_file))
        assert "error" in result
        assert "direct_references" in result
        assert len(result["direct_references"]) == 0
    
    def test_handle_circular_dependencies(self):
        """Test handling of circular dependencies between files."""
        # Create files with circular references
        circular_dir = self.test_dir / "circular"
        circular_dir.mkdir(exist_ok=True)
        
        # Config file
        config_file = circular_dir / "config.json"
        config_file.write_text('{"app_name": "CircularApp", "debug": true}')
        
        # Module A loads config and is imported by Module B
        module_a = circular_dir / "module_a.py"
        module_a.write_text('''
        import json
        import module_b
        
        def load_config():
            with open("config.json", "r") as f:
                return json.load(f)
                
        def get_name():
            return load_config()["app_name"]
        ''')
        
        # Module B imports Module A and uses its config
        module_b = circular_dir / "module_b.py"
        module_b.write_text('''
        import module_a
        
        def is_debug():
            config = module_a.load_config()
            return config["debug"]
        ''')
        
        # Map relationships
        relationship_map = self.mapper.map_repository_config_relationships(str(circular_dir))
        
        # Verify we detected relationships despite circular imports
        assert len(relationship_map["config_files"]) == 1
        assert len(relationship_map["config_to_code"]) == 1
        assert len(relationship_map["code_to_config"]) == 2
        
        # Verify both modules are detected as references
        config_entry = relationship_map["config_to_code"][0]
        reference_paths = [ref["file_path"] for ref in config_entry["direct_references"]]
        assert str(module_a) in reference_paths
        # Module B might be detected as indirect reference
        all_refs = [ref["file_path"] for ref in config_entry["direct_references"]] + \
                  [ref["file_path"] for ref in config_entry["indirect_references"]]
        assert str(module_b) in all_refs

    def test_framework_specific_config_loading(self):
        """Test detection of framework-specific configuration loading patterns."""
        # Create Django-style settings file
        django_dir = self.test_dir / "django_project"
        django_dir.mkdir(exist_ok=True)
        
        # Django settings.py
        settings_file = django_dir / "settings.py"
        settings_file.write_text('''
        DEBUG = True
        ALLOWED_HOSTS = ['localhost', '127.0.0.1']
        
        INSTALLED_APPS = [
            'django.contrib.admin',
            'django.contrib.auth',
            'myapp',
        ]
        
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'mydb',
                'USER': 'postgres',
                'PASSWORD': '${DB_PASSWORD}',
                'HOST': 'localhost',
                'PORT': '5432',
            }
        }
        ''')
        
        # Django views file that imports settings
        views_file = django_dir / "views.py"
        views_file.write_text('''
        from django.http import HttpResponse
        from django.conf import settings
        
        def index(request):
            if settings.DEBUG:
                debug_info = "Debug mode is ON"
            else:
                debug_info = "Debug mode is OFF"
                
            db_name = settings.DATABASES['default']['NAME']
            return HttpResponse(f"Hello from {db_name}! {debug_info}")
        ''')
        
        # Map relationships
        settings_relationships = self.mapper.map_config_to_code_relationships(str(settings_file))
        
        # Verify framework detection
        assert "framework" in settings_relationships
        assert settings_relationships["framework"].lower() == "django"
        
        # Verify relationship detection despite non-standard config loading
        assert len(settings_relationships["direct_references"]) >= 1
        assert str(views_file) in [ref["file_path"] for ref in settings_relationships["direct_references"]]
        
        # Verify parameter detection
        params = settings_relationships.get("parameters", [])
        debug_param = next((p for p in params if p["path"] == "DEBUG"), None)
        assert debug_param is not None
        assert debug_param["referenced"] is True