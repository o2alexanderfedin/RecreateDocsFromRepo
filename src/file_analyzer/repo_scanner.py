"""
Repository Scanner module.

This module provides functionality to scan a repository directory structure,
identify files, and prepare them for AI-based analysis.
"""
import asyncio
import glob
import logging
import os
from pathlib import Path
import time
from typing import Dict, List, Set, Any, Optional, Callable, Union, Tuple

from file_analyzer.core.file_type_analyzer import FileTypeAnalyzer
from file_analyzer.utils.exceptions import FileAnalyzerError

# Configure logging
logger = logging.getLogger("file_analyzer.repo_scanner")


class RepositoryScanner:
    """
    Scanner that recursively traverses repository directories and analyzes files.
    
    This class handles file discovery, filtering, and coordinates with the
    file analyzer to process files in an efficient manner.
    """
    
    # Default exclusion patterns
    DEFAULT_EXCLUSIONS = [
        # VCS directories
        ".git", ".svn", ".hg", ".bzr",
        # Package directories
        "node_modules", "venv", ".venv", "env", ".env", "__pycache__",
        "dist", "build", "target", 
        # IDE directories
        ".idea", ".vscode",
        # Binary file extensions
        "*.exe", "*.dll", "*.so", "*.dylib", "*.pyc", "*.pyo",
        "*.obj", "*.o", "*.a", "*.lib", "*.bin", "*.jar", "*.war",
        "*.ear", "*.class", "*.pyd",
        # Image files
        "*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp", "*.tiff", 
        "*.webp", "*.ico", "*.svg",
        # Audio/Video files
        "*.mp3", "*.mp4", "*.avi", "*.mov", "*.mkv", "*.flv", "*.wav",
        # Archive files
        "*.zip", "*.tar", "*.gz", "*.bz2", "*.rar", "*.7z",
        # Large data files
        "*.pdf", "*.doc", "*.docx", "*.xls", "*.xlsx", "*.ppt", "*.pptx",
        # Other binary formats
        "*.db", "*.sqlite", "*.sqlite3"
    ]
    
    # Maximum file size to analyze (10 MB by default)
    DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    
    # Priority file patterns (will be analyzed first)
    PRIORITY_PATTERNS = [
        # Documentation
        "README*", "*.md", "docs/*", "*/docs/*",
        # Configuration
        "*.json", "*.yaml", "*.yml", "*.toml", "*.ini", "*.config", 
        "package.json", "setup.py", "pyproject.toml",
        # Important source files
        "main.*", "index.*", "app.*", "*.py", "*.js", "*.ts", "*.java", "*.c", "*.cpp", "*.h"
    ]
    
    def __init__(self, 
                 analyzer: FileTypeAnalyzer,
                 exclusions: Optional[List[str]] = None,
                 max_file_size: Optional[int] = None,
                 concurrency: int = 5,
                 batch_size: int = 10,
                 priority_patterns: Optional[List[str]] = None,
                 progress_callback: Optional[Callable[[int, int], None]] = None):
        """
        Initialize the repository scanner.
        
        Args:
            analyzer: FileTypeAnalyzer instance to use for file analysis
            exclusions: List of exclusion patterns (added to defaults)
            max_file_size: Maximum file size to analyze in bytes
            concurrency: Maximum number of concurrent analysis tasks
            batch_size: Number of files to analyze in each batch
            priority_patterns: List of glob patterns for priority files
            progress_callback: Optional callback for progress reporting (files_processed, total_files)
        """
        self.analyzer = analyzer
        self.exclusions = self.DEFAULT_EXCLUSIONS.copy()
        if exclusions:
            self.exclusions.extend(exclusions)
        
        self.max_file_size = max_file_size or self.DEFAULT_MAX_FILE_SIZE
        self.concurrency = concurrency
        self.batch_size = batch_size
        self.priority_patterns = priority_patterns or self.PRIORITY_PATTERNS.copy()
        self.progress_callback = progress_callback
        
        # Statistics
        self.stats = {
            "total_files": 0,
            "analyzed_files": 0,
            "excluded_files": 0,
            "error_files": 0,
            "file_types": {},
            "languages": {},
            "processing_time": 0,
        }
    
    def scan_repository(self, repo_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Scan a repository and analyze all relevant files.
        
        Args:
            repo_path: Path to the repository root directory
            
        Returns:
            Dictionary with scan results and repository statistics
        """
        start_time = time.time()
        repo_path = Path(repo_path).resolve()
        
        if not repo_path.exists() or not repo_path.is_dir():
            raise FileAnalyzerError(f"Repository path does not exist or is not a directory: {repo_path}")
        
        logger.info(f"Starting repository scan at: {repo_path}")
        
        # Reset statistics
        self._reset_stats()
        
        # Get all files
        all_files = self._discover_files(repo_path)
        self.stats["total_files"] = len(all_files)
        
        logger.info(f"Found {len(all_files)} files in repository")
        
        # Filter and prioritize files
        filtered_files = self._filter_files(all_files, repo_path)
        self.stats["excluded_files"] = self.stats["total_files"] - len(filtered_files)
        
        logger.info(f"After filtering, {len(filtered_files)} files will be analyzed")
        
        # Analyze files
        results = self._analyze_files(filtered_files, repo_path)
        
        self.stats["analyzed_files"] = len(results)
        self.stats["processing_time"] = time.time() - start_time
        
        # Generate final statistics
        self._update_stats(results)
        
        logger.info(f"Repository scan completed in {self.stats['processing_time']:.2f} seconds")
        logger.info(f"Files analyzed: {self.stats['analyzed_files']}")
        logger.info(f"Files excluded: {self.stats['excluded_files']}")
        logger.info(f"Files with errors: {self.stats['error_files']}")
        
        return {
            "repository": str(repo_path),
            "analysis_results": results,
            "statistics": self.stats
        }
    
    async def scan_repository_async(self, repo_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Asynchronously scan a repository and analyze all relevant files.
        
        Args:
            repo_path: Path to the repository root directory
            
        Returns:
            Dictionary with scan results and repository statistics
        """
        start_time = time.time()
        repo_path = Path(repo_path).resolve()
        
        if not repo_path.exists() or not repo_path.is_dir():
            raise FileAnalyzerError(f"Repository path does not exist or is not a directory: {repo_path}")
        
        logger.info(f"Starting asynchronous repository scan at: {repo_path}")
        
        # Reset statistics
        self._reset_stats()
        
        # Get all files
        all_files = self._discover_files(repo_path)
        self.stats["total_files"] = len(all_files)
        
        logger.info(f"Found {len(all_files)} files in repository")
        
        # Filter and prioritize files
        filtered_files = self._filter_files(all_files, repo_path)
        self.stats["excluded_files"] = self.stats["total_files"] - len(filtered_files)
        
        logger.info(f"After filtering, {len(filtered_files)} files will be analyzed")
        
        # Analyze files asynchronously
        results = await self._analyze_files_async(filtered_files, repo_path)
        
        self.stats["analyzed_files"] = len(results)
        self.stats["processing_time"] = time.time() - start_time
        
        # Generate final statistics
        self._update_stats(results)
        
        logger.info(f"Repository scan completed in {self.stats['processing_time']:.2f} seconds")
        logger.info(f"Files analyzed: {self.stats['analyzed_files']}")
        logger.info(f"Files excluded: {self.stats['excluded_files']}")
        logger.info(f"Files with errors: {self.stats['error_files']}")
        
        return {
            "repository": str(repo_path),
            "analysis_results": results,
            "statistics": self.stats
        }
    
    def _discover_files(self, repo_path: Path) -> List[Path]:
        """
        Discover all files in the repository.
        
        Args:
            repo_path: Path to the repository root
            
        Returns:
            List of file paths
        """
        all_files = []
        
        # Walk directory tree
        for root, dirs, files in os.walk(repo_path):
            # Convert the root path to a Path object for easier manipulation
            root_path = Path(root)
            
            # Check if the current directory should be excluded by checking all parts
            # This handles nested directories within excluded directories (like .git/hooks/*)
            is_excluded_path = False
            for part in root_path.parts:
                if part in self.exclusions:
                    is_excluded_path = True
                    break
            
            if is_excluded_path:
                # Skip this directory entirely
                dirs[:] = []  # Clear dirs to prevent further traversal into this path
                continue
            
            # Apply directory exclusions (modify dirs in-place to skip excluded directories)
            dirs[:] = [d for d in dirs if not self._is_excluded_dir(d)]
            
            # Add files that aren't excluded
            for file in files:
                file_path = root_path / file
                all_files.append(file_path)
        
        return all_files
    
    def _filter_files(self, files: List[Path], repo_path: Path) -> List[Tuple[Path, bool]]:
        """
        Filter files based on exclusion patterns and file size.
        Prioritize important files.
        
        Args:
            files: List of file paths
            repo_path: Repository root path for relative path calculation
            
        Returns:
            Filtered and prioritized list of (file_path, is_priority) tuples
        """
        filtered_files = []
        
        for file_path in files:
            # Skip excluded files
            if self._is_excluded_file(file_path):
                continue
                
            # Skip files that are too large
            if file_path.stat().st_size > self.max_file_size:
                logger.debug(f"Skipping large file: {file_path} ({file_path.stat().st_size} bytes)")
                continue
            
            # Check if this is a priority file
            is_priority = self._is_priority_file(file_path, repo_path)
            
            # Add to filtered list with priority flag
            filtered_files.append((file_path, is_priority))
        
        # Sort files so priority files come first
        filtered_files.sort(key=lambda x: not x[1])
        
        return filtered_files
    
    def _analyze_files(self, 
                      filtered_files: List[Tuple[Path, bool]], 
                      repo_path: Path) -> Dict[str, Dict[str, Any]]:
        """
        Analyze files using the file type analyzer.
        
        Args:
            filtered_files: List of (file_path, is_priority) tuples
            repo_path: Repository root path for relative path calculation
            
        Returns:
            Dictionary mapping relative file paths to analysis results
        """
        results = {}
        total_files = len(filtered_files)
        
        for i, (file_path, _) in enumerate(filtered_files):
            try:
                # Get relative path for result key
                relative_path = os.path.relpath(file_path, repo_path)
                
                # Analyze file
                result = self.analyzer.analyze_file(file_path)
                
                # Store result
                results[relative_path] = result
                
                # Update progress
                if self.progress_callback:
                    self.progress_callback(i + 1, total_files)
                
                # Log progress periodically
                if (i + 1) % 10 == 0 or (i + 1) == total_files:
                    logger.info(f"Analyzed {i + 1}/{total_files} files ({(i + 1) / total_files * 100:.1f}%)")
                
            except Exception as e:
                logger.error(f"Error analyzing file {file_path}: {str(e)}")
                self.stats["error_files"] += 1
                
                # Add error result
                relative_path = os.path.relpath(file_path, repo_path)
                results[relative_path] = {
                    "error": str(e),
                    "file_type": "unknown",
                    "language": "unknown",
                    "purpose": "unknown",
                    "characteristics": [],
                    "confidence": 0.0
                }
        
        return results
    
    async def _analyze_files_async(self, 
                                 filtered_files: List[Tuple[Path, bool]],
                                 repo_path: Path) -> Dict[str, Dict[str, Any]]:
        """
        Asynchronously analyze files using the file type analyzer.
        
        Args:
            filtered_files: List of (file_path, is_priority) tuples
            repo_path: Repository root path for relative path calculation
            
        Returns:
            Dictionary mapping relative file paths to analysis results
        """
        results = {}
        total_files = len(filtered_files)
        processed_files = 0
        
        # Process files in batches
        for i in range(0, len(filtered_files), self.batch_size):
            batch = filtered_files[i:i + self.batch_size]
            
            # Create tasks for this batch
            tasks = []
            for file_path, _ in batch:
                tasks.append(self._analyze_file_task(file_path, repo_path))
            
            # Run tasks concurrently with limited concurrency
            batch_results = await self._run_tasks_with_concurrency(tasks, self.concurrency)
            
            # Update results
            results.update(batch_results)
            
            # Update processed count
            processed_files += len(batch)
            
            # Update progress
            if self.progress_callback:
                self.progress_callback(processed_files, total_files)
            
            # Log progress
            logger.info(f"Analyzed {processed_files}/{total_files} files ({processed_files / total_files * 100:.1f}%)")
        
        return results
    
    async def _analyze_file_task(self, file_path: Path, repo_path: Path) -> Tuple[str, Dict[str, Any]]:
        """
        Task for analyzing a single file.
        
        Args:
            file_path: Path to the file
            repo_path: Repository root path
            
        Returns:
            Tuple of (relative_path, analysis_result)
        """
        relative_path = os.path.relpath(file_path, repo_path)
        
        try:
            # Use run_in_executor to offload blocking I/O
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self.analyzer.analyze_file, file_path
            )
            
            return (relative_path, result)
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {str(e)}")
            self.stats["error_files"] += 1
            
            error_result = {
                "error": str(e),
                "file_type": "unknown",
                "language": "unknown",
                "purpose": "unknown",
                "characteristics": [],
                "confidence": 0.0
            }
            
            return (relative_path, error_result)
    
    async def _run_tasks_with_concurrency(self, tasks, concurrency):
        """
        Run tasks with limited concurrency.
        
        Args:
            tasks: List of tasks to run
            concurrency: Maximum number of concurrent tasks
            
        Returns:
            Dictionary with combined results
        """
        semaphore = asyncio.Semaphore(concurrency)
        
        async def _semaphore_task(task):
            async with semaphore:
                return await task
        
        # Wrap each task with the semaphore
        semaphore_tasks = [_semaphore_task(task) for task in tasks]
        
        # Run all tasks and gather results
        results = {}
        for result in await asyncio.gather(*semaphore_tasks, return_exceptions=False):
            if result:
                relative_path, analysis_result = result
                results[relative_path] = analysis_result
        
        return results
    
    def _is_excluded_dir(self, dir_name: str) -> bool:
        """
        Check if a directory should be excluded.
        
        Args:
            dir_name: Name of the directory
            
        Returns:
            True if the directory should be excluded
        """
        # VCS and package directories are specified without wildcards in the exclusion list
        for pattern in self.exclusions:
            # Skip patterns with wildcards - they're for file extensions, not directories
            if "*" in pattern:
                continue
                
            # Exact directory name match
            if pattern == dir_name:
                return True
        
        return False
    
    def _is_excluded_file(self, file_path: Path) -> bool:
        """
        Check if a file should be excluded.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file should be excluded
        """
        file_name = file_path.name
        
        # Check against filename/extension patterns
        for pattern in self.exclusions:
            if pattern.startswith("*"):
                # It's an extension pattern like "*.exe"
                if file_name.endswith(pattern[1:]):
                    return True
            elif pattern == file_name:
                # Exact filename match
                return True
        
        return False
    
    def _is_priority_file(self, file_path: Path, repo_path: Path) -> bool:
        """
        Check if a file should be prioritized.
        
        Args:
            file_path: Path to the file
            repo_path: Repository root path
            
        Returns:
            True if the file is a priority
        """
        file_name = file_path.name
        relative_path = os.path.relpath(file_path, repo_path)
        
        for pattern in self.priority_patterns:
            if pattern.startswith("*") and file_name.endswith(pattern[1:]):
                # Extension pattern
                return True
            elif pattern.endswith("*") and file_name.startswith(pattern[:-1]):
                # Prefix pattern
                return True
            elif "*" in pattern:
                # Path pattern with wildcard
                if glob.fnmatch.fnmatch(relative_path, pattern):
                    return True
            elif pattern == file_name:
                # Exact match
                return True
        
        return False
    
    def _reset_stats(self) -> None:
        """Reset the statistics dictionary."""
        self.stats = {
            "total_files": 0,
            "analyzed_files": 0,
            "excluded_files": 0,
            "error_files": 0,
            "file_types": {},
            "languages": {},
            "processing_time": 0,
        }
    
    def _update_stats(self, results: Dict[str, Dict[str, Any]]) -> None:
        """
        Update statistics based on analysis results.
        
        Args:
            results: Analysis results dictionary
        """
        for file_result in results.values():
            # Count file types
            file_type = file_result.get("file_type", "unknown")
            self.stats["file_types"][file_type] = self.stats["file_types"].get(file_type, 0) + 1
            
            # Count languages
            language = file_result.get("language", "unknown")
            self.stats["languages"][language] = self.stats["languages"].get(language, 0) + 1