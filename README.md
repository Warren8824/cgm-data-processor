# CGM Data Processor

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue) [![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://github.com/Warren8824/cgm-data-processor) ![Release Status](https://img.shields.io/badge/status-pre--release-orange) ![Black](https://img.shields.io/badge/code%20style-black-4B8BBE.svg) ![isort](https://img.shields.io/badge/imports-isort-4B8BBE.svg) ![Pylint](https://img.shields.io/badge/code%20quality-pylint-4B8BBE.svg) [![Licence: MIT](https://img.shields.io/badge/licence-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> ⚠️ **Medical Disclaimer**: This is a data analysis tool only and is not intended for use as a medical device.

**Lightweight and fast toolkit for parsing, normalising, and exporting diabetes device data (CGM, insulin, carbs, notes).** Process multiple device backups locally into a consistent output format, enabling long-term unified storage that remains unaffected by device format changes over time. Built by a T1D developer for analysis and research workflows.

---

📚 **[Full Documentation](https://warren8824.github.io/cgm-data-processor/)** | 🐛 **[Report Issues](https://github.com/Warren8824/cgm-data-processor/issues)** | 💬 **[Discussions](https://github.com/Warren8824/cgm-data-processor/discussions)**


## Why This Exists

As someone living with Type 1 diabetes, I've experienced firsthand the frustration when device manufacturers update their hardware or software, breaking compatibility with existing data exports. 
This project solves that problem by:

- **Preserving your historical data** in a standardised format, regardless of device changes
- **Enabling long-term analysis** across different devices and systems
- **Providing control over your own health data** without vendor lock-in
- **Supporting research and personal insights** with clean, consistent datasets

This project would also be suitable for standardising multiple data back-ups from multiple people into one unified format. **Enabling side-by-side comparison and analysis**.

---

## What It Does

This toolkit provides:

- **Format registry** that dynamically loads `DeviceFormat` definitions from `src/core/devices/`
- **Format detector** that validates file structure (CSV, SQLite, JSON, XML) against format specifications. **Note**: The format detector validates the presence/shape of expected tables and columns (structure), it does not validate the semantic correctness of values — that remains the processor's responsibility.
- **Per-type processors** that standardise CGM, insulin, carbs, and notes data with processing metadata
- **Deterministic timestamp detection** and conversion to UTC (epoch, explicit formats, inference fallback)
- **Timeline alignment** onto a reference dataset (default: CGM) with combined aligned CSV export
- **Comprehensive processing logs** capturing all transformations and data quality metrics

---

## Currently Supported Devices

- ✅ **XDrip+** SQLite exports
- ✅ **LibreView** CSV exports
- 🚧 More formats in development

### Call for Device Format Contributors

**We need your help to expand device support!** If you use a diabetes management system not listed above, you can contribute by:

1. Opening an issue with your device/app name
2. Describing the available export format(s)
3. Providing sample files with dummy data (never share real medical data publicly)

If you have basic Python experience and want to add your own format, see our [Contributing Guide](https://warren8824.github.io/cgm-data-processor/contributing/formats/).

---

## Quick Start

### Installation

**Recommended: Use a virtual environment.** Examples below use Windows PowerShell.

#### Using Poetry (recommended for development)

```powershell
pip install poetry
git clone https://github.com/Warren8824/cgm-data-processor.git
cd cgm-data-processor
poetry install --with dev
pre-commit install
```

#### Using pip + venv

```powershell
git clone https://github.com/Warren8824/cgm-data-processor.git
cd cgm-data-processor
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
pre-commit install
```

### Basic Usage

Process a device export and generate CSV outputs:

```powershell
python -m src.cli path\to\export.file --debug
```

#### Key CLI Options

See `src/cli.py` for full details:

```powershell
--debug                     # Enable debug logging
--output PATH               # Output folder (default: data/exports)
--interpolation-limit INT   # Max CGM gaps to interpolate (4 = 20 minutes)
--bolus-limit FLOAT         # Max insulin units for bolus classification
--max-dose FLOAT            # Maximum valid insulin dose threshold
```

### What You Get

Each processing run creates a self-contained folder under `data/exports/`. The folder name uses the data date range and a timestamped run id and looks like:

`{start_date}_to_{end_date}_complete_{run_id}`

Where `run_id` is generated as `YYYYMMDDTHHMMSS` (for example: `2023-06-03_to_2023-10-05_complete_20251004T194625`). Inside you'll find:

```
data/exports/
└── 2023-06-03_to_2023-10-05_complete_20251004T194625/
    ├── cgm.csv                    # Processed CGM readings
    ├── insulin.csv                # Insulin doses (basal/bolus classified)
    ├── carbs.csv                  # Meal/carb entries
    ├── notes.csv                  # Notes and comments
    ├── aligned_data.csv           # Combined timeline across all data types
    ├── processing_notes.json      # Metadata, source units, processing logs
    └── monthly/                   # Per-month CSV splits
        ├── 2023-06/cgm.csv
        ├── 2023-06/insulin.csv
        └── ...
```

---

## Use Cases

- **Personal Data Analysis**: Process and clean your diabetes device data for retrospective analysis
- **Quality Assessment**: Evaluate CGM data completeness and identify gaps in coverage
- **Data Migration**: Convert data between different diabetes management systems
- **Research Projects**: Generate standardised datasets for diabetes research studies
- **Long-Term Storage**: Archive your data in a format that survives device upgrades
- **Pattern Recognition**: Track relationships between CGM, insulin, and meal data over time

---

## Project Architecture

Understanding where things live:

```
src/
├── cli.py                          # CLI entry point and orchestration
├── file_parser/
│   └── format_detector.py         # File structure validators (CSV/SQLite/JSON/XML)
├── core/
│   ├── format_registry.py         # Dynamic format loading
│   ├── devices/                   # Device format definitions
│   │   ├── xdrip/
│   │   ├── libreview/
│   │   └── ...
│   └── aligner.py                 # Timeline alignment and combined DataFrame builder
├── readers/                       # CSV/SQLite readers with timestamp detection
├── processors/                    # Per-type processing (CGM, insulin, carbs, notes)
└── exporters/                     # CSV export and processing_notes.json writer
```

---

## Adding a New Device Format

Quick guide for contributors:

1. Create a new module: `src/core/devices/<vendor>/<format>.py`
2. Define one or more `DeviceFormat` instances describing:
   - `FileConfig` (file structure and name pattern)
   - `TableStructure` (table names, timestamp columns)
   - `ColumnMapping` (mapping from source column names to standardised fields)
3. Ensure `FileConfig.name_pattern` matches expected filenames (uses `Path.match`).
4. Keep modules import-free where possible — `FormatRegistry` imports each module to inspect exported `DeviceFormat` objects.
5. Add tests with representative sample files in `tests/data/` and include small, focused unit tests for detection and parsing.

See our [detailed format contribution guide](https://warren8824.github.io/cgm-data-processor/contributing/formats/) for examples and best practices. Example device format modules to inspect: `src/core/devices/xdrip/sqlite.py` and `src/core/devices/libreview/csv.py`.

---

## Development

### Prerequisites

- Python 3.10+
- Poetry (recommended) or pip + venv

### Quality Tools & Pre-commit Hooks

This project maintains code quality using:

- **Black** — code formatting
- **isort** — import sorting
- **Pylint** — static analysis and linting
- **pytest** — testing framework
- **codespell** — typo detection in documentation and docstrings
- **Pre-commit hooks** — automated checks on staged files

#### Pre-commit Configuration

The `.pre-commit-config.yaml` runs these checks locally:

- `codespell` on `.md`, `.py`, `.rst` files
- `black` for code formatting
- `isort` for import organisation
- `pylint` for static analysis
- `check-uk-english` (local hook) — flags US→UK spelling differences (non-destructive, excludes `.github/scripts/` and `.github/tools/`)

**Windows users:** Activate your virtual environment before running pre-commit:

```powershell
.\.venv\Scripts\Activate.ps1
pre-commit run --all-files
```

### Helper Scripts (Manual Use Only)

These utilities live under `.github/` and are intentionally manual:

- `.github/scripts/check_uk_english.py` — Non-destructive UK English checker (used in pre-commit)
- `.github/scripts/find_us_in_string_literals.py` — AST-based scanner for US spellings in Python strings
- `.github/tools/convert_us_to_uk.py` — Archived bulk replacement tool (use only on branches, review in PRs)

### Running Tests

```powershell
pytest -q
```

If pytest reports no tests, try running specific test files under `tests/` to confirm discovery.

### Documentation

Build and serve documentation locally:

```powershell
# With Poetry
poetry install --with dev
mkdocs serve

# With pip
pip install -r requirements-dev.txt
mkdocs serve
```

Visit `http://localhost:8000` to view the documentation.

---

## Dependencies

### Core

- numpy ≥2.1.0
- pandas ≥2.2.0
- SQLAlchemy ≥2.0.0
- plotly ≥5.0.0

### Documentation

- MkDocs Material
- MkDocstrings

See `pyproject.toml` or `requirements.txt` for the complete dependency list.

---

## Contributing

Contributions are very welcome! The most valuable contributions are:

- **Device format definitions** with representative sample files (dummy data only)
- **Tests** for timestamp detection and format validation
- **Documentation** improvements and usage examples
- **Bug reports** with clear reproduction steps

### Suggested Workflow

1. Open an issue to discuss larger changes or new device formats
2. Create a feature branch from `main`
3. Make your changes and run pre-commit hooks locally
4. Ensure tests pass with `pytest`
5. Open a pull request for review

Please ensure all contributions use UK English spelling throughout.

---

## Project Status

This project is in **pre-release development**.  Current focus areas:

- [x] Core device format support
- [x] Enhancing documentation with more examples
- [ ] Completing test suite coverage
- [ ] Adding basic statistics and visualisations
- [ ] Preparing first stable release

---

## Licence

This project is licenced under the MIT Licence. See the `LICENSE` file for details.

---

## Contact

**Warren Bebbington**  
📧 warrenbebbington88@gmail.com  
💬 [Open an issue](https://github.com/Warren8824/cgm-data-processor/issues) for questions, bug reports, or to share sample files