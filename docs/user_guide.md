# CryptoCorpusBuilder User Guide

## Overview
CryptoCorpusBuilder is a desktop application for building and managing large-scale cryptocurrency research corpora. It combines automated data collection, powerful document processing and deduplication, and built-in analytics to help you maintain a clean, balanced dataset.

## System Requirements
- Windows, macOS or Linux
- Python 3.8 or higher
- A virtual environment is recommended

## Installation
1. Clone or download the project.
2. Install the dependencies in your environment:
   ```bash
   pip install -r requirements.txt
   ```
   For minimal runtime installs use:
   ```bash
   pip install -r requirements.runtime.txt
   ```

## Launching the App
Run the graphical interface from the repository root:
```bash
python CorpusBuilderApp/app/main.py
```
The application window will open with tabs for configuration, collection and processing.

## Creating or Loading a Configuration
The application expects a YAML configuration describing collectors, processors and corpus directories. A minimal example:
```yaml
enabled_collectors:
  - github
enabled_processors:
  - pdf
directories:
  corpus_root: ./data/corpus
  raw_data_dir: ./data/raw
  processed_dir: ./data/processed
  metadata_dir: ./data/metadata
  logs_dir: ./data/logs
```
You can drag this file onto the **Configuration** tab or load it via the menu. To use the same configuration from the command line, pass `--config path/to/file.yaml`.

## Using the App (GUI)
- **Collectors** – start or stop document collectors.
- **Processors** – run batch processors on downloaded files.
- **Corpus Manager** – browse and edit corpus contents.
- **Balancer** – rebalance the corpus to match target allocations.
- **Analytics** – view statistics and keyword trends.
- **Logs** – monitor activity and errors.
The status bar displays queue information so you can track running tasks.

## Using the CLI
The project also provides command-line tools. For example, export a corpus:
```bash
python CorpusBuilderApp/cli.py export-corpus --corpus-dir data/corpus --output-dir data/exports
```
To compare corpus profiles use:
```bash
python CorpusBuilderApp/cli.py diff-corpus --profile-a snapshot1.json --profile-b snapshot2.json
```
You can run collectors, processors and the corpus balancer headlessly with
`cli/execute_from_config.py`:
```bash
python cli/execute_from_config.py --config path/to/config.yaml --run-all
```
Additional flags let you control which phases execute:

- `--collect` – run enabled collectors
- `--extract` – run enabled processors
- `--balance` – run the corpus balancer
- `--preview-only` – show selected modules without running them
- `--series-ids` – FRED collector: comma separated series IDs
- `--max-results` – FRED collector: limit number of data points
- `--search-terms` – GitHub collector: repository search terms
- `--topic` – GitHub collector: optional topic filter
- `--max-repos` – GitHub collector: maximum repositories to fetch
- `--query` – Annas collector: search query
- `--output-dir` – output directory for Annas, SciDB or Web collectors
- `export-corpus --dry-run` – preview export actions without writing files

Preview all phases without executing them:
```bash
python cli/execute_from_config.py --config path/to/config.yaml \
    --collect --extract --balance --preview-only
```

Dry run export example:
```bash
python CorpusBuilderApp/cli.py export-corpus --corpus-dir data/corpus \
    --output-dir exports --dry-run
```

Use `--version` to print the application version or `--matrix` to see which
features are available in the CLI versus the GUI:
```bash
python CorpusBuilderApp/cli.py --version
python CorpusBuilderApp/cli.py --matrix
```
The `--version` flag outputs the package version number. The `--matrix` flag
prints a table comparing CLI commands to GUI actions.
See [CLI vs GUI feature matrix](cli_vs_gui_matrix.md) for details.

## Exporting the Corpus
Create a versioned ZIP archive with manifest using the CLI:
```bash
python CorpusBuilderApp/cli.py export-corpus --corpus-dir data/corpus --output-dir data/exports
python CorpusBuilderApp/cli.py export-corpus --corpus-dir data/corpus --output-dir exports/ --version-tag v1.2.0
```
If the Dashboard is open, you can also trigger an export from the **Tools** or **Corpus Manager** tab.

## Tools

- **check_corpus_structure.py** – validate the directories defined in your
  `ProjectConfig`. Run it with `--config path/to/config.yaml` to check that the
  raw, processed, metadata and logs folders exist and are writable.

## Troubleshooting
- If a configuration fails to load, check the YAML syntax and file paths.
- Logs are stored in the directory defined by `logs_dir` in your configuration.
- Ensure all dependencies are installed if modules fail to start or you see missing-file errors.
