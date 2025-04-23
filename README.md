# File Type Analyzer (v0.1.0)

A tool for automatically analyzing files to determine their type, language, purpose, and key characteristics using AI models.

## Features

- 🔍 **File Analysis**: Automatically detect file types, languages, and purposes.
- 🤖 **AI-Powered**: Leverages AI models (Mistral, OpenAI) for accurate analysis.
- 🔄 **Flexible Providers**: Supports multiple AI providers with a common interface.
- 💾 **Caching**: Efficiently reuses analysis results to minimize API costs.
- 📂 **Directory Support**: Analyze entire directories with filtering options.
- 📊 **Structured Output**: Results in clean, structured JSON format.

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
# Analyze a single file using Mistral AI
file-analyzer path/to/file.py --provider mistral

# Analyze a directory
file-analyzer path/to/directory --provider mistral

# Use a different provider
file-analyzer path/to/file.py --provider openai

# Save results to a file
file-analyzer path/to/directory --output results.json

# Exclude certain patterns
file-analyzer path/to/directory --exclude "**/*.log" --exclude "**/node_modules/**"

# Use the mock provider for testing (no API key needed)
file-analyzer path/to/file.py --provider mock
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
from file_analyzer.core.file_type_analyzer import FileTypeAnalyzer
from file_analyzer.ai_providers.mistral_provider import MistralProvider
from file_analyzer.core.cache_provider import InMemoryCache

# Create an analyzer with Mistral AI
analyzer = FileTypeAnalyzer(
    ai_provider=MistralProvider(api_key="your_api_key"),
    cache_provider=InMemoryCache()
)

# Analyze a file
result = analyzer.analyze_file("path/to/file.py")
print(result)
```

## Design

This project follows SOLID principles:

- **Single Responsibility**: Each class has one well-defined responsibility
- **Open/Closed**: Extensible through new AI providers without modifying existing code
- **Liskov Substitution**: Different implementations can be seamlessly substituted
- **Interface Segregation**: Clean, focused interfaces
- **Dependency Inversion**: High-level modules depend on abstractions

The architecture includes:

- **Core Components**: File reading, hashing, caching, and analysis
- **AI Providers**: Implementations for different AI models
- **CLI Interface**: User-friendly command line tool

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