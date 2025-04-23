from setuptools import setup, find_packages

setup(
    name="file_analyzer",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"":"src"},
    install_requires=[
        "mistralai",
        "python-dotenv",
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
        ],
    },
)