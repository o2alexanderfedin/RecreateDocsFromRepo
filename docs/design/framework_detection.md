# Framework Detection System Design

This document provides a detailed design overview of the Framework Detection system, which identifies frameworks and libraries used in code repositories.

## 1. Introduction

The Framework Detection system is designed to identify programming frameworks and libraries used in source code across multiple languages. It uses a hybrid approach combining rule-based signature matching with AI-assisted analysis to provide comprehensive, accurate detection with high confidence.

### 1.1 Purpose and Goals

The primary purpose of the Framework Detection system is to:

1. Identify which frameworks and libraries are used in a codebase
2. Determine which versions of these frameworks are in use
3. Analyze how frameworks are being used within the code
4. Provide confidence scores for each detection
5. Support the documentation generation process

These capabilities help developers understand codebases more quickly and generate more accurate documentation.

## 2. System Architecture

### 2.1 Component Diagram

```mermaid
classDiagram
    class FrameworkDetector {
        +detect_frameworks(file_path) Dict
        +analyze_repository(repo_path) Dict
        -_identify_frameworks_in_file(file_path, language, code_analysis) List
        -_detect_frameworks_with_ai(file_path, language, content) List
        -_extract_version_info(file_path, language) Dict
        -_extract_project_versions(repo_path) Dict
        -_get_language_from_file(file_path) str
        -_find_code_files(repo_path) List
    }
    
    class FRAMEWORK_SIGNATURES {
        <<constant>>
        +python: Dict
        +java: Dict
        +javascript: Dict
        +typescript: Dict
    }
    
    class VERSION_PATTERNS {
        <<constant>>
        +python: Dict
        +java: Dict
        +javascript: Dict
    }
    
    class CodeAnalyzer {
        +analyze_code(file_path) Dict
    }
    
    class FileTypeAnalyzer {
        +analyze_file(file_path) Dict
    }
    
    class FileReader {
        +read_file(file_path) str
    }
    
    class AIModelProvider {
        +detect_frameworks(file_path, content, language) Dict
    }
    
    class CacheProvider {
        +get(key) Dict
        +set(key, value) void
    }
    
    FrameworkDetector --> FRAMEWORK_SIGNATURES : uses
    FrameworkDetector --> VERSION_PATTERNS : uses
    FrameworkDetector --> CodeAnalyzer : depends on
    FrameworkDetector --> FileTypeAnalyzer : depends on
    FrameworkDetector --> FileReader : uses
    FrameworkDetector --> AIModelProvider : uses
    FrameworkDetector --> CacheProvider : uses
```

### 2.2 Data Flow Diagram

```mermaid
graph TD
    A[Input: File Path] --> B[FrameworkDetector]
    
    B --> C{Get Code Analysis}
    C --> D[CodeAnalyzer]
    D --> E[Code Structure]
    
    E --> F{Is Supported Language?}
    F -->|No| G[Return Empty Result]
    F -->|Yes| H[Match Framework Signatures]
    
    H --> I{Strong Signature Match?}
    I -->|Yes| J[Rule-based Detection]
    I -->|No| K[AI-assisted Detection]
    
    J --> L[Collect Evidence & Features]
    K --> L
    
    L --> M{Dependency File?}
    M -->|Yes| N[Extract Version Info]
    M -->|No| O[Combine Results]
    N --> O
    
    O --> P[Return Detection Results]
```

## 3. Rule-Based Detection

### 3.1 Framework Signatures Structure

The system uses a comprehensive set of signatures to identify frameworks through pattern matching:

```mermaid
graph TD
    A[Framework Signatures] --> B{Language}
    
    B -->|Python| C[Python Frameworks]
    B -->|Java| D[Java Frameworks]
    B -->|JavaScript| E[JavaScript Frameworks]
    B -->|TypeScript| F[TypeScript Frameworks]
    
    C --> C1[Django]
    C --> C2[Flask]
    C --> C3[FastAPI]
    C --> C4[Pandas]
    C --> C5[PyTorch]
    
    D --> D1[Spring]
    D --> D2[Hibernate]
    D --> D3[Jakarta EE]
    D --> D4[JUnit]
    
    E --> E1[React]
    E --> E2[Angular]
    E --> E3[Vue]
    E --> E4[Express]
    
    F --> F1[React w/Types]
    F --> F2[Angular]
    F --> F3[NestJS]
    
    C1 --> G[Signature Types]
    D1 --> G
    E1 --> G
    F1 --> G
    
    G --> G1[Imports]
    G --> G2[File Patterns]
    G --> G3[Directory Patterns]
    G --> G4[Class Names]
    G --> G5[Method Patterns]
    G --> G6[Decorators/Annotations]
```

### 3.2 Example Signature (Django)

```python
"django": {
    "imports": ["django", "from django"],
    "files": ["settings.py", "urls.py", "wsgi.py", "asgi.py"],
    "directories": ["migrations"],
    "classes": ["Model", "Form", "View", "Admin", "Migration"],
    "decorators": ["@admin.register", "@receiver", "@login_required"]
}
```

### 3.3 Version Detection

The system extracts version information from dependency files using regular expression patterns:

```mermaid
graph TD
    A[Version Detection] --> B{File Type}
    
    B -->|requirements.txt| C["Python: r'(?P<framework>[\\w-]+)==(?P<version>[\\d\\.]+)'"]
    B -->|setup.py| D["Python: r'install_requires=\\[.*?[\\'\\"](?P<framework>[\\w-]+)[\\'\\"].*?(?P<version>[\\d\\.]+)'"]
    B -->|pyproject.toml| E["Python: r'(?P<framework>[\\w-]+)\\s*=\\s*[\\'\\"](?P<version>[\\d\\.]+)[\\'\\"]'"]
    
    B -->|pom.xml| F["Java: r'<dependency>.*?<groupId>(?P<framework>[\\w\\.-]+)</groupId>.*?<version>(?P<version>[\\w\\.-]+)</version>'"]
    B -->|build.gradle| G["Java: r'implementation\\s+[\\'\\"](?P<framework>[\\w\\.-]+):(?P<module>[\\w\\.-]+):(?P<version>[\\w\\.-]+)[\\'\\"]'"]
    
    B -->|package.json| H["JavaScript: r'\"(?P<framework>[\\w\\.-]+)\":\\s*\"(?P<version>[\\^~><]?[\\d\\.]+)\"'"]
```

## 4. AI-Assisted Detection

### 4.1 Detection Flow

When rule-based detection doesn't provide strong matches or for complex frameworks, the system falls back to AI-assisted detection:

```mermaid
sequenceDiagram
    participant FD as FrameworkDetector
    participant AI as AIModelProvider
    
    FD->>FD: Try rule-based detection
    Note over FD: Confidence below threshold (0.2)
    
    FD->>FD: Prepare framework detection prompt
    Note over FD: Include known frameworks for language
    
    FD->>AI: detect_frameworks(file_path, content, language)
    AI->>AI: Process content with AI model
    AI-->>FD: AI detection results
    
    FD->>FD: Normalize AI responses
    Note over FD: Convert to standard format
    
    FD->>FD: Combine with rule-based results
    Note over FD: Prioritize high-confidence results
```

### 4.2 Provider-Specific Implementations

```mermaid
classDiagram
    class AIModelProvider {
        <<interface>>
        +detect_frameworks(file_path, content, language) Dict
    }
    
    class MistralProvider {
        +detect_frameworks(file_path, content, language) Dict
        -_create_framework_detection_prompt(file_path, content, language) str
    }
    
    class OpenAIProvider {
        +detect_frameworks(file_path, content, language) Dict
        -_create_framework_detection_prompt(file_path, content, language) str
    }
    
    class MockAIProvider {
        +detect_frameworks(file_path, content, language) Dict
        -_detect_frameworks_for_language(file_path, content, language) List
    }
    
    AIModelProvider <|.. MistralProvider
    AIModelProvider <|.. OpenAIProvider
    AIModelProvider <|.. MockAIProvider
```

## 5. Repository-Wide Analysis

### 5.1 Analysis Process

The Framework Detector can analyze entire repositories to provide a comprehensive view of framework usage:

```mermaid
sequenceDiagram
    participant Client
    participant FD as FrameworkDetector
    
    Client->>FD: analyze_repository(repo_path)
    
    FD->>FD: Find code files in repository
    
    loop For Each File
        FD->>FD: detect_frameworks(file_path)
        FD->>FD: Collect results
    end
    
    FD->>FD: Find project-wide version files
    Note over FD: requirements.txt, package.json, etc.
    
    FD->>FD: Extract version information
    
    FD->>FD: Aggregate framework results
    Note over FD: Combine evidence and features
    
    FD->>FD: Calculate usage statistics
    
    FD-->>Client: Complete repository framework analysis
```

### 5.2 Repository Results Structure

```
{
    "repo_path": "/path/to/repo",
    "frameworks": [
        {
            "name": "django",
            "language": "python",
            "version": "3.2.4",
            "confidence": 0.95,
            "count": 15,
            "usage": [
                {
                    "file_path": "/path/to/models.py",
                    "features": ["models.Model", "migrations"]
                },
                {
                    "file_path": "/path/to/views.py",
                    "features": ["HttpResponse", "TemplateView"]
                }
            ]
        },
        {
            "name": "react",
            "language": "javascript",
            "version": "17.0.2",
            "confidence": 0.9,
            "count": 8,
            "usage": [...]
        }
    ],
    "file_results": {...},
    "statistics": {
        "total_files_analyzed": 45,
        "frameworks_detected": 5,
        "languages": {"python": 20, "javascript": 25},
        "detection_time": 1.5
    }
}
```

## 6. Performance Considerations

### 6.1 Caching Strategy

```mermaid
sequenceDiagram
    participant Client
    participant FD as FrameworkDetector
    participant CP as CacheProvider
    
    Client->>FD: detect_frameworks(file_path)
    
    FD->>FD: Generate cache key from file hash
    FD->>CP: get(cache_key)
    
    alt Cache hit
        CP-->>FD: cached framework results
        FD-->>Client: cached results
    else Cache miss
        FD->>FD: Perform full detection
        FD->>CP: set(cache_key, results)
        FD-->>Client: fresh results
    end
```

### 6.2 Processing Optimizations

1. **Early Filtering**:
   - Skip files that aren't likely to contain framework information
   - Prioritize key files like imports and configuration

2. **Content Limiting**:
   - For AI analysis, only send the most relevant parts of large files
   - Analyze imports and structural elements first

3. **Confidence Thresholds**:
   - Use fast rule-based checks first
   - Only fall back to AI analysis when necessary

4. **Framework-Aware Priorities**:
   - Prioritize checking for frameworks commonly used in the detected language
   - Skip checks for frameworks incompatible with the language

## 7. Extension Points

### 7.1 Adding New Frameworks

To add support for a new framework:

```mermaid
graph TD
    A[Identify Framework] --> B[Document Signature Patterns]
    B --> C[Add to FRAMEWORK_SIGNATURES]
    C --> D[Add Version Patterns if Needed]
    D --> E[Test with Sample Code]
    E --> F[Adjust Confidence Weights]
    F --> G[Update Documentation]
```

Example implementation:

```python
# Add to FRAMEWORK_SIGNATURES
FRAMEWORK_SIGNATURES["python"]["new_framework"] = {
    "imports": ["new_framework", "from new_framework"],
    "patterns": ["NewFrameworkClass", "special_function"],
    "decorators": ["@new_framework.decorator"]
}

# Add to VERSION_PATTERNS if needed
VERSION_PATTERNS["python"]["new_requirement_file.txt"] = r'new_framework[>=](?P<version>[\d\.]+)'
```

### 7.2 Adding New Languages

To add support for a new programming language:

```mermaid
graph TD
    A[Define Language Patterns] --> B[Add Language to PRIMARY_LANGUAGES]
    B --> C[Create Framework Signatures Map]
    C --> D[Add Version Pattern Support]
    D --> E[Implement Language-Specific Detection Logic]
    E --> F[Test with Sample Code]
    F --> G[Update Documentation]
```

Example implementation:

```python
# Add to PRIMARY_LANGUAGES in code_analyzer.py
PRIMARY_LANGUAGES.append("new_language")

# Add language signatures
FRAMEWORK_SIGNATURES["new_language"] = {
    "framework1": {
        "imports": ["framework1"],
        "patterns": ["FrameworkClass"],
        # ...additional signatures
    }
}

# Add version patterns
VERSION_PATTERNS["new_language"] = {
    "dependency_file.ext": r'pattern_to_extract_version'
}
```

## 8. Testing Strategy

### 8.1 Testing Approach

```mermaid
graph TD
    A[Testing Strategy] --> B[Unit Tests]
    A --> C[Integration Tests]
    A --> D[Real API Tests]
    
    B --> B1[Test Individual Detection Methods]
    B --> B2[Test with Mock AI Provider]
    B --> B3[Test Signature Matching]
    B --> B4[Test Version Extraction]
    
    C --> C1[Test with Real Files]
    C --> C2[Test Repository Analysis]
    C --> C3[Test with Mixed Frameworks]
    
    D --> D1[Test with Mistral API]
    D --> D2[Test Framework Detection Prompts]
    D --> D3[Test Response Handling]
```

### 8.2 Key Test Cases

1. **Single Framework Detection**:
   - Test detection of each supported framework individually
   - Verify correct evidence and feature extraction

2. **Mixed Framework Detection**:
   - Test files using multiple frameworks together
   - Verify all frameworks are detected with appropriate confidence

3. **Version Extraction**:
   - Test extraction from various dependency file formats
   - Test with different version formats (semantic versioning, ranges, etc.)

4. **AI Fallback**:
   - Test cases where rule-based detection fails
   - Verify AI provider is called and results are processed correctly

5. **Repository Analysis**:
   - Test with mock repositories containing mixed frameworks
   - Verify statistics and aggregation logic

## 9. Usage Examples

### 9.1 Detecting Frameworks in a Single File

```python
# Create a framework detector
detector = FrameworkDetector(
    ai_provider=MistralProvider(api_key="your_key"),
    cache_provider=InMemoryCache()
)

# Detect frameworks in a file
result = detector.detect_frameworks("path/to/file.py")
print(f"Detected frameworks: {[f['name'] for f in result['frameworks']]}")
```

### 9.2 Analyzing an Entire Repository

```python
# Create a framework detector
detector = FrameworkDetector(
    ai_provider=MistralProvider(api_key="your_key"),
    cache_provider=InMemoryCache()
)

# Analyze entire repository
repo_result = detector.analyze_repository("path/to/repo")

# Display framework usage
for framework in repo_result["frameworks"]:
    print(f"{framework['name']} ({framework['version']}): Used in {framework['count']} files")
    print(f"  Confidence: {framework['confidence']}")
    print(f"  Features: {set(f for usage in framework['usage'] for f in usage['features'])}")
```

### 9.3 Integration with Documentation Generation

```python
# Analyze repository for frameworks
frameworks = detector.analyze_repository("path/to/repo")["frameworks"]

# Generate framework documentation section
doc = ["## Frameworks and Libraries\n"]
for framework in frameworks:
    doc.append(f"### {framework['name']} (v{framework['version']})")
    doc.append(f"**Language**: {framework['language']}")
    doc.append(f"**Usage**: Found in {framework['count']} files")
    
    # List key features
    features = set(f for usage in framework['usage'] for f in usage['features'])
    doc.append("\n**Key Components Used**:")
    for feature in features:
        doc.append(f"- {feature}")
    
    doc.append("\n")

# Write documentation
with open("framework_documentation.md", "w") as f:
    f.write("\n".join(doc))
```

## 10. Conclusion

The Framework Detection system is a powerful component that provides valuable insights into the frameworks and libraries used in a codebase. Its hybrid approach combining rule-based detection with AI-assisted analysis ensures high accuracy while maintaining performance.

Key strengths of the system include:

1. **Comprehensive Detection**: Supports multiple languages and frameworks
2. **Accurate Version Information**: Extracts version data from dependency files
3. **Detailed Usage Analysis**: Identifies how frameworks are being used
4. **Repository-Wide View**: Provides a holistic view of framework usage
5. **Extensible Design**: Easy to add support for new frameworks and languages

This system forms a critical part of the overall code analysis and documentation generation process, enabling more complete and accurate understanding of codebases.