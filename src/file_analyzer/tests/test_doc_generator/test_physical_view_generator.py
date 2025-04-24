"""
Unit tests for the physical view generator.
"""
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import os
import tempfile

from file_analyzer.ai_providers.mock_provider import MockAIProvider
from file_analyzer.doc_generator.physical_view_generator import PhysicalViewGenerator
from file_analyzer.core.file_reader import FileReader
from file_analyzer.core.file_hasher import FileHasher
from file_analyzer.core.cache_provider import InMemoryCache

class TestPhysicalViewGenerator(unittest.TestCase):
    """Test case for the PhysicalViewGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_provider = MockAIProvider()
        self.cache = InMemoryCache()
        self.file_reader = MagicMock(spec=FileReader)
        self.file_hasher = FileHasher()
        
        # Create mock code analyzer
        self.mock_code_analyzer = MagicMock()
        
        # Create generator with mock code analyzer
        self.generator = PhysicalViewGenerator(
            ai_provider=self.mock_provider,
            code_analyzer=self.mock_code_analyzer,
            file_reader=self.file_reader,
            file_hasher=self.file_hasher,
            cache_provider=self.cache
        )
        
        # Repository path for testing
        self.repo_path = Path("/test/repo")
        
        # Setup common mocks
        self.generator._find_deployment_files = MagicMock(return_value=[
            Path("/test/repo/Dockerfile"),
            Path("/test/repo/kubernetes/deployment.yaml"),
            Path("/test/repo/docker-compose.yml")
        ])
        
        self.generator._find_infrastructure_files = MagicMock(return_value=[
            Path("/test/repo/terraform/main.tf"),
            Path("/test/repo/cloudformation/template.json")
        ])
    
    def test_generate_deployment_diagram(self):
        """Test generation of deployment diagrams."""
        # Mock file reading
        def mock_read_file(file_path):
            if "Dockerfile" in str(file_path):
                return """FROM python:3.8
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]"""
            elif "deployment.yaml" in str(file_path):
                return """apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: api-server:latest
        ports:
        - containerPort: 8080"""
            elif "docker-compose.yml" in str(file_path):
                return """version: '3'
services:
  web:
    build: .
    ports:
      - "8000:8000"
  db:
    image: postgres
    environment:
      POSTGRES_PASSWORD: password"""
            return ""
        
        self.file_reader.read_file.side_effect = mock_read_file
        
        # Mock AI provider response
        self.mock_provider.analyze_content = MagicMock(return_value={
            "nodes": [
                {"id": "web-server", "type": "server", "name": "Web Server"},
                {"id": "api-server", "type": "server", "name": "API Server"},
                {"id": "database", "type": "database", "name": "PostgreSQL Database"}
            ],
            "artifacts": [
                {"id": "web-app", "type": "container", "name": "Web Application", "node": "web-server"},
                {"id": "api-app", "type": "container", "name": "API Application", "node": "api-server"}
            ],
            "connections": [
                {"source": "web-app", "target": "api-app", "type": "HTTP"},
                {"source": "api-app", "target": "database", "type": "SQL"}
            ]
        })
        
        # Generate diagram
        result = self.generator.generate_deployment_diagram(
            self.repo_path,
            title="Test Deployment Diagram"
        )
        
        # Verify result structure
        self.assertEqual(result["title"], "Test Deployment Diagram")
        self.assertEqual(result["diagram_type"], "deployment")
        self.assertEqual(result["syntax_type"], "mermaid")
        
        # Check diagram content
        self.assertIn("graph TD", result["content"])
        
        # Check nodes and artifacts
        self.assertTrue(len(result["nodes"]) >= 3)  # At least 3 nodes
        self.assertTrue(len(result["artifacts"]) >= 2)  # At least 2 artifacts
        
        # Verify stats
        self.assertEqual(self.generator.stats["deployment_diagrams_generated"], 1)
    
    def test_generate_infrastructure_diagram(self):
        """Test generation of infrastructure diagrams."""
        # Mock file reading
        def mock_read_file(file_path):
            if "main.tf" in str(file_path):
                return """provider "aws" {
  region = "us-west-2"
}

resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
}

resource "aws_db_instance" "default" {
  allocated_storage    = 10
  engine               = "mysql"
  engine_version       = "5.7"
  instance_class       = "db.t2.micro"
  name                 = "mydb"
  username             = "admin"
  password             = "password"
}"""
            elif "template.json" in str(file_path):
                return """{
  "Resources": {
    "EC2Instance": {
      "Type": "AWS::EC2::Instance",
      "Properties": {
        "InstanceType": "t2.micro",
        "ImageId": "ami-0c55b159cbfafe1f0"
      }
    },
    "S3Bucket": {
      "Type": "AWS::S3::Bucket"
    }
  }
}"""
            return ""
        
        self.file_reader.read_file.side_effect = mock_read_file
        
        # Mock AI provider response
        self.mock_provider.analyze_content = MagicMock(return_value={
            "resources": [
                {"id": "ec2-1", "type": "compute", "name": "Web Server", "provider": "AWS"},
                {"id": "db-1", "type": "database", "name": "MySQL Database", "provider": "AWS"},
                {"id": "s3-1", "type": "storage", "name": "S3 Bucket", "provider": "AWS"}
            ],
            "networks": [
                {"id": "vpc-1", "type": "vpc", "name": "Main VPC", "provider": "AWS"}
            ],
            "connections": [
                {"source": "ec2-1", "target": "db-1", "type": "internal"},
                {"source": "ec2-1", "target": "s3-1", "type": "internal"}
            ]
        })
        
        # Generate diagram
        result = self.generator.generate_infrastructure_diagram(
            self.repo_path,
            title="Test Infrastructure Diagram"
        )
        
        # Verify result structure
        self.assertEqual(result["title"], "Test Infrastructure Diagram")
        self.assertEqual(result["diagram_type"], "infrastructure")
        self.assertEqual(result["syntax_type"], "mermaid")
        
        # Check diagram content
        self.assertIn("graph TD", result["content"])
        
        # Check resources
        self.assertTrue(len(result["resources"]) >= 3)  # At least 3 resources
        
        # Verify stats
        self.assertEqual(self.generator.stats["infrastructure_diagrams_generated"], 1)
    
    def test_generate_diagram(self):
        """Test the generate_diagram method."""
        # Mock the specific generator methods
        self.generator.generate_deployment_diagram = MagicMock(return_value={"diagram_type": "deployment"})
        self.generator.generate_infrastructure_diagram = MagicMock(return_value={"diagram_type": "infrastructure"})
        
        # Test deployment diagram
        result = self.generator.generate_diagram(self.repo_path, "deployment")
        self.assertEqual(result["diagram_type"], "deployment")
        self.generator.generate_deployment_diagram.assert_called_once()
        
        # Test infrastructure diagram
        result = self.generator.generate_diagram(self.repo_path, "infrastructure")
        self.assertEqual(result["diagram_type"], "infrastructure")
        self.generator.generate_infrastructure_diagram.assert_called_once()
        
        # Test invalid diagram type
        with self.assertRaises(ValueError):
            self.generator.generate_diagram(self.repo_path, "invalid_type")
    
    def test_get_stats(self):
        """Test retrieving statistics."""
        # Update stats manually to test retrieval
        self.generator.stats["deployment_diagrams_generated"] = 3
        self.generator.stats["infrastructure_diagrams_generated"] = 2
        self.generator.stats["deployment_nodes_found"] = 15
        self.generator.stats["infrastructure_resources_found"] = 8
        
        # Get stats
        stats = self.generator.get_stats()
        
        # Verify stats
        self.assertEqual(stats["deployment_diagrams_generated"], 3)
        self.assertEqual(stats["infrastructure_diagrams_generated"], 2)
        self.assertEqual(stats["deployment_nodes_found"], 15)
        self.assertEqual(stats["infrastructure_resources_found"], 8)

if __name__ == '__main__':
    unittest.main()