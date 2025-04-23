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