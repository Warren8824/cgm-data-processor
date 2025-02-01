<div class="hero">
  <h1>Installation</h1>
  <p>Set up CGM Data Processor for development</p>
</div>

## Simple install

```bash
# Clone repository
git clone https://github.com/Warren8824/cgm-data-processor.git
cd cgm-data-processor

# Install dependencies using pip
pip install -r requirements.txt

# Or using Poetry 
poetry install
```

And as simple as that the system is ready to use. - Check out our [Basic Usage](./quickstart/basic.md) page.

## 🛠️ Development Setup

<div class="feature-card">
<ul>
    <li>Python 3.10+ required</li>
    <li>Poetry for dependency management (Preferred)</li>
    <li>Git for version control</li>
</ul>
</div>

```bash
# Clone repository
git clone https://github.com/Warren8824/cgm-data-processor.git
cd cgm-data-processor

# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# Create and activate new environment

# macOS/Linux:
poetry env activate
source $(poetry env info --path)/bin/activate

# Windows(Powershell):
poetry env activate
(Invoke-Expression "$(poetry env info --path)\Scripts\Activate")

# Install development dependencies

# Using poetry:
poetry install --with dev

# or using venv:
pip install -r requirements-dev.txt


# Setup pre-commit hooks
poetry run pre-commit install

# Run tests
poetry run pytest
```

✅ Verify Installation

```python
from src.core.format_registry import FormatRegistry

# Should print available formats
registry = FormatRegistry()
print(registry.formats)
```