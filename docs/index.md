![CGM Logo](assets/logo_main.png)
# 
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


A powerful Python tool for processing and analyzing Continuous Glucose Monitoring (CGM) data from various diabetes devices. This tool automatically detects file formats, processes data, and aligns multiple data streams for comprehensive diabetes data analysis.

## Features

- **Automatic Format Detection**: Intelligently identifies data formats from different CGM devices
- **Multi-Device Support**: 
    - Dexcom CGM systems
    - Libre CGM systems
    - XDrip+ data
- **Flexible Data Processing**:
    - CGM readings
    - Insulin doses
    - Carbohydrate intake
    - Notes and events
- **Smart Data Alignment**: Automatically aligns different data streams by timestamp
- **Extensible Architecture**: Easy to add support for new devices and data formats

## Quick Start

### Installation

```bash
pip install cgm-data-processor
```

### Basic Usage

Process a single diabetes device data file:

```bash
cgm-process path/to/your/file.csv
```

Enable detailed analysis with debug mode:

```bash
cgm-process path/to/your/file.csv --debug
```

## Processing Pipeline

1. **Format Detection**: Automatically identifies the source device and data format
2. **Data Reading**: Extracts data using format-specific readers
3. **Data Processing**: Processes and validates data streams
4. **Data Alignment**: Aligns multiple data streams by timestamp
5. **Analysis**: Provides detailed data analysis in debug mode


```mermaid
graph LR
    A[Your Data File] --> B[Format Detection]
    B --> C[Data Reading]
    C --> D[Processing]
    D --> E[Alignment]
    E --> F[Export]
```

## Project Status

The project is under active development. Current focus areas:


- Implementation of data exporters
- Enhanced data visualization
- Additional device format support

## Documentation

- [Getting Started Guide](getting-started/index.md)
- [Supported Formats](user-guide/supported-formats/index.md)
- [API Reference](api/index.md)
- [Development Guide](development/index.md)


