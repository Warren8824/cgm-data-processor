# User Guide

Welcome to the CGM Data Processor user guide! This guide will help you understand how to effectively use the package to process and analyze your Continuous Glucose Monitoring data.

## What You Can Do

With CGM Data Processor, you can:

- Load data from XDrip+ SQLite backups
- Clean and standardize glucose readings
- Classify insulin treatments (basal/bolus)
- Align data to consistent 5-minute intervals
- Analyze data quality and gaps
- Visualize data patterns and issues

## Getting Started

If you're new to CGM Data Processor, we recommend following this learning path:

1. **Basic Data Processing**
    - [Loading and Exporting Data](tutorials/load_and_export_data.md): Learn how to load your XDrip+ data and export processed results

2. **Understanding the Data**
    - [Data Processing Pipeline](concepts/processing_pipeline.md): Understand how your data is processed
      - [Gap Analysis](concepts/gap_analysis.md): Learn about data quality assessment

## Core Concepts

### Data Loading
CGM Data Processor currently supports XDrip+ SQLite backup files, loading:

- Glucose readings from the BgReadings table
- Insulin and carbohydrate data from the Treatments table

### Data Processing
Your data goes through several processing steps:

1. Cleaning and validation
2. Unit standardization (mg/dL and mmol/L)
3. Insulin classification
4. Timeline alignment
5. Gap analysis

### Output Formats
You can export your processed data in multiple formats:

1. Complete aligned dataset
2. Separate component datasets:
   - Processed glucose readings
   - Classified insulin treatments
   - Validated carbohydrate entries

## Common Use Cases

### Basic Data Export
```python
from preprocessing.loading import XDrip
from preprocessing.cleaning import clean_glucose
from preprocessing.alignment import align_diabetes_data

# Load and process data
data = XDrip('xdrip_backup.sqlite')
glucose_df = clean_glucose(data.load_glucose_df())

# Export processed data
glucose_df.to_csv('processed_glucose.csv')
```

### Quality Assessment
```python
from analysis.gap_analysis import analyse_glucose_gaps
from visualization.gap_dashboard import create_gap_dashboard

# Analyze data quality
gaps_data = analyse_glucose_gaps(aligned_df)
dashboard = create_gap_dashboard(gaps_data)
```

## Best Practices

1. **Data Quality**
    - Always check your XDrip+ backup is recent
    - Review gap analysis before detailed analysis
    - Document any known sensor changes or issues

2. **Processing**
    - Start with default parameters
    - Adjust interpolation limits based on your needs
    - Verify insulin classification results

3. **Analysis**
    - Consider gap impact on your analysis
    - Use appropriate visualizations
    - Document processing decisions

## Need Help?

- Check the [API Reference](../api/index.md) for detailed function documentation
- Review [Example Notebooks](tutorials/load_and_export_data.md) for practical guides
- Submit issues on [GitHub](https://github.com/Warren8824/cgm-data-processor/issues)

## Next Steps

Ready to start processing your data?

1. Follow the [Loading and Exporting Data](tutorials/load_and_export_data.md) tutorial
2. Review the [Data Processing Pipeline](concepts/processing_pipeline.md)
3. Learn about [Gap Analysis](concepts/gap_analysis.md)

## Contributing

Interested in contributing to CGM Data Processor?

- Read our [Contributing Guide](../development/contributing.md)
- Check the [Development Guide](../development/contributing.md) for setup instructions
- Review our [roadmap](../development/roadmap.md) for planned features