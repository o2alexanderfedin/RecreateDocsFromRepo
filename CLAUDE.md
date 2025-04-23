# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Test Commands
- Install: `pip install -r requirements.txt`
- Run: `python main.py --repo-path /path/to/repository --output-dir /path/to/output`
- Test: `pytest`
- Single test: `pytest tests/path_to_test.py::test_function_name -v`
- Lint: `flake8` or `ruff check .`
- Type checking: `mypy .`

## Code Style Guidelines
- Follow PEP 8 conventions for Python code
- Use type hints for all function parameters and return values
- Imports: standard library first, then third-party, then local modules
- Naming: snake_case for variables/functions, PascalCase for classes
- Docstrings: Google style for all modules, classes, and functions
- Error handling: use explicit try/except blocks with specific exceptions
- Maximum line length: 88 characters (Black formatter standard)
- Use f-strings for string formatting
- Logger usage: Use the logging module instead of print statements