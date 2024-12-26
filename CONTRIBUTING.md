# CGM Data Processor - Code Style Guide

This document outlines our project's coding standards and lint rules. We use pylint to maintain code quality and consistency across the project.

## Quick Start

1. Install development dependencies:
```bash
pip install pylint black isort
```

2. Run the linter:
```bash
pylint src/
```

## Core Principles

Our code style is guided by these principles:
- Readability over cleverness
- Consistency across the codebase
- Maintainable and well-documented code
- Pragmatic approach to style rules

## Naming Conventions

We follow standard Python naming conventions:
- Functions and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`
- Protected/private attributes: `_leading_underscore`

Allowed short names: `i`, `j`, `k`, `ex`, `id`, `df`, `_`

## Code Structure

### File Organization
- Maximum file length: 1000 lines
- Maximum line length: 100 characters
- Imports should be grouped and sorted (handled by isort)

### Function and Class Design
- Maximum function arguments: 5
- Maximum local variables: 25
- Maximum return statements: 6
- Maximum branches: 12
- Maximum statements: 50
- Classes should have:
  - Maximum parents: 7
  - Maximum attributes: 7
  - Minimum public methods: 2
  - Maximum public methods: 20

## Documentation

- All modules should have docstrings
- Minimum docstring length: 10 characters
- TODO/FIXME/XXX comments are tracked
- Docstrings are required except for private methods (starting with `_`)

## Disabled Rules

We've disabled certain pylint rules where they conflict with our tooling or preferences:

1. `R1735`: Dict literals vs dict()
   - Both `{"key": "value"}` and `dict(key="value")` are acceptable
   - Choose based on readability in context

2. `C0301`: Line length
   - Handled by Black formatter
   - Maximum line length is 100 characters
   - URLs are exempt from line length limits

3. `E0401`: Import errors
   - Handled in CI/CD pipeline
   - Local development may show these warnings depending on environment setup

## Type Checking

We allow generated members for common libraries:
- numpy.*
- torch.*
- cv2.*
- pd.*

## Code Similarity

- Minimum similarity lines: 4
- Ignores comments, docstrings, and imports when checking for duplicates
- Focus on identifying actual code duplication

## Error Handling

- Avoid catching generic exceptions (use specific exception classes)
- Exception handlers should be meaningful and documented

## Quality Metrics

Our code is evaluated on a 10-point scale using the formula:
```
10.0 - ((float(5 * error + warning + refactor + convention) / statement) * 10)
```

## Pre-commit Hooks

We recommend setting up pre-commit hooks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pycqa/pylint
    rev: v2.17.0
    hooks:
      - id: pylint
        args: [--rcfile=.pylintrc]
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
```

## Common Issues and Solutions

1. Import errors (E0401):
   ```python
   # Incorrect
   from readers.base import BaseReader
   
   # Correct
   from src.readers.base import BaseReader
   ```

2. Too many local variables:
   ```python
   # Consider breaking large functions into smaller ones
   def complex_function():
       result1 = process_part1()
       result2 = process_part2()
       return combine_results(result1, result2)
   ```

3. Line length:
   ```python
   # Break long lines at logical points
   long_function_call(
       argument1,
       argument2,
       argument3
   )
   ```

## Contributing

1. Run the linter before committing:
   ```bash
   pylint src/
   ```

2. Address any issues or document why they should be ignored
3. Ensure your code passes all checks in CI/CD
4. Include tests for new functionality

Remember: These rules are guidelines, not rigid requirements. If you have a good reason to deviate from them, document why in your code or pull request.