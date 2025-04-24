# RecreateDocsFromRepo (v0.23.0)

A complete AI-powered system for analyzing codebases and generating comprehensive documentation.

## Features

- 🔍 **File Analysis**: Automatically detect file types, languages, and purposes.
- 🤖 **AI-Powered**: Leverages AI models (Mistral, OpenAI) for accurate analysis.
- 🔄 **Flexible Providers**: Supports multiple AI providers with a common interface.
- 💾 **Caching**: Efficiently reuses analysis results to minimize API costs.
- 📂 **Repository Support**: Analyze entire repositories with intelligent filtering.
- 📊 **Structured Output**: Results in clean, structured JSON format.
- 📝 **Documentation Generation**: Creates complete Markdown documentation.
- 📈 **UML Diagrams**: Generates UML diagrams for architectural views.
- 🧭 **Navigation**: Provides comprehensive navigation elements.
- 📦 **Documentation Assembly**: Creates a cohesive, validated documentation package.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/RecreateDocsFromRepo.git
cd RecreateDocsFromRepo

# Install the package
pip install -e .

# For OpenAI support
pip install -e ".[openai]"

# For development
pip install -e ".[dev]"
```

## Usage

### Command Line

```bash
# Analyze a repository and generate documentation
python main.py --repo-path /path/to/repository --output-dir /path/to/output

# Use a specific AI provider
python main.py --repo-path /path/to/repository --provider mistral

# Generate documentation with enhanced navigation
python main.py --repo-path /path/to/repository --output-dir docs/

# Generate UML diagrams for architecture documentation
python main.py --repo-path /path/to/repository --include-diagrams

# Create final documentation assembly
python main.py --repo-path /path/to/repository --final-assembly

# Customize assembly options
python main.py --repo-path /path/to/repository --final-assembly --assembly-format html --no-validate --no-optimize

# Use the mock provider for testing (no API key needed)
python main.py --repo-path /path/to/repository --provider mock
```

### Environment Variables

Set your API keys as environment variables:

```bash
# For Mistral AI
export MISTRAL_API_KEY=your_mistral_api_key

# For OpenAI
export OPENAI_API_KEY=your_openai_api_key
```

### Python API

```python
from file_analyzer.repo_scanner import RepositoryScanner
from file_analyzer.core.file_type_analyzer import FileTypeAnalyzer
from file_analyzer.core.code_analyzer import CodeAnalyzer
from file_analyzer.core.framework_detector import FrameworkDetector
from file_analyzer.ai_providers.mistral_provider import MistralProvider
from file_analyzer.core.cache_provider import InMemoryCache
from file_analyzer.doc_generator.markdown_generator import generate_documentation
from file_analyzer.doc_generator.documentation_assembler import DocumentationAssembler, AssemblyConfig

# Create providers
ai_provider = MistralProvider(api_key="your_api_key")
cache_provider = InMemoryCache()

# Create analyzers
file_analyzer = FileTypeAnalyzer(ai_provider=ai_provider, cache_provider=cache_provider)
code_analyzer = CodeAnalyzer(ai_provider=ai_provider, file_type_analyzer=file_analyzer, cache_provider=cache_provider)
framework_detector = FrameworkDetector(ai_provider=ai_provider, code_analyzer=code_analyzer, file_type_analyzer=file_analyzer, cache_provider=cache_provider)

# Create repository scanner
scanner = RepositoryScanner(
    file_analyzer=file_analyzer,
    code_analyzer=code_analyzer,
    framework_detector=framework_detector
)

# Scan repository
repo_analysis = scanner.scan(repo_path="/path/to/repository")

# Generate documentation
documentation_result = generate_documentation(
    repo_analysis=repo_analysis,
    output_dir="/path/to/output",
    include_relationships=True,
    include_framework_details=True
)

# Create final assembly
assembly_config = AssemblyConfig(
    output_dir="/path/to/output/assembled",
    input_dirs=["/path/to/output"],
    validate_output=True,
    optimize_output=True
)
assembler = DocumentationAssembler(assembly_config)
assembly_result = assembler.assemble_documentation()

print(f"Documentation generated: {documentation_result['documentation_files_generated']} files")
print(f"Assembly processed: {assembly_result['files_processed']} files")
```

## Design

This project follows SOLID principles throughout all components:

- **Single Responsibility**: Each class has one well-defined responsibility
- **Open/Closed**: Extensible through new providers and components without modifying existing code
- **Liskov Substitution**: Different implementations can be seamlessly substituted
- **Interface Segregation**: Clean, focused interfaces for each component
- **Dependency Inversion**: High-level modules depend on abstractions, not implementations

The architecture includes:

- **Repository Analysis**: File reading, code analysis, framework detection
- **AI Providers**: Implementations for different AI models (Mistral, OpenAI)
- **Documentation Generation**: Markdown formatting, template-based generation
- **UML Diagrams**: Generators for all views in the 4+1 architectural model
- **Documentation Structure**: Hierarchical organization with multiple views
- **Navigation Components**: Breadcrumbs, TOC, cross-references
- **Final Assembly**: Integration, validation, optimization
- **CLI Interface**: Comprehensive command line tool

## Testing

Tests are written using pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=file_analyzer

# Run specific test file
pytest src/file_analyzer/tests/test_file_reader.py
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.