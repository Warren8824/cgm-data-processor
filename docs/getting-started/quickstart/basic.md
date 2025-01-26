<div class="hero">
  <h1>Basic Usage</h1>
  <p>Getting started with your diabetes data</p>
</div>

## 🚀 Quick Start 

<div class="feature-card">
<p>Basic steps:</p>
<ul>
    <li>Download this tool from GitHub</li>
    <li>Install Python 3.10 or newer</li>
    <li>Open a terminal/command prompt in the downloaded folder</li>
    <li>Run: <code>python -m src.cli your_data_file.sqlite</code></li>
</ul>
</div>

## 📁 Output Options

<div class="feature-card">
<p>Choose where to save your processed data:</p>
<ul>
    <li>Default location: <code>./data/exports</code></li>
    <li>Custom location: <code>python -m src.cli your_data_file.sqlite --output path/to/folder</code></li>
</ul>
</div>

## 💡 Example

<div class="feature-card">
<p>XDrip+ workflow:</p>
<ul>
    <li>Export SQLite file from XDrip+</li>
    <li>Place file in tool folder</li>
    <li>Run: <code>python -m src.cli xdrip_data.sqlite --output my_analysis</code></li>
    <li>Find processed data in the 'my_analysis' folder</li>
</ul>
</div>
