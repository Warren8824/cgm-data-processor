# CGM Data Processing Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)

A versatile Python tool designed to standardize and analyze Continuous Glucose Monitoring (CGM) data from various sources. Currently compatible with XDrip+ SQLite backups, it features a robust framework with plans to support additional CGM platforms in the future.

## Features

- Standardizes CGM data into a consistent 5-minute interval format
- Handles data cleaning and validation
- Integrates glucose readings with insulin and carbohydrate records
- Provides comprehensive gap analysis and quality metrics
- Supports both mg/dL and mmol/L units
- Intelligent handling of missing data with configurable interpolation
- Interactive quality assessment dashboards

Check out our [Full Documentation](https://warren8824.github.io/cgm-data-processor/)

![cgm_quality_dashboard](https://github.com/Warren8824/cgm-data-processor/blob/main/notebooks%2Fexamples%2Fimg%2Fgaps_dashboard.png)

## Development Setup

This project uses Poetry for dependency management and includes several development tools for code quality.

### Prerequisites
- Python 3.8 or higher
- Poetry (Python package manager)

### Installation

1. Install Poetry:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Clone the repository:
```bash
git clone https://github.com/Warren8824/cgm-data-processor.git
cd cgm-data-processor
```

3. Install dependencies:
```bash
poetry install
```

4. Set up pre-commit hooks:
```bash
poetry run pre-commit install
```

### Development Tools

This project uses several tools to maintain code quality:

- **Poetry**: Dependency management and packaging
- **Black**: Code formatting
- **Pylint**: Code linting
- **pytest**: Testing framework
- **pre-commit**: Git hooks for code quality checks

### Running Tests

```bash
poetry run pytest
```

## Project Structure

[Note: This section will be updated as the modular structure is implemented]

## Quick Start

[Note: Import paths will be updated during refactoring]

```python
# Example code will be updated with new module structure
```

## Documentation

The project is currently undergoing restructuring to improve modularity and extensibility. Documentation will be updated to reflect the new structure as it's implemented.

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting PRs.

### Development Workflow

1. Create a new branch for your feature/fix
2. Ensure all tests pass
3. Format code with Black: `poetry run black .`
4. Check linting with Pylint: `poetry run pylint src tests`
5. Submit a Pull Request

## Roadmap

- [x] Initial setup for XDrip+ SQLite backups
- [x] Setup development tools (Poetry, Black, Pylint)
- [ ] Implement test suite
- [ ] Complete modular restructuring
- [ ] Support for additional CGM platforms
- [ ] Advanced meal response analysis
- [ ] Machine learning integration
- [ ] Web interface
- [ ] API development

## License

[MIT] - See [LICENSE](LICENSE) file for details

## Citation

If you use this tool in your research, please cite:

```bibtex
[Citation details to be added]
```

## Support

- Submit issues through the [Issue Tracker](link-to-issues)
- Join our [Discussion Forum](link-to-discussions)
- Email: [support email]

## Acknowledgments

- XDrip+ development team
- [Additional acknowledgments]

## Project Status

This project is in active development. Current version: [version number]

---
