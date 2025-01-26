<div class="hero">
  <h1>Error Handling</h1>
  <p>Common errors and troubleshooting</p>
</div>

## ❌ Common Errors

<div class="feature-card">
<ul>
    <li>FormatDetectionError: File format not recognized</li>
    <li>DataProcessingError: Invalid or corrupt data</li>
    <li>AlignmentError: Cannot align datasets</li>
    <li>FileAccessError: Cannot read input file</li>
</ul>
</div>

## 🔍 Troubleshooting

<div class="feature-card">

```bash
# Enable debug mode for detailed errors
python -m src.cli data.sqlite --debug

# Common debug output:
✓ Format Detection Successful
✗ Data Reading Failed: Missing required columns
   Details: Table 'BgReadings' missing 'calculated_value'
```

</div>

## 🚫 Data Validation Errors

<div class="feature-card">
<ul>
    <li>Invalid glucose values (outside 40-400 mg/dL)</li>
    <li>Insulin doses exceeding max_dose</li>
    <li>Missing timestamps or required fields</li>
    <li>Duplicate timestamps in CGM data</li>
</ul>
</div>
