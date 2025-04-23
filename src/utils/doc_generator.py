from pathlib import Path
from loguru import logger
from jinja2 import Environment, FileSystemLoader
import os

class DocGenerator:
    """Utility class for generating documentation from templates."""
    
    def __init__(self, template_dir: Path = None):
        if template_dir is None:
            # Use default templates directory in the package
            template_dir = Path(__file__).parent.parent / "templates"
            
        self.env = Environment(loader=FileSystemLoader(template_dir))
        logger.info(f"Initialized document generator with templates from {template_dir}")
    
    def render_template(self, template_name: str, context: dict, output_path: Path) -> Path:
        """Render a template with the given context and save to output path.
        
        Args:
            template_name: Name of the template file
            context: Dictionary of variables to pass to the template
            output_path: Path where the rendered file should be saved
            
        Returns:
            Path to the rendered file
        """
        try:
            template = self.env.get_template(template_name)
            output = template.render(**context)
            
            # Ensure output directory exists
            os.makedirs(output_path.parent, exist_ok=True)
            
            with open(output_path, 'w') as f:
                f.write(output)
                
            logger.info(f"Generated documentation at {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            raise
