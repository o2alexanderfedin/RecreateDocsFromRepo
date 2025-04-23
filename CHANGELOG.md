# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-04-23

### Added
- Repository Scanner component for analyzing entire code repositories
  - Recursive directory traversal with configurable exclusions
  - Intelligent file filtering (binary, large files, common exclusions)
  - Priority-based file processing
  - Both synchronous and asynchronous processing modes
  - Concurrency control and batch processing
  - Progress reporting for large repositories
  - Comprehensive file statistics collection
- Command-line interface for the Repository Scanner
  - Support for different AI providers
  - Configurable concurrency and batch size
  - Progress reporting with progress bar
  - Output formatting options
  - JSON file output

### Changed
- Updated task documentation to reflect completed components

### Fixed
- Improved directory exclusion logic for nested paths

## [0.1.0] - 2025-04-23

### Added
- Initial version of the File Type Analyzer component
- Core implementation with SOLID design principles
- Multiple AI provider support:
  - Mistral AI integration
  - OpenAI provider support
  - Mock provider for testing
- Caching system to optimize API usage
- File reading and hashing utilities
- Error handling and fallback mechanisms
- Command-line interface for file analysis
- Unit and integration tests
- Real API integration tests
- Documentation for usage and development

### Changed
- N/A (initial release)

### Fixed
- N/A (initial release)