<div class="hero">
  <h1>Data Processing</h1>
  <p>Understanding and configuring data processing options</p>
</div>

## 🔄 Processing Parameters

<div class="feature-card">
<ul>
    <li>CGM Gap Handling: How many missing readings to interpolate</li>
    <li>Insulin Classification: Thresholds for bolus vs basal</li>
    <li>Data Validation: Maximum valid insulin doses</li>
</ul>
</div>

## ⚙️ Configuration Examples

<div class="feature-card">

```bash
# Conservative gap filling (15 mins max)
python -m src.cli data.sqlite --interpolation-limit 3

# Higher insulin thresholds
python -m src.cli data.sqlite --bolus-limit 12.0 --max-dose 25.0

# Strict validation
python -m src.cli data.sqlite --bolus-limit 6.0 --max-dose 12.0
```

</div>

## 📊 Output Structure

<div class="feature-card">
<ul>
    <li>complete_dataset/: Full processed data with applied parameters</li>
    <li>monthly/: Split data maintaining processing settings</li>
    <li>processing_notes.json: Configuration and quality metrics</li>
</ul>
Example Output Structure:

```bash
data/exports
├── 2023-06-03_to_2024-09-28_complete
│   ├── aligned_data.csv
│   ├── carbs.csv
│   ├── cgm.csv
│   ├── insulin.csv
│   ├── notes.csv
│   └── processing_notes.json
└── monthly
    ├── 2023-06
    │   ├── aligned_data.csv
    │   ├── carbs.csv
    │   ├── cgm.csv
    │   ├── insulin.csv
    │   ├── notes.csv
    │   └── processing_notes.json
    ├── 2023-07
    │   ├── aligned_data.csv
    │   ├── carbs.csv
    │   ├── cgm.csv
    │   ├── insulin.csv
    │   ├── notes.csv
    │   └── processing_notes.json
```
</div>
