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

check out our [Full Documentation](https://warren8824.github.io/cgm-data-processor/)

![cgm_quality_dashboard](https://github.com/Warren8824/cgm-data-processor/blob/main/notebooks%2Fexamples%2Fimg%2Fgaps_dashboard.png)

## Installation

```bash
pip install [package-name]  # Once published to PyPI
```

For development installation:
```bash
git clone https://github.com/Warren8824/cgm-data-processor.git
cd cgm-data-processor
pip install -e .
```

## Quick Start

```python
from preprocessing.loading import XDrip
from preprocessing.cleaning import clean_glucose, clean_classify_insulin, clean_classify_carbs
from preprocessing.alignment import align_diabetes_data

# Load data from XDrip+ backup
data = XDrip('path_to_backup.sqlite')

# Process individual components
glucose_df = clean_glucose(data.load_glucose_df())
insulin_df = clean_classify_insulin(data.load_treatment_df())
carb_df = clean_classify_carbs(data.load_treatment_df())

# Create aligned dataset
aligned_df = align_diabetes_data(glucose_df, carb_df, insulin_df)
```

## Documentation

Detailed documentation is available in the following notebooks:
- `notebooks/examples/load_and_export_data.ipynb`: Getting started with the tool
- `notebooks/examples/data_quality.ipynb`: *To be implemented*
- `notebooks/examples/advanced_features.ipynb`: *To be implemented*

### Data Processing Pipeline

1. **Data Loading**: Extract data from XDrip+ SQLite backup
2. **Cleaning & Validation**: 
   - Glucose readings validated and converted to standard units
   - Insulin records classified (basal/bolus)
   - Carbohydrate entries validated
3. **Timeline Alignment**: All data aligned to 5-minute intervals
4. **Quality Assessment**: Gap analysis and data quality metrics
5. **Export**: Standardized CSV files for further analysis

## Example Usage

See the [example notebook](notebooks/examples/load_and_export_data.ipynb) for detailed usage examples.

## Data Format Specifications

### Input Requirements
- XDrip+ SQLite backup file
- [Additional format specifications to be added]

### Output Format
Generated CSV files include:
- `complete.csv`: Aligned dataset with all measurements
- `glucose_reading.csv`: Processed glucose readings
- `carbs.csv`: Validated carbohydrate records
- `insulin.csv`: Classified insulin records

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting PRs.

### Development Setup
1. Fork the repository
2. Create a virtual environment
3. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```
4. Run tests:
```bash
pytest tests/
```

## Roadmap

- [x] Initial setup for XDrip+ SQLite backups
- [ ] Setup test suite
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
