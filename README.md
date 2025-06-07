# codex_try

[![Tests](https://github.com/OWNER/REPO/actions/workflows/test.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/test.yml)

## Installation

1. Create and activate a virtual environment (Python 3.8+ recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
2. Install the project dependencies:
   ```bash
   pip install -r CorpusBuilderApp/requirements.txt
   ```
   The requirements file contains all mandatory packages. If you plan to use the
   graphical interface, ensure that `PySide6` is installed. It is already listed
   in the requirements but can be installed separately with `pip install PySide6`.

## Running the Application

The main UI can be launched with:
```bash
python CorpusBuilderApp/app/main.py
```
For command-line operations, use the CLI helper:
```bash
python cli/execute_from_config.py --help
```

## Running Tests

Tests are written with `pytest`. After installing the dependencies, run:
```bash
pytest
```
Some UI tests require `PySide6`; without it they will be skipped.
