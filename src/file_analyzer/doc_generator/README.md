# Per-File Documentation Generator

This module provides functionality to generate detailed Markdown documentation for each file in a repository based on analysis results.

## Features

- Generates one Markdown file per source file in the repository
- Creates documentation directory structure mirroring the repository
- Includes file metadata, code structure, and framework information
- Supports custom templates for different file types
- Integrates with the repository scanner and framework detector
- Generates an index file for easy navigation
- Supports file relationship analysis and linking

## Usage

### Command Line

```bash
# Generate documentation for a repository
doc-generator /path/to/repository --output-dir docs/generated

# Use a specific AI provider
doc-generator /path/to/repository --provider mistral --api-key YOUR_API_KEY

# Exclude certain files or directories
doc-generator /path/to/repository --exclude node_modules --exclude .git

# Customize documentation options
doc-generator /path/to/repository --no-code-snippets --max-code-lines 20 --no-relationships

# Use existing analysis results
doc-generator /path/to/repository --analysis-file analysis.json
```

### Python API

```python
from file_analyzer.repo_scanner import RepositoryScanner
from file_analyzer.core.file_type_analyzer import FileTypeAnalyzer
from file_analyzer.core.code_analyzer import CodeAnalyzer
from file_analyzer.core.framework_detector import FrameworkDetector
from file_analyzer.ai_providers.mock_provider import MockAIProvider
from file_analyzer.doc_generator.markdown_generator import generate_documentation

# Create the components for repository analysis
ai_provider = MockAIProvider()
file_analyzer = FileTypeAnalyzer(ai_provider=ai_provider)
code_analyzer = CodeAnalyzer(ai_provider=ai_provider, file_type_analyzer=file_analyzer)
framework_detector = FrameworkDetector(ai_provider=ai_provider, code_analyzer=code_analyzer)

# Create repository scanner
repo_scanner = RepositoryScanner(
    file_analyzer=file_analyzer,
    code_analyzer=code_analyzer,
    framework_detector=framework_detector
)

# Scan repository
repo_analysis = repo_scanner.scan(repo_path="/path/to/repository")

# Generate documentation
generate_documentation(
    repo_analysis=repo_analysis,
    output_dir="docs/generated",
    include_code_snippets=True,
    max_code_snippet_lines=15,
    include_relationships=True
)
```

## Customizing Templates

You can provide your own templates to customize the generated documentation:

```bash
doc-generator /path/to/repository --template-dir /path/to/templates
```

### Built-in Templates

The system includes several built-in templates:

- `generic_file.md.j2` - Default template for any file type
- `python_file.md.j2` - Optimized for Python source files
- `web_file.md.j2` - For HTML, CSS, JavaScript, and TypeScript files
- `config_file.md.j2` - For configuration files (JSON, YAML, TOML, etc.)
- `markup_file.md.j2` - For documentation files (Markdown, reStructuredText, etc.)

### Creating Custom Templates

You can create your own templates following these naming conventions:

1. **Language-specific templates**: Name as `{language}_file.md.j2` (e.g., `java_file.md.j2`, `ruby_file.md.j2`)
2. **Generic fallback template**: Use `generic_file.md.j2`

Template selection follows this priority order:
1. Language-specific template (e.g., `python_file.md.j2` for Python files)
2. Category-specific template (e.g., `web_file.md.j2` for HTML/CSS/JS)
3. Generic fallback template (`generic_file.md.j2`)

## Output Structure

The generated documentation follows this structure:

```
docs/generated/
├── index.md                # Main index with repository overview
├── src/                    # Mirrors the repository structure
│   ├── module1/
│   │   ├── file1.py.md     # Documentation for file1.py
│   │   └── file2.py.md     # Documentation for file2.py
│   └── module2/
│       └── file3.py.md     # Documentation for file3.py
└── ...
```

## Dependencies

- Repository Scanner
- File Type Analyzer
- Code Analyzer
- Framework Detector
- Jinja2 templating engine