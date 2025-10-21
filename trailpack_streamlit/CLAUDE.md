# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**trailpack** is a Python boilerplate package for creating Brightway ecosystem packages. It's a template project designed for Brightcon Hackathon Group 1, providing the foundational structure for Python packages with testing, documentation, and CI/CD setup.

## Development Setup

Install the package in development mode with dependencies:

```bash
pip install -e ".[dev]"
```

For testing dependencies:

```bash
pip install -e ".[testing]"
```

## Common Commands

### Testing

Run the full test suite:

```bash
pytest
```

Run with coverage (configured in pyproject.toml):

```bash
pytest --cov trailpack --cov-report term-missing --verbose
```

### Code Quality

This project uses pre-commit hooks. Install them with:

```bash
pip install pre-commit
pre-commit install
```

Code formatting follows Black style (line-length: 88) and isort for imports.

### Building

Build the package:

```bash
python -m build
```

### Documentation

Build documentation locally:

```bash
# Using conda/mamba
conda env create -f docs/environment.yml
conda activate sphinx_trailpaack
sphinx-build docs _build/html --builder=html --jobs=auto --write-all
```

Or with pip:

```bash
pip install -e ".[dev,docs]"
sphinx-build docs docs/_build
```

## Project Structure

- `trailpack/` - Main package directory
  - `__init__.py` - Package initialization with version info
- `tests/` - Test directory
  - `conftest.py` - Pytest fixtures
- `docs/` - Sphinx documentation
- `pyproject.toml` - Project configuration, dependencies, and tool settings

## Key Configuration

- **Python versions**: 3.9, 3.10, 3.11, 3.12
- **Testing**: pytest with coverage
- **Code style**: Black (88 chars), isort, flake8
- **Build system**: setuptools>=68.0
- **Version**: Dynamically loaded from `trailpack.__version__`

## Adding New Functionality

1. Add code to `trailpack/` directory
2. Expose public APIs in `trailpack/__init__.py` via `__all__`
3. Add tests in `tests/` directory
4. Update documentation if needed
