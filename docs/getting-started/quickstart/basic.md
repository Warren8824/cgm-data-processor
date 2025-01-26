<div class="hero">
  <h1>Basic Usage</h1>
  <p>Understanding and configuring data processing</p>
</div>

## 📊 Core Usage

<div class="feature-card">

```python
from pathlib import Path
from src.core.aligner import Aligner
from src.core.format_registry import FormatRegistry
from src.core.exceptions import ProcessingError
from src.file_parser.format_detector import FormatDetector
from src.processors import DataProcessor

def process_data(file_path: str, 
                interpolation_limit: int = 4,
                bolus_limit: float = 8.0,
                max_dose: float = 15.0):
    """
    Process diabetes device data with custom parameters
    
    Args:
        file_path: Path to data file
        interpolation_limit: Max CGM gaps to interpolate (4 = 20 mins)
        bolus_limit: Max insulin units for bolus classification
        max_dose: Maximum valid insulin dose
    """
    registry = FormatRegistry()
    detector = FormatDetector(registry)
    
    # Detect format
    format, error, _ = detector.detect_format(Path(file_path))
    if not format:
        raise ProcessingError(f"No valid format detected: {error}")
        
    # Process with custom parameters
    processor = DataProcessor()
    processed_data = processor.process_tables(
        table_data=table_data, 
        detected_format=format,
        cgm_params={'interpolation_limit': interpolation_limit},
        insulin_params={
            'bolus_limit': bolus_limit,
            'max_limit': max_dose
        }
    )
    
    return processed_data
```

</div>

## ⚙️ Configuration Options

<div class="feature-card">
<ul>
    <li>interpolation_limit: Number of missing CGM readings to interpolate</li>
    <li>bolus_limit: Threshold for classifying insulin as bolus vs basal</li>
    <li>max_dose: Maximum valid insulin dose (higher values flagged)</li>
</ul>
</div>

## 🚀 Command Line Usage

<div class="feature-card">

```bash
# Basic usage
python -m src.cli data.sqlite

# With custom parameters
python -m src.cli data.sqlite 
# Optional arguments
    --interpolation-limit 6 
    --bolus-limit 10.0 
    --max-dose 20.0 
    --output ./my_analysis
```
</div>
