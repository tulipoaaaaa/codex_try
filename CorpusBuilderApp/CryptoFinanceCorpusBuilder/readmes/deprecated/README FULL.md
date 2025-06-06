# ai_trading_dev

## Benchmarking Mistral-7B v0.1 and v4b LoRA Adapter (v4b)

To benchmark both the vanilla base model and the v4b LoRA-augmented model, use the following command:

```sh
python scripts/bench_infer.py --models mistralai/Mistral-7B-v0.1 mistral7b_v01_lora_v4b --dtypes fp16 int8 --out reports/bench_gpu_0506.csv
```

- `mistralai/Mistral-7B-v0.1` benchmarks the vanilla base model.
- `mistral7b_v01_lora_v4b` benchmarks the base model with the v4b LoRA adapter attached (from Hugging Face repo `FernanMartin/AITradinc`, revision `937ed80`).

**Special logic:**
- For the LoRA model in int8 mode, the script loads the base model with 8-bit quantization (using `BitsAndBytesConfig(load_in_8bit=True)`) and then attaches the LoRA adapter. For fp16/bf16, it uses the floating point dtype as usual.
- No need to set `LORA_ADAPTER` for this workflow; the adapter is loaded directly from Hugging Face.

**Output:**
- Results are saved to the specified CSV file, with clear line-items for both the base and LoRA-augmented models in both fp16 and int8 modes.

This ensures reproducible, apples-to-apples benchmarking for both model variants.

# AI Trading LLM Inference Wrappers

## Canonical Single-Prompt Wrapper

The canonical script for single-prompt inference is now:

```
lora_training/smoke_tests/lora_single_prompt_wrapper_v4b2.py
```

### Usage Example

```bash
python lora_training/smoke_tests/lora_single_prompt_wrapper_v4b2.py \
  --prompt "### QUESTION:\nDefine gamma exposure.\n### ANSWER:" \
  --max_new_tokens 80 --rag --no_sample --explain --explain_tokens 60
```

### Key CLI Flags
- `--prompt` (required): The prompt/question to answer.
- `--max_new_tokens`: Max tokens to generate for the answer.
- `--rag`: Enable RAG context retrieval.
- `--no_sample` / `--do_sample`: Deterministic or sampling generation.
- `--explain`: Generate a model explanation for the answer.
- `--explain_tokens`: Max tokens for explanation.
- `--model_path`, `--adapter_path`: Override model/adapter.
- `--load_8bit`, `--load_4bit`: Quantization options.

### Output Schema
- `completion`: The model's answer.
- `confidence`: Confidence score (3 decimal places).
- `explanation`: Explanation (if requested).
- `rag_used`: Whether RAG was used.
- `top_sources`: List of RAG sources (empty if RAG not used).

---

## Canonical Batch Wrapper

The canonical script for batch inference is now:

```
lora_training/smoke_tests/lora_batch_query_wrapper_v4b.py
```

### Usage Example

```bash
python lora_training/smoke_tests/lora_batch_query_wrapper_v4b.py \
  --input path/to/prompts.jsonl \
  --out path/to/answers.jsonl \
  --max_new_tokens 80 --rag --no_sample --explain --explain_tokens 60 --batch_size 8 --stream --metrics_port 9101
```

- The input file should be a JSONL or CSV with a `prompt` field per line.
- The output is a JSONL file with one result per prompt, matching the schema below.

### Key CLI Flags
- `--input` (required): Path to JSONL or CSV file with prompts.
- `--out` (required): Output JSONL path.
- `--max_new_tokens`: Max tokens to generate per answer.
- `--batch_size`: Number of prompts per batch (default: 8).
- `--rag`: Enable RAG context retrieval.
- `--no_sample` / `--do_sample`: Deterministic or sampling generation.
- `--explain`: Generate a model explanation for each answer.
- `--explain_tokens`: Max tokens for explanation.
- `--model_path`, `--adapter_path`: Override model/adapter.
- `--load_8bit`, `--load_4bit`: Quantization options.
- `--stream`: Write each result as soon as it is produced.
- `--metrics_port`: Expose Prometheus metrics on this port (e.g., 9101).

### Output Schema
- `completion`: The model's answer.
- `confidence`: Confidence score (3 decimal places).
- `explanation`: Explanation (if requested).
- `rag_used`: Whether RAG was used.
- `top_sources`: List of RAG sources (empty if RAG not used).

---

## Legacy Scripts

The previous v4b script is now archived and should not be used for new development. See `lora_training/archived/` for legacy code.

# CryptoFinanceCorpusBuilder Modernization & Collector Integration

## Project Modernization Overview

This project has been refactored into a modular, pip-installable Python package with robust, testable, and isolated collector logic. The workflow and CLI are designed for safe, repeatable corpus building and testing.

### Key Modernization Steps
- **Modular Structure:** All code is organized into CLI, config, processors, sources/specific_collectors, storage, utils, and tests.
- **Verification Script:** `verify_setup.py` checks dependencies, config files, environment variables, and directories.
- **Robust CLI:** The CLI (`crypto_corpus_cli.py`) supports:
  - Collector-specific hardcoded logic, matching notebook cells for each collector.
  - Safe, testable output directories (e.g., `data/test_collect/<collector>`).
  - Collector-specific CLI flags for fine-grained control.
  - Absolute imports and proper `__init__.py` files for package recognition.
- **Config Management:** Config files are loaded robustly, with fallback to package-relative paths. Each collector must have a top-level entry in `config/enhanced_sources.json`.
- **No Shared Logic Changes:** Any bugfixes or special handling are hardcoded for the current collector only, never globally, to avoid side effects.

## Collector Integration Process

### General Rule
> **Any changes that affect all collectors (shared logic, processing, or error handling) should NOT be made globally. Instead, such changes should be hardcoded or scoped only for the specific collector as we integrate each one.**

### Step-by-Step Collector Integration
1. **Provide the notebook cell for the collector.**
2. **Hardcode the notebook logic into the CLI** for that collector only (inside the `collect_from_source` function, e.g., `if source_name == 'arxiv': ...`).
3. **Add collector-specific CLI flags** (e.g., `--arxiv-clear-output-dir`, `--github-repo-name`, `--bitmex-max-pages`).
4. **Print detailed, notebook-style output** for each collector, including file counts, sample content, and directory listings.
5. **Test in a safe, isolated output directory** (e.g., `data/test_collect/<collector>`).
6. **Update the config file** (`config/enhanced_sources.json`) to include a top-level entry for each collector you want to run.
7. **Never change shared modules or logic for all collectors** unless absolutely necessary; always scope changes to the collector block.

### Example CLI Usage

#### Arxiv Collector
```sh
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources arxiv --output-dir data/test_collect/arxiv --arxiv-clear-output-dir --arxiv-max-results 2 --arxiv-search-terms "crypto trading" "market microstructure" --arxiv-verbose
```

#### GitHub Collector
```sh
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources github --output-dir data/test_collect/github --github-clear-output-dir --github-repo-name freqtrade/freqtrade --github-keywords trading strategy
```

#### Quantopian Collector
```sh
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources quantopian --output-dir data/test_collect/quantopian --quantopian-clear-output-dir --quantopian-repo-name quantopian/research_public --quantopian-keywords volatility
```

#### BitMEX Collector
```sh
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources bitmex_research --output-dir data/test_collect/bitmex --bitmex-clear-output-dir --bitmex-max-pages 1 --bitmex-keywords bitcoin regulation
```

#### FRED Collector
```sh
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources fred --output-dir data/test_collect/fred --fred-clear-output-dir --fred-series-ids VIXCLS DTWEXBGS --fred-search-terms volatility --fred-max-results 2
```

#### ISDA Collector
```sh
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources isda --output-dir data/test_collect/isda --isda-clear-output-dir --isda-max-sources 5 --isda-keywords swap
```

## Collector-Specific Keyword/DOI/Title Search

- **BitMEX**: Supports keyword filtering via the `--bitmex-keywords` CLI flag. Only posts whose content contains at least one of the specified keywords will be processed and downloaded.
- **GitHub**: Supports keyword filtering via the `--github-keywords` CLI flag. Only files (README, notebooks, code, etc.) whose filename or content matches any keyword are shown in the output.
- **Quantopian**: Supports keyword filtering via the `--quantopian-keywords` CLI flag. Only notebooks whose title or content matches any keyword are processed and shown in the output.
- **ISDA**: Supports keyword filtering via the `--isda-keywords` CLI flag. Only PDFs whose link text or nearby HTML matches any keyword are downloaded and processed.
- **Other Collectors**: The same pattern will be extended to future collectors in a similarly isolated, per-collector manner. No shared logic will be changed.

### Example Usage

```sh
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources github --output-dir data/test_collect/github --github-clear-output-dir --github-repo-name freqtrade/freqtrade
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources quantopian --output-dir data/test_collect/quantopian --quantopian-clear-output-dir --quantopian-repo-name quantopian/research_public --quantopian-keywords volatility
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources isda --output-dir data/test_collect/isda --isda-clear-output-dir --isda-max-sources 5 --isda-keywords swap
```

- See the CLI help for other collector-specific keyword/title/DOI options.

## Keyword/DOI/Title-Driven Search: System Design & Status

### Project Goal Recap
- The system is designed to build a crypto-finance corpus by collecting documents (papers, repos, datasets, etc.) from various sources.
- The **selection of what to collect** (papers, repos, etc.) is driven by:
  - **Keywords** (e.g., "volatility", "portfolio optimization")
  - **DOIs** (for scientific papers)
  - **Titles** or other metadata
- These search terms are typically configured in JSON config files (e.g., `config/enhanced_sources.json`) or in supporting files referenced by the config.

### How This Is/Should Be Applied in Each Collector

#### Arxiv
- **Config:** `search_terms` and `categories` in the config file.
- **CLI:** Accepts `--arxiv-search-terms` and `--arxiv-max-results`.
- **Logic:** The hardcoded block in the CLI passes these search terms to the collector, which queries arXiv for matching papers.
- **Status:** **Fully functional.** You can control search terms via CLI or config.

#### GitHub
- **Config:** `repositories` and `topics` in the config file.
- **CLI:** Accepts `--github-repo-name` (for a single repo); could be extended to accept search terms or topics.
- **Logic:** Currently, the hardcoded block downloads a specific repo. The original collector logic could be extended to search by topic or keyword if needed.
- **Status:** **Functional for direct repo download.** Not yet generalized for keyword/topic search, but can be extended.

#### Quantopian
- **Config:** `repo_name` in the config file.
- **CLI:** Accepts `--quantopian-repo-name`.
- **Logic:** Downloads the specified repo; does not currently support keyword search within the repo, but could be extended to do so (e.g., search for notebooks with certain titles).
- **Status:** **Functional for direct repo download.** Not yet generalized for keyword/title search within the repo.

#### BitMEX
- **Config:** No explicit keyword config; could be extended.
- **CLI:** Now accepts `--bitmex-keywords` for keyword search in post content.
- **Logic:** Scrapes the latest research posts and prints which keywords are found in each post.
- **Status:** **Now supports keyword search in post content.**

#### FRED
- **Config:** `series_ids` and `search_terms` in the config file.
- **CLI:** Accepts `--fred-series-ids` and `--fred-search-terms`.
- **Logic:** Passes these to the collector, which queries the FRED API for matching series/data.
- **Status:** **Fully functional.** You can control search terms and series IDs via CLI or config.

#### ISDA
- **Config:** No explicit keyword config; the logic scrapes known documentation pages and looks for PDFs.
- **Logic:** The hardcoded block could be extended to filter or prioritize links by keyword/title if needed.
- **Status:** **Functional for broad scraping.** Not yet generalized for keyword/title/DOI search, but can be extended.

### General Pattern for Keyword/DOI/Title Search
- **Config files** (e.g., `enhanced_sources.json`) should include fields like `search_terms`, `dois`, `titles`, or similar for each collector.
- **CLI flags** should allow overriding or specifying these at runtime.
- **Collector logic** should:
  - Accept these parameters.
  - Use them to filter or drive the search/query process (e.g., only download papers/repos/posts that match).
- **For collectors that do not yet support this:**  
  - The hardcoded block should be extended to read these fields from the config/CLI and apply them during scraping or API calls.

### Current Status Table

| Collector   | Keyword/DOI/Title Search | Configurable? | CLI Override? | Status/Notes |
|-------------|-------------------------|---------------|--------------|-------------|
| arxiv       | Yes (search_terms)      | Yes           | Yes          | Fully functional |
| github      | Repo name only (now)    | Yes           | Yes          | Repo/topic search can be added |
| quantopian  | Repo name only (now)    | Yes           | Yes          | Can add notebook/title search |
| bitmex      | Yes (now, post content) | Yes           | Yes          | Now supports keyword search |
| fred        | Yes (series_ids, search_terms) | Yes   | Yes          | Fully functional |
| isda        | Not yet                 | No            | No           | Can add keyword/title filter |

### Recommendations / Next Steps
- **For arxiv and fred:** No action needed; already support keyword-driven search.
- **For github, quantopian, bitmex, isda:**  
  - Extend the hardcoded logic to accept and use `search_terms`, `titles`, or `dois` from config/CLI.
  - For example, in github/quantopian, filter repos/notebooks by title/keyword; in bitmex/isda, filter posts/PDFs by title/keyword.
- **Update config files** to include these fields for all collectors.
- **Document** the expected config structure and CLI flags for each collector.

### Summary
- **Your system is already functional for keyword/DOI/title-driven search for arxiv, fred, and now bitmex.**
- **Other collectors can be extended to support this by updating their hardcoded logic to use config/CLI search terms.**
- **This pattern is clear and easy to replicate for future collectors.**

---

This README provides enough context and detail for anyone to replicate the modernization and collector integration process, or to continue the work in a new environment or chat.

# Anna's Archive Collectors

## Main Library Collector

Supports both single and batch search/download using robust, authenticated logic.

### Single Book Download
```sh
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect_annas --query "Mastering Bitcoin Antonopoulos" --output-dir data/test_annas --client cookie
```
- `--query`: Book title or search string
- `--client`: Which Anna's Archive client to use (`simple`, `updated`, `cookie`, `enhanced`). Use `cookie` for authenticated, high-quality downloads.
- `--output-dir`: Test-safe output directory

### Batch Book Download
```sh
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect_annas --batch-json books.json --output-dir data/test_annas --client cookie
```
- `--batch-json`: Path to JSON file with a list of books/queries (see below for format)
- Each entry should have at least a `title` or `query` field, and optionally `domain`, `pdf_name`, `txt_name`.

#### Example `books.json`
```json
[
  {"title": "The Black Swan: The Impact of the Highly Improbable", "author": "Nassim Nicholas Taleb", "domain": "risk_management", "format": "pdf"},
  {"title": "Options, Futures, and Other Derivatives", "author": "John C. Hull", "domain": "crypto_derivatives", "format": "pdf"},
  {"title": "Market Microstructure Theory", "author": "Maureen O'Hara", "domain": "market_microstructure", "format": "pdf"}
]
```

## Anna's Archive SCIDB Collector

Download scientific papers by DOI, either singly or in batch, with robust error handling and test-safe output.

### Single DOI Download
```sh
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources annas_scidb_search --scidb-doi 10.1016/j.physa.2018.02.169 --output-dir data/test_collect/annas_scidb
```

### Batch DOI Download
```sh
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources annas_scidb_search --scidb-json-file dois.json --output-dir data/test_collect/annas_scidb
```
- `--scidb-json-file`: Path to a JSON file with a list of objects, each with a `doi` and optional `domain`.
- `--scidb-domain`: Default domain to use if not specified per entry.

#### Example `dois.json`
```json
[
  {"doi": "10.1111/prd.12104", "domain": "market_microstructure"},
  {"doi": "10.1016/j.physa.2018.02.169", "domain": "high_frequency_trading"}
]
```

## Test-Safe, Isolated Logic
- All collectors use test-safe output directories by default (e.g., `data/test_collect/<collector>` or `data/test_annas`).
- Each collector's logic is hardcoded and isolated; no shared logic is changed for new features.
- All new CLI flags are documented above and in `--help` output.

## Current State & Next Steps
- All major collectors (arxiv, github, quantopian, bitmex, fred, isda, annas_main_library, annas_scidb_search) are integrated and robust.
- Batch and single Anna's Archive support is fully functional.
- Next: Integrate a general web scraping collector (see `archives/data_scraper_scripts_legacy` for legacy logic). This can be done in a similarly isolated, test-safe way.

---

For more details, see the CLI help or the relevant section above. If you add a new collector, follow the same pattern: hardcode logic, use test-safe output, and document all new CLI flags and usage.

## Modular Collector Structure (2024+)

**As of the latest refactor, all collector logic is now fully modularized.**

- Each collector (ISDA, BitMEX, Anna's Archive, General Web Corpus, etc.) has its own file in `CryptoFinanceCorpusBuilder/cli/` (e.g., `collect_isda.py`, `collect_bitmex.py`, etc.).
- The main CLI (`crypto_corpus_cli.py`) only dispatches to these per-collector modules. No collector logic lives in the CLI itself.
- All logic, imports, config, and CLI flag parsing for each collector is self-contained in its own file.
- No shared logic or base classes are used for collectors. All changes are per-collector and isolated.
- To add a new collector, create a new `collect_<name>.py` file in `cli/` and add a dispatch in the CLI.
- The old collector classes in `sources/specific_collectors/` (e.g., `isda_collector.py`, `bitmex_collector.py`, `annas_archive_client.py`) are now legacy for those collectors and can be deleted or archived if not used elsewhere.

**Developer Workflow:**
- To add or update a collector, edit its `collect_<name>.py` file in `cli/`.
- To add a new collector, copy the pattern of an existing `collect_*.py` file, implement all logic locally, and add a dispatch in `crypto_corpus_cli.py`.
- Do not add shared logic or base classes for collectors. All logic must be per-collector.
- If you remove a collector, delete its `collect_*.py` file and remove its dispatch from the CLI.

**Example File Structure:**
```
CryptoFinanceCorpusBuilder/
  cli/
    crypto_corpus_cli.py
    collect_isda.py
    collect_bitmex.py
    collect_annas_main_library.py
    collect_annas_scidb_search.py
    collect_general_web_corpus.py
    ...
```

**Legacy/Obsolete Files:**
- Old collector classes in `sources/specific_collectors/` for ISDA, BitMEX, Anna's Archive, etc., are now legacy and can be deleted if not used elsewhere.
- Utility clients (e.g., `CookieAuthClient.py`, `enhanced_client.py`) are still used and should be kept.

**Testing:**
- CLI/integration tests should still work as before.
- If you have unit tests for old collector classes, update them to test the new `run_*_collector` functions.

# CryptoFinanceCorpusBuilder CLI (2024+ Modular Structure)

**Important:** All CLI commands and tests must be run in the `dedup_env` virtual environment for correct package resolution and dependency management.

## New CLI Command Structure

The CLI now uses subcommands for all major actions:
- `collect`: Collect data from one or more sources
- `process`: Process collected data (placeholder)
- `stats`: Show corpus statistics (placeholder)

### Example Usage

Activate your environment first:
```sh
.\.venv\Scripts\Activate  # or the dedup_env equivalent
```

#### Collect from one or more sources
```sh
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources arxiv --output-dir data/test_collect/arxiv --arxiv-clear-output-dir --arxiv-max-results 2
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources bitmex_research --output-dir data/test_collect/bitmex --bitmex-clear-output-dir --bitmex-max-pages 1 --bitmex-keywords bitcoin regulation
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources isda --output-dir data/test_collect/isda --isda-clear-output-dir --isda-max-sources 5 --isda-keywords swap
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources annas_main_library --output-dir data/test_collect/annas_main_library
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources annas_scidb_search --scidb-doi 10.1016/j.physa.2018.02.169 --output-dir data/test_collect/annas_scidb
```

#### Process collected data (placeholder)
```sh
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli process --input-dir data/test_collect/arxiv --output-dir data/test_processed
```

#### Show corpus statistics (placeholder)
```sh
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli stats --corpus-dir data/test_collect/arxiv
```

### CLI Help
```sh
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli --help
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --help
```

## Modular Collector Logic
- All collector logic is now in `CryptoFinanceCorpusBuilder/cli/collectors/` as `collect_<name>.py` files.
- The CLI only dispatches to these per-collector modules.
- No collector logic lives in the CLI itself.
- All logic, imports, config, and CLI flag parsing for each collector is self-contained in its own file.
- No shared logic or base classes are used for collectors. All changes are per-collector and isolated.

## Environment Note
- **Always activate the `dedup_env` (or `.venv`) before running any CLI or test commands.**
- All dependencies must be installed in this environment for the CLI and collectors to work.

## NOTE: Text Extraction & Monitoring

Currently, **text extraction from PDFs (to populate the `_extracted` folders for monitoring and downstream tasks) is NOT automated as part of the corpus collection workflow**. After collecting PDFs, you must run the extraction manually using the batch extraction script:

```sh
python CryptoFinanceCorpusBuilder/processors/batch_text_extractor.py
```

- By default, this script processes `data/corpus_1`. To use it with test folders, modify the `corpus_dir` variable at the top of the script to point to your test directory (e.g., `data/test_collect`).
- Only after extraction will the monitoring script (`monitor_progress.py`) report meaningful extracted file statistics.

**TODO:** Integrate automated text extraction into the corpus build pipeline in a future update.

---

# Pipeline Development Progress

## Current & Planned Stages

- **Data Collection**
  - Modular collectors for all major sources (arxiv, github, quantopian, bitmex, fred, isda, annas_main_library, annas_scidb_search)
  - Test-safe, isolated output directories
  - CLI and config-driven collection

- **Text Extraction**
  - Manual batch extraction using `batch_text_extractor.py` (see note below)
  - **TODO:** Automate extraction as part of the pipeline

- **Corpus Monitoring**
  - `monitor_progress.py` tracks file counts, sizes, and extraction status
  - Generates reports and time-series charts
  - **In Progress:**
    - File integrity checks (corrupted PDFs, empty/small text files)
    - Error logging in JSON (timestamp, error type, file path)
    - Extraction status dashboard (top-level metrics, filterable lists of problem files)
    - **NEW:** Status notifications at 25%, 50%, 75% milestones (console and log)
    - **NEW:** Error detection and recovery integration (logs ready for UI)
    - **NEW:** Main execution script now includes explicit batch numbers, real progress monitoring, disk space verification, and final TF/CN split validation.

- **Web UI (Planned)**
  - Simple dashboard for monitoring and corpus health
  - Will display top-level metrics, trends, and filterable lists of issues
  - Designed for easy integration with monitoring data
  - **Boss's UX Note:** The UX should prioritize monitoring dashboard visibility and simple corpus search functionality.

## Next Steps
1. Update main execution script (done)
2. Run small test of whole suite
3. Build UI
4. Run test with UI
5. Final peer review of strategy
6. LAUNCH (oh yeah baby!)
7. **After the new core is built, merge the old corpus with the new corpus. Investigate and implement deduplication strategies, such as blocking titles already present in the current corpus (using the existing list of titles), to ensure only new and unique content is added.**
   - The search strategy is already optimized to fill gaps based on the current corpus, so deduplication by title is a key part of the merging process.
8. **Consider adding a language tag to output metadata and/or integrating a language detection library (e.g., langdetect or fastText) for more robust filtering and compliance with English-content prioritization rules.**
9. **Implement a system-level QualityControlService (e.g., processors/quality_control.py) for centralized, domain-aware content quality checks. Load domain-specific keyword lists from config, support different evaluation strategies (keyword, language, readability), and set thresholds by domain/source. Update all collectors to use this centralized quality control step, passing document context (domain, source) for consistent, balanced corpus building (e.g., 60/40 crypto/traditional finance split). This will ensure robust, adaptable quality control across the entire pipeline before UI development.**

   - *Rationale:* During testing, we encountered an error where the quality filter was too crypto-focused (e.g., requiring 'bitcoin', 'blockchain', etc.), causing high-quality traditional finance books (like 'The Black Swan') to be incorrectly flagged as low quality. This risks an unbalanced corpus and undermines the intended 60/40 crypto/traditional finance split. A domain-aware, system-level quality control service will ensure all domains are evaluated fairly and consistently, preventing false negatives and supporting robust, balanced corpus growth.

---

## Environment & Setup Notes

- The monitoring suite requires the following Python packages:
  - `pandas`
  - `PyPDF2`
- These are now checked by `verify_setup.py`. If missing, install with:
  ```sh
  pip install pandas PyPDF2
  ```
- Always run `python verify_setup.py` after pulling new code or before running monitoring scripts to ensure all dependencies are present.

---

# Monitoring Suite Achievements & Test Log

## Summary of Achievements
- **Automated Corpus Monitoring:**
  - Tracks file counts, sizes, and extraction status per domain.
  - Detects and auto-deletes corrupted PDFs, logging them for re-download.
  - Detects empty or suspiciously small extracted text files.
  - Maintains a JSON error log with timestamps, error types, and file paths.
  - Maintains a redownload queue for problematic files.
  - Generates a dashboard with per-domain and overall analytics (percentages of corrupted, missing, empty, and failed files).
  - Produces human-readable reports and time-series charts for corpus growth and health.
  - **NEW:** Logs status notifications at 25%, 50%, and 75% milestones (console and status_log.json).
  - **NEW:** Periodically checks error logs and redownload queue for recovery integration (UI-ready logs).
  - **NEW:** Main execution script now features explicit batch numbers, real progress monitoring, disk space verification, and final TF/CN split validation.
- **Robust Analytics:**
  - Calculates and logs percentages for corrupted PDFs, empty/small text files, missing extractions, failed downloads, and successful extractions.
  - Dashboard and analytics are ready for future web UI integration.

## Test Log
- **End-to-End Test Workflow Completed:**
  - Created a test domain with:
    - A valid PDF
    - A corrupted PDF (text file with .pdf extension)
    - An empty .txt file in the extracted folder
  - Ran the monitoring suite, which:
    - Detected and auto-deleted the corrupted PDF
    - Logged the corrupted PDF and empty .txt file in the error log
    - Added the corrupted PDF to the redownload queue
    - Generated a dashboard with correct analytics (50% corrupted, 100% empty, 50% missing extractions, 0% successful extractions)
    - Produced a human-readable report and time-series charts
- **All outputs verified and correct.**

**Ready for review and next steps.**

---

## Web UI (Planned)

### Vision
A modern, responsive web dashboard that provides real-time visibility into corpus health, error recovery, and search—empowering both technical and non-technical users.

### Core Features
1. **Monitoring Dashboard (Landing Page)**
   - Live corpus health overview (totals, rates, progress bars, milestone notifications)
   - Error & recovery feed (filterable)
   - Trends & charts (time-series, domain breakdowns)
2. **Corpus Search & Exploration**
   - Simple and advanced search/filtering
   - File details, download, and re-extraction/re-download triggers
3. **Error Management & Recovery**
   - Redownload queue management
   - Error resolution tracking
4. **Notifications & Milestones**
   - Visual/log milestone alerts (25%, 50%, 75%, 100%)
   - Custom error/missing extraction alerts
5. **Admin & Audit Tools**
   - Test/simulation controls
   - Audit log/history

### Tech Stack Recommendation
- **Backend:** FastAPI or Flask (serving monitoring/search endpoints)
- **Frontend:** React (Material UI or Ant Design)
- **Visualization:** Chart.js, Plotly, or ECharts
- **Authentication:** Optional simple login for admin
- **Deployment:** Dockerized or run from venv

### UX Priorities
- Dashboard visibility first
- Simple, powerful search
- Actionable insights (errors/recovery)
- Responsive and accessible

### Integration Plan
- **Phase 1:** Read/display monitoring outputs (JSON, CSV, charts)
- **Phase 2:** Add search/filtering/file details
- **Phase 3:** Error management/recovery actions
- **Phase 4:** Notifications/milestone tracking/admin tools
- **Phase 5:** Continuous feedback/iteration

### Boss's UX Note
> The UX should prioritize monitoring dashboard visibility and simple corpus search functionality.

### How to Run and Access the UI
- The UI will run from your Python virtual environment (`dedup_venv`) for backend and (optionally) Node.js for frontend.
- **To start the UI:**
  - For a Python backend: `python -m ui_app` or similar (from the venv)
  - For a React frontend: `npm start` (from the `ui/` directory)
- **Access the UI in your browser:**
  - Go to `http://localhost:8000` (or the port specified by the app)
- **To create a desktop shortcut (Windows):**
  1. Right-click on your desktop, choose "New > Shortcut"
  2. Enter the URL (e.g., `http://localhost:8000`) as the location
  3. Name the shortcut (e.g., "Corpus Monitoring UI")
  4. This shortcut will open the UI in your default browser and does NOT need to be inside the venv
- The backend and frontend should be running for the UI to be accessible.

---

# Deduplication Cache & Duplicate Download Avoidance

## Purpose
To prevent re-downloading files that are already present in the main corpus or have already been downloaded in the current pipeline run, the system uses a **deduplication title cache**. This ensures:
- No duplicate downloads versus the main corpus (corpus_1)
- No duplicate downloads within a new batch (new titles are only downloaded once)

## How It Works
- **Title Cache Generation:**
  - A script (`scripts/extract_title_cache.py`) extracts and normalizes all titles (from the `id` column) in `data/corpus_1/corpus_all.csv`.
  - Normalization: lowercase, remove punctuation, trim whitespace.
  - The cache is saved as `data/title_cache_<YYYYMMDD>.txt` (one normalized title per line).
- **Usage in Collectors:**
  - Collectors (e.g., Anna's Archive) accept an `--existing-titles` argument pointing to the cache file.
  - Before downloading, each candidate title is normalized and checked against the cache.
  - If a match is found, the download is skipped and logged as a duplicate.
  - Within a batch, newly downloaded titles are also tracked to avoid intra-batch duplicates.

## Regenerating the Title Cache
To update the deduplication cache (e.g., after adding new files to the main corpus):
```sh
python scripts/extract_title_cache.py
```
This will create a new cache file in `data/` with the current date.

## Example Collector Usage
```sh
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect_annas --batch-json books.json --output-dir data/test_annas --client cookie --existing-titles data/title_cache_20250510.txt
```

## Summary of Deduplication Logic
- **Versus Main Corpus:**
  - All new downloads are checked against the normalized title cache from `corpus_1`.
- **Within New Downloads:**
  - Each collector tracks titles downloaded in the current run and skips any duplicates.
- **Result:**
  - No file is downloaded more than once, either compared to the main corpus or within a new batch.

## File Locations
- **Title cache:** `data/title_cache_<YYYYMMDD>.txt`
- **Main corpus:** `data/corpus_1/corpus_all.csv`
- **Extraction script:** `scripts/extract_title_cache.py`
- **Collector logic:** `CryptoFinanceCorpusBuilder/cli/collectors/collect_annas_main_library.py` (and similar for other collectors)

---

# Deduplication Normalization Consistency & Debugging

## Normalization Function (MUST MATCH EXACTLY)

All deduplication logic (cache creation and collectors) must use this function:

```python
def normalize_title(title):
    import re
    return re.sub(r'[^\w\s]', '', str(title).lower()).strip()
```

- Do **not** modify or reimplement this function elsewhere.
- Copy-paste it exactly into every collector and the cache script.

## Debugging Deduplication

If deduplication is not working:
- Add these debug lines before the deduplication check in your collector:
  ```python
  print(f"DEBUG: Normalized title: '{normalize_title(title)}'")
  print(f"DEBUG: First 5 cache entries: {list(titles_cache)[:5]}")
  print(f"DEBUG: Cache size: {len(titles_cache)}")
  ```
- Manually compare the normalized title to the cache entries.
- Ensure all file reads/writes use `encoding='utf-8'` and strip whitespace.

## Unicode-Safe Debug Printing (Windows & Cross-Platform)

On Windows and some other platforms, printing Unicode (e.g., Greek letters, math symbols) to the console can cause `UnicodeEncodeError` due to limited console encoding (like cp1252). To ensure debug output is always safe and readable:

- Use the following helper in any collector that prints debug info to the console:

```python
def ascii_safe(s):
    """Make string safe for console output on any platform."""
    return str(s).encode('ascii', errors='replace').decode('ascii')
```

- Print debug info using this helper:

```python
print(f"DEBUG: Normalized title: {ascii_safe(normalize_title(title))}")
print(f"DEBUG: First 5 cache entries: {[ascii_safe(x) for x in list(titles_cache)[:5]]}")
```

- For full Unicode debug info, also write to a log file:

```python
with open('dedup_debug.log', 'a', encoding='utf-8') as f:
    f.write(f"Collector: <name>, Title: {normalize_title(title)}\n")
    f.write(f"Cache entries: {list(titles_cache)[:5]}\n\n")
```

This ensures:
- Console output never crashes due to Unicode issues.
- All Unicode information is preserved for later analysis in the log file.
- No changes to core logic or collector independence are required.

**Always use this pattern for debug prints in collectors to guarantee cross-platform compatibility.**

---

# Universal Deduplication for High-Volume Collectors (arXiv, BitMEX, GitHub)

## Overview
As of May 2025, the deduplication title cache logic is now implemented for the three highest-volume collectors:
- **arXiv**
- **BitMEX**
- **GitHub**

Each collector now accepts an `--existing-titles` (or `existing_titles`) argument, loads and normalizes the cache, and skips downloads whose normalized title is present in the cache. This ensures robust, cross-collector duplicate avoidance.

## CLI Usage Example
```sh
# arXiv (example, adjust for your CLI wrapper)
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources arxiv --existing-titles data/title_cache_20250510.txt ...

# BitMEX
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources bitmex_research --existing-titles data/title_cache_20250510.txt ...

# GitHub
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources github --existing-titles data/title_cache_20250510.txt ...
```

## Title Normalization
- Lowercase
- Remove all punctuation
- Trim whitespace
- Unicode and special characters are handled consistently

## Testing & Validation Plan
1. **Test Collectors Separately First**
   - Run each collector individually with a small test cache and batch.
2. **Log Skipped Titles**
   - Temporarily enable logging of all skipped titles to verify correct filtering.
3. **Check Edge Cases**
   - Include titles with special characters, Unicode, and odd formatting in both cache and test data.
4. **Verify Error Handling**
   - Run collectors with missing or empty cache files to confirm graceful handling and clear messaging.
5. **Start Small**
   - Use a limited batch with known duplicates and unique items for initial validation.
6. **Full Pipeline Test**
   - Once individual collectors are validated, run the full pipeline with the same cache to ensure cross-collector consistency.

## Best Practices
- Always regenerate the title cache after major corpus updates.
- Review logs for skipped titles and false positives.
- Update CLI help text and documentation for all new parameters.
- Never change shared logic; all deduplication is per-collector.

## Next Steps
- Complete phased testing as described above.
- Monitor for any issues or regressions.
- If further collectors are added, follow the same deduplication pattern.

---

# NOTE: Test Output Directories

**Important:** All deduplication and pipeline tests should use test output directories (e.g., `data/test_collect/arxiv`, `data/test_collect/bitmex`, `data/test_collect/github`).

- **Do not use or overwrite the main corpus directories during testing.**
- When you are ready to deploy or run the full production pipeline, update all `--output-dir` arguments to point to the real corpus locations (e.g., `data/corpus_1/`).
- This ensures your main corpus remains clean and only contains validated, deduplicated data.
- **Always run a full end-to-end test with a sample of your final search in a test directory before switching to production output directories.**

Add this note to the deduplication and testing sections for clarity.

---


## Deduplication System Validation & Production Readiness

The deduplication system was thoroughly validated against 11 distinct edge cases, including:
- Unicode and special characters
- Whitespace variations
- Case sensitivity
- Punctuation and special formatting
- Abbreviations and near-matches

**Results:**
- Zero false positives or negatives were observed in testing.
- All normalization and cache logic performed as expected.

**Recommendation:**
- The deduplication system is robust and ready for real-world, production use.
- Future edge cases can be added to the test suite as needed for ongoing validation.

---

# Handling Non-PDF Data in the Corpus Pipeline

The corpus includes not only PDFs but also code, HTML, markdown, and structured data files. To ensure all data is usable for downstream training and analytics, the following extraction and normalization strategies will be applied:

1. **Code files (.py, .ipynb):**
   - Extract both code and comments/docstrings, preserving important context.
2. **HTML files:**
   - Use BeautifulSoup to extract main content, filtering out navigation, ads, and boilerplate.
3. **Markdown (.md):**
   - Convert to plain text while preserving structure (e.g., headings, lists).
4. **JSON/CSV:**
   - Convert to a readable text format that maintains relationships between data points.

A dedicated pipeline step will normalize all extracted text into a consistent format, similar to PDF extractions, so that downstream processes have uniform input regardless of original file type.

**Note:**
- This approach ensures all data types are handled appropriately and consistently for model training and analytics.
- Implementation of these extraction strategies is planned for the next pipeline phase.

---

### Extraction Quality Control (Planned)

The extraction pipeline will implement the following quality control measures:

- **Minimum Content Thresholds:**
  - Enforce a 100-token minimum for extracted text.
  - Flag (not discard) PDFs with <500 tokens for manual review, moving them to a low-quality directory.

- **Language & Content Detection:**
  - Add language detection using langdetect or fastText.
  - Keep non-English content that contains unique, high-quality information (notably CN or DE crypto research papers).
  - Target 85-90% English content overall to maintain training signal quality.
  - Add a language tag to metadata for all documents.

- **Duplicate Detection:**
  - Implement early-stage duplicate detection using hash functions on extracted text.
  - For near-duplicates, use MinHash/LSH with an 80% similarity threshold.
  - Tag potential duplicates in metadata rather than removing automatically.

- **Additional Quality Measures:**
  - Check text for corruption markers (random character sequences, encoding issues).
  - Measure crypto-finance relevance using domain-specific keyword density.
  - Add a quality score (0-100) to metadata based on content length, language clarity, and domain relevance.
  - Flag machine-translated content, which often has lower quality signal.

This approach preserves valuable non-English resources while preventing excessive token budget allocation to non-core materials. All flagged or low-quality files will be available for manual review and future curation.

---

# Anna's Archive Batch Collector Test Results

- The batch collector was tested with a books.json containing three titles.
- The pipeline correctly processed only those books, applied deduplication, and performed quality checks on each download.
- High-quality PDFs were saved for books that passed the quality check.
- Note: The current quality logic is crypto-focused (looks for crypto keywords in extracted text). For non-crypto books, this logic may need to be broadened to avoid false negatives.

---

# PDF vs Non-PDF Extraction Alignment Plan

To ensure consistent quality and domain balance across all corpus content, the non-PDF extraction pipeline will be incrementally enhanced to match the PDF extraction pipeline's quality standards.

## Current Feature Gap
- The initial non-PDF extractor covers core extraction and quality flagging, but lacks advanced features present in the PDF pipeline (domain relevance scoring, chunking, duplicate detection, advanced quality metrics).

## Priority Enhancements
1. **Domain relevance scoring** (highest priority):
   - Maintains the 60/40 crypto/traditional split and filters for domain-relevant content.
   - Will use domain-specific keyword density or weighted match, with a relevance score added to metadata.
2. **Chunking for large files:**
   - Enables robust processing of large codebases and datasets without memory issues.
   - Will split large files into semantically meaningful chunks for extraction and quality control.
3. **Duplicate detection:**
   - Removes redundant content common in code/data repositories.
   - Will use hash-based and (optionally) MinHash/LSH for near-duplicate detection.

## Implementation Plan
- **Step 1:** Test the current implementation for basic extraction and quality flagging.
- **Step 2:** Add domain-aware scoring immediately after validation.
- **Step 3:** Implement chunking for large files.
- **Step 4:** Add duplicate detection.
- **Step 5:** Iterate and refine until full feature parity with PDF extraction is achieved.

**Goal:**
- Achieve full alignment and consistent, high-quality, domain-balanced extraction for all file types in the corpus.

---

**Dependencies:**
- `markdown`
- `nbformat`
- `langdetect`
- `beautifulsoup4`
- `pandas`

Run `python verify_setup.py` to check for all required packages before running the extractor.

---

## Non-PDF Extraction Pipeline Dependencies

To use the non-PDF extraction pipeline (e.g., `batch_nonpdf_extractor.py`), you must install the following Python dependencies:

- nltk (for stemming)
- pandas
- nbformat
- beautifulsoup4
- markdown
- langdetect

Install all dependencies:

```bash
pip install nltk pandas nbformat beautifulsoup4 markdown langdetect
```

You must also download the NLTK punkt data (only once):

```bash
python -c "import nltk; nltk.download('punkt')"
```

## Non-PDF Extraction Pipeline: Overview, Usage, and Progress

### Overview
This module provides a robust, modular pipeline for extracting and normalizing text from non-PDF data types in the corpus, including:
- Python code (`.py`)
- Jupyter notebooks (`.ipynb`)
- Markdown (`.md`)
- HTML (`.html`, `.htm`)
- JSON (`.json`)
- CSV (`.csv`)

It is designed to match the quality and metadata standards of the PDF extraction pipeline, with additional features for domain relevance, language detection, and quality control.

### Key Features
- **Automatic file type detection and extraction logic** for all supported formats
- **Normalization** of extracted text for downstream analytics and model training
- **Quality control:**
  - Language detection
  - Token thresholds (minimum and low-quality flags)
  - Domain relevance scoring (with CLI control)
  - Duplicate/irrelevant flagging
- **Domain relevance scoring:**
  - Uses domain-specific keyword lists (from config or fallback)
  - Weights multi-word phrases higher than single words
  - Applies basic stemming (e.g., "trade", "trading", "trader" all match)
  - Tracks and outputs which specific keywords matched (for debugging/analysis)
- **Metadata enrichment:**
  - Includes language, quality flag, domain, relevance score, relevance flag, and matched keywords
- **Output structure:**
  - Extracted files and metadata are saved in `_extracted` or `low_quality` subfolders under the specified output directory

### How to Run
From the project root, run:

```bash
python -m CryptoFinanceCorpusBuilder.processors.batch_nonpdf_extractor \
  --input-dir data/test_collect/bitmex/bitmex_research \
  --output-dir data/test_collect/bitmex/bitmex_research_outputs \
  --domain market_microstructure \
  --relevance-threshold 30
```

- Adjust `--input-dir` and `--output-dir` as needed.
- Set `--domain` to the appropriate domain for your test set (e.g., `market_microstructure`, `risk_management`, etc.).
- The output will be organized into `_extracted` and `low_quality` subfolders.

### Adding/Testing Files
- Place real or synthetic test files of any supported type in your input directory.
- To test with traditional finance content, copy relevant files (e.g., from `data/corpus_1/market_microstructure_extracted/`) into your test directory.
- For Jupyter notebooks, ensure the file is valid JSON; empty or corrupt notebooks will be skipped with a warning.

### Error Handling & Troubleshooting
- The pipeline now gracefully skips invalid or empty `.ipynb` files and prints a warning.
- If you see a `ModuleNotFoundError` for `nltk` or other dependencies, run `python verify_install.py` and follow the install instructions.
- If you encounter a `DeprecationWarning` for `datetime.utcnow()`, it is safe to ignore for now; future updates will use timezone-aware datetimes.

### Recent Progress & Enhancements
- Added robust domain relevance scoring with phrase weighting, stemming, and matched keyword tracking
- Improved error handling for invalid/corrupt Jupyter notebooks
- Added real traditional finance test files and a valid notebook for comprehensive testing
- Updated README and added a dependency verification script (`verify_install.py`)
- All outputs now include detailed metadata for downstream analysis and debugging

### Output Interpretation
- Extracted text and metadata are saved in the output directory under `_extracted` (high quality) or `low_quality` (flagged/low relevance)
- Each output `.json` file contains fields such as `language`, `quality_flag`, `domain`, `relevance_score`, `relevance_flag`, and `matched_keywords`
- Use these fields to filter, audit, or further process your corpus

### Next Steps
- Continue adding real test files for all supported formats and domains
- Further refine quality control and domain scoring as needed
- Integrate with the main corpus pipeline and monitoring tools

For any issues, check the warnings in the console, review the output metadata, and use `python verify_install.py` to ensure your environment is set up correctly.

## Current Status & Next Steps (Non-PDF Extraction Pipeline)

### Current Status
- Robust, modular extraction and normalization for all supported non-PDF file types (code, markdown, HTML, JSON, CSV, notebooks)
- Quality control: language detection, token thresholds, domain relevance scoring, and detailed metadata
- Production-safe: gracefully handles empty/corrupt files, logs warnings, and never crashes on bad input
- All outputs include rich metadata for downstream analytics and monitoring

### Next Steps (in order of priority)

1. **Chunking for Large Files**
   - Add intelligent chunking for files exceeding a configurable token threshold (e.g., 10,000 tokens)
   - **Implementation priority:**
     - Start with Jupyter notebooks (highest priority due to size/frequency)
     - Then Python files (common in repos)
     - Then JSON/CSV (important for data files)
   - Preserve semantic boundaries (e.g., notebook cells, function/class boundaries, row/object boundaries)
   - Maintain linkage between chunks in metadata (chunk index, total chunks, parent file reference)
   - **Each chunk will include a content summary in metadata** (for search/filtering)
   - **Each chunk will maintain minimum context** (e.g., import statements for Python)
   - Fallback strategy ensures all files can be processed

2. **Duplicate Detection**
   - Implement hash-based exact duplicate detection
   - Add MinHash/LSH for near-duplicate detection (80% similarity threshold)
   - Store duplicate/near-duplicate information in metadata for each chunk/file

3. **Quality Improvements**
   - Add corruption detection (e.g., random character sequences, encoding issues)
   - Implement machine translation detection
   - Enhance language detection with confidence thresholds and fallback logic

4. **Integration with Main Pipeline**
   - Connect the non-PDF extractor to the main corpus pipeline
   - Ensure consistent metadata and file structure across PDF and non-PDF extractions
   - Add aggregated statistics for corpus balance monitoring (e.g., crypto/tradfi split, language, quality flags)

**Chunking is the immediate priority** as it addresses operational needs for large files. Duplicate detection will follow to maintain corpus quality, then quality improvements and full integration.

> **Boss's Note:** Consider a future enhancement to PDF extraction that uses section detection (headings/chapters), but keep this as a lower priority for now.

---

## Output Directory Structure: PDF and Non-PDF Extraction

To ensure consistency, traceability, and high corpus quality, both PDF and non-PDF extractions should follow a unified, domain/source-based directory structure, with clear separation of high-quality and low-quality outputs, chunked files, and metadata.

### Directory Layout

```
corpus_root/
│
├── <domain_or_source>/                # e.g., crypto_derivatives, github, arxiv, etc.
│   ├── _extracted/                    # High-quality extracted and chunked text and metadata
│   │   ├── <original_file>.txt        # Full extracted text (single chunk)
│   │   ├── <original_file>.json       # Metadata for full file
│   │   ├── <original_file>.chunk0.txt # Chunked text (if chunking applied)
│   │   ├── <original_file>.chunk0.json# Metadata for chunk 0
│   │   ├── <original_file>.chunk1.txt # Chunked text (if chunking applied)
│   │   ├── <original_file>.chunk1.json# Metadata for chunk 1
│   │   └── ...
│   └── low_quality/                   # Low-quality or flagged outputs (short, low relevance, etc.)
│       ├── <original_file>.txt
│       ├── <original_file>.json
│       └── ...
│
├── logs/                              # (Optional) Extraction logs, error reports, etc.
```

### PDF Extraction Specifics

- PDFs are processed into text and chunked at logical boundaries (e.g., by page, section, or paragraph, depending on the pipeline).
- Each PDF file produces:
  - `<original_file>.txt` — Full extracted text (if not chunked)
  - `<original_file>.chunkN.txt` — Chunked text (if chunking applied, e.g., by page or section)
  - Corresponding `.json` metadata for each `.txt` or chunk, including:
    - Source file path, extraction date, language, quality flag, token count, domain, relevance score, chunk index, number of chunks, and any PDF-specific metadata (e.g., page numbers, OCR confidence, etc.)
- Low-quality PDFs (e.g., too short, low relevance, corrupt, or failed OCR) are saved in the `low_quality/` subfolder with the same naming convention.

### Example

```
corpus_root/
├── crypto_derivatives/
│   ├── _extracted/
│   │   ├── report1.pdf.chunk0.txt
│   │   ├── report1.pdf.chunk0.json
│   │   ├── report1.pdf.chunk1.txt
│   │   ├── report1.pdf.chunk1.json
│   │   └── ...
│   └── low_quality/
│       ├── badscan.pdf.txt
│       ├── badscan.pdf.json
│       └── ...
├── github/
│   ├── _extracted/
│   │   ├── repo_README.md.txt
│   │   ├── repo_README.md.json
│   │   └── ...
│   └── low_quality/
│       └── ...
└── logs/
    └── extraction_2025-05-10.log
```

### Best Practices

- Consistent chunking and metadata: Use the same chunking and metadata standards for both PDF and non-PDF files.
- Domain/source separation: Keep all files organized by domain or source for easy filtering and downstream processing.
- Traceability: Always include the original file path and extraction date in metadata.
- Quality control: Use the `low_quality/` subfolder for any file or chunk that does not meet quality/relevance thresholds.

---

This structure ensures:
- Seamless integration of PDF and non-PDF data
- Consistent, high-quality corpus organization
- Easy extension for new domains, sources, or file types

# Enhanced Non-PDF Deduplication Workflow (2025+)

## Overview
The non-PDF deduplication workflow now includes advanced features for more granular tracking, reporting, and auditability, beyond what is currently implemented for PDF deduplication. These enhancements are modular and self-contained, and do not affect the working PDF pipeline.

## Key Features
- **Group-wise Deduplication Reporting:**
  - Each duplicate group is assigned a unique `duplicate_group_id` (e.g., `dg-001`).
  - The deduplication report includes detailed information for each group: type, kept file, duplicates, and per-group token loss.
- **Per-file Metadata Enrichment:**
  - Every file in a duplicate group has its `.json` metadata updated with:
    - `deduplicated`: true/false
    - `duplicate_group_id`: e.g., `dg-001`
    - `deduplication_date`: ISO timestamp
    - `kept_file`: true/false
    - `is_duplicate_of`: path to the kept file (if applicable)
    - `token_loss`: number of tokens lost if this file is a duplicate
- **Token Loss Calculation:**
  - Token loss is tracked both per group and for the entire corpus, supporting detailed corpus balance monitoring.
- **Deduplication Report Format:**
  - The report is compatible with the PDF deduplication summary, but includes additional fields:
    ```json
    {
      "deduplication_date": "2025-05-10T15:30:00",
      "strategy": "keep_first",
      "total_groups": 12,
      "total_duplicates": 35,
      "token_loss": 45628,
      "duplicate_groups": [
        {
          "group_id": "dg-001",
          "type": "exact_hash",
          "kept_file": "/path/to/kept/file.txt",
          "duplicates": ["/path/to/duplicate1.txt", "/path/to/duplicate2.txt"],
          "token_loss": 3240
        }
      ]
    }
    ```

## Compatibility and Future Alignment
- These enhancements are **not yet present in the PDF deduplication workflow**.
- The non-PDF deduplication report is compatible with the PDF system for summary statistics, but includes additional fields for advanced tracking.
- All enhancements are modular and self-contained, ensuring backward compatibility and no disruption to the PDF pipeline.
- Future alignment: Once the non-PDF implementation is proven, these features may be backported to the PDF deduplication system for full cross-pipeline consistency.

## Rationale
This staged approach delivers better functionality for non-PDF files without disrupting the working PDF pipeline. It allows for rapid iteration and validation of new features, with a clear migration path for future improvements to the PDF workflow.

# Next Steps: Quality, Integration, and Testing Improvements (Planned)

The following enhancements are the next priorities for the non-PDF and overall corpus pipeline. These features are not yet fully implemented, but will be developed, tested, and documented in sequence:

## 1. Quality Improvements
- **Corruption Detection:**
  - Goal: Flag files/chunks with random, non-linguistic, or corrupted content (e.g., excessive non-printable characters, repeated symbols, low word diversity).
  - Approach: Implement detection logic and add a `corruption_flag` or `corruption_score` to metadata. Move flagged files to `low_quality/` and log them.
- **Machine Translation Detection:**
  - Goal: Flag likely machine-translated text, which is often lower quality.
  - Approach: Use heuristics or a lightweight model to detect MT artifacts. Add a `machine_translated_flag` to metadata.
- **Enhanced Language Detection Confidence:**
  - Goal: Only accept language detection results above a confidence threshold.
  - Approach: Use a language detection library with confidence scores, add `language_confidence` to metadata, and flag/move files with low confidence.

## 2. Integration with Main Pipeline
- **Connect Non-PDF Extractor to Main Workflow:**
  - Goal: Make non-PDF extraction a first-class step in the main corpus build.
  - Approach: Add CLI/config hooks to run non-PDF extraction as part of the main pipeline, ensuring outputs go to correct domain/source folders.
- **Consistent File Structure and Metadata:**
  - Goal: Harmonize non-PDF and PDF outputs for downstream compatibility.
  - Approach: Review and align all metadata fields and directory structures, adjusting as needed for consistency.
- **Aggregated Statistics for Monitoring:**
  - Goal: Enable corpus health and balance monitoring.
  - Approach: Implement a script to aggregate and report total files, token counts, and breakdowns by domain, language, quality, etc.

## 3. Comprehensive Testing
- **Automated Test Suite for All File Types:**
  - Goal: Ensure extraction, chunking, and deduplication work for every supported type and edge case.
  - Approach: Write a test runner that asserts expected outputs, metadata, and flags for all test files.
- **Validation for Token Counts and Extraction Quality:**
  - Goal: Guarantee that token counts and quality flags are correct.
  - Approach: Add assertions in the test suite for token count ranges, quality/corruption/language flags, and consistency between text and metadata.
- **Corpus Balance Reports:**
  - Goal: Track and visualize corpus composition (domain, language, quality, etc.).
  - Approach: Extend the statistics script to output balance reports (e.g., CSV summaries, charts) for monitoring and dashboard integration.

These improvements will further enhance the robustness, quality, and auditability of the corpus pipeline, and ensure seamless integration and monitoring across all data types.

# PDF Pipeline Quality Improvements: Status and Future Alignment

Currently, advanced quality checks such as corruption detection, machine translation detection, and enhanced language detection confidence are **not yet implemented in the PDF extraction pipeline**. These features are being developed first for the non-PDF pipeline, with modular code and robust tests.

**Once validated, these quality modules will be backported to the PDF pipeline** to ensure consistent, high-quality standards across all document types. This staged approach allows for rapid iteration and reliability before full integration.

**Future Plan:**
- Integrate the new quality checks into the PDF pipeline after successful deployment in the non-PDF workflow.
- Maintain a unified, modular quality control system for both PDF and non-PDF data.

This ensures the entire corpus benefits from the latest quality improvements, with minimal duplication of effort and maximum maintainability.

# Enhanced Language Detection (2025+)

## Overview
The pipeline now includes advanced language confidence and mixed-language detection for all extracted text. This module:
- Uses probabilistic language detection to assign a confidence score to each chunk
- Segments text to detect mixed-language content and flags accordingly
- Adds the following fields to metadata:
  - `language_confidence`
  - `mixed_language_flag`
  - `mixed_languages`
  - `language_detection_reasons`
  - `language_detection_severity`
- Updates `quality_flag` to include `low_confidence` or `mixed_language` if detected
- CLI/config options: `--lang-confidence-threshold`, `--mixed-lang-ratio`

This feature is fully integrated into the non-PDF pipeline and will be backported to the PDF pipeline for consistent quality control.

# Machine Translation Detection (2025+)

## Overview
The pipeline now includes robust machine translation detection for all extracted text. This module:
- Uses high-precision heuristics: translation disclaimers, repeated n-grams, unnatural phrasing, functional/content word ratio, missing articles, verb tense patterns, rare word ratio
- Loads thresholds and patterns from a config file (see below)
- Adds the following fields to metadata:
  - `machine_translated_flag`
  - `machine_translation_score`
  - `machine_translation_reasons`
  - `machine_translation_severity`
- Updates `quality_flag` to include `machine_translated` if flagged
- Logs all flagged content for review
- CLI/config option: `--mt-config`

## Sample Config File
```json
{
  "disclaimer_patterns": [
    "translated by", "machine translation", "automatic translation",
    "originally written in", "this document was automatically translated",
    "translation provided by", "translated from", "google translate"
  ],
  "ngram_repetition_threshold": 4,
  "rare_word_ratio_threshold": 0.15,
  "functional_to_content_ratio": 0.7,
  "missing_article_threshold": 0.08,
  "unusual_verb_tense_threshold": 0.12,
  "domain_exclusions": ["blockchain", "cryptocurrency", "API", "function", "parameter"],
  "code_comment_thresholds": {
    "ngram_repetition": 6,
    "rare_word_ratio": 0.25
  }
}
```

## Heuristic Examples
- **Translation disclaimer:**
  - True positive: "This document was automatically translated."
  - False positive: "This document was written by a translator."
- **N-gram repetition:**
  - True positive: "In the same time, ... In the same time, ... In the same time, ..."
  - False positive: "In the same time zone, ... In the same time frame, ..."
- **Functional/content word ratio:**
  - True positive: "In the of the and the to the ..."
  - False positive: "The quick brown fox jumps over the lazy dog."
- **Missing articles:**
  - True positive: "Cat sat on mat. Dog ran fast."
  - False positive: "The cat sat on the mat. The dog ran fast."
- **Unusual verb tense:**
  - True positive: "He had finished. She was going. They are running."
  - False positive: "He finished. She goes. They run."
- **Rare word ratio:**
  - True positive: "The quixotic zephyr juxtaposed the xylophone."
  - False positive: "The cat sat on the mat."

## Tuning Guidelines
- Adjust thresholds in the config file to match your corpus and domain
- Use higher thresholds for code comments or technical documentation
- Review logs for false positives and adjust patterns as needed

This feature is fully integrated into the non-PDF pipeline and will be backported to the PDF pipeline for consistent quality control.

## Recent Enhancements: Machine Translation & Quality Control (Non-PDF Pipeline)

- **Modular Heuristic-Based Machine Translation Detector**: Added a robust, configurable detector for non-PDF files (Python, Jupyter, Markdown, HTML, JSON, CSV, etc.) using multiple heuristics:
  - Translation disclaimers
  - N-gram repetition
  - Functional/content word ratio
  - Missing articles
  - Unusual verb tense
  - Rare word ratio
  - Multi-language detection
- **Multi-Factor Logic**: Only flags as machine translated if a major trigger is present (e.g., disclaimer, n-gram, repeated phrase) or at least two minor heuristics are triggered. This reduces false positives and increases precision.
- **Confidence & Severity**: Outputs confidence and severity based on triggered heuristics and text length.
- **Comprehensive Test Suite**: All heuristics are covered with edge cases, minimum threshold checks, and multi-trigger scenarios. The test suite is aligned with the detector's logic and precision/recall trade-offs.
- **Verbose Output**: All triggered heuristics and reasons are included in the metadata for downstream analysis and debugging.
- **Integration Ready**: Detector is ready for batch processing, metadata enrichment, and downstream quality control.

### **Important: PDF Pipeline Alignment**
> These improvements have been implemented for the non-PDF pipeline. **They must be ported to the PDF extraction and quality control pipeline** to ensure consistency and maintain high standards across all document types.



### Phase 1: PDF Pipeline Enhancement
1. **Refactor PDF Extraction**
   - Modularize PDF extraction with a new `process_pdf_file` function
   - Support chunking by page/section with semantic boundaries
   - Output structure and metadata aligned with non-PDF pipeline
2. **Integrate Quality Control Modules**
   - Port language confidence, corruption, and machine translation detection
   - Apply all quality modules to PDF content and chunks
   - Add confidence thresholds and quality flags to metadata
3. **Update Output Structure and Metadata**
   - Store extracted text and metadata in `_extracted` and `low_quality` folders
   - Standardize metadata fields and chunking logic
4. **Align CLI/Config Options and Testing**
   - Add CLI/config parameters for thresholds and detection options
   - Create comprehensive test suite for PDF pipeline
   - Ensure integration with PDF deduplication and reporting

### Phase 2: Unified Extraction & Reporting System
5. **Create Unified Extractor Factory**
   - Build a factory class to select the appropriate extractor for any file type
   - Standardize quality metrics and metadata across all extractors
   - Update corpus manager to use the unified extractor
6. **Implement Domain Balance Analyzer**
   - Develop analyzer for domain balance tracking and visualization
   - Add CLI commands for running analysis and generating reports
7. **Develop Coverage Gap Analyzer**
   - Build system to identify domain coverage gaps and recommend collection priorities
   - Integrate with dynamic collection configuration
8. **Automated, Balance-Driven Collection**
   - Implement logic to adjust collection priorities based on real-time corpus statistics
   - Generate dynamic batch configs to target underrepresented domains
9. **Testing and Documentation**
   - Perform end-to-end testing with sample data
   - Update documentation and provide usage examples
10. **Continuous Monitoring and Optimization**
   - Run balance analysis after each batch
   - Refine extraction, quality, and reporting logic as needed
   - Set milestone targets and track progress toward 60/40 goal

## Immediate Next Steps
- Begin with Phase 1: Refactor PDF extraction and port quality control modules
- Once PDF pipeline is aligned, proceed to unified extraction and reporting system
- Use the new analyzers and dynamic configs to drive balanced, high-quality corpus growth

---

*For further details or to continue this work, see the hand-off prompt and implementation notes at the end of this README.*

---

## ⚠️ Important: Input/Output Paths for Extraction Scripts

When running the PDF or non-PDF extraction scripts in production or for testing, **ensure you set the input and output directory paths to the correct corpus or test folders**. 

- Some scripts may have hardcoded paths (e.g., `corpus_dir = Path("./data/test_collect")`).
- For production, update these to point to your actual corpus data directories.
- **Recommended:** Refactor scripts to accept `--input-dir` and `--output-dir` as CLI arguments for maximum flexibility (as in the non-PDF extractor).
- Always verify the paths before running large-scale extractions to avoid processing the wrong files or overwriting important data.

See script docstrings and CLI help (`--help`) for details.

- `PyMuPDF` (fitz) and `pdfminer.six` are now required for robust PDF extraction. The pipeline will automatically use these as fallbacks if PyPDF2 cannot extract text from a PDF. Install with:
  ```bash
  pip install pymupdf pdfminer.six
  ```
- These packages are essential for production-grade extraction from a wide variety of PDF types, including research papers, scanned documents (text-based), and legacy PDFs.
- `pytesseract` and `Pillow` are now required for OCR fallback in PDF extraction. Install with:
  ```bash
  pip install pytesseract Pillow
  ```
- **Tesseract OCR must also be installed on your system.**
  - On Ubuntu: `sudo apt-get install tesseract-ocr`
  - On Mac: `brew install tesseract`
  - On Windows: Download from https://github.com/tesseract-ocr/tesseract
- The extractor will automatically use OCR if all text-based extraction methods fail for a PDF page.

# Environment & End-to-End Setup (2025+)

## 1. Activate Your Virtual Environment
```powershell
.\.venv\Scripts\activate
# or
.\dedup_venv\Scripts\activate
```

## 2. Install All Dependencies
```bash
pip install -r requirements.txt
```

## 3. Ensure System Dependencies for PDF Extraction
- **Tesseract OCR** must be installed system-wide:
  - Windows: Download from https://github.com/tesseract-ocr/tesseract
  - Ubuntu: `sudo apt-get install tesseract-ocr`
  - Mac: `brew install tesseract`

## 4. Set PYTHONPATH for Robust Imports
Before running any tests or scripts that import from `CryptoFinanceCorpusBuilder`, set your PYTHONPATH to the project root:
```powershell
$env:PYTHONPATH="G:\ai_trading_dev"
```
*(or the equivalent for your OS/shell)*

## 5. Ensure All Folders Have `__init__.py`
Place an (even empty) `__init__.py` file in:
- `CryptoFinanceCorpusBuilder/`
- `CryptoFinanceCorpusBuilder/processors/`
- `CryptoFinanceCorpusBuilder/tests/`
- `CryptoFinanceCorpusBuilder/tests/pdf_extraction/`

## 6. Run All Tests End-to-End
```bash
pytest -s CryptoFinanceCorpusBuilder/tests/
```

---

# Quickstart (Summary)
1. Activate venv
2. Install requirements
3. Install Tesseract OCR
4. Set PYTHONPATH
5. Run tests or scripts

---

# Troubleshooting
- If you see `ModuleNotFoundError: No module named 'CryptoFinanceCorpusBuilder'`, ensure you have set PYTHONPATH and have `__init__.py` files in all package folders.
- For missing dependencies, re-run `pip install -r requirements.txt`.
- For PDF extraction errors, ensure Tesseract OCR is installed system-wide.

---

# (The rest of the README continues as before, with usage, CLI, and collector instructions...)

## Quality Control & Scientific Paper Handling

### Quality Control Service

The system now includes a centralized `QualityControlService` for consistent, domain-aware content quality checks:

```python
# processors/quality_control.py
class QualityControlService:
    def __init__(self, config=None):
        self.config = config or self._load_default_config()
        
    def check_quality(self, text, metadata):
        # Run all detectors
        # Aggregate flags
        # Return updated metadata
```

#### Key Features
- **Domain-Aware Thresholds**: Different quality thresholds for different domains
- **Scientific Paper Detection**: Special handling for academic papers
- **Configurable Parameters**: All thresholds and checks are configurable
- **Rich Metadata**: Comprehensive quality flags and scores

### Scientific Paper Handling

Scientific papers require special handling due to their unique characteristics:

```python
SCIENTIFIC_PAPER_THRESHOLDS = {
    'min_tokens': 50,  # Lower minimum for scientific papers
    'low_quality_tokens': 50,  # Much lower threshold for scientific papers
    'chunk_size': 10000,  # Keep chunk size the same
    'quality_relaxations': {
        'reference_density': 0.3,  # Allow up to 30% references
        'citation_density': 0.2,   # Allow up to 20% citations
        'formula_density': 0.4     # Allow up to 40% formulas
    }
}
```

#### Detection Logic
```python
def detect_scientific_paper(text, metadata):
    indicators = [
        'doi' in metadata.get('keywords', []),
        'references' in text.lower(),
        'abstract' in text.lower(),
        'introduction' in text.lower(),
        'conclusion' in text.lower(),
        'references' in text.lower(),
        'bibliography' in text.lower()
    ]
    return sum(indicators) >= 3  # If 3 or more indicators present
```

#### Quality Check Relaxations
- Skip reference/citation density checks for scientific papers
- Adjust token count thresholds based on paper type
- Consider formula density in quality assessment
- Relax language detection for technical content

### Default Quality Thresholds

```python
DEFAULT_THRESHOLDS = {
    'min_tokens': 100,
    'low_quality_tokens': 500,
    'chunk_size': 10000,
    'language_confidence': 0.8,
    'corruption': 0.3,
    'machine_translation': 0.7,
    'relevance': 30
}
```

### Domain-Specific Thresholds

Each domain can have its own quality thresholds:

```python
DOMAIN_THRESHOLDS = {
    'scientific_papers': SCIENTIFIC_PAPER_THRESHOLDS,
    'trading_strategies': {
        'min_tokens': 200,
        'low_quality_tokens': 1000,
        'chunk_size': 8000
    },
    'market_analysis': {
        'min_tokens': 150,
        'low_quality_tokens': 800,
        'chunk_size': 12000
    }
}
```

### Integration with Collectors

All collectors now use the centralized quality control service:

```python
def process_file(file_path, output_dir):
    # Extract text and basic metadata
    text, metadata = extract_content(file_path)
    
    # Detect document type
    is_scientific = detect_scientific_paper(text, metadata)
    
    # Get appropriate thresholds
    thresholds = SCIENTIFIC_PAPER_THRESHOLDS if is_scientific else DEFAULT_THRESHOLDS
    
    # Run quality checks
    quality_service = QualityControlService()
    quality_checks = quality_service.check_quality(text, metadata, thresholds)
    
    # Save with quality metadata
    save_with_metadata(text, metadata, quality_checks, output_dir)
```

### Quality Control Dashboard

The web UI includes a quality control dashboard showing:
- Quality metrics by domain
- Scientific paper detection statistics
- Threshold effectiveness analysis
- Quality flag distribution

# CryptoFinanceCorpusBuilder

## Test Structure

The project includes several test suites to ensure quality and reliability:

### Test Suites

1. `test_processors.py`
   - Tests text extraction from various file types (text, markdown, notebooks)
   - Tests domain classification functionality
   - Uses unittest framework
   - Most appropriate for testing the enhanced PDF extractor's text extraction and domain classification features

2. `test_collectors.py`
   - Tests API, web, and repository collectors
   - Tests specific collectors like ArxivCollector
   - Uses unittest framework with mocking
   - Useful for testing data collection pipeline

### Test Data

1. `integration_pdfs/`
   - Large collection of real-world PDFs
   - Used for integration testing
   - Contains various document types (papers, documentation, etc.)

2. `integration_pdfs_small/`
   - Smaller subset of PDFs for quick testing
   - Contains representative samples of different document types
   - Ideal for development and quick verification

## Short-term Timeline

1. PDF Extractor Enhancement (Current Focus)
   - [x] Implement enhanced text extraction with structured output
   - [x] Add table and formula extraction
   - [x] Integrate with quality control system
   - [x] Test with existing test suites
   - [x] Verify multiprocessing performance
   - [x] Document new features

2. Non-PDF Extractor Alignment
   - [x] Align non-PDF extractor with enhanced structure
   - [ ] Update unified extractor
   - [ ] Test with existing test suites
   - [ ] Document changes

3. Corpus Manager Updates
   - [ ] Update to handle enhanced output format
   - [ ] Add support for structured data
   - [ ] Test integration
   - [ ] Document changes

4. Quality Control Integration
   - [ ] Verify quality control integration
   - [ ] Test with real-world documents
   - [ ] Document quality metrics

5. Documentation and Testing
   - [ ] Update all documentation
   - [ ] Add more test cases to existing suites
   - [ ] Create integration tests
   - [ ] Document test coverage

## Running Tests

To run the test suites:

```bash
# Run all tests
python -m unittest discover CryptoFinanceCorpusBuilder/tests

# Run specific test suite
python -m unittest CryptoFinanceCorpusBuilder/tests/test_processors.py
python -m unittest CryptoFinanceCorpusBuilder/tests/test_collectors.py
```

## Test Data Requirements

When adding new test files:
1. Use existing test suites
2. Follow unittest framework
3. Use appropriate test data from integration_pdfs directories
4. Document test cases and expected behavior
5. Keep test files small and focused
```

# Test Structure & Coverage

## Test Suites Overview

The project includes several test suites organized by functionality and scope:

### 1. Core Test Suites (CryptoFinanceCorpusBuilder/tests/)
- **test_processors.py**
  - Tests text extraction from various file types (text, markdown, notebooks)
  - Tests domain classification functionality
  - Uses unittest framework
  - Includes comprehensive test cases for:
    - Text file extraction
    - Markdown file extraction
    - Jupyter notebook extraction
    - Domain classification with title weighting
    - Edge cases and error handling

- **test_collectors.py**
  - Tests API, web, and repository collectors
  - Tests specific collectors (e.g., ArxivCollector)
  - Uses unittest framework with mocking
  - Covers:
    - API collector initialization and requests
    - Web collector page fetching and parsing
    - Arxiv collector search and response parsing
    - Error handling and edge cases

### 2. Integration Tests (Root Directory)
- **test_monitoring_workflow.py**
  - Tests the corpus monitoring system
  - Creates test environment with:
    - Valid PDF
    - Corrupted PDF
    - Empty text file
  - Verifies monitoring script functionality
  - Tests error logging and reporting

- **test_functionality.py**
  - End-to-end tests of CLI functionality
  - Tests all major collectors:
    - Arxiv
    - ISDA
    - BitMEX
    - Anna's Archive (Main Library and SCIDB)
    - General Web Corpus
  - Verifies CLI commands and options
  - Tests output directory handling

### 3. Deduplication Tests (scripts/)
- **test_deduplication_collectors.py**
  - Tests deduplication logic across collectors
  - Covers edge cases:
    - Unicode and special characters
    - Whitespace variations
    - Case sensitivity
    - Punctuation and formatting
    - Abbreviations and variants
  - Tests integration with:
    - Arxiv collector
    - BitMEX collector
    - GitHub collector

### 4. Test Data
- **integration_pdfs/** (CryptoFinanceCorpusBuilder/tests/)
  - Large collection of real-world PDFs
  - Used for integration testing
  - Contains various document types

- **integration_pdfs_small/** (CryptoFinanceCorpusBuilder/tests/)
  - Smaller subset for quick testing
  - Representative samples of different types
  - Ideal for development and verification

### 5. Utility Tests
- **test_single_pdf_extract.py**
  - Quick test for PDF text extraction
  - Tests basic extractor functionality

- **test_selenium.py**
  - Tests web scraping capabilities
  - Verifies Selenium setup and configuration

## Running Tests

### Run All Tests
```bash
# Run all test suites
python -m unittest discover CryptoFinanceCorpusBuilder/tests

# Run specific test suite
python -m unittest CryptoFinanceCorpusBuilder/tests/test_processors.py
python -m unittest CryptoFinanceCorpusBuilder/tests/test_collectors.py
```

### Run Integration Tests
```bash
# Run monitoring workflow test
python test_monitoring_workflow.py

# Run functionality tests
python test_functionality.py

# Run deduplication tests
python scripts/test_deduplication_collectors.py
```

## Test Data Requirements

When adding new test files:
1. Use existing test suites where possible
2. Follow unittest framework conventions
3. Use appropriate test data from integration_pdfs directories
4. Document test cases and expected behavior
5. Keep test files small and focused
6. Include edge cases and error conditions
7. Use mocking for external dependencies

## Test Coverage Goals
- Unit tests for all core functionality
- Integration tests for collector workflows
- End-to-end tests for CLI operations
- Deduplication testing across collectors
- Error handling and edge cases
- Performance testing for large files
- Cross-platform compatibility

// ... existing code ...

## Extractor Alignment Plan (2024-05-25)

### Overview
This plan outlines the steps to align the PDF and non-PDF extractors while maintaining their specialized functionality. The goal is to create a unified, robust extraction system that handles all file types consistently while preserving type-specific features.

### 1. Common Interface
- Create a shared `BaseExtractor` class that both PDF and non-PDF extractors inherit from
- Standardize the extraction result format between both extractors
- Use the same quality metrics structure across both

### 2. Shared Utilities
- Move common functions (safe_filename, count_tokens, quality_flag) to a shared utils module
- Create a unified metadata extraction system
- Standardize the output directory structure

### 3. Quality Control
- Use the same corruption detection thresholds for both
- Apply consistent language detection rules
- Share the same domain classification logic
- Use identical quality flagging criteria

### 4. Processing Pipeline
- Implement the same chunking strategy for large files
- Use consistent timeout handling
- Share the same parallel processing approach
- Apply similar progress tracking

### 5. Output Format
- Standardize JSON metadata structure
- Use the same file naming conventions
- Implement consistent logging format
- Share the same error reporting structure

### Implementation Timeline
1. **Phase 1 (Week 1)**
   - Create BaseExtractor class
   - Move shared utilities
   - Standardize metadata format

2. **Phase 2 (Week 2)**
   - Align quality control systems
   - Implement shared processing pipeline
   - Standardize output formats

3. **Phase 3 (Week 3)**
   - Testing and validation
   - Performance optimization
   - Documentation updates

### Benefits
- Consistent quality control across all file types
- Unified error handling and reporting
- Shared utilities reduce code duplication
- Standardized output format simplifies downstream processing
- Better maintainability and extensibility

// ... existing code ...

## Extraction Pipeline (2024-05-25)

The CryptoFinanceCorpusBuilder implements a robust extraction pipeline that handles both PDF and non-PDF documents. The pipeline is designed with modularity, quality control, and extensibility in mind.

### Architecture Overview

1. **Base Extractor (`BaseExtractor`)**
   - Abstract base class that defines the common interface for all extractors
   - Handles file processing, quality control, and metadata management
   - Implements parallel processing with configurable worker count
   - Manages output organization and logging

2. **PDF Extractor (`PDFExtractor`)**
   - Inherits from `BaseExtractor`
   - Uses multiple extraction methods (PyPDF2, PyMuPDF, pdfminer) for robustness
   - Integrates specialized mixins for table and formula detection
   - Handles PDF-specific metadata and structure

3. **Non-PDF Extractor (`NonPDFExtractor`)**
   - Inherits from `BaseExtractor`
   - Supports various file formats (Markdown, HTML, JSON, etc.)
   - Implements format-specific extraction strategies
   - Maintains consistent output format with PDF extractor

### Quality Control System

1. **Configuration (`QualityConfig`)**
   - Pydantic models for type-safe configuration
   - Configurable thresholds for quality metrics
   - Domain-specific settings for crypto-finance content
   - Validation rules for output format

2. **Quality Metrics**
   - Token count and distribution
   - Sentence and paragraph structure
   - Language detection and confidence
   - Corruption detection
   - Domain classification

3. **Output Validation**
   - Required and optional fields
   - Schema validation
   - Format consistency checks
   - Metadata completeness

### Specialized Features

1. **Table Extraction (`TableMixin`)**
   - Uses Camelot for PDF table detection
   - Handles complex table structures
   - Configurable timeout and accuracy thresholds
   - Outputs structured table data

2. **Formula Detection (`FormulaMixin`)**
   - LaTeX formula detection using regex patterns
   - Supports multiple formula types
   - Validates formula structure
   - Preserves formula context

### Usage Example

```python
from CryptoFinanceCorpusBuilder.processors.pdf_extractor import PDFExtractor
from CryptoFinanceCorpusBuilder.models.quality_config import QualityConfig

# Initialize extractor
extractor = PDFExtractor(
    input_dir="path/to/pdfs",
    output_dir="path/to/output",
    quality_config="path/to/config.json"
)

# Run extraction
results = extractor.run()

# Process results
for result in results['successful']:
    print(f"Processed: {result['source_file']}")
    print(f"Tables found: {result['table_count']}")
    print(f"Formulas found: {result['formula_count']}")
    print(f"Quality score: {result['quality_metrics']['quality_score']}")
```

### Output Structure

Each processed file generates two output files:
1. `{filename}.txt`: Extracted text content
2. `{filename}.json`: Metadata including:
   - Extraction methods used
   - Tables and formulas
   - Quality metrics
   - Language detection
   - Corruption detection
   - Domain classification

### Error Handling

- Graceful failure handling for each extraction method
- Detailed error logging
- Fallback mechanisms for failed extractions
- Quality-based output organization

### Performance Considerations

- Parallel processing with configurable worker count
- Timeout handling for long-running operations
- Memory-efficient processing of large files
- Caching of intermediate results

### Extending the Pipeline

1. **Adding New Extractors**
   - Inherit from `BaseExtractor`
   - Implement `extract_text` method
   - Add format-specific processing

2. **Custom Quality Metrics**
   - Extend `QualityConfig` models
   - Implement new quality checks
   - Update validation rules

3. **New Features**
   - Create new mixins for specialized functionality
   - Integrate with existing pipeline
   - Update configuration and validation

// ... existing code ...

Documentation Entry: Quality Control for Structured Data
Quality Control Improvements for Structured Data
CSV-Specific Quality Metrics:
The extractor now includes CSV-specific quality checks to reduce false positives. These checks analyze header consistency, row/column uniformity, and detect common data corruption patterns unique to CSVs.
CSV Structure Handling:
The extraction pipeline preserves CSV structure in the .txt output, ensuring headers and data rows are clearly separated by commas. The quality control module flags files with missing headers, inconsistent row lengths, or excessive empty fields.
Quality Thresholds for Structured Data:
Quality thresholds for structured data (CSV, JSON) have been reviewed and adjusted. The system now uses token count, header validation, and schema consistency as part of the quality metrics. Files failing these checks are flagged as low_quality in the metadata.
Status Check: Has Corpus Balancing Been Done?
Corpus balancing (analyzing and ensuring even distribution across domains and file types) has not yet been implemented in the current codebase. The next step is to design and develop this functionality.
Next Steps
1. Design Corpus Rebalance Suite
Architecture:
The balancer should scan the processed corpus, analyze domain and file type distribution, and generate a report.
It should provide recommendations or scripts to move, copy, or flag files to achieve balance.
Consider modular design: a core analyzer, a reporting module, and (optionally) an auto-balancer.
Consultation:
Prepare a design doc and consult with your boss for feedback before implementation.
2. Develop Corpus Balance Suite
Foundation Search:
I will search all folders (especially in CryptoFinanceCorpusBuilder) for any existing Python scripts related to corpus balancing, domain analysis, or distribution reporting that can be used as a foundation.
3. End-to-End Testing
Testing Plan:
Test each pipeline part individually (collectors, extractors, deduplicators, etc.).
Then run a full pipeline test with a small sample, ensuring all components interact as expected.
Immediate Actions
Review and summarize the following files for architectural understanding and current usage:
README FULL.md
DEPLOYMENT_PLAN_20240511.md
tests/pdf_extraction/TEST_EXTRACTION_PIPELINE_20240511.md
Scan the codebase for any scripts related to corpus balancing.
For each .py file, indicate:
If it is used, for what purpose, and by which script it is called.
If not used, mark as "currently not used".
Draft a new high-level README:
Overview of the system and its components.
File-by-file breakdown (used/unused).
Design plan for the corpus balancer.
Roadmap for further testing and launch.

Absolutely! Here’s a **log entry update** summarizing what you’ve completed and what’s next:

---

## ✅ **Completed Steps**

### 1. **Extractor Robustness & Metadata Quality**
- **PDF and Non-PDF Extractors:** Both are fully integrated, robust, and modular.
- **Metadata Normalization:** All extracted files (PDF and non-PDF) now have consistent, top-level, production-ready metadata.
- **Automated & Manual Validation:** CLI tools and scripts allow for both automated and manual metadata validation and normalization.

### 2. **CLI Integration**
- **New CLI Commands:** Added `normalize-metadata` and `validate-metadata` commands for easy corpus-wide operations.
- **Extractor Flags:** Both extractors now support the `--auto-normalize` flag (default: True), making normalization seamless and opt-in.

### 3. **Batch Processing & Automation**
- **Parallel Batch Extraction:** Both extractors support efficient, parallel batch processing for large corpora.
- **Auto-Normalization in Pipeline:** Normalization is now idempotent, safe, and runs automatically after extraction.

### 4. **Testing & Verification**
- **End-to-End Tests:** Successfully ran batch extractions and normalization on both PDF and non-PDF test sets.
- **Zero Failures:** All files processed and normalized without errors.
- **Output Audited:** Verified that all required fields are present and correctly structured in the output.

---

## ⏭️ **Next Steps**

### 1. **Configuration Synchronization**
- **Goal:** Ensure all extractors, validators, and CLI tools use a unified, version-controlled configuration for domains, quality thresholds, and processing rules.
- **Tasks:**
  - Centralize config files (domain, quality, etc.)
  - Add CLI/config sync commands if needed
  - Document config update workflow

### 2. **Corpus Balancer Integration**
- **Goal:** Analyze and rebalance the corpus for domain, quality, and representation.
- **Tasks:**
  - Run corpus analytics (domain distribution, Gini coefficient, etc.)
  - Use the balancer to generate and execute rebalancing plans
  - Validate balanced output and document results

### 3. **Scheduled/Automated Normalization (Optional)**
- **Goal:** Set up scheduled jobs or hooks to auto-normalize new data as it arrives.
- **Tasks:**
  - Add cron job, Windows Task Scheduler, or pipeline hook
  - Monitor and log normalization runs

### 4. **Documentation & Reporting**
- **Goal:** Finalize user/developer documentation and generate reports/dashboards for stakeholders.
- **Tasks:**
  - Update README and CLI docs
  - Generate sample reports and dashboards

---

**You are now ready to move on to configuration synchronization and corpus balancing!**  
If you want a more detailed breakdown or a project management checklist, just let me know!
