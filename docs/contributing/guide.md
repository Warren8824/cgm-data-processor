# Contributing to Diabetes Data Processing Project

Welcome to our diabetes data processing project! We're working to create a unified tool that can process and analyze data from various diabetes management devices and applications. Your contributions can help make diabetes data more accessible and useful for everyone.

## Setting Up Your Development Environment

We use Poetry for dependency management to ensure consistent development environments. If you haven't used Poetry before, it's a modern Python package manager that handles dependencies and virtual environments automatically.

1. First, install Poetry if you haven't already:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/[username]/diabetes-data-processing.git
   cd diabetes-data-processing
   ```

3. Install dependencies using Poetry:
   ```bash
   poetry install
   ```
   This will create a virtual environment and install all required dependencies.

If you prefer using pip, you can alternatively:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

## Code Style and Quality Standards

Our project maintains high code quality standards through consistent style and thorough testing. We follow these core principles:

1. Readability takes precedence over clever solutions
2. Consistency across the entire codebase
3. Well-documented and maintainable code
4. Pragmatic approach to style rules

### Code Style Specifications

We follow standard Python naming conventions:

- Functions and variables use `snake_case`
- Classes use `PascalCase`
- Constants use `UPPER_CASE`
- Protected/private attributes use `_leading_underscore`

File and Function Structure:

- Maximum line length: 100 characters
- Maximum file length: 1000 lines
- Functions should have no more than 5 arguments
- Classes should have no more than 7 attributes and 20 public methods

Documentation Requirements:

- All modules must have docstrings
- Public methods require docstrings; private methods (starting with `_`) do not
- Type hints are required for function parameters and return values

We use pre-commit hooks to maintain code quality. After setting up your environment, install the pre-commit hooks:
```bash
poetry run pre-commit install
```

## How You Can Help

### 1. Share Sample Data Files

We currently need sample data files from various diabetes management devices and applications. This helps us understand different data formats and ensure our tool works correctly. Please use our [New Device Format Submission](https://github.com/Warren8824/cgm-data-processor/issues/new?template=new_format_submission.yml) issue on Github.

#### Currently Supported Formats:
- XDrip+ SQLite backup files

#### Priority Formats We'd Like to Support:

- Dexcom G6/G7 exports
- Freestyle Libre 1/2/3 exports
- Medtronic pump data
- Tandem t:slim pump data
- Nightscout database exports
- Tidepool platform exports

#### Data Submission Guidelines

When submitting sample files:

1. Remove Personal Information:
   - Anonymize all personal identifiers
   - Replace actual names with placeholder text
   - Remove medical ID numbers and device serial numbers
   - Ensure timestamps are within a reasonable timeframe (e.g., last 7 days)

2. Prepare Your Files:
   - Export data using standard export features
   - Document your export process
   - Note software/firmware versions
   - Include relevant export settings

3. Submit Your Contribution:
   - Create an issue with tag `new-format-sample`
   - Attach anonymized sample files
   - Include device/application details and export method

### 2. Format Definition Contributions

To contribute a new format definition:

1. Study our existing XDrip+ SQLite format as a template:

   ```python
   XDRIP_SQLITE_FORMAT = DeviceFormat(
       name="xdrip_sqlite",
       files=[
           FileConfig(
               name_pattern="*.sqlite",
               file_type=FileType.SQLITE,
               tables=[...]
           )
       ],
   )
   ```

2. Create your format definition:
   - Place new formats in `src/core/devices/`
   - Include comprehensive documentation
   - Define table structures and column mappings
   - Specify data types and units
   - Document timestamp formats

3. Submit your contribution:
   - Fork the repository
   - Create a branch: `git checkout -b new-format/[device-name]`
   - Add your format definition
   - Include sample data files that demonstrate the format structure
   - Create a pull request

## Quality Assurance

When contributing new code or format definitions, ensure quality through these steps:

1. Run the test suite:
   ```bash
   poetry run pytest
   ```

2. Ensure code quality:
   ```bash
   poetry run pylint src/
   poetry run black src/
   poetry run isort src/
   ```



## Error Handling

When adding new functionality:
- Use specific exception classes from `core/exceptions.py`
- Avoid catching generic exceptions
- Add meaningful error messages
- Document error conditions in docstrings

## Commit Guidelines

Write clear, descriptive commit messages:

```
Add Dexcom G6 format definition

- Implements basic CSV parsing for Dexcom clarity exports
- Adds unit conversion for mmol/L to mg/dL
- Includes timestamp standardization
- Fixes #123
```

## Getting Help

- Create an issue with tag `question` for general queries
- Join our discussions in the GitHub Discussions tab
- Check existing issues and pull requests for similar topics

## Code of Conduct

We are committed to providing a welcoming and inclusive experience for everyone. Please:

- Be respectful and considerate in communications
- Focus on the technical aspects of contributions
- Help others learn and grow
- Report inappropriate behavior to project maintainers

## License

By contributing to this project, you agree that your contributions will be licensed under the same terms as the project (see our [License page](license.md)).

Thank you for helping make diabetes data more accessible and useful for everyone!