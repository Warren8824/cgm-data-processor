## Copilot / AI Agent Quick Instructions (cgm-data-processor)

Purpose: give AI coding agents the specific, actionable knowledge needed to be productive in this repo.

Quick run (example) — PowerShell

```powershell
# Process the included sample SQLite export and write CSVs to ./exports/test
python -m src.cli data/sample.sqlite --debug --output data/exports/test

# Run tests
poetry run pytest -q

# Serve docs (dev deps required)
poetry run mkdocs serve
```

Key places to look

- `src/cli.py` — main entrypoint. Use `python -m src.cli <file>`; common flags: `--debug`, `--output`, `--interpolation-limit`, `--bolus-limit`, `--max-dose`.
- `src/core/format_registry.py` — dynamically loads format definitions from `src/core/devices/`. Formats are registered as `DeviceFormat` instances; registry keys are constructed as `format_def.name + '_' + file_type.value`.
- `src/core/devices/` — device format definitions live here. Example: `src/core/devices/xdrip/sqlite.py` defines `XDRIP_SQLITE_FORMAT` (a `DeviceFormat` with `FileConfig` and `TableStructure`). New formats: add a module exporting a `DeviceFormat` instance.
- `src/readers/base.py` — `BaseReader.register(file_type)` decorator registers readers. Reader selection: `BaseReader.get_reader_for_format(fmt, file_path)` matches `FileConfig.name_pattern` via `Path.match`.
- `src/processors/` — processors are registered in `src/processors/__init__.py`. The top-level `DataProcessor` orchestrates per-type processing (CGM, insulin, carbs, notes).
- `src/core/aligner.py` — alignment logic. Important: alignment expects a monotonic `DatetimeIndex` and that the modal time delta equals the requested `freq` (default `'5min'`). Alignment produces an `AlignmentResult` with combined DataFrame and processing notes.
- `src/exporters/csv.py` — `create_csv_exporter()` factory and `CSVExporter` implementation (exports CSVs + `processing_notes.json`).

Patterns and repo-specific conventions

- Device formats are pure data: modules should create one or more `DeviceFormat` objects (see `XDRIP_SQLITE_FORMAT` and `LIBREVIEW_CSV_FORMAT`) — `FormatRegistry` scans all `.py` files under `src/core/devices` and registers any `DeviceFormat` instances it finds.
- File pattern matching uses `Path.match(file_pattern)`. Prefer glob-like patterns such as `*.sqlite` or `*.csv` and ensure they match the input path when testing.
- Readers must be registered with `@BaseReader.register(FileType.<TYPE>)`. Implement `read_table(self, table_structure)` and return `TableData` objects; use `read_all_tables()` to process all declared tables.
- Timestamp detection: `BaseReader.detect_timestamp_format()` uses a deterministic heuristic (sample up to 50 values, numeric epoch detection, limited explicit formats, fallback to pandas). Be conservative when modifying this — many formats rely on its behavior.
- Registry format key: call sites occasionally expect `format_name + '_' + filetype`, e.g., `registry.get_format('xdrip_sqlite_sqlite')` — use `registry.formats` or helper methods like `get_formats_for_file()` when possible.

Developer workflows & commands

- Install (Poetry):
  - `poetry install --with dev` (development deps: pytest, mkdocs, pre-commit, etc.)
  - `pre-commit install`
- Install (pip):
  - `pip install -r requirements-dev.txt`
  - `pre-commit install`
- Tests: `poetry run pytest` or `pytest -q`
- Docs: `poetry run mkdocs serve` (or `mkdocs serve` if dev deps installed globally)

Integration and extension points

- Add a new device format: create `src/core/devices/<vendor>/<format>.py` and export a `DeviceFormat` instance (similar to `XDRIP_SQLITE_FORMAT`). Keep `files: [FileConfig(...)]` with `name_pattern`, `file_type`, and `tables`.
- Add a new reader: implement a reader class and register it with `@BaseReader.register(FileType.<TYPE>)` so `get_reader_for_format()` can select it.
- Add processor logic: extend `src/processors/<type>.py` and ensure it is imported/registered in `src/processors/__init__.py` so `DataProcessor()` will pick it up.

Things that commonly break (watch for these)

- Alignment errors: `Aligner._validate_timeline` will raise if the reference DataFrame index isn't a `DatetimeIndex`, isn't monotonic, or the modal delta doesn't equal the expected `freq`. When adding formats or changing CGM sampling, update tests or the alignment frequency.
- Format loading: `FormatRegistry` ignores `__init__.py` files and imports every `.py` under `src/core/devices`. Syntax errors or runtime imports in those files will break registry loading — keep those modules minimal and pure-data if possible.
- Path matching: `FileConfig.name_pattern` uses `Path.match`; tests should confirm patterns match real file paths (including nested paths).

References (examples to open)

- `src/cli.py` — CLI flow: detect format -> get `BaseReader` -> `DataProcessor.process_tables()` -> `Aligner.align()` -> exporter factory `create_csv_exporter()`
- `src/core/format_registry.py` and `src/core/devices/xdrip/sqlite.py`
- `src/readers/base.py` (timestamp heuristics + registration)
- `src/core/aligner.py` (alignment rules)

If anything above is unclear or you'd like more examples (e.g., a template for adding a new device format or reader), tell me which example you want and I'll add it.

## Docs setup & UK English

This project uses MkDocs Material and `mkdocstrings` for API reference; the active configuration is in `mkdocs.yml`. Keep the docs and in-code documentation consistent with the live config:

- Server / build commands (PowerShell):
  - Serve locally: `poetry run mkdocs serve` (dev deps required)
  - Build for publishing: `poetry run mkdocs build -d site`

- Key `mkdocs.yml` settings to respect:
  - `theme.name: material` and the `mkdocstrings` handler for Python are already configured (docstring_style: `google`). Prefer Google-style docstrings in new modules.
  - `plugins` includes `git-revision-date-localized`, `minify`, `redirects` and `search` — avoid removing unless necessary.
  - Navigation (`nav`) is authoritative for docs structure; update `nav` when adding new user-guide or API pages.

- Practical checks to keep docs correct and aligned:
  - When adding or changing public symbols (classes/functions) ensure the docstring is Google-style and that mkdocstrings picks it up (run `mkdocs serve` and verify new pages appear under API Reference).
  - If adjusting `mkdocs.yml`, run `poetry run mkdocs build` to surface YAML/schema problems early.
  - Keep code examples copyable and use UK English in prose and comments (see below).

- UK English conventions (apply everywhere: docs, README, code comments, docstrings):
  - Use UK spellings: organise, initialise, behaviour, colour, centre, metre, analyse, licence (where applicable), favour `-ise` and `-our` spellings.
  - Use single quotes for prose where natural (project uses plain Markdown; be consistent within a file).
  - Prefer British date formats in prose (e.g., 12 October 2025) if writing dates in docs.

- Automated checks & PR guidance (recommendations):
  - Add a pre-commit spellchecker for prose (e.g., `codespell` or `pre-commit` hook using `cspell`) and configure it to prefer `en-GB`. This prevents accidental US spellings in docs and docstrings.
  - In PRs that change public APIs or docs: include a screenshot or link to the built docs pages (running `mkdocs serve` locally) and a short note confirming UK English was used.

If you want, I can add a template `CONTRIBUTING` snippet for docs changes and a suggested `pre-commit` hook config to enforce `en-GB` spelling.
