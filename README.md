# CGM Data Processor
> ⚠️ **Note**: This is a data analysis tool only and is not intended for use as a medical device.
> 
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Black](https://img.shields.io/badge/code%20style-black-000000.svg)
![isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat)
![Status](https://img.shields.io/badge/status-pre--release-orange)

A Python package for processing and analysing continuous glucose monitor (CGM), insulin, and meal data from diabetes management systems. Features robust gap detection, data alignment, and quality assessment. Built by a T1D developer.


Full documentation including detailed API reference, user guides, and examples can be found at our
[Documentation Site](https://warren8824.github.io/cgm-data-processor/) hosted Using Github pages.

## Call for Device Format Contributors

We're looking for T1D developers and users to help expand our device format support. If you use a diabetes management system and can share sample export files (with dummy data), please:

1. Open an issue with the device/app name
2. Describe the export format(s) available
3. Provide sample files if possible

Currently supporting:

- XDrip+ SQLite exports
- More formats coming soon!

## Installation

### Using Poetry

```bash
# Install Poetry
pip install poetry

# Install package
git clone https://github.com/Warren8824/cgm-data-processor.git
cd cgm-data-processor
poetry install
```

### Using pip

```bash
git clone https://github.com/Warren8824/cgm-data-processor.git
cd cgm-data-processor
pip install -r requirements.txt

# For development dependencies
pip install -r requirements-dev.txt
```

## Features

Current implementation:

- Automatic format detection
- CGM data processing:
  - Gap detection and interpolation
  - Processing step tracking
  - Detailed quality reporting
- Insulin data processing:
  - Dose classification (basal/bolus)
  - Type detection from metadata
- Meal/carb data processing
- Notes/comments processing
- Timeline synchronisation
- Comprehensive processing logs
- CSV export with metadata

## Use Cases

- Data Analysis: Process and clean diabetes device data for research or personal analysis

- Quality Assessment: Evaluate CGM data completeness and identify gaps
- Data Migration: Convert data between different diabetes management systems

- Retrospective Review: Analyze historical diabetes management data with proper timeline alignment

- Research Projects: Process diabetes device data in standardized formats for research studies

- Personal Insights: Track patterns in CGM, insulin, and meal data over time

## Usage

```bash
python -m src.cli path/to/data.file [options]

# Options:
#   --debug                    # Enable debug logging
#   --output OUTPUT           # Export directory (default: ./exports)
#   --interpolation-limit INT # Max CGM gaps to interpolate (4 = 20 mins)
#   --bolus-limit FLOAT      # Max insulin units for bolus classification
#   --max-dose FLOAT         # Maximum valid insulin dose
```

## Development

### Prerequisites
- Python 3.10+

### Setup

```bash
git clone https://github.com/Warren8824/cgm-data-processor.git
cd cgm-data-processor

# Using Poetry
poetry install --with dev
pre-commit install

# Using pip
pip install -r requirements-dev.txt
pre-commit install
```

### Quality Tools
- Black (code formatting)
- isort (import sorting)
- Pylint (linting)
- Pytest (testing)
- Pre-commit hooks

### Documentation

```bash
# Using Poetry
poetry install --with dev
mkdocs serve

# Using pip

pip install -r requirements-dev.txt
mkdocs serve
```

## Project Status

Pre-release development focusing on:
- [ ] Core format implementations
- [ ] Test suite completion
- [ ] Documentation
- [ ] Basic statistics and visualisations
- [ ] First release

## Dependencies

Core:
- numpy ≥2.1.0
- pandas ≥2.2.0
- SQLAlchemy ≥2.0.0
- plotly ≥5.0.0

Documentation:
- MkDocs Material
- MkDocstrings

## Contributing

We welcome contributions, especially:

- Device format definitions
- Sample export files (with dummy data)
- Bug reports
- Feature requests

Please open an issue to discuss before submitting PRs.

## License

MIT

## Contact

Warren8824 (warrenbebbington88@gmail.com)
