# codex_try


[![Tests](https://github.com/tulipoaaaaa/codex_try/actions/workflows/test.yml/badge.svg)](https://github.com/tulipoaaaaa/codex_try/actions/workflows/test.yml)

## Installation

Install the full development requirements and then any development extras:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

`requirements.txt` contains all runtime and development dependencies. For
minimal Docker or PyInstaller builds use `requirements.runtime.txt` instead,
which only includes the packages needed at runtime. The optional
`requirements-dev.txt` file adds linting and test tools.

## Environment configuration

See [docs/environment_config.md](docs/environment_config.md) for the list of
required environment variables and details on switching between test and
production modes.

## Testing

The test suite can run without PySide6 installed by setting the environment
variable `PYTEST_QT_STUBS=1`. This enables stubbed Qt classes so tests work in
headless or CI environments. Only limited behaviour is covered, so full UI
tests should still be executed locally with PySide6 available.

The test `tests/ui_wrappers/test_balancer_wrapper.py` relies on PySide6 (or the
`PYTEST_QT_STUBS` environment variable) and is marked with the
`optional_dependency` marker. Run only optional tests with:

```bash
pytest -m optional_dependency
```

Skip them using:

```bash
pytest -m "not optional_dependency"
```

## Pre-push hook

A convenience script is provided at `scripts/pre_push.sh` to run linting and the
unit tests before code is pushed. Install the hook by linking it into your local
Git hooks directory:

```bash
ln -s ../../scripts/pre_push.sh .git/hooks/pre-push
```

The script will run `ruff` if it is installed, or fall back to `flake8`. It then
executes `pytest`. The push will be blocked if any of these steps fail.

## 🖥️ Running GUI on Linux or headless environments

Install Qt system dependencies:

```bash
sudo apt install libegl1 libxcb-icccm4 libxkbcommon-x11-0
```

Launch the application with offscreen rendering:

```bash
HEADLESS=1 python app/main.py
```

The Tools menu includes an **Import Corpus** option for loading corpus archives exported from another installation.

## Command Line Interface

Several CLI tools accompany the GUI for scripted or headless usage. The main
entry points live in `CorpusBuilderApp/cli.py` and `cli/execute_from_config.py`.
See the [full CLI usage](docs/user_guide.md#using-the-cli) for details.

Key commands include:

- `export-corpus` – archive a corpus for distribution
- `diff-corpus` – compare two corpus profile JSON files
- `generate-default-config` – write a template ProjectConfig YAML
- `sync-domain-config` – update domain_config.py from balancer_config
- Pipeline execution via `execute_from_config.py`

For a complete comparison of what the command line and GUI each offer, see [docs/cli_vs_gui_matrix.md](docs/cli_vs_gui_matrix.md).

Useful flags:

- `--version` – print the application version
- `--matrix` – show CLI and GUI feature parity
- `--collect` – run enabled collectors
- `--extract` – run enabled processors
- `--balance` – run the corpus balancer
- `--preview-only` – list modules without executing them
- `--series-ids` – FRED collector: comma separated series IDs
- `--max-results` – FRED collector: limit number of data points
- `--search-terms` – GitHub collector: repository search terms
- `--topic` – GitHub collector: optional topic filter
- `--max-repos` – GitHub collector: maximum repositories to fetch
- `--query` – Annas collector: search query
- `--output-dir` – output directory for Annas, SciDB or Web collectors
- `export-corpus --dry-run` – preview export actions without writing files
- `--version-tag`     Optional version label used in the exported archive filename

Example preview run:
```bash
python cli/execute_from_config.py --config path/to/config.yaml \
    --collect --extract --balance --preview-only
```

Example dry run export:
```bash
python CorpusBuilderApp/cli.py export-corpus --corpus-dir data/corpus \
    --output-dir exports --dry-run
```

### Example Commands
```bash
python CorpusBuilderApp/cli.py check-corpus --config config.yaml --auto-fix
```

## License

This project is proprietary and all rights are reserved by Bored AI Labs.
To inquire about licensing, contact [legal@boredailabs.com](mailto:legal@boredailabs.com).

