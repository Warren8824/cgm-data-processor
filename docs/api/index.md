# API Reference

This section provides detailed documentation for all public modules and functions in the CGM Data Processor package.

## Package Structure

The package is organized into three main components:

### Preprocessing
Tools for loading, cleaning, and aligning CGM data.

1. [`preprocessing.loading`](preprocessing/loading.md): Data loading from XDrip+ SQLite backups
    - `XDrip`: Main class for database operations
    - `load_glucose_df()`: Load glucose readings
    - `load_treatment_df()`: Load insulin and carb treatments

2. [`preprocessing.cleaning`](preprocessing/cleaning.md): Data cleaning and classification
    - `clean_glucose()`: Process and interpolate glucose readings
    - `clean_classify_insulin()`: Clean and classify insulin treatments
    - `clean_classify_carbs()`: Clean carbohydrate entries

3. [`preprocessing.alignment`](preprocessing/alignment.md): Data alignment utilities
    - `align_diabetes_data()`: Align all components to 5-minute intervals

### Analysis
Tools for analyzing CGM data quality and patterns.

- [`analysis.gap_analysis`](analysis/gaps.md): Gap detection and analysis
    - `analyse_glucose_gaps()`: Comprehensive gap analysis metrics

### Visualization
Tools for creating interactive visualizations.

- [`visualization.gap_dashboard`](visualisation/gap_dashboard.md): Interactive dashboards
    - `create_gap_dashboard()`: Generate gap analysis dashboard

## Common Workflows

### Basic Data Processing
```python
from preprocessing.loading import XDrip
from preprocessing.cleaning import clean_glucose, clean_classify_insulin, clean_classify_carbs
from preprocessing.alignment import align_diabetes_data

# Load data
data = XDrip('path_to_backup.sqlite')
glucose_df = data.load_glucose_df()
treatment_df = data.load_treatment_df()

# Clean and process
glucose_df = clean_glucose(glucose_df)
insulin_df = clean_classify_insulin(treatment_df)
carb_df = clean_classify_carbs(treatment_df)

# Align data
aligned_df = align_diabetes_data(glucose_df, carb_df, insulin_df)
```

### Gap Analysis
```python
from analysis.gap_analysis import analyse_glucose_gaps
from visualization.gap_dashboard import create_gap_dashboard

# Analyze gaps
gaps_data = analyse_glucose_gaps(aligned_df)

# Create visualization
dashboard = create_gap_dashboard(gaps_data)
```

## Data Structures

### Input Data
- XDrip+ SQLite backup file containing:
    - BgReadings table: Glucose measurements
    - Treatments table: Insulin and carbohydrate records

### Key DataFrame Structures

#### Glucose DataFrame
```python
glucose_df.columns = [
    'mg_dl',           # Glucose values in mg/dL
    'mmol_l',          # Glucose values in mmol/L
    'missing'          # Boolean flag for missing values
]
```

#### Insulin DataFrame
```python
insulin_df.columns = [
    'bolus',           # Bolus insulin doses
    'basal',           # Basal insulin doses
    'labeled_insulin'  # Boolean flag for labeled doses
]
```

#### Carbs DataFrame
```python
carbs_df.columns = [
    'carbs'            # Carbohydrate amounts in grams
]
```

#### Aligned DataFrame
```python
aligned_df.columns = [
    'mg_dl',           # Glucose in mg/dL
    'mmol_l',          # Glucose in mmol/L
    'missing',         # Missing value flag
    'carbs',           # Carbohydrates in grams
    'bolus',           # Bolus insulin doses
    'basal',           # Basal insulin doses
    'labeled_insulin'  # Insulin labeling flag
]
```

## Error Handling

The package includes error handling for common issues:
- Invalid SQLite files
- Missing or corrupted data
- Data format issues
- Configuration validation

See individual module documentation for specific error details.

## Configuration Options

Key configuration parameters:
- `interpolation_limit`: Maximum gap interpolation (default: 4 intervals = 20 minutes)
- `bolus_limit`: Maximum insulin dose for bolus classification (default: 8.0 units)
- `max_limit`: Maximum valid insulin dose (default: 15.0 units)

## See Also

- [User Guide](../user-guide/index.md) for detailed usage instructions
- [Examples](../user-guide/tutorials/load_and_export_data.md) for practical tutorials
- [Development Guide](../development/contributing.md) for contribution guidelines