from setuptools import setup, find_packages

setup(
    name="file_analyzer",
    version="0.8.0",
    packages=find_packages(where="src"),
    package_dir={"":"src"},
    install_requires=[
        "mistralai",
        "python-dotenv",
        "jinja2>=3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov",
            "black",
        ],
        "openai": ["openai>=1.0.0"],
    },
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "file-analyzer=file_analyzer.main:main",
            "repo-scanner=file_analyzer.repo_scanner_cli:main",
            "cache-manager=file_analyzer.cache_manager:main",
            "doc-generator=file_analyzer.doc_generator.cli:main",
        ],
    },
)