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
    <li>Poetry for dependency management</li>
    <li>Git for version control</li>
</ul>
</div>

```bash
# Clone repository
git clone https://github.com/Warren8824/cgm-data-processor.git
cd cgm-data-processor

# Install development dependencies 
poetry install --with dev

# Setup pre-commit hooks
poetry run pre-commit install
```

✅ Verify Installation

```python
from src.core.format_registry import FormatRegistry

# Should print available formats
registry = FormatRegistry()
print(registry.formats)
```