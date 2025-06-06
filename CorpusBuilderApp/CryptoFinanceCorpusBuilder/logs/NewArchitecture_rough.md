# NewArchitecture_rough.md

## Anna's Libraries - sys.path Manipulation

Anna's Archive collector scripts (e.g., collect_annas_main_library.py) use sys.path manipulation and dynamic imports. This is required due to their complex, legacy structure and is intentionally left unchanged for stability. Any future refactor should carefully consider these dependencies.

## enhanced_scidb_collector.py - Anna's Library Collector

- This script intentionally uses sys.path manipulation and imports from sources.base_collector for legacy/compatibility reasons. It is not refactored to absolute imports.
- It appears to be unused, as collect_annas_scidb_search.py now calls enhanced_client.py instead of this collector.

## Import Consistency in Non-Anna's Collectors

- All non-Anna's collectors in shared_tools/collectors already use absolute, package-style imports consistent with the new architecture. No changes were needed during the audit.
- Next: Identify and log potentially unused collectors for cleanup or deprecation.

# Config Patterns for Topic Switching (Collectors)

| Collector                | How to Switch Topic/Config                |
|--------------------------|-------------------------------------------|
| Anna's Main Library      | Pass new `--batch-json` with your terms   |
| Anna's SCIDB             | Pass new `--scidb-json-file` with DOIs    |
| General Web Corpus       | Edit `config/domain_config.py`            |
| Arxiv                    | Pass new `--arxiv-search-terms` (needs --categories for full flexibility) |
| GitHub                   | Pass new `--github-repo-name` or `topic`  |
| BitMEX                   | Pass new `--bitmex-keywords`              |

## Scientific Papers Workflow
- Anna's Library: Use keyword-based batch_json for broad topic search. If DOIs are required, you must pre-generate a DOI list (see below).
- arxiv_collector.py: Only alternative for scientific papers by keyword, but currently hardcoded to q-fin. Needs --categories CLI argument for other fields.
- Generating DOI lists: Use arXiv API, CrossRef API, or similar bibliographic databases to search by keyword and export DOIs. Example: Use arXiv's API to search for papers, then extract DOIs from the results for batch processing.

## Current Limitation
- If you want to collect scientific papers by keyword and not by DOI, Anna's Library is best. If you need DOIs, you must generate them externally.
- arxiv_collector.py can be made flexible with a quick CLI fix to accept categories.

## Template batch_json Files for Anna's Library

- Created batch_science.json and batch_history.json with science and history book titles, respectively.
- These files are intended to be passed to Anna's Library collector using the --batch-json argument to test topic-agnostic capability.
- Usage example:
  python -m CryptoFinanceCorpusBuilder.shared_tools.collectors.collect_annas_main_library --batch-json shared_tools/collectors/batch_science.json
- This will confirm that Anna's Library can collect books on any topic, not just crypto.

Key Finding:
The Anna's Library collector works for any topic.
To adapt for a new project, update the meaningful_words list in collect_annas_main_library.py to include keywords relevant to your topic (e.g., science, history, etc.).
The rest of the workflow (batch file, CLI, output) is already project-agnostic.
Action for New Projects:
Edit the meaningful_words list to match your domain.
Optionally, make this list CLI-configurable for even more flexibility.
Result:
The system is modular, robust, and ready for multi-project use with minimal changes.

## Anna's Library Multi-Topic Test: Success

- The collector works for any topic. For new projects, update the `meaningful_words` list in `collect_annas_main_library.py` to match your domain.
- All other workflow steps (batch file, CLI, output) are already project-agnostic.

## Next Steps
- Add --categories to arxiv_collector.py for flexible category selection.
- Make domain_config.py CLI-configurable.
- Document the new project workflow and create a command cheat list for users.

## CLI Quick Wins Implemented

- `arxiv_collector.py` now supports a `--categories` argument for flexible arXiv category selection.
- `collect_general_web_corpus.py` now supports a `--domain-config` argument to specify a custom domain_config.py file.
- Next: Create a command cheat list for all major collectors and workflows.

## [2024-06-09] Cheat List Complete, Ready for CLI Collector Testing
- Cheat list in logs/NewArchitecture_Commands.md now covers all major collectors and processors, with arguments and troubleshooting tips.
- Next: Systematic CLI execution test for each collector from project root.
- Reminder: Log all issues, import/path errors, and edge cases in the main progress log.
- If any collector fails, capture full error and context for follow-up.

## [2024-06-09] BitMEX Collector CLI Added, CLI Audit for Other Collectors
- BitMEX collector now has a CLI entry point (argparse) for --output-dir, --bitmex-keywords, --bitmex-max-pages, --existing-titles.
- collect_isda.py: No CLI entry point (no argparse). Needs a CLI wrapper for consistent testing.
- fred_collector.py: No CLI entry point. Only callable as a class/module.
- github_collector.py: No CLI entry point. Only callable as a class/module.
- quantopian_collector.py: No CLI entry point. Only callable as a class/module.
- Recommendation: Add argparse-based CLI entry points to these collectors for full parity, onboarding, and automated testing.

## [2024-06-XX] BitMEX Collector Direct Script Test

- Created and ran direct test scripts for both cli/collectors/collect_bitmex.py and shared_tools/collectors/collect_bitmex.py.
- Set bitmex_keywords=None and bitmex_max_pages=10 to ensure all posts are collected.
- Both collectors produced valid outputs, confirming that the scraping logic is robust and not dependent on CLI/argparse.
- This approach is recommended for debugging or validating collectors outside of CLI context.
- If future CLI issues arise, use direct script execution for diagnosis.

## 2024-03-14: FRED Collector CLI Implementation
- **Task**: Implemented CLI interface for FRED data collector
- **Changes**:
  - Added argparse-based CLI wrapper to `fred_collector.py`
  - Implemented support for multiple collection methods:
    - Series IDs (e.g., VIXCLS, DTWEXBGS)
    - Search terms (e.g., "volatility", "inflation")
    - Categories (e.g., 95, 32992)
    - Max results limit
  - Added debug output for API key loading and collection parameters
  - Integrated with existing .env file for API key management
- **Testing**:
  - Verified CLI functionality with various parameter combinations
  - Confirmed proper data collection and file output
  - Tested error handling and rate limiting
- **Documentation**:
  - Updated `NewArchitecture_Commands.md` with FRED collector examples
  - Updated `NewArchitecture_Logging.md` with collector-specific logging details
- **Next Steps**:
  - Implement similar CLI interfaces for other collectors
  - Add more comprehensive error handling
  - Consider adding progress bars for long-running collections

## 2024-05-31: Quantopian Collector CLI Test
- **Task**: Validated CLI interface for Quantopian research collector
- **Process**:
  - Ran the collector via CLI with `--output-dir data/tests/quantopian_cli_test`
  - Cloned the Quantopian research_public repository from GitHub
  - Discovered 204 Jupyter notebook files in the repository
  - Saved metadata for all notebooks to `quantopian_notebooks.json` in the output directory
- **Results**:
  - Repository successfully cloned to `data/tests/quantopian_cli_test/research_public`
  - Metadata file created with entries for all discovered notebooks
  - Logging output confirmed each step and final record count
- **Conclusion**:
  - Collector is working as intended, producing correct output and logs
  - Ready for further integration or batch processing

## 2024-05-31: GitHub Collector CLI Test (Search Terms)
- **Task**: Tested GitHub collector CLI with --search-terms and --max-repos arguments
- **Process**:
  - Ran the collector via CLI with `--output-dir data/tests/github_cli_test --search-terms "cryptocurrency" "blockchain" --max-repos 3`
  - Collector searched for repositories matching the provided terms
  - Deduplication logic skipped already-cloned repositories (e.g., bitcoin/bitcoin)
  - Newly discovered repositories (e.g., unionlabs/union) were cloned to the output directory
- **Results**:
  - 2 unique repositories present in the output directory after the run
  - Logging output confirmed deduplication, cloning, and final record count
- **Conclusion**:
  - Search-terms functionality and deduplication work as intended
  - --max-repos limit is enforced across all terms
  - Collector is robust for repeated and varied CLI usage

## 2024-05-31: Repo Collector CLI Test
- **Task**: Validated CLI interface for repository collector
- **Process**:
  - Ran the collector via CLI with `--output-dir data/tests/repo_cli_test --query https://github.com/bitcoin/bitcoin.git --branch develop` (non-existent branch)
  - Collector reported error for missing branch with clear log output
  - Retested with `--branch master` (existing branch)
  - Successfully cloned the repository to the output directory
- **Results**:
  - Error handling for non-existent branches is robust and informative
  - Repository successfully cloned when valid branch is specified
  - Output directory contains the expected repository
- **Conclusion**:
  - Repo collector CLI supports branch selection and provides clear error feedback
  - Extraction of repository contents is handled by the non-pdf extractor in a separate workflow

## 2024-05-31: API Collector CLI Test
- **Task**: Validated CLI interface for API collector
- **Process**:
  - Ran the collector via CLI with `--output-dir data/tests/api_cli_test --endpoint "coins/markets" --params '{\"vs_currency\": \"usd\", \"ids\": \"bitcoin\"}' --base-url "https://api.coingecko.com/api/v3" --method GET`
  - Collector called the CoinGecko public API for real-time Bitcoin market data
  - All CLI arguments (endpoint, params, base URL, method) were parsed and passed correctly
  - Response was saved to `api_response.json` in the output directory
- **Results**:
  - API response file contains valid market data for Bitcoin
  - Debug output confirmed all arguments and response path
- **Conclusion**:
  - API collector CLI is now flexible and robust for real-world API testing
  - Ready for further integration or batch processing

## 2024-05-31: Web Collector CLI Test
- **Task**: Validated CLI interface for generic web scraper
- **Process**:
  - Ran the collector via CLI with various URLs and options (e.g., --file-ext pdf, --no-robots)
  - Successfully fetched and parsed web pages, extracted links, and attempted downloads
  - Some sites (e.g., arXiv, NASA) did not yield downloads due to indirect links, anti-bot measures, or link format issues
  - Successfully downloaded files from simple sites with direct links
- **Results**:
  - Collector is a generic web scraper that can be modified for specific sites or link formats as needed
  - Output and debug logs are clear and informative
- **Conclusion**:
  - The web_collector is robust for basic scraping and can serve as a template for more advanced or site-specific scrapers in the future
  - All major collectors have now been tested from the CLI except ISDA

   Component Status & Testing

### PDF & Non-PDF Extractors
- Both extractors are robust and fully tested.
- Support chunking, quality control, and metadata enrichment.
- Output: `.txt` and `.json` files in `_extracted` and `low_quality` subfolders.
- CLI usage and troubleshooting are documented below.

### Deduplication
- Fully tested for both PDF and non-PDF pipelines.
- Handles edge cases (unicode, whitespace, case, punctuation, abbreviations).
- Produces detailed deduplication reports and updates per-file metadata.
- CLI and programmatic usage are documented.

### Corpus Manager
- Manages metadata, indexing, and corpus structure.
- Used by other modules (deduplicator, extractors, balancer).
- Not typically run as a standalone CLI, but can be tested via scripts or Python shell.
- Example test:
  ```python
  from CryptoFinanceCorpusBuilder.storage.corpus_manager import CorpusManager
  cm = CorpusManager("data/test_corpus")
  cm.add_document("somefile.pdf", "crypto_derivatives")
  cm.print_corpus_stats()
  ```

### Corpus Balancer
- Ensures balanced domain/type representation.
- CLI-wrapped: `analyze-balance`, `rebalance`, and `auto-rebalance` commands available in `crypto_corpus_cli.py`.
- Example CLI usage:
  ```bash
  python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli analyze-balance --corpus-dir <corpus>
  python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli rebalance --corpus-dir <corpus> --strategy quality_weighted
  python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli auto-rebalance --corpus-dir <corpus>
  ```
- Comprehensive test suite: `pytest -v CryptoFinanceCorpusBuilder/tests/test_corpus_balance.py`
- See `readmes/balancer integration guide and examples.md` for advanced usage and automation.

### Summary Table: How to Test

| Component         | Test File/Script                        | CLI Command/How to Test                                      |
|-------------------|-----------------------------------------|--------------------------------------------------------------|
| Corpus Manager    | scripts/corpus_cleanup.py, corpus_integrity_check.py | Use scripts or import in Python shell                        |
| Corpus Balancer   | tests/test_corpus_balance.py            | `pytest -v CryptoFinanceCorpusBuilder/tests/test_corpus_balance.py`<br>`python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli analyze-balance --corpus-dir ...` |
| Deduplication     | scripts/test_deduplication_collectors.py| Run script or use deduplicator CLI/module                    |
| Extractors        | See README, tested via CLI              | Use CLI commands for PDF/non-PDF extraction                  |

---

- All documentation and module-specific READMEs should be kept up to date as features are added or changed.
- For advanced corpus balancing and automation, see `readmes/balancer integration guide and examples.md`. 

2024-05-28: Directory/Config Refactor Milestone
ProjectConfig: New class in shared_tools for all path management.
YAML Fix: Only cache_dir is stored/loaded, fixing round-trip bug.
Safe Serialization: Now uses yaml.safe_dump.
Error Handling: Directory creation now robust to permission/OS errors.
API Stability: No breaking changes to how paths are accessed.
Next Steps: All pipeline modules to migrate to use ProjectConfig.
Phase-Appropriate: No over-engineering; advanced features planned for later.

## Unified Configuration and Logging (2024-03-19)

### Design Goals
1. Single source of truth for all configuration
2. Consistent logging across all components
3. Easy to modify and maintain
4. Backward compatibility with legacy systems
5. Support for future extensibility

### Architecture Overview
```
master_config.yaml
├── Base Directories
│   ├── corpus_dir
│   └── cache_dir
├── Collectors
│   ├── arxiv
│   ├── scidb
│   └── github
├── Extractors
│   ├── pdf
│   └── nonpdf
├── Domains
│   ├── crypto_derivatives
│   ├── high_frequency_trading
│   └── ...
└── Logging
    ├── level
    ├── file
    ├── max_size
    └── format
```

### Implementation Notes
1. **Configuration Management**
   - YAML-based configuration for readability
   - Schema validation using Pydantic
   - Default values for all settings
   - Environment variable overrides

2. **Logging System**
   - Centralized configuration
   - Component-specific log levels
   - Automatic rotation
   - Structured logging format

3. **Backward Compatibility**
   - Legacy mode support
   - Gradual migration path
   - Configuration migration tools

### Future Considerations
1. **Configuration Management**
   - Add support for environment-specific configs
   - Add configuration validation tools
   - Add configuration migration tools
   - Add configuration documentation generator

2. **Logging Enhancements**
   - Add log aggregation
   - Add log analysis tools
   - Add log visualization
   - Add log-based monitoring

3. **System Integration**
   - Add support for distributed runs
   - Add support for cloud storage
   - Add support for containerization
   - Add support for CI/CD integration

## Configuration Updates (2024-03-XX)

### New Configuration Structure
- Separated test and production configurations
- Moved cache to E: drive
- Implemented complete domain set
- Added search terms configuration

### Key Changes
1. Environment Separation
   - Test environment with reduced values
   - Production environment with full values
   - Separate domain configurations

2. Directory Structure
   - Test and production data separation
   - Cache on E: drive
   - Logs on G: drive

3. Domain Configuration
   - Complete set of 8 domains
   - Search terms per domain
   - Quality thresholds
   - Target ratios

4. Processing Pipeline
   - Collector configurations
   - Extractor configurations
   - Processor configurations
   - Quality control settings

### Next Steps
1. Integrate remaining processors with new configuration
2. Update collectors to use new configuration
3. Implement directory structure creation
4. Add configuration validation
5. Update documentation

## [2024-03-19] Processor Architecture Updates

### Overview
The processor architecture has been updated to support the new master configuration system while maintaining backward compatibility. This update provides a more robust and flexible processing pipeline.

### Processor Structure

#### 1. Base Processor
```python
class BaseProcessor:
    def __init__(self, project_config=None, config_path=None):
        self.config = self._load_config(project_config, config_path)
        self.logger = self._setup_logger()
        
    def _load_config(self, project_config, config_path):
        if project_config and hasattr(project_config, 'processors'):
            return self._load_from_project_config(project_config)
        return self._load_from_file(config_path)
```

#### 2. Quality Control Pipeline
```python
class QualityControl(BaseProcessor):
    def __init__(self, project_config=None, config_path=None):
        super().__init__(project_config, config_path)
        self.detectors = {
            'translation': MachineTranslationDetector(self.config),
            'language': LanguageConfidenceDetector(self.config),
            'corruption': CorruptionDetector(self.config)
        }
```

#### 3. Specialized Processors
```python
class ChartImageExtractor(BaseProcessor):
    def process(self, document):
        charts = self.extract_charts(document)
        return self.validate_and_save(charts)

class FinancialSymbolProcessor(BaseProcessor):
    def process(self, document):
        symbols = self.extract_symbols(document)
        return self.validate_symbols(symbols)

class DomainClassifier(BaseProcessor):
    def process(self, document):
        scores = self.classify_domains(document)
        return self.select_domain(scores)
```

### Configuration Integration

#### 1. Master Config Structure
```yaml
processors:
  quality_control:
    enabled: true
    checks:
      language: {...}
      corruption: {...}
      duplication: {...}
      translation: {...}
    processing: {...}

  specialized:
    charts: {...}
    symbols: {...}

  domain_classifier: {...}
```

#### 2. Legacy Config Support
```python
def _load_from_project_config(self, project_config):
    # Try new structure first
    if hasattr(project_config, 'processors'):
        return self._get_processor_config(project_config)
    # Fall back to legacy structure
    return self._get_legacy_config(project_config)
```

### Processing Pipeline

#### 1. Document Processing
```python
def process_document(self, document):
    try:
        # Pre-processing
        document = self.pre_process(document)
        
        # Main processing
        result = self.process(document)
        
        # Post-processing
        return self.post_process(result)
    except Exception as e:
        self.logger.error(f"Processing failed: {e}")
        return None
```

#### 2. Batch Processing
```python
def process_batch(self, documents):
    with ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
        futures = [executor.submit(self.process_document, doc) 
                  for doc in documents]
        return [f.result() for f in as_completed(futures)]
```

### Error Handling

#### 1. Configuration Errors
```python
class ConfigurationError(Exception):
    def __init__(self, message, config_path=None):
        super().__init__(message)
        self.config_path = config_path
```

#### 2. Processing Errors
```python
class ProcessingError(Exception):
    def __init__(self, message, document=None):
        super().__init__(message)
        self.document = document
```

### Testing Structure

#### 1. Unit Tests
```python
def test_processor_config():
    processor = Processor(project_config=test_config)
    assert processor.config is not None
    assert processor.config.enabled is True

def test_processor_legacy():
    processor = Processor(config_path="legacy_config.json")
    assert processor.config is not None
```

#### 2. Integration Tests
```python
def test_processor_pipeline():
    pipeline = ProcessingPipeline(project_config=test_config)
    results = pipeline.process_documents(test_documents)
    assert all(r.success for r in results)
```

### Next Steps
1. Implement automated test suite
2. Add performance monitoring
3. Enhance error recovery
4. Optimize batch processing
5. Add progress reporting

## Test Structure

### Unit Tests
- Fast, isolated tests
- No external dependencies
- Test core functionality
- Examples:
  - Collector initialization
  - Domain determination
  - Error handling

### Integration Tests
- Real-world functionality tests
- Marked with @pytest.mark.integration
- Test actual downloads
- Examples:
  - DOI collection
  - File validation
  - Metadata generation
  - Cleanup

### Test Environment
- Isolated test directories
- Test-specific configuration
- Automatic cleanup
- No impact on production data

