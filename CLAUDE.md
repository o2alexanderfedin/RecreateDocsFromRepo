# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Workflow
- Follow Test-Driven Development (TDD) process
  1. Write tests first for new functionality
  2. Commit the tests (they should fail at this point)
  3. Implement the functionality to make tests pass
  4. Commit the implementation
- Use solo developer Git workflow (no PRs)
  1. Create feature branch: `git checkout -b feature/JIRA-ID-feature-name`
  2. After implementation, merge directly to develop: `git checkout develop && git merge --no-ff feature/branch-name -m "Merge message"`
  3. Push develop branch: `git push origin develop`
  4. Delete feature branch: `git branch -d feature/branch-name && git push origin --delete feature/branch-name`

## Issue Management
- When working on an issue, use the format: `feature/CATEGORY-NUMBER-TASK-NUMBER-description`
- Example: `feature/DOC-04-TASK-03-file-relationship-linkage`
- Always reference the issue number in commit messages

## Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Individual feature branches
- `release/*`: Release preparation branches
- No pull requests - use direct merges to develop

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