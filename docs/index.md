<div class="hero">
  <h1>CGM Data Processor</h1>
  <p>A robust Python framework for processing and analysing diabetes device data</p>
</div>

![Python](https://img.shields.io/badge/python-3.10%2B-blue)

![Release Status](https://img.shields.io/badge/status-pre--release-orange)
![Black](https://img.shields.io/badge/code%20style-black-4B8BBE.svg)
![isort](https://img.shields.io/badge/imports-isort-4B8BBE.svg)
![Pylint](https://img.shields.io/badge/code%20quality-pylint-4B8BBE.svg)
[![licence: MIT](https://img.shields.io/badge/licence-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📈 Process Your Diabetes Data

<div class="feature-card">
  <p>Analyse data from multiple diabetes management systems including XDrip+ and Freestyle Libre. Handle CGM readings, insulin doses, carbs, and treatment notes with confidence.</p>
</div>

## 🩸 CGM Analysis
- Gap detection
- Configurable Interpolation
- Quality metrics

## 💉 Treatment Data
- Insulin doses
- Carb intake
- Event notes

## 🧑‍🔬 Advanced Features

- Automated format detection
- Data alignment
- Flexible export options
- Complete metadata carried through to output format

## 🚀 Quick Start

Install CGM Data Processor - [Installation Guide](./getting-started/installation.md)

The simplest way to use the CGM Data Processor is to run `python -m src.cli path/to/data/export.file` from the root directory. The following arguments can be supllied:

```bash
python -m src.cli data.sqlite \
    --debug                  # Display verbose output
    --interpolation-limit 6  # Max CGM gaps to fill (6 = 30 mins)
    --bolus-limit 10.0       # Max bolus insulin units
    --max-dose 20.0          # Max valid insulin dose
    --output ./my_analysis   # Output location
```

![cli_script](assets/cli_screenshot.png)

The cli script, performs multiple processing steps and outputs standardised CSV data. The library can be used in many different configurations depending on your use case. For individual use cases check out our [API Reference](https://warren8824.github.io/cgm-data-processor/api/core/data-types) section.

Example of simple use case:
```python
from src.core.exceptions import DataProcessingError, ReaderError
from src.core.format_registry import FormatRegistry
from src.file_parser.format_detector import FormatDetector
from src.processors import DataProcessor
from src.readers import BaseReader

# Initialise format detection
registry = FormatRegistry()
detector = FormatDetector(registry)
processor = DataProcessor()
file_path = "example_data.sqlite"

# Process file
detected_format, _, _ = detector.detect_format(file_path)
reader = BaseReader.get_reader_for_format(detected_format, file_path)
    with reader:
        table_data = reader.read_all_tables()
        if not table_data:
            raise ReaderError("No valid data found in file")
        try:
            processed_data = processor.process_tables(
                table_data=table_data,
                detected_format=detected_format,
            )
            if not processed_data:
                raise DataProcessingError("No data could be processed")

        except DataProcessingError as e:
            raise DataProcessingError(f"Failed to process data: {str(e)}") from e
```

## 💡 Key Features

<div class="feature-card" markdown="1">
<ul>
   <li>Automated format detection for multiple data sources</li>
   <li>Robust data validation and cleaning</li>
   <li>Gap detection and interpolation for CGM data</li>
   <li>Treatment classification and verification</li>
   <li>Flexible data export options</li>
</ul>
</div>

## 📊 Example Output Structure

<div class="feature-card">

![output_example](assets/output_structure.png)
</div>

## 🛡️ Responsible Use
<div class="feature-card">
This tool is designed for data analysis only. Not intended for real-time monitoring or medical decision making. Always consult healthcare providers for medical advice.
</div>
