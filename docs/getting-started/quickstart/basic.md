<div class="hero">
  <h1>Basic Usage</h1>
  <p>Process and analyze your diabetes data</p>
</div>

## 🚀 Command Line Usage

<div class="feature-card">
<ul>
    <li>Basic: <code>python -m src.cli data.sqlite</code></li>
    <li>Custom output: <code>python -m src.cli data.sqlite --output my_folder</code></li>
    <li>Debug mode: <code>python -m src.cli data.sqlite --debug</code></li>
</ul>
</div>

## ⚙️ Processing Options

<div class="feature-card">

```bash
python -m src.cli data.sqlite \
    --interpolation-limit 6   # Max CGM gaps to fill (6 = 30 mins)
    --bolus-limit 10.0       # Max bolus insulin units
    --max-dose 20.0          # Max valid insulin dose
    --output ./my_analysis   # Output location
```

</div>

## 📊 Parameter Guide

<div class="feature-card">
<ul>
    <li><code>interpolation-limit</code>: Gaps larger than this won't be filled (default: 4 = 20 mins)</li>
    <li><code>bolus-limit</code>: Doses above this classified as basal (default: 8.0 units)</li>
    <li><code>max-dose</code>: Doses above this flagged as invalid (default: 15.0 units)</li>
</ul>
</div>
