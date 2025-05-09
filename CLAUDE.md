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
  3. Make final implementation commit with issue closing reference:
     - `git commit -m "Implement feature description. Closes #ISSUE-NUMBER"`
  4. Finish feature: `git flow feature finish FEATURE-NAME`
     - Alternative manual steps:
       a. `git checkout develop`
       b. `git merge --no-ff feature/branch-name -m "Merge feature/branch-name: Description"`
       c. `git push origin develop`
       d. `git branch -d feature/branch-name && git push origin --delete feature/branch-name`
  5. Merge feature to current release branch (if one exists):
     - `git checkout release/[CURRENT_VERSION]`
     - `git merge --no-ff develop -m "Merge develop into release/[CURRENT_VERSION]: Add feature description"`
     - `git push origin release/[CURRENT_VERSION]`
  6. Always verify issue is closed and close it manually if needed:
     - Check issue status: `gh issue view ISSUE-NUMBER`
     - Close issue manually: `gh issue close ISSUE-NUMBER --reason completed`
     - Add closure comment: `gh issue comment ISSUE-NUMBER --body "Implementation complete, merged to develop and release/[CURRENT_VERSION]"`
     
  7. Check and update parent issues:
     - After closing a task issue, check if the parent user story should be closed
     - After closing a user story, check if the parent epic should be closed
     - Follow the hierarchical issue management rules in the Issue Management section
  
- For releases:
  1. Start release: `git flow release start VERSION`
  2. Make version bump and final adjustments
  3. Finish release: `git flow release finish VERSION`
     - This merges to both main and develop, creates a tag
  4. Push changes: `git push origin develop && git push origin main && git push --tags`

- For hotfixes (production bugs):
  1. Start hotfix: `git flow hotfix start VERSION`
  2. Implement and test the fix
  3. Update version numbers and CHANGELOG.md
  4. Finish hotfix: `git flow hotfix finish VERSION`
     - This merges to both main and develop, creates a tag
  5. Push changes: `git push origin develop && git push origin main && git push --tags`

- Emergency procedure (avoid when possible):
  1. Direct main update: `git checkout main`
  2. Make changes and test thoroughly
  3. Commit: `git commit -m "Emergency fix: description"`
  4. Push main: `git push origin main`
  5. Sync to develop: `git checkout develop && git merge main && git push origin develop`

## Issue Management
- When working on an issue, use the format: `feature/CATEGORY-NUMBER-TASK-NUMBER-description`
- Example: `feature/DOC-04-TASK-03-file-relationship-linkage`
- Always reference the issue number in commit messages
- Close issues automatically when work is complete:
  - Include "Closes #ISSUE-NUMBER" or "Fixes #ISSUE-NUMBER" in commit message
  - Example: `git commit -m "Implement file relationship linkage. Closes #43"`
  - IMPORTANT: Always explicitly verify issue closure:
    - Check issue status: `gh issue view ISSUE-NUMBER`
    - Close issue manually if not closed automatically: `gh issue close ISSUE-NUMBER --reason completed`
    - Add closure comment: `gh issue comment ISSUE-NUMBER --body "Implementation complete in commit SHA: $(git rev-parse HEAD)"`

### Hierarchical Issue Management Rules
- When a task/fix is completed:
  1. Close the task/fix issue with appropriate comment
  2. Check if this was the last open task for its parent user story
  3. If no more active tasks exist, close the parent user story
  4. Check if this was the last open user story for its parent epic
  5. If no more active user stories exist, close the parent epic

- Re-opening rules:
  1. If a new task is added to a closed user story → Re-open the user story
  2. If a closed user story is re-opened → Check if its parent epic needs to be re-opened
  3. If a new user story is added to a closed epic → Re-open the epic

- Follow these steps to check and update parent issues:
  ```bash
  # Check if all tasks for a user story are closed
  gh issue list --search "user-story:USER-STORY-NUMBER state:open"
  
  # If no results, close the user story
  gh issue close USER-STORY-NUMBER --reason completed
  gh issue comment USER-STORY-NUMBER --body "All tasks completed - closing user story"
  
  # Check if all user stories for an epic are closed
  gh issue list --search "epic:EPIC-NUMBER state:open"
  
  # If no results, close the epic
  gh issue close EPIC-NUMBER --reason completed
  gh issue comment EPIC-NUMBER --body "All user stories completed - closing epic"
  ```

## Branch Strategy (Git Flow)
- `main`: Production-ready code, only updated through:
  - Merges from release branches (new versions)
  - Merges from hotfix branches (bug fixes)
  - Emergency direct fixes (exceptional cases only)
- `develop`: Integration branch for features, primary development branch
- `feature/*`: Individual feature branches, branch from and merge to develop
- `release/*`: Release preparation branches, branch from develop and merge to main AND develop
- `hotfix/*`: Emergency fixes for production, branch from main and merge to main AND develop
- No pull requests - use direct merges following Git Flow conventions
- Run git flow commands when appropriate:
  - Start feature: `git flow feature start FEATURE-NAME`
  - Finish feature: `git flow feature finish FEATURE-NAME`
  - Start release: `git flow release start VERSION`
  - Finish release: `git flow release finish VERSION`
  - Start hotfix: `git flow hotfix start VERSION`
  - Finish hotfix: `git flow hotfix finish VERSION`

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