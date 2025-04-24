"""
Physical View Diagram Generator implementation.

This module provides the PhysicalViewGenerator class for creating UML diagrams
that represent the physical structure of a system (deployment and infrastructure diagrams).
"""
import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple, Union

from file_analyzer.doc_generator.base_diagram_generator import BaseDiagramGenerator
from file_analyzer.ai_providers.provider_interface import AIModelProvider
from file_analyzer.core.file_reader import FileReader
from file_analyzer.core.file_hasher import FileHasher
from file_analyzer.core.cache_provider import CacheProvider
from file_analyzer.core.code_analyzer import CodeAnalyzer
from file_analyzer.utils.exceptions import FileAnalyzerError

logger = logging.getLogger("file_analyzer.physical_view_generator")


class PhysicalViewGenerator(BaseDiagramGenerator):
    """
    Generates UML Physical View diagrams for code repositories.
    
    Creates deployment diagrams and infrastructure diagrams using Mermaid syntax
    based on deployment configuration files and infrastructure definitions.
    """
    
    def __init__(
        self,
        ai_provider: AIModelProvider,
        code_analyzer: Optional[CodeAnalyzer] = None,
        file_reader: Optional[FileReader] = None,
        file_hasher: Optional[FileHasher] = None,
        cache_provider: Optional[CacheProvider] = None,
    ):
        """
        Initialize the physical view generator.
        
        Args:
            ai_provider: Provider for AI model access
            code_analyzer: CodeAnalyzer for analyzing code files (optional)
            file_reader: Component for reading files (optional)
            file_hasher: Component for hashing files (optional)
            cache_provider: Provider for caching results (optional)
        """
        super().__init__(
            ai_provider=ai_provider,
            code_analyzer=code_analyzer,
            file_reader=file_reader,
            file_hasher=file_hasher,
            cache_provider=cache_provider
        )
        
        # Extend stats with physical view specific metrics
        self.stats.update({
            "deployment_diagrams_generated": 0,
            "infrastructure_diagrams_generated": 0,
            "deployment_nodes_found": 0,
            "deployment_artifacts_found": 0,
            "infrastructure_resources_found": 0
        })
    
    def generate_diagram(self, repo_path: Union[str, Path], diagram_type: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a physical view diagram of the specified type.
        
        Args:
            repo_path: Path to the repository root
            diagram_type: Type of diagram to generate ('deployment', 'infrastructure')
            **kwargs: Additional arguments for specific diagram types
            
        Returns:
            Dictionary containing diagram data with Mermaid syntax
        """
        result = None
        
        if diagram_type == "deployment":
            result = self.generate_deployment_diagram(repo_path, **kwargs)
        elif diagram_type == "infrastructure":
            result = self.generate_infrastructure_diagram(repo_path, **kwargs)
        else:
            raise ValueError(f"Unsupported diagram type: {diagram_type}")
        
        # Update base stats
        self.stats["diagrams_generated"] += 1
        
        return result
    
    def generate_deployment_diagram(
        self, 
        repo_path: Union[str, Path], 
        focus_area: str = None,
        title: str = "Deployment Diagram"
    ) -> Dict[str, Any]:
        """
        Generate a UML deployment diagram showing hardware nodes and deployed artifacts.
        
        Args:
            repo_path: Path to the repository root
            focus_area: Optional sub-path to focus on
            title: Title for the diagram
            
        Returns:
            Dictionary containing diagram data with Mermaid syntax
        """
        repo_path = Path(repo_path) if isinstance(repo_path, str) else repo_path
        
        # Determine focus path
        focus_path = repo_path
        if focus_area:
            focus_path = repo_path / focus_area
            if not focus_path.exists() or not focus_path.is_dir():
                raise FileNotFoundError(f"Focus area not found: {focus_path}")
        
        # Check cache
        cache_key = f"deployment_diagram:{focus_path}"
        cached_result = self._check_cache(cache_key)
        if cached_result:
            return cached_result
        
        # Find deployment configuration files
        deployment_files = self._find_deployment_files(focus_path)
        
        if not deployment_files:
            logger.warning(f"No deployment configuration files found in {focus_path}")
            # Create a minimal deployment diagram
            nodes = [{"id": "app-server", "type": "server", "name": "Application Server"}]
            artifacts = [{"id": "app", "type": "application", "name": "Application", "node": "app-server"}]
            connections = []
        else:
            # Load and analyze configuration files
            file_contents = {}
            for file_path in deployment_files:
                try:
                    content = self.file_reader.read_file(file_path)
                    file_contents[str(file_path)] = content
                except Exception as e:
                    logger.error(f"Error reading {file_path}: {str(e)}")
            
            # Use AI to analyze deployment configuration
            nodes, artifacts, connections = self._analyze_deployment_configurations(deployment_files, file_contents)
        
        # Generate diagram
        diagram = self._generate_mermaid_deployment_diagram(nodes, artifacts, connections, title)
        
        # Prepare result
        result = {
            "title": title,
            "diagram_type": "deployment",
            "syntax_type": "mermaid",
            "content": diagram,
            "nodes": nodes,
            "artifacts": artifacts,
            "connections": connections,
            "metadata": {
                "repository": str(repo_path),
                "focus_area": focus_area,
                "node_count": len(nodes),
                "artifact_count": len(artifacts),
                "connection_count": len(connections)
            }
        }
        
        # Cache result
        self._save_to_cache(cache_key, result)
        
        # Update stats
        self.stats["deployment_diagrams_generated"] += 1
        self.stats["deployment_nodes_found"] += len(nodes)
        self.stats["deployment_artifacts_found"] += len(artifacts)
        
        return result
    
    def generate_infrastructure_diagram(
        self, 
        repo_path: Union[str, Path], 
        provider: str = None,
        title: str = "Infrastructure Diagram"
    ) -> Dict[str, Any]:
        """
        Generate a UML infrastructure diagram showing cloud resources and connections.
        
        Args:
            repo_path: Path to the repository root
            provider: Optional cloud provider filter (aws, azure, gcp)
            title: Title for the diagram
            
        Returns:
            Dictionary containing diagram data with Mermaid syntax
        """
        repo_path = Path(repo_path) if isinstance(repo_path, str) else repo_path
        
        # Check cache
        cache_key = f"infrastructure_diagram:{repo_path}:{provider or 'all'}"
        cached_result = self._check_cache(cache_key)
        if cached_result:
            return cached_result
        
        # Find infrastructure as code files
        infrastructure_files = self._find_infrastructure_files(repo_path, provider)
        
        if not infrastructure_files:
            logger.warning(f"No infrastructure as code files found in {repo_path}" +
                          (f" for provider {provider}" if provider else ""))
            # Create a minimal infrastructure diagram
            resources = [{"id": "server", "type": "compute", "name": "Server", "provider": "generic"}]
            networks = [{"id": "network", "type": "network", "name": "Network", "provider": "generic"}]
            connections = [{"source": "server", "target": "network", "type": "connection"}]
        else:
            # Load and analyze infrastructure files
            file_contents = {}
            for file_path in infrastructure_files:
                try:
                    content = self.file_reader.read_file(file_path)
                    file_contents[str(file_path)] = content
                except Exception as e:
                    logger.error(f"Error reading {file_path}: {str(e)}")
            
            # Use AI to analyze infrastructure configurations
            resources, networks, connections = self._analyze_infrastructure_configurations(
                infrastructure_files, file_contents
            )
        
        # Generate diagram
        diagram = self._generate_mermaid_infrastructure_diagram(resources, networks, connections, title)
        
        # Prepare result
        result = {
            "title": title,
            "diagram_type": "infrastructure",
            "syntax_type": "mermaid",
            "content": diagram,
            "resources": resources,
            "networks": networks,
            "connections": connections,
            "metadata": {
                "repository": str(repo_path),
                "provider": provider,
                "resource_count": len(resources) + len(networks),
                "connection_count": len(connections)
            }
        }
        
        # Cache result
        self._save_to_cache(cache_key, result)
        
        # Update stats
        self.stats["infrastructure_diagrams_generated"] += 1
        self.stats["infrastructure_resources_found"] += len(resources) + len(networks)
        
        return result
    
    def _find_deployment_files(self, path: Path) -> List[Path]:
        """
        Find deployment configuration files in the repository.
        
        Args:
            path: Repository path to search in
            
        Returns:
            List of file paths for deployment configurations
        """
        deployment_files = []
        
        # Define patterns for deployment files
        deployment_patterns = {
            # Docker files
            "Dockerfile": None,
            "docker-compose.y*ml": None,
            "*.dockerfile": None,
            "**/docker/**": None,
            
            # Kubernetes files
            "**/kubernetes/**.{yaml,yml}": None,
            "**/k8s/**.{yaml,yml}": None,
            "**/*deployment*.{yaml,yml}": None,
            "**/*service*.{yaml,yml}": None,
            "**/*ingress*.{yaml,yml}": None,
            
            # Other container configurations
            "**/docker-swarm/**.{yaml,yml}": None,
            "**/nomad/**.{hcl,nomad}": None,
            "**/helm/**": None,
            
            # Deployment scripts
            "**/deploy.sh": None,
            "**/deployment/**.sh": None,
            "**/scripts/deploy*.sh": None,
            "**/scripts/deploy*.py": None,
            
            # CI/CD configurations
            ".github/workflows/**.{yaml,yml}": None,
            ".gitlab-ci.yml": None,
            "Jenkinsfile": None,
            ".circleci/config.yml": None,
            "azure-pipelines.yml": None,
            ".travis.yml": None,
            "appveyor.yml": None
        }
        
        # Collect files that match deployment patterns
        for root, dirs, files in os.walk(path):
            # Skip version control and dependency directories
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", "venv"}]
            
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(path)
                
                # Check for direct filename matches
                if file in deployment_patterns:
                    deployment_files.append(file_path)
                    continue
                
                # Check for pattern matches
                for pattern in deployment_patterns:
                    if self._match_glob_pattern(str(rel_path), pattern):
                        deployment_files.append(file_path)
                        break
        
        return deployment_files
    
    def _find_infrastructure_files(self, path: Path, provider: str = None) -> List[Path]:
        """
        Find infrastructure as code files in the repository.
        
        Args:
            path: Repository path to search in
            provider: Optional cloud provider filter
            
        Returns:
            List of file paths for infrastructure configurations
        """
        infrastructure_files = []
        
        # Define patterns for infrastructure files by provider
        provider_patterns = {
            "aws": [
                "**/*.tf", "**/*.tfvars", 
                "**/cloudformation/**.{json,yaml,yml}",
                "**/cdk/**.{ts,js,py}",
                "**/aws-sam/**.{yaml,yml}"
            ],
            "azure": [
                "**/*.tf", "**/*.tfvars",
                "**/arm/**.{json}",
                "**/bicep/**.{bicep}"
            ],
            "gcp": [
                "**/*.tf", "**/*.tfvars",
                "**/deployment-manager/**.{yaml,yml}",
                "**/gcp/**.{yaml,yml}"
            ],
            "generic": [
                "**/*.tf", "**/*.tfvars",
                "**/pulumi/**.{ts,js,py}",
                "**/serverless/**.{yaml,yml}"
            ]
        }
        
        # Choose patterns based on provider
        patterns = []
        if provider:
            if provider in provider_patterns:
                patterns = provider_patterns[provider]
            else:
                logger.warning(f"Unknown provider: {provider}, using generic patterns")
                patterns = provider_patterns["generic"]
        else:
            # If no provider specified, use all patterns
            for prov_patterns in provider_patterns.values():
                patterns.extend(prov_patterns)
        
        # Collect files that match infrastructure patterns
        for root, dirs, files in os.walk(path):
            # Skip version control and dependency directories
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", "venv"}]
            
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(path)
                
                # Check for pattern matches
                for pattern in patterns:
                    if self._match_glob_pattern(str(rel_path), pattern):
                        infrastructure_files.append(file_path)
                        break
        
        return infrastructure_files
    
    def _analyze_deployment_configurations(
        self, 
        files: List[Path], 
        file_contents: Dict[str, str]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Analyze deployment configuration files to extract nodes, artifacts, and connections.
        
        Args:
            files: List of file paths
            file_contents: Dictionary of file contents by path
            
        Returns:
            Tuple of (nodes, artifacts, connections)
        """
        # Prepare input for AI analysis
        file_info = []
        for file_path in files:
            content = file_contents.get(str(file_path), "")
            file_type = self._get_file_type(file_path)
            
            file_info.append({
                "path": str(file_path),
                "type": file_type,
                "content": content[:5000]  # Limit content size for AI
            })
        
        # Prepare the analysis prompt
        prompt = f"""Analyze the following deployment configuration files and extract information about hardware nodes, 
execution environments, and deployed artifacts:

{json.dumps(file_info, indent=2)}

Identify:
1. Hardware nodes (servers, devices, cloud resources)
2. Execution environments (containers, VMs, runtimes)
3. Artifacts deployed to each environment
4. Communication paths between nodes
5. Dependencies between artifacts

Format your response as a structured JSON object with the following structure:
{{
  "nodes": [
    {{"id": "node-id", "type": "server|database|storage|etc", "name": "Human readable name"}},
    ...
  ],
  "artifacts": [
    {{"id": "artifact-id", "type": "container|application|service|etc", "name": "Human readable name", "node": "node-id"}},
    ...
  ],
  "connections": [
    {{"source": "node-id-or-artifact-id", "target": "node-id-or-artifact-id", "type": "http|sql|etc", "label": "Optional label"}},
    ...
  ]
}}
"""
        
        try:
            # Use AI to analyze the deployment files
            result = self.ai_provider.analyze_content(
                ", ".join(str(f) for f in files), 
                prompt
            )
            
            # Extract the components from the AI response
            nodes = result.get("nodes", [])
            artifacts = result.get("artifacts", [])
            connections = result.get("connections", [])
            
            return nodes, artifacts, connections
            
        except Exception as e:
            logger.error(f"Error in AI deployment configuration analysis: {str(e)}")
            
            # Provide a minimal fallback if AI analysis fails
            nodes = [{"id": "server", "type": "server", "name": "Server"}]
            artifacts = [{"id": "app", "type": "application", "name": "Application", "node": "server"}]
            connections = []
            
            return nodes, artifacts, connections
    
    def _analyze_infrastructure_configurations(
        self, 
        files: List[Path], 
        file_contents: Dict[str, str]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Analyze infrastructure as code files to extract resources, networks, and connections.
        
        Args:
            files: List of file paths
            file_contents: Dictionary of file contents by path
            
        Returns:
            Tuple of (resources, networks, connections)
        """
        # Prepare input for AI analysis
        file_info = []
        for file_path in files:
            content = file_contents.get(str(file_path), "")
            file_type = self._get_file_type(file_path)
            
            file_info.append({
                "path": str(file_path),
                "type": file_type,
                "content": content[:5000]  # Limit content size for AI
            })
        
        # Prepare the analysis prompt
        prompt = f"""Analyze the following infrastructure as code files and extract information about 
cloud resources, networks, and their connections:

{json.dumps(file_info, indent=2)}

Identify:
1. Compute resources (servers, instances, functions)
2. Storage resources (databases, object storage, file systems)
3. Network resources (VPCs, subnets, load balancers)
4. Security resources (security groups, IAM roles)
5. Connections between resources

Format your response as a structured JSON object with the following structure:
{{
  "resources": [
    {{"id": "resource-id", "type": "compute|database|storage|function|etc", "name": "Human readable name", "provider": "aws|azure|gcp|etc"}},
    ...
  ],
  "networks": [
    {{"id": "network-id", "type": "vpc|subnet|loadbalancer|etc", "name": "Human readable name", "provider": "aws|azure|gcp|etc"}},
    ...
  ],
  "connections": [
    {{"source": "resource-id-or-network-id", "target": "resource-id-or-network-id", "type": "contains|connects|accesses|etc", "label": "Optional label"}},
    ...
  ]
}}
"""
        
        try:
            # Use AI to analyze the infrastructure files
            result = self.ai_provider.analyze_content(
                ", ".join(str(f) for f in files), 
                prompt
            )
            
            # Extract the components from the AI response
            resources = result.get("resources", [])
            networks = result.get("networks", [])
            connections = result.get("connections", [])
            
            return resources, networks, connections
            
        except Exception as e:
            logger.error(f"Error in AI infrastructure configuration analysis: {str(e)}")
            
            # Provide a minimal fallback if AI analysis fails
            resources = [{"id": "server", "type": "compute", "name": "Server", "provider": "generic"}]
            networks = [{"id": "network", "type": "network", "name": "Network", "provider": "generic"}]
            connections = [{"source": "server", "target": "network", "type": "connection"}]
            
            return resources, networks, connections
    
    def _generate_mermaid_deployment_diagram(
        self, 
        nodes: List[Dict[str, Any]], 
        artifacts: List[Dict[str, Any]], 
        connections: List[Dict[str, Any]], 
        title: str
    ) -> str:
        """
        Generate a Mermaid deployment diagram from nodes, artifacts, and connections.
        
        Args:
            nodes: List of nodes (servers, devices)
            artifacts: List of artifacts (applications, services)
            connections: List of connections between nodes and artifacts
            title: Title for the diagram
            
        Returns:
            String with Mermaid diagram syntax
        """
        diagram = f"graph TD\n    %% {title}\n"
        
        # Create node type mapping for visual representation
        node_shapes = {
            "server": "[[\"Server: {name}\"]",
            "database": "[\"Database: {name}\"(()]",
            "storage": "[\"Storage: {name}\"[()]]",
            "device": "[\"Device: {name}\"]",
            "cloud": "[[\"Cloud: {name}\"]]",
            "container": "[\"{name}\"]",
            "runtime": "[[\"{name}\"]]"
        }
        
        # Add nodes
        for node in nodes:
            node_id = node["id"]
            node_type = node.get("type", "server")
            node_name = node.get("name", node_id)
            
            # Get shape based on type or use default server shape
            shape_template = node_shapes.get(node_type.lower(), "[\"{name}\"]")
            shape = shape_template.format(name=node_name)
            
            diagram += f"    {node_id}{shape}\n"
        
        # Add subgraphs for grouped nodes
        node_groups = {}
        for node in nodes:
            if "group" in node:
                group = node["group"]
                if group not in node_groups:
                    node_groups[group] = []
                node_groups[group].append(node["id"])
        
        for group_name, group_nodes in node_groups.items():
            diagram += f"    subgraph {group_name}\n"
            for node_id in group_nodes:
                diagram += f"        {node_id}\n"
            diagram += "    end\n"
        
        # Add artifacts
        for artifact in artifacts:
            artifact_id = artifact["id"]
            artifact_type = artifact.get("type", "application")
            artifact_name = artifact.get("name", artifact_id)
            node_id = artifact.get("node")
            
            # Use different shape based on artifact type
            if artifact_type.lower() == "container":
                shape = f">{artifact_name}]"
            elif artifact_type.lower() in ["database", "storage"]:
                shape = f"[({artifact_name})]"
            else:
                shape = f"({artifact_name})"
            
            diagram += f"    {artifact_id}{shape}\n"
            
            # Connect artifact to its node if specified
            if node_id:
                diagram += f"    {node_id} --- {artifact_id}\n"
        
        # Add connections
        for conn in connections:
            source_id = conn["source"]
            target_id = conn["target"]
            conn_type = conn.get("type", "")
            conn_label = conn.get("label", conn_type)
            
            # Add arrow showing connection
            if conn_label:
                diagram += f"    {source_id} -->|{conn_label}| {target_id}\n"
            else:
                diagram += f"    {source_id} --> {target_id}\n"
        
        return diagram
    
    def _generate_mermaid_infrastructure_diagram(
        self, 
        resources: List[Dict[str, Any]], 
        networks: List[Dict[str, Any]], 
        connections: List[Dict[str, Any]], 
        title: str
    ) -> str:
        """
        Generate a Mermaid infrastructure diagram from resources, networks, and connections.
        
        Args:
            resources: List of resources (servers, databases, etc.)
            networks: List of networks (VPCs, subnets, etc.)
            connections: List of connections between resources and networks
            title: Title for the diagram
            
        Returns:
            String with Mermaid diagram syntax
        """
        diagram = f"graph TD\n    %% {title}\n"
        
        # Create resource type mapping for visual representation
        resource_shapes = {
            "compute": "[\"{name}\"]",
            "database": "[(\"{name}\")]",
            "storage": "[(\"{name}\")]",
            "function": "[\"{name}\"/]",
            "api": "[[\"{name}\"]]",
            "loadbalancer": "[[\"{name}\"]]"
        }
        
        # Create provider styles
        provider_styles = {
            "aws": " style {id} fill:#FF9900,stroke:#232F3E",
            "azure": " style {id} fill:#008AD7,stroke:#0072C6",
            "gcp": " style {id} fill:#4285F4,stroke:#073042",
            "generic": ""
        }
        
        # Add resources
        for resource in resources:
            resource_id = resource["id"]
            resource_type = resource.get("type", "compute")
            resource_name = resource.get("name", resource_id)
            provider = resource.get("provider", "generic").lower()
            
            # Get shape based on type or use default compute shape
            shape_template = resource_shapes.get(resource_type.lower(), "[\"{name}\"]")
            shape = shape_template.format(name=resource_name)
            
            diagram += f"    {resource_id}{shape}\n"
            
            # Add provider-specific styling
            style = provider_styles.get(provider, "")
            if style:
                diagram += style.format(id=resource_id) + "\n"
        
        # Add networks
        for network in networks:
            network_id = network["id"]
            network_type = network.get("type", "network")
            network_name = network.get("name", network_id)
            provider = network.get("provider", "generic").lower()
            
            # Networks usually shown as clouds or hexagons
            if network_type.lower() in ["vpc", "vnet"]:
                shape = f"{{{{{network_name}}}}}"
            else:
                shape = f"[{network_name}]"
            
            diagram += f"    {network_id}{shape}\n"
            
            # Add provider-specific styling
            style = provider_styles.get(provider, "")
            if style:
                diagram += style.format(id=network_id) + "\n"
        
        # Add subgraphs for cloud providers
        cloud_resources = {}
        for item in resources + networks:
            provider = item.get("provider", "generic").lower()
            if provider != "generic":
                if provider not in cloud_resources:
                    cloud_resources[provider] = []
                cloud_resources[provider].append(item["id"])
        
        for provider, provider_resources in cloud_resources.items():
            diagram += f"    subgraph {provider.upper()}\n"
            for resource_id in provider_resources:
                diagram += f"        {resource_id}\n"
            diagram += "    end\n"
        
        # Add connections
        for conn in connections:
            source_id = conn["source"]
            target_id = conn["target"]
            conn_type = conn.get("type", "")
            conn_label = conn.get("label", conn_type)
            
            # Add arrow showing connection
            if conn_label:
                diagram += f"    {source_id} -->|{conn_label}| {target_id}\n"
            else:
                diagram += f"    {source_id} --> {target_id}\n"
        
        return diagram
    
    def _match_glob_pattern(self, path: str, pattern: str) -> bool:
        """
        Check if a path matches a glob pattern.
        
        Args:
            path: Path to check
            pattern: Glob pattern
            
        Returns:
            True if the path matches the pattern
        """
        # Convert glob pattern to regex pattern
        regex_pattern = pattern.replace(".", r"\.").replace("**", ".+").replace("*", "[^/]+")
        return bool(re.match(f"^{regex_pattern}$", path))
    
    def _get_file_type(self, file_path: Path) -> str:
        """
        Determine the type of a file based on its extension and name.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File type string
        """
        file_name = file_path.name.lower()
        suffix = file_path.suffix.lower()
        
        # Docker files
        if file_name == "dockerfile" or suffix == ".dockerfile":
            return "dockerfile"
        elif "docker-compose" in file_name and suffix in [".yml", ".yaml"]:
            return "docker-compose"
        
        # Kubernetes files
        elif suffix in [".yml", ".yaml"]:
            content = file_path.read_text() if file_path.exists() else ""
            if "apiVersion:" in content and "kind:" in content:
                return "kubernetes"
            
            # CI/CD files
            elif file_name == ".travis.yml":
                return "travis-ci"
            elif file_name == ".gitlab-ci.yml":
                return "gitlab-ci"
            elif "github/workflows" in str(file_path):
                return "github-actions"
            elif file_name == "azure-pipelines.yml":
                return "azure-pipelines"
        
        # Infrastructure as code files
        elif suffix == ".tf":
            return "terraform"
        elif suffix == ".tfvars":
            return "terraform-vars"
        elif suffix == ".json" and "cloudformation" in str(file_path):
            return "cloudformation"
        elif suffix == ".json" and "arm" in str(file_path):
            return "azure-arm"
        
        # Default to the file extension without the dot
        return suffix[1:] if suffix else "unknown"