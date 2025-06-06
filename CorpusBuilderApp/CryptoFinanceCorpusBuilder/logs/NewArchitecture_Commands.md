# Command Cheat List (Draft)

### Anna's Library Collector
```
python -m CryptoFinanceCorpusBuilder.shared_tools.collectors.collect_annas_main_library --batch-json "<path_to_batch_json>" --output-dir <output_dir> [--existing-titles <titles_file>]
```
- Downloads books from Anna's Archive using a batch JSON of titles.
- Requires AA_ACCOUNT_COOKIE in .env.
- Troubleshooting: Ensure output dir exists and cookie is valid.

### Arxiv Collector
```
python -m CryptoFinanceCorpusBuilder.shared_tools.collectors.arxiv_collector --output-dir <output_dir> [--categories <cat1> <cat2>] [--search-terms <term1> <term2>] [--max-results <N>] [--start-index <N>] [--clear-output-dir] [--existing-titles <titles_file>]
```
- Collects papers from arXiv by category or search term.
- Categories default to q-fin.* if not specified.
- Troubleshooting: Use --clear-output-dir to avoid mixing runs.

### General Web Corpus Collector
```
python -m CryptoFinanceCorpusBuilder.shared_tools.collectors.collect_general_web_corpus --output-dir <output_dir> [--domain-config <path_to_domain_config.py>]
```
- Downloads web corpus using domain config.
- Requires AA_ACCOUNT_COOKIE in .env.
- Troubleshooting: Check domain config and output dir.

### Anna's SCIDB Search Collector
```
python -m CryptoFinanceCorpusBuilder.shared_tools.collectors.collect_annas_scidb_search --output-dir <output_dir> [--scidb-doi <doi>] [--scidb-json-file <json_file>] [--scidb-domain <domain>]
```
- Downloads papers from Anna's Archive SCIDB by DOI or batch JSON.
- Requires AA_ACCOUNT_COOKIE in .env.
- Troubleshooting: JSON file must be a list of paper objects with 'doi'.

### Enhanced SciDB Collector
```
python -m CryptoFinanceCorpusBuilder.shared_tools.collectors.enhanced_scidb_collector --output-dir <output_dir> [--doi-list <json_file>] [--search-terms <txt_file>] [--domain <domain>] [--max-results <N>]
```
- Collects papers from SciDB by DOI list or search terms.
- Troubleshooting: Either --doi-list or --search-terms is required.

### ISDA Collector
```
python -m CryptoFinanceCorpusBuilder.shared_tools.collectors.collect_isda --output-dir <output_dir> [--isda-keywords <kw1> <kw2>] [--isda-max-sources <N>] [--isda-clear-output-dir]
```
- Downloads ISDA documentation and PDFs.
- Troubleshooting: Use --isda-clear-output-dir to reset output.

### BitMEX Collector
- No CLI entry point. Run as a module or import and call `run_bitmex_collector()`.
- Usage: See code for details. Output dir: ./data/bitmex_research

### Batch PDF Extractor (Enhanced)
```
python -m CryptoFinanceCorpusBuilder.shared_tools.processors.batch_text_extractor_enhanced_prerefactor --input-dir <pdf_dir> --output-dir <output_dir> [--num-workers <N>] [--batch-size <N>] [--timeout <N>] [--verbose]
```
- Extracts text, tables, formulas from PDFs in batch.
- Troubleshooting: Use --verbose for debug info. Check output for failed files.

### Batch Non-PDF Extractor (Enhanced)
```
python -m CryptoFinanceCorpusBuilder.shared_tools.processors.batch_nonpdf_extractor_enhanced --input-dir <input_dir> --output-dir <output_dir> [--num-workers <N>] [--batch-size <N>] [--timeout <N>] [--verbose]
```
- Extracts text from non-PDF files (HTML, CSV, JSON, etc).
- Troubleshooting: Use --verbose for debug info. Check output for failed files.

### Deduplicator
```
python -m CryptoFinanceCorpusBuilder.shared_tools.processors.deduplicator --input-dir <corpus_dir> --output-dir <output_dir> [--dedup-mode <mode>] [--verbose]
```
- Deduplicates corpus files and updates metadata.
- Troubleshooting: Use --verbose for detailed logs.

*This list will be expanded as more workflows are finalized.*

# New Architecture Commands

## Data Collection Commands

### FRED Data Collection
```bash
# Basic usage with series IDs
python -m CryptoFinanceCorpusBuilder.shared_tools.collectors.fred_collector --output-dir data/tests/fred_cli_test --series-ids VIXCLS

# Search by terms
python -m CryptoFinanceCorpusBuilder.shared_tools.collectors.fred_collector --output-dir data/tests/fred_cli_test --search-terms "volatility" "inflation"

# Search by categories
python -m CryptoFinanceCorpusBuilder.shared_tools.collectors.fred_collector --output-dir data/tests/fred_cli_test --categories 95 32992

# Limit results
python -m CryptoFinanceCorpusBuilder.shared_tools.collectors.fred_collector --output-dir data/tests/fred_cli_test --max-results 5

# Combine parameters
python -m CryptoFinanceCorpusBuilder.shared_tools.collectors.fred_collector --output-dir data/tests/fred_cli_test --series-ids VIXCLS DTWEXBGS --search-terms volatility --max-results 2
```

### GitHub Data Collection
```bash
# Basic usage
python -m CryptoFinanceCorpusBuilder.shared_tools.collectors.github_collector --output-dir data/tests/github_cli_test

# With specific repository
python -m CryptoFinanceCorpusBuilder.shared_tools.collectors.github_collector --output-dir data/tests/github_cli_test --repo "bitcoin/bitcoin"
```

### Web Data Collection
```bash
# Basic usage
python -m CryptoFinanceCorpusBuilder.shared_tools.collectors.web_collector --output-dir data/tests/web_cli_test

# With specific URL
python -m CryptoFinanceCorpusBuilder.shared_tools.collectors.web_collector --output-dir data/tests/web_cli_test --url "https://example.com"
```

### API Data Collection
```bash
# Basic usage
python -m CryptoFinanceCorpusBuilder.shared_tools.collectors.api_collector --output-dir data/tests/api_cli_test

# With specific endpoint
python -m CryptoFinanceCorpusBuilder.shared_tools.collectors.api_collector --output-dir data/tests/api_cli_test --endpoint "v1/data"
```

### Repository Data Collection
```bash
# Basic usage
python -m CryptoFinanceCorpusBuilder.shared_tools.collectors.repo_collector --output-dir data/tests/repo_cli_test

# With specific repository
python -m CryptoFinanceCorpusBuilder.shared_tools.collectors.repo_collector --output-dir data/tests/repo_cli_test --repo "bitcoin/bitcoin"
```

## Environment Setup
All collectors require proper environment variables to be set. These can be set in a `.env` file in the project root:

```env
# FRED API
FRED_API_KEY=your_fred_api_key

# GitHub API
GITHUB_TOKEN=your_github_token

# Other API keys as needed
```

## Output Structure
Each collector creates its own directory structure under the specified output directory:

```
data/tests/
├── fred_cli_test/
│   ├── VIXCLS_CBOE_Volatility_Index_VIX.json
│   ├── VIXCLS_CBOE_Volatility_Index_VIX.csv
│   └── ...
├── github_cli_test/
│   └── ...
└── ...
```

## Debug Output
Each collector provides debug output showing:
- Loaded API keys
- CLI arguments
- Collection parameters
- Number of records collected
- Output directory

Example:
```
[DEBUG] Loaded FRED_API_KEY: 05796b72da56e97a6f7ea908ecf57b59
[DEBUG] CLI args: Namespace(output_dir='data/tests/fred_cli_test', series_ids=['VIXCLS'], max_results=2)
[DEBUG] FREDCollector.collect called with:
  series_ids: ['VIXCLS']
  search_terms: None
  categories: None
  max_results: 2
  api_key: 05796b72da56e97a6f7ea908ecf57b59
Collected 4 FRED records. Output dir: data\tests\fred_cli_test
```