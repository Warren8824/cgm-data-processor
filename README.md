# XGastro-EDA (xDrip+ Gastroparesis Screening EDA)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)

## Overview

XGastro-EDA is an open-source toolkit for analyzing Continuous Glucose Monitoring (CGM) data from xDrip+, with a focus on comprehensive data quality assessment and preparation for advanced analysis, including future data visualisations and statistical analysis, gastroparesis screening capabilities, MDI regime optimisation capabilities and more. This tool helps Type 1 diabetics leverage their existing CGM data for deeper insights.

## 🌟 Key Features

### Data Processing & Quality Assessment
- Automated processing of xDrip+ SQLite database exports
- Sophisticated insulin classification (basal/bolus)
- Intelligent carbohydrate data cleaning
- Comprehensive gap analysis in CGM readings
- Dual unit support (mmol/L and mg/dL)

### Analysis Capabilities
- Data quality metrics and visualization
- Meal impact analysis preparation
- Insulin pattern analysis
- Gap detection and characterization
- Quality scoring for meal entries

### Visualization
- Gap analysis dashboard
- Complete data quality dashboard
- Meal data quality dashboard
- Temporal pattern analysis
- Gap analysis visualizations
- Insulin distribution plots
- Meal quality distribution charts

## 📊 Project Structure
```
xgastro-eda/
├── notebooks/
│   └── examples/    
│       └── analysis_demo.ipynb    # Sample analysis workflow
├── src/
│   ├── preprocessing/         # Data cleaning & preparation
│   ├── analysis/             # Analysis components
│   └── visualisation/        # Plotting & dashboard generation
├── data/                     # Data directory (gitignored)
└── docs/                     # Documentation
```

## 🚀 Getting Started

1. Clone the repository:
```bash
git clone https://github.com/yourusername/xgastro-eda.git
cd xgastro-eda
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Export your xDrip+ database and place it in the `data/` directory

4. Run the analysis notebook:
```bash
jupyter notebook notebooks/analysis_demo.ipynb
```

## 📈 Current Status

- ✅ Core data processing pipeline
- ✅ Quality assessment framework
- ✅ Basic meal analysis
- 🏗️ Pre-meal stability analysis (In Development)
- 🏗️ Gastroparesis screening components (In Development)

## 💡 Future Plans

- Pre-meal glucose stability analysis
- Advanced gastroparesis screening metrics
- Machine learning-based pattern recognition
- Integration with other CGM data sources
- Community-driven reference datasets
- Web-based analysis interface

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.