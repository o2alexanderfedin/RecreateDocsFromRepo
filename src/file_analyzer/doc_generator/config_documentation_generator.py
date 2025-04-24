"""
Configuration documentation generator.

This module provides specialized functionality for generating
detailed documentation for configuration files, integrating
results from the config analyzer and relationship mapper.
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from file_analyzer.core.config_relationship_mapper import ConfigRelationshipMapper
from file_analyzer.core.file_reader import FileReader
from file_analyzer.ai_providers.provider_interface import AIModelProvider
from file_analyzer.doc_generator.ai_documentation_generator import AiDocumentationGenerator

logger = logging.getLogger("file_analyzer.doc_generator.config_documentation_generator")


class ConfigDocumentationGenerator:
    """
    Generates enhanced documentation for configuration files.
    
    This class specializes in creating comprehensive documentation for
    configuration files, including parameter details, relationships with
    code, environmental variable usage, and practical examples.
    """
    
    def __init__(
        self,
        ai_provider: AIModelProvider,
        relationship_mapper: Optional[ConfigRelationshipMapper] = None,
        file_reader: Optional[FileReader] = None
    ):
        """
        Initialize the config documentation generator.
        
        Args:
            ai_provider: Provider for AI model access
            relationship_mapper: Mapper for config-code relationships (optional)
            file_reader: Component for reading files (optional)
        """
        self.ai_provider = ai_provider
        self.relationship_mapper = relationship_mapper
        self.file_reader = file_reader or FileReader()
        self.ai_doc_generator = AiDocumentationGenerator(ai_provider)
    
    def generate_config_documentation(
        self, 
        config_file_path: Union[str, Path],
        relationship_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive documentation for a configuration file.
        
        Args:
            config_file_path: Path to the configuration file
            relationship_data: Pre-computed relationship data (optional)
            
        Returns:
            Dictionary with enhanced documentation data
        """
        path = Path(config_file_path) if isinstance(config_file_path, str) else config_file_path
        
        try:
            # Get relationship data if not provided
            if relationship_data is None and self.relationship_mapper:
                logger.debug(f"Mapping relationships for {path}")
                relationship_data = self.relationship_mapper.map_config_to_code_relationships(path)
            
            # Read file content
            file_content = self.file_reader.read_file(path)
            
            # Extract key information from relationships
            parameters = relationship_data.get("parameters", []) if relationship_data else []
            environment_vars = relationship_data.get("environment_vars", []) if relationship_data else []
            env_var_usages = relationship_data.get("env_var_usages", []) if relationship_data else []
            direct_references = relationship_data.get("direct_references", []) if relationship_data else []
            indirect_references = relationship_data.get("indirect_references", []) if relationship_data else []
            
            # Format parameters for documentation
            formatted_parameters = []
            for param in parameters:
                formatted_parameters.append({
                    "name": param.get("path", ""),
                    "value": param.get("value", ""),
                    "type": param.get("type", ""),
                    "documentation": self._generate_parameter_documentation(param),
                    "referenced": param.get("referenced", False)
                })
            
            # Generate environment variable descriptions
            env_var_descriptions = {}
            for env_var in environment_vars:
                # Extract base name if it's in ${VAR} format
                var_name = env_var
                if env_var.startswith("${") and env_var.endswith("}"):
                    var_name = env_var[2:-1]
                
                env_var_descriptions[env_var] = self._generate_env_var_documentation(var_name, env_var_usages)
            
            # Map parameter usage in code files
            param_usage = self._map_parameter_usage(parameters, direct_references, indirect_references)
            
            # Generate AI documentation
            ai_documentation = self._generate_ai_documentation(path, file_content, relationship_data)
            
            # Build the final documentation context
            documentation_data = {
                "variables": formatted_parameters,
                "environment_vars": environment_vars,
                "env_var_descriptions": env_var_descriptions,
                "param_usage": param_usage,
                "ai_documentation": ai_documentation
            }
            
            return documentation_data
        except Exception as e:
            logger.error(f"Error generating config documentation for {path}: {str(e)}")
            return {
                "error": f"Failed to generate documentation: {str(e)}"
            }
    
    def _generate_parameter_documentation(self, parameter: Dict[str, Any]) -> str:
        """Generate documentation for a configuration parameter."""
        param_type = parameter.get("type", "").lower()
        param_path = parameter.get("path", "")
        param_value = parameter.get("value", "")
        
        # Start with basic documentation
        doc = ""
        
        # Check for existing documentation
        if "documentation" in parameter:
            return parameter["documentation"]
        
        # Generate based on type and naming conventions
        if param_type == "string":
            if "url" in param_path.lower():
                doc = "URL endpoint for the service."
            elif "path" in param_path.lower() or "dir" in param_path.lower():
                doc = "File system path."
            elif "name" in param_path.lower():
                doc = "Name identifier."
            else:
                doc = "String configuration value."
        
        elif param_type == "integer" or param_type == "number":
            if "port" in param_path.lower():
                doc = "Network port number."
            elif "timeout" in param_path.lower():
                doc = "Timeout duration in seconds."
            elif "size" in param_path.lower():
                doc = "Size limit in bytes/entries."
            elif "max" in param_path.lower():
                doc = "Maximum allowed value."
            elif "min" in param_path.lower():
                doc = "Minimum allowed value."
            else:
                doc = "Numeric configuration value."
        
        elif param_type == "boolean":
            if "enabled" in param_path.lower() or "enable" in param_path.lower():
                doc = "Flag to enable/disable this feature."
            elif "debug" in param_path.lower():
                doc = "Flag to enable debug mode."
            else:
                doc = "Boolean configuration flag."
        
        elif param_type == "array":
            doc = "List of configuration values."
        
        elif param_type == "object":
            doc = "Complex configuration object."
        
        elif param_type == "environment_variable":
            doc = "Value loaded from environment variable."
        
        # If we have an AI provider, try to enhance the documentation
        try:
            if self.ai_provider and param_path and param_value:
                context = {
                    "parameter_path": param_path,
                    "parameter_value": param_value,
                    "parameter_type": param_type,
                    "basic_documentation": doc
                }
                
                enhanced_doc = self.ai_provider.simple_completion(
                    f"Provide a concise, informative description for a configuration parameter. "
                    f"Parameter: {param_path}, Value: {param_value}, Type: {param_type}. "
                    f"Initial description: {doc}. "
                    f"Limit to about 8-10 words, focus on purpose. Must be factual, not speculative.",
                    max_tokens=50
                )
                
                if enhanced_doc and len(enhanced_doc.strip()) > 0:
                    doc = enhanced_doc.strip()
        except Exception as e:
            logger.warning(f"Error enhancing parameter documentation for {param_path}: {str(e)}")
        
        return doc
    
    def _generate_env_var_documentation(
        self, 
        env_var: str, 
        env_var_usages: List[Dict[str, Any]]
    ) -> str:
        """Generate documentation for an environment variable."""
        # Find usages of this environment variable
        usages = [usage for usage in env_var_usages if usage.get("var_name") == env_var]
        
        # Basic description
        description = "Configuration value that should be set in the environment."
        
        # Enhance description based on naming convention
        lowercase_name = env_var.lower()
        if "password" in lowercase_name or "secret" in lowercase_name or "key" in lowercase_name:
            description = "Sensitive credential or API key that should be kept secure."
        elif "host" in lowercase_name or "url" in lowercase_name:
            description = "Service endpoint or hostname."
        elif "port" in lowercase_name:
            description = "Network port number."
        elif "path" in lowercase_name or "dir" in lowercase_name:
            description = "File system path."
        elif "timeout" in lowercase_name:
            description = "Timeout value in seconds."
        
        # Try to enhance with AI if available
        try:
            if self.ai_provider:
                enhanced_desc = self.ai_provider.simple_completion(
                    f"Provide a concise description for an environment variable. "
                    f"Variable name: {env_var}. Initial description: {description}. "
                    f"Limit to about 10-12 words, focus on purpose. Must be factual, not speculative.",
                    max_tokens=50
                )
                
                if enhanced_desc and len(enhanced_desc.strip()) > 0:
                    description = enhanced_desc.strip()
        except Exception as e:
            logger.warning(f"Error enhancing environment variable documentation for {env_var}: {str(e)}")
        
        return description
    
    def _map_parameter_usage(
        self,
        parameters: List[Dict[str, Any]],
        direct_references: List[Dict[str, Any]],
        indirect_references: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Map how parameters are used in code files."""
        param_usage = {}
        
        # Process only referenced parameters
        referenced_params = [p for p in parameters if p.get("referenced", False)]
        
        for param in referenced_params:
            param_path = param.get("path", "")
            if not param_path:
                continue
            
            usages = []
            
            # Check direct references first
            for ref in direct_references:
                file_path = ref.get("file_path", "")
                references = ref.get("references", [])
                
                for reference in references:
                    line = reference.get("line", None)
                    
                    usages.append({
                        "file_path": file_path,
                        "line": line,
                        "purpose": "Direct usage"
                    })
            
            # Add indirect references if parameter is important
            if param.get("type") in ["string", "integer", "boolean"] and len(usages) > 0:
                for ref in indirect_references:
                    file_path = ref.get("file_path", "")
                    usages.append({
                        "file_path": file_path,
                        "purpose": "Indirect usage"
                    })
            
            # Add to the map if we found usages
            if usages:
                param_usage[param_path] = usages
        
        return param_usage
    
    def _generate_ai_documentation(
        self,
        file_path: Path,
        content: str,
        relationship_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI-enhanced documentation for the config file."""
        try:
            # Prepare metadata for AI documentation
            metadata = {
                "file_type": "config",
                "language": relationship_data.get("format", "unknown") if relationship_data else "unknown",
                "frameworks": [{"name": relationship_data.get("framework", "")}] if relationship_data and relationship_data.get("framework") else [],
                "purpose": "Configuration settings management",
                "parameters": relationship_data.get("parameters", []) if relationship_data else [],
                "environment_vars": relationship_data.get("environment_vars", []) if relationship_data else [],
                "code_structure": {
                    "structure": {
                        "variables": [
                            {"name": p.get("path", ""), "value": p.get("value", "")} 
                            for p in relationship_data.get("parameters", [])
                        ] if relationship_data else []
                    }
                }
            }
            
            # Generate generic AI documentation
            raw_documentation = self.ai_doc_generator.generate_file_documentation(
                file_path=str(file_path),
                content=content,
                metadata=metadata
            )
            
            # Enhance with config-specific examples
            enhanced_examples = self._generate_config_usage_examples(file_path, relationship_data)
            if enhanced_examples:
                raw_documentation["usage_examples"] = enhanced_examples
            
            return raw_documentation
        except Exception as e:
            logger.error(f"Error generating AI documentation for {file_path}: {str(e)}")
            return {}
    
    def _generate_config_usage_examples(
        self, 
        file_path: Path,
        relationship_data: Dict[str, Any]
    ) -> List[str]:
        """Generate config-specific usage examples."""
        if not relationship_data:
            return []
        
        examples = []
        file_format = relationship_data.get("format", "").lower()
        direct_references = relationship_data.get("direct_references", [])
        
        # Find a relevant code file that uses this config
        example_code_file = None
        if direct_references:
            example_code_file = direct_references[0].get("file_path", "")
        
        # Create examples based on the file format
        if file_format == "json":
            examples.append(f"```python\nimport json\n\n# Load the configuration file\nwith open('{os.path.basename(file_path)}', 'r') as config_file:\n    config = json.load(config_file)\n\n# Access configuration values\n```")
        
        elif file_format in ["yaml", "yml"]:
            examples.append(f"```python\nimport yaml\n\n# Load the configuration file\nwith open('{os.path.basename(file_path)}', 'r') as config_file:\n    config = yaml.safe_load(config_file)\n\n# Access configuration values\n```")
        
        elif file_format == "toml":
            examples.append(f"```python\nimport toml\n\n# Load the configuration file\nwith open('{os.path.basename(file_path)}', 'r') as config_file:\n    config = toml.load(config_file)\n\n# Access configuration values\n```")
        
        elif file_format == "python" and relationship_data.get("framework") == "django":
            examples.append(f"```python\nfrom django.conf import settings\n\n# Access Django settings\ndebug_mode = settings.DEBUG\n```")
        
        # Add example for environment variables if present
        if relationship_data.get("environment_vars", []):
            env_var = relationship_data["environment_vars"][0]
            var_name = env_var
            if env_var.startswith("${") and env_var.endswith("}"):
                var_name = env_var[2:-1]
            
            examples.append(f"```bash\n# Set required environment variables before running your application\nexport {var_name}=your_value\n```")
        
        return examples


def generate_config_file_documentation(
    config_file_path: Union[str, Path],
    relationship_mapper: ConfigRelationshipMapper,
    ai_provider: AIModelProvider
) -> Dict[str, Any]:
    """
    Generate documentation for a config file with one function call.
    
    Args:
        config_file_path: Path to the config file
        relationship_mapper: Mapper for config-code relationships
        ai_provider: Provider for AI completions
        
    Returns:
        Dictionary with documentation data
    """
    generator = ConfigDocumentationGenerator(
        ai_provider=ai_provider,
        relationship_mapper=relationship_mapper
    )
    
    return generator.generate_config_documentation(config_file_path)