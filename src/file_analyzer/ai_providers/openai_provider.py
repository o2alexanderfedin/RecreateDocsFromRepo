"""
OpenAI provider implementation.
"""
import json
from typing import Dict, Any, List

from file_analyzer.ai_providers.provider_interface import AIModelProvider
from file_analyzer.utils.exceptions import AIProviderError
# Import will be loaded at runtime to avoid circular imports 
# from file_analyzer.core.framework_detector import FRAMEWORK_SIGNATURES


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
        
    def detect_frameworks(self, file_path: str, content: str, language: str) -> Dict[str, Any]:
        """
        Detect frameworks and libraries used in a code file using OpenAI.
        
        Args:
            file_path: Path to the file being analyzed
            content: Content of the file to analyze
            language: Programming language of the code
            
        Returns:
            Dictionary with detected frameworks and libraries
        """
        prompt = self._create_framework_detection_prompt(file_path, content, language)
        
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
                if "frameworks" not in result:
                    # If response doesn't match expected format, try to extract frameworks
                    frameworks = []
                    for key, value in result.items():
                        if isinstance(value, (dict, list)):
                            if key.lower() == "frameworks":
                                # Found the frameworks key but not at the top level
                                frameworks = value if isinstance(value, list) else [value]
                                break
                            elif isinstance(value, dict) and "confidence" in value:
                                # A framework object not in a list
                                frameworks.append({"name": key, **value})
                        elif isinstance(value, (float, int)) and 0 <= value <= 1:
                            # Simple confidence score
                            frameworks.append({
                                "name": key,
                                "confidence": float(value),
                                "evidence": ["AI-based detection"],
                                "features": []
                            })
                    
                    return {"frameworks": frameworks, "confidence": 0.7}
                
                return result
                
            except json.JSONDecodeError as e:
                # Return a fallback result if JSON parsing fails
                return {
                    "frameworks": [],
                    "confidence": 0.0,
                    "error": f"Failed to parse model response as JSON: {e}"
                }
                
        except Exception as e:
            # Return a fallback result if API call fails
            return {
                "frameworks": [],
                "confidence": 0.0,
                "error": f"API call failed: {str(e)}"
            }
    
    def _create_framework_detection_prompt(self, file_path: str, content: str, language: str) -> str:
        """
        Create a specialized prompt for framework detection.
        
        Args:
            file_path: Path to the file being analyzed
            content: Content of the file to analyze
            language: Programming language of the code
            
        Returns:
            Prompt string for framework detection
        """
        # Import at runtime to avoid circular imports
        from file_analyzer.core.framework_detector import FRAMEWORK_SIGNATURES
        
        # Get known frameworks for this language to include in the prompt
        known_frameworks = []
        if language.lower() in FRAMEWORK_SIGNATURES:
            known_frameworks = list(FRAMEWORK_SIGNATURES[language.lower()].keys())
        
        frameworks_list = ", ".join(known_frameworks) if known_frameworks else f"common {language} frameworks"
        
        return f"""
        Analyze this {language} code file and identify frameworks or libraries in use.
        
        File path: {file_path}
        Code content: 
        ```{language}
        {content[:4000]}  # Limit content size for analysis
        ```
        
        Identify all frameworks and libraries used in this code (such as {frameworks_list}).
        Look for import statements, specialized syntax, framework-specific patterns, and architecture.
        For each framework detected, provide:
        1. Name of the framework
        2. Confidence level (0.0 to 1.0)
        3. Evidence of usage (imports, patterns, etc.)
        4. Features being used from the framework
        
        Respond ONLY with a JSON object matching this exact schema:
        {{
            "frameworks": [
                {{
                    "name": "framework name",
                    "confidence": float (0-1),
                    "evidence": ["list of evidence that led to detection"],
                    "features": ["list of framework features being used"]
                }}
            ],
            "confidence": float (0-1)
        }}
        
        If no frameworks are detected, return an empty frameworks array.
        """