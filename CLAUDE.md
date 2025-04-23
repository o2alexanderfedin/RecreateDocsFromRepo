# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Workflow
- Follow Test-Driven Development (TDD) process
  1. Write tests first for new functionality
  2. Commit the tests (they should fail at this point)
  3. Implement the functionality to make tests pass
  4. Commit the implementation

- Use Git Flow for branch management (solo developer, no PRs)
  1. Start feature: `git flow feature start CATEGORY-NUMBER-TASK-NUMBER-description`
     - Alternative: `git checkout -b feature/CATEGORY-NUMBER-TASK-NUMBER-description develop`
  2. Develop with TDD (tests first, then implementation)
  3. Finish feature: `git flow feature finish FEATURE-NAME`
     - Alternative manual steps:
       a. `git checkout develop`
       b. `git merge --no-ff feature/branch-name -m "Merge feature/branch-name: Description"`
       c. `git push origin develop`
       d. `git branch -d feature/branch-name && git push origin --delete feature/branch-name`
  
- For releases:
  1. Start release: `git flow release start VERSION`
  2. Make version bump and final adjustments
  3. Finish release: `git flow release finish VERSION`
  4. Push changes: `git push origin develop && git push origin main && git push --tags`

## Issue Management
- When working on an issue, use the format: `feature/CATEGORY-NUMBER-TASK-NUMBER-description`
- Example: `feature/DOC-04-TASK-03-file-relationship-linkage`
- Always reference the issue number in commit messages

## Branch Strategy (Git Flow)
- `main`: Production-ready code, only merge from release or hotfix branches
- `develop`: Integration branch for features, primary development branch
- `feature/*`: Individual feature branches, branch from and merge to develop
- `release/*`: Release preparation branches, branch from develop and merge to main and develop
- `hotfix/*`: Emergency fixes for production, branch from main and merge to main and develop
- No pull requests - use direct merges following Git Flow conventions
- Run git flow commands when appropriate:
  - Start feature: `git flow feature start FEATURE-NAME`
  - Finish feature: `git flow feature finish FEATURE-NAME`
  - Start release: `git flow release start VERSION`
  - Finish release: `git flow release finish VERSION`

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