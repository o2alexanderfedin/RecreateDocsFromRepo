# Git Flow Process

This repository follows the Git Flow workflow with an additional `release/current` branch that always points to the latest stable release.

## Branch Structure

- `main` - Production-ready code (stable)
- `develop` - Next release development branch
- `feature/*` - Feature branches
- `release/*` - Release preparation branches
- `hotfix/*` - Hotfix branches for production issues
- `release/current` - Always points to the latest stable release (currently v0.7.0)

## Workflow

### Feature Development

```bash
# Start a new feature (link to GitHub issue)
git flow feature start ISSUE-123-feature-description

# Work on the feature...
git add .
git commit -m "Implement feature"

# Or with issue closing keyword
git commit -m "Add login functionality. Fixes #123"

# Finish the feature (merges to develop)
git flow feature finish ISSUE-123-feature-description
```

When a feature is merged into develop, GitHub Actions will:
1. Run all tests to ensure the feature works correctly
2. Automatically close associated GitHub issues if:
   - The feature branch name follows the pattern `feature/ISSUE-123-description`
   - Commit messages include closing keywords like "Fixes #123", "Closes #123", etc.
3. Add a comment to the issue noting that it was closed automatically

### Release Process

```bash
# Start a release
git flow release start x.y.z

# Make release preparations (update version numbers, etc.)
git add .
git commit -m "Update version to x.y.z"

# Finish the release (merges to main and develop, creates tag)
git flow release finish x.y.z

# Push changes to remote
git push origin develop
git push origin main
git push origin --tags

# Update release/current branch to point to the latest release
./git-flow-update-current
```

### Hotfix Process

```bash
# Start a hotfix
git flow hotfix start x.y.z

# Make necessary fixes
git add .
git commit -m "Fix critical issue"

# Finish the hotfix (merges to main and develop, creates tag)
git flow hotfix finish x.y.z

# Push changes to remote
git push origin develop
git push origin main
git push origin --tags

# Update release/current branch to point to the latest release
./git-flow-update-current
```

## Using release/current

The `release/current` branch always points to the latest stable release and is useful for:

1. CI/CD systems that deploy the latest release
2. Users who want the latest stable code without knowing version numbers
3. Providing a consistent reference point for the current production version

This branch is automatically updated when running the `git-flow-update-current` script after completing a release or hotfix.

## Setting Up

If you need to set up Git Flow on a new machine:

```bash
# Initialize git flow
git flow init

# Use the following configuration:
# - Production branch: main
# - Development branch: develop
# - Feature prefix: feature/
# - Release prefix: release/
# - Hotfix prefix: hotfix/
# - Support prefix: support/
# - Version tag prefix: (empty)
```