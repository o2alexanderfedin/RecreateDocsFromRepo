# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2025-04-23

### Added
- Framework Detection System for identifying frameworks and libraries in code:
  - Support for Python, Java, JavaScript, and TypeScript frameworks
  - Comprehensive signatures for popular frameworks like Django, Flask, React, Spring, etc.
  - Version extraction from dependency files (requirements.txt, package.json, etc.)
  - AI-assisted detection with rule-based fallback mechanisms
  - Repository-wide framework analysis with usage statistics
  - Documentation of framework usage patterns
- Enhanced AI provider interfaces:
  - Extended with framework detection capabilities
  - Specialized prompts for framework detection in different languages
  - Robust error handling and response formatting
- Comprehensive test suite:
  - Unit tests with proper mocking for reproducibility
  - Integration tests with real files
  - Real API tests for Mistral AI integration
  - Test coverage reports and documentation

### Changed
- Improved AI provider interface with runtime imports to avoid circular dependencies
- Enhanced error handling with better logging
- Updated test infrastructure to support real API testing with environment variables
- Updated package exports to include new framework components
- Improved code structure to more cleanly separate concerns

### Fixed
- Fixed circular import issues between modules
- Improved mock implementation for testing

## [0.4.0] - 2025-04-23

### Added
- AI Code Analyzer component for detailed code structure extraction:
  - Support for primary languages (Python, Java, JavaScript, TypeScript)
  - Extraction of classes, methods, functions, variables, and imports
  - Language-specific construct detection (interfaces, types, decorators)
  - Documentation extraction from comments and docstrings
  - File chunking for handling large code files
  - Comprehensive mock implementation for testing
- Enhanced AI provider interfaces:
  - Extended Mistral provider with code analysis capabilities
  - Extended OpenAI provider with code analysis capabilities
  - Specialized prompts for different programming languages
  - Strong error handling and response formatting
- Comprehensive test suite:
  - Unit tests for all code analyzer components
  - Integration tests with existing systems
  - Real API tests for Mistral AI integration

### Changed
- Improved language detection with case-insensitive matching
- Enhanced file type detection to handle varying type descriptions
- Updated provider interface to support code structure analysis

### Fixed
- Fixed issue with case sensitivity in language detection
- Improved error handling for unsupported file types

## [0.3.0] - 2025-04-23

### Added
- Enhanced caching system with multiple backends:
  - In-memory cache with LRU eviction and TTL
  - SQLite-based persistent cache
  - File system cache for larger datasets
  - Tiered caching system combining multiple backends
- Cache management features:
  - Cache statistics tracking and reporting
  - Automatic cache expiration and eviction
  - Cache pre-warming capabilities
  - Cache configuration system
- New cache-manager CLI utility:
  - View cache statistics
  - Clear cache data
  - Pre-warm cache with known file types
  - Export cache data
- Enhanced command-line options for caching in file-analyzer and repo-scanner tools
- Comprehensive test suite for all cache implementations

### Changed
- Updated FileTypeAnalyzer to use the enhanced caching system
- Improved CLI interface with better organization of options
- Enhanced progress reporting with cache statistics

### Fixed
- Fixed potential race conditions in cache access
- Improved error handling in cache operations

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