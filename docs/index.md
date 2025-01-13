# CGM Data Processor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)

A versatile Python tool designed to standardise and analyse Continuous Glucose Monitoring (CGM) data from various sources. Currently compatible with XDrip+ SQLite backups, it features a robust framework with plans to support additional CGM platforms in the future.

## Key Features

1. **Standardised Data**:
    - Consistent 5-minute interval format for all CGM data
2. **Comprehensive Processing**:
    - Robust data cleaning and validation
    - Support for both mg/dL and mmol/L units
    - Intelligent handling of missing data with configurable interpolation
    - Integration of glucose readings with insulin and carbohydrate records
3. **Advanced Analysis**:
    - Comprehensive gap analysis and quality metrics
    - Interactive quality assessment dashboards
    - Smart classification of insulin (basal/bolus)
4. **Flexible Export**:
    - Multiple CSV formats for further analysis

## Installation

```bash
# For users (once published to PyPI)
pip install [package-name]

# For developers
git clone https://github.com/Warren8824/cgm-data-processor.git
cd cgm-data-processor
pip install -e .
```

## Quick Start

```python
from preprocessing.loading import XDrip
from preprocessing.cleaning import clean_glucose, clean_classify_insulin, clean_classify_carbs
from aligners.cgm import align_diabetes_data

# Load data from XDrip+ backup
data = XDrip('path_to_backup.sqlite')

# Process individual components
glucose_df = clean_glucose(data.load_glucose_df())
insulin_df = clean_classify_insulin(data.load_treatment_df())
carb_df = clean_classify_carbs(data.load_treatment_df())

# Create aligned dataset
aligned_df = align_diabetes_data(glucose_df, carb_df, insulin_df)
```

## Data Processing Pipeline

1. **Data Loading**
    - Extract data from XDrip+ SQLite backup
    - Support for additional platforms planned

2. **Cleaning & Validation**
    - Glucose readings validated and converted to standard units
    - Intelligent insulin classification (basal/bolus)
    - Carbohydrate entry validation

3. **Timeline Alignment**
    - All data aligned to 5-minute intervals
    - Smart handling of missing data
    - Integration of multiple data types

4. **Quality Assessment**
    - Comprehensive gap analysis
    - Data quality metrics
    - Interactive dashboards

![CGM Gap Analysis Dashboard](user-guide/tutorials/load_and_export_data_files/load_and_export_data_17_1.png){: style="height:1100px;width:660px"}

**Export Options**

- `complete.csv`: Aligned dataset with all measurements
- `glucose_reading.csv`: Processed glucose readings
- `carbs.csv`: Validated carbohydrate records
- `insulin.csv`: Classified insulin records

## Documentation Structure

[**Getting Started**](installation/index.md)

- Basic setup and installation
- First steps with the tool
- Quick usage examples

[**User Guide**](user-guide/index.md)

- Detailed usage instructions
- Configuration options
- Best practices

[**API Reference**](api/index.md)

- Complete API documentation
- Module references
- Code examples

[**Examples**](user-guide/tutorials/load_and_export_data.md)

- Jupyter notebook tutorials(To be added soon)
- Real-world use cases(To be added soon)
- Advanced features(To be added soon)

## Project Status & Roadmap

### Completed
- :material-checkbox-marked: Initial setup for XDrip+ SQLite backups
- :material-checkbox-marked: Basic data processing pipeline
- :material-checkbox-marked: Gap analysis functionality
- :material-checkbox-marked: Interactive dashboards

### In Progress
- :material-checkbox-blank: Setup test suite
- :material-checkbox-blank: Support for additional CGM platforms
- :material-checkbox-blank: Advanced meal record quality analysis
- :material-checkbox-blank: Diabetes Management Analysis and Visualisations!!!
- :material-checkbox-blank: Web interface
- :material-checkbox-blank: API development

## Contributing

We welcome contributions! See our [Contributing Guide](development/contributing.md) for:

- Development setup
- Code style guidelines
- Pull request process
- Bug reporting guidelines

## Support & Community

- 📚 [Documentation](#contributing)
- 🐛 [Issue Tracker](https://github.com/Warren8824/cgm-data-processor/issues)
- 💡 [Discussions](https://github.com/Warren8824/cgm-data-processor/discussions)

## License

This project is licensed under the MIT License - see the [LICENSE](about/license.md) file for details.

## Acknowledgments

- XDrip+ development team for their excellent CGM application
- All contributors to this project
- The diabetes tech community for their support and feedback