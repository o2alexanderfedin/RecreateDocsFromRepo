"""
Framework detection implementation.

This module provides functionality to detect frameworks and libraries
in use across primary programming languages (Python, Java, JavaScript/TypeScript).
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Set

from file_analyzer.ai_providers.provider_interface import AIModelProvider
from file_analyzer.core.file_reader import FileReader
from file_analyzer.core.file_hasher import FileHasher
# Import only what we need from code_analyzer
from file_analyzer.core.code_analyzer import PRIMARY_LANGUAGES
from file_analyzer.core.cache_provider import CacheProvider
from file_analyzer.utils.exceptions import FileAnalyzerError

# Forward references for type checking only
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from file_analyzer.core.file_type_analyzer import FileTypeAnalyzer  
    from file_analyzer.core.code_analyzer import CodeAnalyzer

logger = logging.getLogger("file_analyzer.framework_detector")

# Framework signatures for different languages
FRAMEWORK_SIGNATURES = {
    "python": {
        "django": {
            "imports": ["django", "from django"],
            "files": ["settings.py", "urls.py", "wsgi.py", "asgi.py"],
            "directories": ["migrations"],
            "classes": ["Model", "Form", "View", "Admin", "Migration"],
            "decorators": ["@admin.register", "@receiver", "@login_required"]
        },
        "flask": {
            "imports": ["flask", "from flask"],
            "patterns": ["app = Flask", "Blueprint"],
            "decorators": ["@app.route", "@blueprint.route"]
        },
        "fastapi": {
            "imports": ["fastapi", "from fastapi"],
            "patterns": ["app = FastAPI", "APIRouter"],
            "decorators": ["@app.get", "@app.post", "@app.put", "@router.get"]
        },
        "pytorch": {
            "imports": ["torch", "from torch"],
            "classes": ["nn.Module", "Dataset", "DataLoader"]
        },
        "tensorflow": {
            "imports": ["tensorflow", "tf", "from tensorflow"],
            "patterns": ["tf.keras", "tf.data", "tf.Graph"]
        },
        "pandas": {
            "imports": ["pandas", "pd", "from pandas"]
        },
        "numpy": {
            "imports": ["numpy", "np", "from numpy"]
        },
        "sqlalchemy": {
            "imports": ["sqlalchemy", "from sqlalchemy"],
            "classes": ["Base", "Column", "Model", "Session"],
            "decorators": ["@declarative_base"]
        }
    },
    "java": {
        "spring": {
            "imports": ["org.springframework", "spring-boot", "spring-core"],
            "annotations": ["@Controller", "@Service", "@Repository", "@Component", "@Autowired", "@Bean"],
            "classes": ["SpringApplication", "ApplicationContext"]
        },
        "hibernate": {
            "imports": ["org.hibernate", "javax.persistence"],
            "annotations": ["@Entity", "@Table", "@Column", "@Id", "@GeneratedValue"]
        },
        "jakarta_ee": {
            "imports": ["jakarta.enterprise", "jakarta.inject", "javax.ejb", "javax.servlet"],
            "annotations": ["@Inject", "@Stateless", "@Stateful", "@RequestScoped"]
        },
        "junit": {
            "imports": ["org.junit", "junit.framework"],
            "annotations": ["@Test", "@Before", "@After", "@BeforeClass", "@RunWith"]
        },
        "android": {
            "imports": ["android.app", "android.os", "android.widget"],
            "classes": ["Activity", "Fragment", "Intent", "View", "Context"]
        }
    },
    "javascript": {
        "react": {
            "imports": ["react", "from 'react'", "from \"react\""],
            "patterns": ["React.Component", "useState", "useEffect", "extends Component", "createContext"],
            "jsx": ["<div>", "<React.Fragment>", "<>"]
        },
        "angular": {
            "imports": ["@angular/core", "@angular/common"],
            "decorators": ["@Component", "@Injectable", "@NgModule", "@Input", "@Output"]
        },
        "vue": {
            "imports": ["vue", "from 'vue'"],
            "patterns": ["new Vue", "createApp", "defineComponent"]
        },
        "express": {
            "imports": ["express", "from 'express'"],
            "patterns": ["express()", "app.get", "app.post", "app.use", "router.get"]
        },
        "next": {
            "imports": ["next", "from 'next'"],
            "functions": ["getStaticProps", "getServerSideProps", "getInitialProps"]
        }
    },
    "typescript": {
        # TypeScript shares many frameworks with JavaScript
        "react": {
            "imports": ["react", "from 'react'", "from \"react\""],
            "patterns": ["React.Component", "useState", "useEffect", "extends Component", "createContext"],
            "jsx": ["<div>", "<React.Fragment>", "<>"],
            "types": ["React.FC", "React.ReactNode", "React.Component<", "React.Props"]
        },
        "angular": {
            "imports": ["@angular/core", "@angular/common"],
            "decorators": ["@Component", "@Injectable", "@NgModule", "@Input", "@Output"]
        },
        "vue": {
            "imports": ["vue", "from 'vue'"],
            "patterns": ["new Vue", "createApp", "defineComponent"],
            "types": ["Vue.Component", "Vue.Directive"]
        },
        "nestjs": {
            "imports": ["@nestjs/common", "@nestjs/core"],
            "decorators": ["@Controller", "@Injectable", "@Module", "@Get", "@Post"]
        }
    }
}

# Version identification patterns
VERSION_PATTERNS = {
    "python": {
        "requirements.txt": r'(?P<framework>[\w-]+)==(?P<version>[\d\.]+)',
        "setup.py": r'install_requires=\[.*?[\'"](?P<framework>[\w-]+)[\'"].*?(?P<version>[\d\.]+)',
        "pyproject.toml": r'(?P<framework>[\w-]+)\s*=\s*[\'"](?P<version>[\d\.]+)[\'"]'
    },
    "java": {
        "pom.xml": r'<dependency>.*?<groupId>(?P<framework>[\w\.-]+)</groupId>.*?<version>(?P<version>[\w\.-]+)</version>',
        "build.gradle": r'implementation\s+[\'"](?P<framework>[\w\.-]+):(?P<module>[\w\.-]+):(?P<version>[\w\.-]+)[\'"]'
    },
    "javascript": {
        "package.json": r'"(?P<framework>[\w\.-]+)":\s*"(?P<version>[\^~><=]?[\d\.]+)"'
    }
}


class FrameworkDetector:
    """
    Detects frameworks and libraries in code repositories.
    
    This class builds on the code analyzer to identify frameworks and libraries
    used in different programming languages, along with version information
    and patterns of usage.
    """
    
    def __init__(
        self,
        ai_provider: AIModelProvider,
        code_analyzer: Optional["CodeAnalyzer"] = None,
        file_type_analyzer: Optional["FileTypeAnalyzer"] = None,
        file_reader: Optional[FileReader] = None,
        file_hasher: Optional[FileHasher] = None,
        cache_provider: Optional[CacheProvider] = None,
    ):
        """
        Initialize the framework detector.
        
        Args:
            ai_provider: Provider for AI model access
            code_analyzer: CodeAnalyzer for detailed code analysis (optional)
            file_type_analyzer: FileTypeAnalyzer for language detection (optional)
            file_reader: Component for reading files (optional)
            file_hasher: Component for hashing files (optional)
            cache_provider: Provider for caching results (optional)
        """
        self.ai_provider = ai_provider
        self.file_reader = file_reader or FileReader()
        self.file_hasher = file_hasher or FileHasher()
        
        # Import at runtime to avoid circular imports
        from file_analyzer.core.file_type_analyzer import FileTypeAnalyzer as FTA
        from file_analyzer.core.code_analyzer import CodeAnalyzer as CA
        
        # Create file type analyzer if not provided
        if file_type_analyzer is None:
            self.file_type_analyzer = FTA(
                ai_provider=ai_provider,
                file_reader=self.file_reader,
                file_hasher=self.file_hasher,
                cache_provider=cache_provider
            )
        else:
            self.file_type_analyzer = file_type_analyzer
        
        # Create code analyzer if not provided
        if code_analyzer is None:
            self.code_analyzer = CA(
                ai_provider=ai_provider,
                file_type_analyzer=self.file_type_analyzer,
                file_reader=self.file_reader,
                file_hasher=self.file_hasher,
                cache_provider=cache_provider
            )
        else:
            self.code_analyzer = code_analyzer
        
        self.cache_provider = cache_provider
        
        # Statistics for framework detection
        self.detection_stats = {
            "total_files_analyzed": 0,
            "frameworks_detected": 0,
            "languages": {},
            "detection_time": 0,
        }
    
    def detect_frameworks(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Detect frameworks used in a single code file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Dictionary with framework detection results
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path
        
        try:
            # First get the language and code structure
            code_analysis = self.code_analyzer.analyze_code(str(path))
            language = code_analysis.get("language", "").lower()
            
            # Skip if not a supported language
            if language not in PRIMARY_LANGUAGES:
                return {
                    "file_path": str(path),
                    "language": language,
                    "frameworks": [],
                    "confidence": 0.0
                }
            
            # Analyze file for framework usage
            frameworks = self._identify_frameworks_in_file(path, language, code_analysis)
            
            # Get version information if available
            version_info = self._extract_version_info(path, language)
            
            # Combine with version information
            for framework in frameworks:
                if framework["name"] in version_info:
                    framework["version"] = version_info[framework["name"]]
            
            # Update statistics
            self.detection_stats["total_files_analyzed"] += 1
            self.detection_stats["frameworks_detected"] += len(frameworks)
            self.detection_stats["languages"][language] = self.detection_stats["languages"].get(language, 0) + 1
            
            return {
                "file_path": str(path),
                "language": language,
                "frameworks": frameworks,
                "confidence": max([f["confidence"] for f in frameworks], default=0.0)
            }
            
        except Exception as e:
            logger.error(f"Error detecting frameworks in {path}: {str(e)}", exc_info=True)
            return {
                "file_path": str(path),
                "language": "unknown",
                "frameworks": [],
                "error": str(e),
                "confidence": 0.0
            }
    
    def analyze_repository(self, repo_path: Union[str, Path], file_paths: Optional[List[Union[str, Path]]] = None) -> Dict[str, Any]:
        """
        Detect frameworks used in a repository.
        
        Args:
            repo_path: Path to the repository root
            file_paths: Optional list of specific file paths to analyze
            
        Returns:
            Dictionary with repository-wide framework detection results
        """
        repo_path = Path(repo_path) if isinstance(repo_path, str) else repo_path
        
        # Reset statistics
        self.detection_stats = {
            "total_files_analyzed": 0,
            "frameworks_detected": 0,
            "languages": {},
            "detection_time": 0,
        }
        
        # If specific files provided, analyze only those
        if file_paths:
            paths_to_analyze = [Path(p) if isinstance(p, str) else p for p in file_paths]
        else:
            # Otherwise, find all potential code files
            paths_to_analyze = self._find_code_files(repo_path)
            
        # Analyze each file
        file_results = {}
        all_frameworks = {}
        
        for path in paths_to_analyze:
            result = self.detect_frameworks(path)
            file_results[str(path)] = result
            
            # Track frameworks across the repository
            for framework in result.get("frameworks", []):
                fw_name = framework["name"]
                if fw_name not in all_frameworks:
                    all_frameworks[fw_name] = {
                        "name": fw_name,
                        "language": result.get("language", "unknown"),
                        "usage": [],
                        "version": framework.get("version"),
                        "confidence": framework.get("confidence", 0.0),
                        "count": 0
                    }
                
                all_frameworks[fw_name]["count"] += 1
                all_frameworks[fw_name]["usage"].append({
                    "file_path": result.get("file_path"),
                    "features": framework.get("features", [])
                })
                
                # Take highest confidence
                if framework.get("confidence", 0.0) > all_frameworks[fw_name]["confidence"]:
                    all_frameworks[fw_name]["confidence"] = framework.get("confidence", 0.0)
        
        # Look for project-wide version files (e.g., requirements.txt, package.json)
        project_versions = self._extract_project_versions(repo_path)
        
        # Adjust framework versions based on project-wide files
        for fw_name, version_info in project_versions.items():
            if fw_name in all_frameworks:
                all_frameworks[fw_name]["version"] = version_info
                all_frameworks[fw_name]["confidence"] = max(all_frameworks[fw_name]["confidence"], 0.9)
        
        # Create final result
        framework_list = list(all_frameworks.values())
        framework_list.sort(key=lambda x: x["count"], reverse=True)
        
        return {
            "repo_path": str(repo_path),
            "frameworks": framework_list,
            "file_results": file_results,
            "statistics": self.detection_stats
        }
    
    def _identify_frameworks_in_file(self, file_path: Path, language: str, code_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify frameworks used in a specific file based on code analysis.
        
        Args:
            file_path: Path to the file
            language: Programming language of the file
            code_analysis: Results from code analysis
            
        Returns:
            List of detected frameworks with confidence scores
        """
        frameworks = []
        content = self.file_reader.read_file(file_path)
        
        # Skip if not a supported language
        if language not in FRAMEWORK_SIGNATURES:
            return frameworks
        
        # Use rule-based detection first
        signatures = FRAMEWORK_SIGNATURES.get(language, {})
        code_structure = code_analysis.get("structure", {})
        imports = code_structure.get("imports", [])
        classes = code_structure.get("classes", [])
        
        for framework_name, signature in signatures.items():
            confidence = 0.0
            features = []
            evidence = []
            
            # Check imports
            for import_sig in signature.get("imports", []):
                for imp in imports:
                    if import_sig.lower() in imp.lower():
                        confidence += 0.4
                        evidence.append(f"Import: {imp}")
                        features.append(imp)
                        break
            
            # Check files
            for file_sig in signature.get("files", []):
                if file_path.name.lower() == file_sig.lower():
                    confidence += 0.3
                    evidence.append(f"File name: {file_path.name}")
                    break
            
            # Check directories
            for dir_sig in signature.get("directories", []):
                if any(p.name.lower() == dir_sig.lower() for p in file_path.parents):
                    confidence += 0.2
                    evidence.append(f"Directory: {dir_sig}")
                    break
            
            # Check patterns in content
            for pattern in signature.get("patterns", []):
                if pattern.lower() in content.lower():
                    confidence += 0.3
                    evidence.append(f"Pattern: {pattern}")
                    features.append(pattern)
            
            # Check classes
            for class_sig in signature.get("classes", []):
                for cls in classes:
                    if isinstance(cls, dict) and class_sig.lower() in cls.get("name", "").lower():
                        confidence += 0.3
                        evidence.append(f"Class: {cls.get('name')}")
                        features.append(cls.get("name"))
                        break
            
            # Check decorators
            for decorator_sig in signature.get("decorators", []):
                if decorator_sig.lower() in content.lower():
                    confidence += 0.3
                    evidence.append(f"Decorator: {decorator_sig}")
                    features.append(decorator_sig)
            
            # Check annotations (Java)
            for annotation_sig in signature.get("annotations", []):
                if annotation_sig.lower() in content.lower():
                    confidence += 0.3
                    evidence.append(f"Annotation: {annotation_sig}")
                    features.append(annotation_sig)
            
            # Check JSX patterns
            for jsx_sig in signature.get("jsx", []):
                if jsx_sig in content:
                    confidence += 0.3
                    evidence.append(f"JSX: {jsx_sig}")
                    features.append("JSX syntax")
            
            # Normalize confidence to 0-1 range
            confidence = min(confidence, 1.0)
            
            # Add framework if confidence is high enough
            if confidence > 0.2:
                frameworks.append({
                    "name": framework_name,
                    "confidence": confidence,
                    "evidence": evidence,
                    "features": list(set(features))  # Remove duplicates
                })
        
        # If no frameworks detected with rule-based approach and file is substantial,
        # use AI-based detection as fallback
        if not frameworks and len(content) > 100:
            ai_frameworks = self._detect_frameworks_with_ai(file_path, language, content)
            frameworks.extend(ai_frameworks)
        
        # Sort by confidence
        frameworks.sort(key=lambda x: x["confidence"], reverse=True)
        return frameworks
    
    def _detect_frameworks_with_ai(self, file_path: Path, language: str, content: str) -> List[Dict[str, Any]]:
        """
        Use AI to detect frameworks when rule-based detection fails.
        
        Args:
            file_path: Path to the file
            language: Programming language of the file
            content: Content of the file
            
        Returns:
            List of detected frameworks with confidence scores
        """
        try:
            # Check if AI provider implements detect_frameworks
            if hasattr(self.ai_provider, "detect_frameworks"):
                result = self.ai_provider.detect_frameworks(str(file_path), content, language)
                return result.get("frameworks", [])
            
            # Otherwise, create a specialized prompt for framework detection
            result = self.ai_provider.analyze_content(
                str(file_path),
                f"""Analyze this {language} code and identify frameworks or libraries in use:
                
                ```{language}
                {content[:2000]}  # Limit content size for AI analysis
                ```
                
                Identify any frameworks or libraries (like Django, React, Spring, etc.) 
                with confidence level and evidence. Focus on imports, patterns, class 
                hierarchies, and framework-specific syntax.
                """
            )
            
            # Parse result
            frameworks = []
            if "frameworks" in result:
                return result["frameworks"]
            
            # Fallback parsing if AI didn't return the expected format
            for key, value in result.items():
                if isinstance(value, (float, int)) and 0 <= value <= 1:
                    frameworks.append({
                        "name": key,
                        "confidence": float(value),
                        "evidence": ["AI-based detection"],
                        "features": []
                    })
            
            return frameworks
            
        except Exception as e:
            logger.warning(f"AI-based framework detection failed: {str(e)}")
            return []
    
    def _extract_version_info(self, file_path: Path, language: str) -> Dict[str, str]:
        """
        Extract version information from a file.
        
        Args:
            file_path: Path to the file
            language: Programming language of the file
            
        Returns:
            Dictionary mapping framework names to versions
        """
        versions = {}
        
        # Skip if not a supported language
        if language not in VERSION_PATTERNS:
            return versions
        
        # Check if this is a version file (e.g., requirements.txt, package.json)
        for version_file, pattern in VERSION_PATTERNS.get(language, {}).items():
            if file_path.name == version_file:
                try:
                    import re
                    content = self.file_reader.read_file(file_path)
                    
                    for match in re.finditer(pattern, content):
                        framework = match.group("framework")
                        version = match.group("version")
                        versions[framework] = version
                except Exception as e:
                    logger.warning(f"Error extracting version info: {str(e)}")
        
        return versions
    
    def _extract_project_versions(self, repo_path: Path) -> Dict[str, str]:
        """
        Extract version information from project files.
        
        Args:
            repo_path: Path to the repository root
            
        Returns:
            Dictionary mapping framework names to versions
        """
        versions = {}
        
        # Common version files to check
        version_files = [
            # Python
            "requirements.txt",
            "setup.py",
            "pyproject.toml",
            # JavaScript
            "package.json",
            # Java
            "pom.xml",
            "build.gradle"
        ]
        
        # Check each potential version file
        for version_file in version_files:
            file_path = repo_path / version_file
            if file_path.exists():
                try:
                    language = self._get_language_from_file(file_path)
                    file_versions = self._extract_version_info(file_path, language)
                    versions.update(file_versions)
                except Exception as e:
                    logger.warning(f"Error extracting versions from {file_path}: {str(e)}")
        
        return versions
    
    def _get_language_from_file(self, file_path: Path) -> str:
        """
        Determine the language of a file based on its extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Language name or empty string if unknown
        """
        extension = file_path.suffix.lower()
        
        if extension in [".py", ".pyc", ".pyo", ".pyd"]:
            return "python"
        elif extension in [".js", ".jsx", ".mjs"]:
            return "javascript"
        elif extension in [".ts", ".tsx"]:
            return "typescript"
        elif extension in [".java", ".class", ".jar"]:
            return "java"
        elif file_path.name in ["requirements.txt", "setup.py", "pyproject.toml"]:
            return "python"
        elif file_path.name in ["package.json", "package-lock.json", "yarn.lock"]:
            return "javascript"
        elif file_path.name in ["pom.xml", "build.gradle"]:
            return "java"
        else:
            return ""
    
    def _find_code_files(self, repo_path: Path) -> List[Path]:
        """
        Find all potential code files in a repository.
        
        Args:
            repo_path: Path to the repository root
            
        Returns:
            List of file paths
        """
        code_extensions = {
            # Python
            ".py",
            # JavaScript/TypeScript
            ".js", ".jsx", ".ts", ".tsx", ".mjs",
            # Java
            ".java",
            # Version files
            ".json", ".txt", ".xml", ".gradle", ".toml"
        }
        
        exclude_dirs = {
            ".git", "node_modules", "venv", ".venv", "env", ".env", "__pycache__",
            "build", "dist", "target", "out"
        }
        
        code_files = []
        
        # Walk the repository
        for root, dirs, files in os.walk(repo_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in code_extensions):
                    file_path = Path(root) / file
                    code_files.append(file_path)
        
        return code_files