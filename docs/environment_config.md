# Environment Configuration

This project relies on several environment variables to locate configuration files and provide credentials for the collectors. Variables can be placed in a `.env` file at the repository root or exported in your shell. The `.env` file is automatically loaded when the application or tests start.

## Example `.env` layout

```bash
# Select which configuration to load
ENVIRONMENT=test  # or "production"

# Optional paths
PYTHON_PATH=/usr/bin/python3
VENV_PATH=/home/user/venv
TEMP_DIR=/tmp/ccb

# API keys
GITHUB_TOKEN=ghp_exampletoken
AA_ACCOUNT_COOKIE=sessionid=abc123
AA_COOKIE=sessionid=abc123   # alternate variable name
FRED_API_KEY=fred_example
BITMEX_API_KEY=bitmex_key
BITMEX_API_SECRET=bitmex_secret
ARXIV_EMAIL=user@example.com

# Processing options
PDF_THREADS=4
TEXT_THREADS=4
BATCH_SIZE=50
MAX_RETRIES=3
TIMEOUT=300

# Corpus directories
CORPUS_ROOT=/data/corpus
RAW_DATA_DIR=/data/corpus/raw
PROCESSED_DIR=/data/corpus/processed
METADATA_DIR=/data/corpus/metadata
LOGS_DIR=/data/corpus/logs
```

Only the variables relevant to your workflow need to be defined. If a value is omitted, sensible defaults from `ProjectConfig` will be used.

## Switching between test and production

The active environment is controlled by the `ENVIRONMENT` variable. Set it to `test` or `production` in your `.env` file (or export it in the shell) before launching the application or running command-line tools. The GUI also exposes an environment selector in the **Configuration** tab that updates the same value.

Different YAML configuration files can be used for each environment (for example `config/test.yaml` and `config/production.yaml`). Changing `ENVIRONMENT` ensures the appropriate configuration is loaded.

For automated tests or headless operation you can simply set `ENVIRONMENT=test`.
