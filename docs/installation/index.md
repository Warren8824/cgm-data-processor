# Installation

This guide will help you set up CGM Data Processor on your system.

## Prerequisites

Before installing CGM Data Processor, ensure you have:

- Python 3.10 or higher
- pip (Python package installer)

## Installation Methods

Currently, there are two ways to install CGM Data Processor:

### Development Installation (Current Method)

For now, install directly from the GitHub repository:

```bash
git clone https://github.com/Warren8824/cgm-data-processor.git
cd cgm-data-processor
```

#### For Users
Install the package and its dependencies:
```bash
pip install -r requirements.txt
```

#### For Developers
Install additional development dependencies:
```bash
pip install -r requirements-dev.txt
```

### PyPI Installation (Coming Soon)

In the future, you'll be able to install the package directly using pip:

```bash
pip install [package-name]  # Not yet available
```

## Dependencies

All required dependencies are automatically installed when using either `requirements.txt` (for users) or `requirements-dev.txt` (for developers). These include all necessary packages for:

- Data processing
- Analysis
- Visualization
- Development tools (if using requirements-dev.txt)

## Verifying Your Installation

To verify that CGM Data Processor is installed correctly, you can run this simple test in Python:

```python
from preprocessing.loading import XDrip
from preprocessing.cleaning import clean_glucose
from aligners.cgm import align_diabetes_data

print("CGM Data Processor is installed correctly!")
```

If no import errors occur, the installation was successful.

## Development Setup

If you're planning to contribute to CGM Data Processor, follow these additional steps after installation:

1. Firstly setup and start a new virtual environment:
   ```bash
   python -m venv venv  # Use python3 depending on setup
   ```
   ```bash
   source venv/bin/activate # Slightly different if using windows  
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. Verify the test environment:
   ```bash
   pytest tests/
   ```

## Next Steps

After installation, you might want to:

1. Follow the [Loading and Exporting Data](../user-guide/tutorials/load_and_export_data.md) tutorial
2. Check out the [API Reference](../api/index.md)
3. Review example notebooks in the `notebooks/examples/` directory

## Troubleshooting

If you encounter any issues during installation:

1. Ensure you're using Python 3.10 or higher:
   ```bash
   python --version
   ```

2. Verify pip is installed correctly:
   ```bash
   pip --version
   ```

3. If you encounter any dependency conflicts, try installing in a fresh virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Future Updates

When the package becomes available on PyPI, this guide will be updated with simplified installation instructions. Check back for updates!