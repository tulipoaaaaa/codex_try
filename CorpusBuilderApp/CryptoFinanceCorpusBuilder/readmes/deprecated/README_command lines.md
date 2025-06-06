# Crypto-Finance Corpus Builder

This project provides a modular, extensible framework for building, managing, and analyzing a comprehensive corpus of crypto-finance documents from a variety of sources.

---

## Directory Structure

```
CryptoFinanceCorpusBuilder/
│
├── cli/                           # Command-line interface (CLI) entry point
├── config/                        # Configuration files and settings
├── processors/                    # Text extraction and processing tools
├── sources/                       # Data collectors for various sources
│   └── specific_collectors/       # Source-specific collectors (e.g., Anna's Archive, Arxiv, etc.)
├── storage/                       # Corpus and metadata management
└── ...                            # Other supporting modules
```

---

## Main Components

- **CLI Entry Point:**  
  - `cli/crypto_corpus_cli.py`
  - Use as a module:  
    ```bash
    python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli [command] [options]
    ```
  - Or, for legacy compatibility (if a copy exists in project root):  
    ```bash
    python command_interface.py [command] [options]
    ```

- **Config:**  
  - All configuration files are in `config/`. The main source configuration is now `enhanced_sources.json` (default for the CLI).

- **Processors:**  
  - Text extraction, deduplication, and domain classification logic in `processors/`.

- **Collectors:**  
  - Modular collectors for each data source in `sources/specific_collectors/`.
  - Anna's Archive, Arxiv, GitHub, FRED, ISDA, BitMEX, and more.

- **Corpus Management:**  
  - `storage/corpus_manager.py` manages the corpus and metadata.

---

## Usage

### Collecting Data from a Source

```bash
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources arxiv github --config CryptoFinanceCorpusBuilder/config/enhanced_sources.json --output-dir data/corpus_1
```

Or, since enhanced_sources.json is now the default:

```bash
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources arxiv github --output-dir data/corpus_1
```

### Collecting from Anna's Archive

```bash
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect_annas --query "cryptocurrency trading" --client cookie --output-dir data/corpus_1/annas
```
- `--client` can be `simple`, `updated`, `cookie`, or `enhanced` depending on your needs and authentication setup.

### Processing Collected Data

```bash
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli process --input-dir data/corpus_1 --output-dir data/corpus_1/processed
```

### Generating Corpus Statistics

```bash
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli stats --corpus-dir data/corpus_1
```

---

## Anna's Archive Integration

- Anna's Archive collectors and helpers are now fully integrated and can be accessed via the CLI.
- Cookie-based authentication is supported for advanced download capabilities.
- See the `sources/specific_collectors/` directory for implementation details.

---

## Development Notes and Best Practices

- **Modular Imports:**  
  Use absolute imports (e.g., `from CryptoFinanceCorpusBuilder.processors.text_extractor import TextExtractor`) for clarity and maintainability.

- **Path References:**  
  Use `Path` objects and reference files relative to the module directory for portability:
  ```python
  from pathlib import Path
  MODULE_DIR = Path(__file__).parent
  CONFIG_DIR = MODULE_DIR / "../config"
  ```

- **Testing:**  
  Test each component after any structural change. Use the CLI to verify all commands work as expected.

- **Extending the Framework:**  
  To add a new data source, create a new collector in `sources/specific_collectors/` and register it in the CLI.

- **Configuration:**  
  All configuration files should be placed in `config/`. Update paths in your scripts accordingly.

- **Documentation:**  
  Keep this README and any module-specific READMEs up to date as you add features or change the structure.

---

## Troubleshooting

- **Symlinks:**  
  If your system does not support symlinks, use the provided `command_interface.py` copy for legacy compatibility.
- **Environment Variables:**  
  For Anna's Archive, ensure your `.env` file contains the necessary API keys or cookies.

---

## Contributing

- Please follow the modular structure and add new features as submodules or collectors.
- Write tests for new collectors or processors and place them in `tests/`.

---

If you have any questions or need further guidance, please refer to the code comments, docstrings, or open an issue in your project tracker. 