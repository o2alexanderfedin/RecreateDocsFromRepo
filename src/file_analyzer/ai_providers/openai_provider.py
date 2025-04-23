"""
OpenAI provider implementation.
"""
import json
from typing import Dict, Any

from file_analyzer.ai_providers.provider_interface import AIModelProvider
from file_analyzer.utils.exceptions import AIProviderError


class OpenAIProvider(AIModelProvider):
    """OpenAI implementation."""
    
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model_name: OpenAI model to use (default: gpt-3.5-turbo)
        """
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model_name = model_name
        except ImportError:
            raise AIProviderError("OpenAI SDK not installed. Install with: pip install openai")
        except Exception as e:
            raise AIProviderError(f"Failed to initialize OpenAI client: {str(e)}")
    
    def analyze_content(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Analyze content using OpenAI API.
        
        Args:
            file_path: Path to the file being analyzed
            content: Content of the file to analyze
            
        Returns:
            Dictionary with analysis results
        """
        prompt = self._create_analysis_prompt(file_path, content)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            try:
                return json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                return {
                    "error": "Failed to parse model response as JSON",
                    "file_type": "unknown",
                    "language": "unknown",
                    "purpose": "unknown",
                    "characteristics": [],
                    "confidence": 0.0
                }
                
        except Exception as e:
            return {
                "error": f"API call failed: {str(e)}",
                "file_type": "unknown",
                "language": "unknown",
                "purpose": "unknown",
                "characteristics": [],
                "confidence": 0.0
            }
    
    def analyze_code(self, file_path: str, content: str, language: str) -> Dict[str, Any]:
        """
        Send code content to OpenAI model for structural analysis.
        
        This method overrides the default implementation in AIModelProvider
        to provide specialized code analysis for different languages.
        
        Args:
            file_path: Path to the file being analyzed
            content: Content of the file to analyze
            language: Programming language of the code
            
        Returns:
            Dictionary with code structure analysis
        """
        prompt = self._create_code_analysis_prompt(file_path, content, language)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            try:
                result = json.loads(response.choices[0].message.content)
                
                # Ensure we return in the expected format
                if "structure" not in result:
                    # If OpenAI doesn't return the expected format, wrap the result
                    return {"structure": result}
                return result
            except json.JSONDecodeError as e:
                # Return a basic structure if JSON parsing fails
                return {
                    "structure": {
                        "imports": [],
                        "classes": [],
                        "functions": [],
                        "variables": [],
                        "language_specific": {},
                        "confidence": 0.5,
                        "error": f"Failed to parse model response as JSON: {e}"
                    }
                }
                
        except Exception as e:
            # Return a basic structure if API call fails
            return {
                "structure": {
                    "imports": [],
                    "classes": [],
                    "functions": [],
                    "variables": [],
                    "language_specific": {},
                    "confidence": 0,
                    "error": f"API call failed: {str(e)}"
                }
            }
    
    def _create_analysis_prompt(self, file_path: str, content: str) -> str:
        """
        Create the analysis prompt for the OpenAI model.
        
        Args:
            file_path: Path to the file being analyzed
            content: Content of the file to analyze
            
        Returns:
            Prompt string for the AI model
        """
        return f"""
        Analyze this file and provide metadata about it in JSON format.
        
        File path: {file_path}
        File content: 
        ```
        {content}
        ```
        
        Determine the following:
        1. File type (code, configuration, documentation, etc.)
        2. Programming language (if applicable)
        3. Purpose of this file in a software project
        4. Key characteristics for documentation
        
        Respond ONLY with a JSON object with these keys:
        {{
            "file_type": string,
            "language": string,
            "purpose": string,
            "characteristics": list[string],
            "confidence": float (0-1)
        }}
        """
        
    def _create_code_analysis_prompt(self, file_path: str, content: str, language: str) -> str:
        """
        Create a specialized prompt for code structure analysis.
        
        Args:
            file_path: Path to the file being analyzed
            content: Content of the file to analyze
            language: Programming language of the code
            
        Returns:
            Prompt string for code analysis
        """
        language_constructs = {
            "python": "classes, functions, methods, imports, variables, decorators",
            "java": "classes, methods, interfaces, fields, packages, annotations",
            "javascript": "classes, functions, methods, variables, imports, exports",
            "typescript": "classes, interfaces, types, functions, methods, variables, imports, exports"
        }
        
        constructs = language_constructs.get(language.lower(), "code structures")
        
        return f"""
        Analyze this {language} code file and extract its structure in JSON format.
        
        File path: {file_path}
        Code content: 
        ```{language}
        {content}
        ```
        
        Extract the following structural elements:
        1. All imports and external dependencies
        2. Classes with their methods and properties
        3. Functions (parameters and purpose)
        4. Variables and constants
        5. {language}-specific constructs ({constructs})
        
        For each element, extract documentation if available (docstrings, comments).
        
        Respond ONLY with a JSON object matching this exact schema:
        {{
            "structure": {{
                "imports": [list of import statements],
                "classes": [
                    {{
                        "name": "class name", 
                        "methods": ["list of method names"],
                        "properties": ["list of property names"],
                        "documentation": "class docstring or comment"
                    }}
                ],
                "functions": [
                    {{
                        "name": "function name",
                        "parameters": ["list of parameter names"],
                        "documentation": "function docstring or comment"
                    }}
                ],
                "variables": [
                    {{
                        "name": "variable name", 
                        "scope": "module/class/function"
                    }}
                ],
                "language_specific": {{
                    "key features specific to {language}": []
                }},
                "confidence": float (0-1)
            }}
        }}
        
        Ensure your analysis is accurate and thorough. This will be used for documentation generation.
        """