# Copilot Instructions for `langchain_learning`

## Project Overview

This repository is for experiments and learning with LangChain and related tooling. The structure is minimal, with most configuration focused on code quality and automation.

## Key Workflows

- **Pre-commit Hooks**: Code formatting and linting are enforced via `.pre-commit-config.yaml` using:
  - `black` (Python formatter, line length 79)
  - `isort` (import sorting, Black profile)
  - `pylint` (Python linter, uses `.venv/bin/pylint` for system language)
- **Git Integration**: Standard `.git` directory and hooks are present. No custom hooks detected; pre-commit is managed via the config file.

## Patterns & Conventions

- **Python Code Style**: All Python code should be formatted with Black and imports sorted with isort. Pylint is used for linting.
- **No Source Files Present**: As of this analysis, there are no Python source files or README. If adding code, follow the above style conventions.
- **No README**: Add a `README.md` to document project goals, setup, and usage if the project grows.

## How to Contribute

1. **Install pre-commit**:  
   ```sh
   pip install pre-commit
   pre-commit install
   ```
2. **Commit Workflow**:  
   On commit, pre-commit will auto-format and lint your code. Fix any issues before pushing.

## Example Workflow

```sh
# Format and lint all files before commit
pre-commit run --all-files
```

## Directory Reference

- `.pre-commit-config.yaml`: Pre-commit hook configuration
- `.github/copilot-instructions.md`: AI agent instructions (this file)
- `.git/`: Standard git directory

## AI Agent Guidance

- Enforce code style and linting via pre-commit.
- Reference `.pre-commit-config.yaml` for tool versions and arguments.
- If adding Python code, use Black formatting and isort for imports.
- No custom build or test commands are present; add these to README if needed.
