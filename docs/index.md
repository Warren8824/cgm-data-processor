<div class="hero">
  <h1>CGM Data Processor</h1>
  <p>A robust Python framework for processing and analyzing diabetes device data</p>
</div>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Black](https://img.shields.io/badge/code%20style-black-000000.svg)
![isort](https://img.shields.io/badge/imports-isort-4B8BBE.svg)
![Pylint](https://img.shields.io/badge/code%20quality-pylint-yellow.svg)

## 📈 Process Your Diabetes Data

<div class="feature-card">
  <p>Analyze data from multiple diabetes management systems including XDrip+, Dexcom, and Freestyle Libre. Handle CGM readings, insulin doses, carbs, and treatment notes with confidence.</p>
</div>

## ❤️ CGM Analysis
- Gap detection
- Noise filtering
- Quality metrics

## 💉 Treatment Data
- Insulin doses
- Carb intake
- Event notes

## 🚀 Advanced Features
- Automated format detection
- Data alignment
- Flexible export options

## Quick Start

```python
from src.core.format_registry import FormatRegistry
from src.file_parser.format_detector import FormatDetector
from src.processors import DataProcessor

# Initialize format detection
registry = FormatRegistry()
detector = FormatDetector(registry)

# Process file
format, _, _ = detector.detect_format("my_data.sqlite")
processed_data = process_file("my_data.sqlite")
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

## 🛡️ Responsible Use
<div class="feature-card">
This tool is designed for data analysis only. Not intended for real-time monitoring or medical decision making. Always consult healthcare providers for medical advice.
</div>
