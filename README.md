# CGM Data Processor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Black](https://img.shields.io/badge/code%20style-black-000000.svg)
![isort](https://img.shields.io/badge/imports-isort-4B8BBE.svg)
![Pylint](https://img.shields.io/badge/code%20quality-pylint-yellow.svg)
![Requirements](https://img.shields.io/badge/dependencies-up%20to%20date-brightgreen.svg)
![Docs](https://img.shields.io/badge/docs-MkDocs-blue)
![Status](https://img.shields.io/badge/status-in%20progress-yellow)
![Maintenance](https://img.shields.io/badge/maintenance-active-brightgreen.svg)

A Python package for processing and analyzing diabetes device data, providing robust data alignment, gap detection, and quality assessment capabilities. Built by a T1D developer to standardize diabetes data analysis.

> ⚠️ **Note**: This is a data analysis tool only and is not intended for use as a medical device.

## Features

- **Automatic Format Detection**: Intelligently identifies and processes data from:
  - Dexcom CGM systems
  - Libre CGM systems
  - XDrip+ data exports
  
- **Smart Data Processing**:
  - CGM data cleaning and gap detection
  - Insulin dose classification (basal/bolus)
  - Carbohydrate intake normalization
  - Automated timestamp alignment

- **Robust Validation**:
  - Format-specific validation rules
  - Data quality assessment
  - Unit conversion and verification
  - Gap detection and reporting

- **Extensible Architecture**:
  - Easy to add new device formats
  - Plugin system for data processors
  - Flexible output formatting

## Installation

### Prerequisites

- Python 3.10 or higher
- Poetry (recommended) or pip

### Using Poetry (Recommended)

```bash
# Clone the repository
git clone https://github.com/Warren8824/cgm-data-processor.git
cd cgm-data-processor

# Install dependencies
poetry install

# For development dependencies
poetry install --with dev
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/Warren8824/cgm-data-processor.git
cd cgm-data-processor

# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

## Quick Start

```python
from pathlib import Path
from cgm_data_processor import DataProcessor

# Process a single file
file_path = Path("my_cgm_data.sqlite")
processor = DataProcessor()
results = processor.process_file(file_path)

# Access processed data
cgm_data = results.get(DataType.CGM)
insulin_data = results.get(DataType.INSULIN)
```

## Development

### Setting Up Development Environment

```bash
# Install development dependencies
poetry install --with dev

# Install pre-commit hooks
pre-commit install
```

### Code Style

This project uses:
- Black for code formatting
- isort for import sorting
- pylint for linting

```bash
# Format code
poetry run black .
poetry run isort .

# Run linting
poetry run pylint src/
```

### Documentation

The documentation is built using MkDocs with Material theme:

```bash
# Install documentation dependencies
poetry install --with dev

# Serve documentation locally
poetry run mkdocs serve

# Build documentation
poetry run mkdocs build
```

## Roadmap

- [ ] Add export module with support for:
  - CSV exports
  - SQLite database
  - Parquet files
  - Monthly/yearly data aggregation
- [ ] Comprehensive test suite
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Additional device format support
- [ ] Batch processing capabilities
- [ ] Extended health data type support

## Contributing

Contributions are welcome! Please see our [Contributing Guide](docs/development/contributing.md) for details.

### Development Process

1. Fork the repository
2. Create a feature branch
3. Write your changes
4. Write tests that prove your changes work
5. Run code formatting
   ```bash
   poetry run black .
   poetry run isort .
   ```
6. Push your changes
7. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Documentation

Full documentation is available at [GitHub Pages](https://Warren8824.github.io/cgm-data-processor/).

Key documentation sections:
- [Getting Started](https://Warren8824.github.io/cgm-data-processor/getting-started/)
- [User Guide](https://warren8824.github.io/cgm-data-processor/user-guide/)
- [API Reference](https://warren8824.github.io/cgm-data-processor/api)
- [Developer Guide](https://warren8824.github.io/cgm-data-processor/dev-guide/)

## Project Status

This project is under active development. The core data processing and alignment features are implemented, with export functionality coming soon. The first PyPI release will be available once the export module is complete.

For the latest updates, please check the [Changelog](https://warren8824.github.io/cgm-data-processor/about/changelog/) .