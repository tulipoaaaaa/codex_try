# New Architecture Logging

## Overview
The new architecture implements a comprehensive logging system that provides visibility into the data collection process, API interactions, and error handling.

## Logging Levels
- **DEBUG**: Detailed information for debugging
- **INFO**: General operational information
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failed operations
- **CRITICAL**: Critical errors that may require immediate attention

## Collector-Specific Logging

### FRED Collector
```python
[DEBUG] Loaded FRED_API_KEY: <api_key>
[DEBUG] CLI args: Namespace(...)
[DEBUG] FREDCollector.collect called with:
  series_ids: [...]
  search_terms: [...]
  categories: [...]
  max_results: <number>
  api_key: <api_key>
```

### GitHub Collector
```python
[INFO] GitHubCollector: Initializing with token
[DEBUG] Rate limits: {'core': {'limit': 5000, 'remaining': 4999}}
[INFO] Processing repository: <repo_name>
```

### Web Collector
```python
[INFO] WebCollector: Starting collection from <url>
[DEBUG] Response status: 200
[INFO] Saved content to: <file_path>
```

### API Collector
```python
[INFO] ApiCollector: Making request to <endpoint>
[DEBUG] Request parameters: {...}
[INFO] Response received: <status_code>
```

### Arxiv Collector
```python
[INFO] ArxivCollector: Starting collection from <url>
[DEBUG] Response status: 200
[INFO] Saved content to: <file_path>
```

## Log File Structure
Logs are stored in the `logs` directory with the following structure:
```
logs/
├── collectors/
│   ├── fred_collector.log
│   ├── github_collector.log
│   └── ...
├── api/
│   └── api_requests.log
└── errors/
    └── error.log
```

## Debug Output Format
Each collector provides standardized debug output showing:
1. Environment variables (API keys)
2. CLI arguments
3. Collection parameters
4. Operation results
5. Output directory

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

## Error Handling
Errors are logged with full stack traces and context:
```
[ERROR] Failed to collect data from FRED API
[ERROR] Status code: 429
[ERROR] Response: {'error': 'Rate limit exceeded'}
[ERROR] Stack trace:
  File "fred_collector.py", line 123, in collect
    response = self.api_request(endpoint, params)
  ...
```

## Rate Limiting
Rate limit information is logged for API-based collectors:
```
[INFO] Rate limits for api.stlouisfed.org:
  - Limit: 20 requests per minute
  - Remaining: 15
  - Reset: 2024-03-14 15:30:00
```

## File Operations
File operations are logged with paths and sizes:
```
[INFO] Saved file: data/tests/fred_cli_test/VIXCLS_CBOE_Volatility_Index_VIX.json
[INFO] File size: 1242.10 KB
[INFO] File type: JSON
```

## Best Practices
1. Always check debug output for API key loading
2. Monitor rate limit logs for API-based collectors
3. Review error logs for failed operations
4. Use appropriate log levels for different types of information
5. Include relevant context in log messages 

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


2024-05-28: ProjectConfig Foundation and Directory Standardization

1. ProjectConfig Foundation
Designed and implemented a robust ProjectConfig class in shared_tools.
Standardizes and auto-creates all required corpus subfolders (raw, extracted, reports, logs, config, etc.).
Supports an optional cache directory (e.g., on a secondary drive).
Uses pathlib for platform-agnostic path handling.
Provides a single source of truth for all path management in the pipeline.
2. YAML Config Persistence
Fixed YAML round-trip bug: Now only stores/loads cache_dir (not cache_data_dir), ensuring correct config reloads.
Serialization now uses yaml.safe_dump for security.
Preserved all existing properties and API for backward compatibility.
3. Error Handling
Added robust error handling for directory creation (catches permission and OS errors, raises clear exceptions).
4. Risk-Averse, Phase-Appropriate Approach
Deferred advanced features (Pydantic, lazy creation, hot-reload) to later phases.
Kept the implementation simple and stable for foundational work.
5. Ready for Integration
The new ProjectConfig is ready to be used by all pipeline components.
The codebase is now prepared for the next phase: full pipeline integration and testing.


Implemented ProjectConfig in shared_tools as the canonical path and folder management class.
All corpus and cache directories are now auto-created and validated on initialization.
YAML config persistence fixed: only cache_dir is stored/loaded, preventing reload bugs.
Serialization uses yaml.safe_dump for security.
Error handling added for directory creation (permission/OS errors).
Existing API and property access patterns preserved for stability.
Advanced features (schema validation, hot-reload, lazy creation) deferred to future phases.
This lays the groundwork for robust, modular, and scalable pipeline integration.


10 Actionable Next Steps (Path to Production)
Migrate All Components: Refactor all collectors, processors, CLI, and balancer modules to use ProjectConfig for all path and directory management.
Test Auto-Rebalance Loop: Write and run unit/integration tests for the auto-rebalance feedback loop using the new config structure.
Pipeline Integration Test: Run a full end-to-end test: collect → extract → balance → auto-rebalance, using the new folder structure.
CLI Smoke Tests: Test all CLI commands, including edge cases and dry-run/execute modes, to ensure compatibility with ProjectConfig.
Implement ConfigWatcher (Phase 2/3): Add a file watcher for dynamic config reloading (using watchdog), but keep it separate from ProjectConfig.
User Interface MVP: Begin work on a dashboard for corpus monitoring and manual triggers (Phase 3).
Backend API: Develop REST endpoints for UI integration and external automation.
User Acceptance Testing: Conduct internal UAT, gather feedback, and iterate on UX/CLI.
Documentation: Update README, getting started guides, and API docs to reflect the new architecture and usage patterns.
QA & Launch: Perform a security review, final testing, and production deployment.

Path to Production (Merging with High-Level Plan)
Phase 1: Foundation (COMPLETE: ProjectConfig, bugfixes, error handling)
Phase 2: Core Validation (IN PROGRESS: Integration tests, CLI smoke tests)
Phase 3: User Interface (Dashboard MVP, Backend API)
Phase 4: User Validation (UAT, feedback, iteration)
Phase 5: Production (Documentation, QA, launch)

---
2024-05-28: ProjectConfig Integration (batch_text_extractor_enhanced_prerefactor.py)
- Integrated ProjectConfig into shared_tools/processors/batch_text_extractor_enhanced_prerefactor.py.
- Added --project-config CLI argument for YAML-based config.
- Backward compatible: if --project-config is not provided, falls back to --input-dir/--output-dir.
- All path management now uses ProjectConfig properties when available.
- No breaking changes for existing users.
- This is the first step in incremental rollout of ProjectConfig across the pipeline.

---
2024-05-28: Test Setup and Execution for PDF and Non-PDF Processors

1. Test YAML Configs Created:
   - PDF Test Config: G:/ai_trading_dev/CryptoFinanceCorpusBuilder/config/project_config_pdf_test.yaml
   - Non-PDF Test Config: G:/ai_trading_dev/CryptoFinanceCorpusBuilder/config/project_config_nonpdf_test.yaml

2. Test Scripts Created:
   - PDF Test Script: G:/ai_trading_dev/CryptoFinanceCorpusBuilder/tests/test_pdf_extractor_projectconfig.py
   - Non-PDF Test Script: G:/ai_trading_dev/CryptoFinanceCorpusBuilder/tests/test_nonpdf_extractor_projectconfig.py

3. Test Execution:
   - PDF Processor Test:
     - Input: G:/ai_trading_dev/data/test_collect/portfolio_construction
     - Output: G:/ai_trading_dev/data/test_output/pdf_extractor_test
     - CLI Commands:
       - With ProjectConfig: python -m CryptoFinanceCorpusBuilder.tests.test_pdf_extractor_projectconfig
       - With Legacy Args: python -m CryptoFinanceCorpusBuilder.tests.test_pdf_extractor_projectconfig --input-dir G:/ai_trading_dev/data/test_collect/portfolio_construction --output-dir G:/ai_trading_dev/data/test_output/pdf_extractor_test

   - Non-PDF Processor Test:
     - Input: G:/ai_trading_dev/data/test_collect/test_fourfiles
     - Output: G:/ai_trading_dev/data/test_output/nonpdf_extractor_test
     - CLI Commands:
       - With ProjectConfig: python -m CryptoFinanceCorpusBuilder.tests.test_nonpdf_extractor_projectconfig
       - With Legacy Args: python -m CryptoFinanceCorpusBuilder.tests.test_nonpdf_extractor_projectconfig --input-dir G:/ai_trading_dev/data/test_collect/test_fourfiles --output-dir G:/ai_trading_dev/data/test_output/nonpdf_extractor_test

4. Verification:
   - Both tests verify that output files are created in the correct test output directories.
   - No files are written to the production/final corpus folders.

5. Next Steps:
   - Run the tests and verify output files.
   - Document any issues or improvements needed.

---
2024-05-28: PDF Processor Refinements

1. Improved Metadata Handling:
   - Preserved original data types from PyPDF2 metadata
   - Added proper handling of IndirectObject values
   - Ensures JSON serialization while maintaining data integrity
   - Better support for downstream processing

2. Adjusted Token Thresholds:
   - Lowered MIN_TOKEN_THRESHOLD to 50 (from 100)
   - Lowered LOW_QUALITY_TOKEN_THRESHOLD to 200 (from 500)
   - Removed separate test mode thresholds
   - Better suited for our actual document types

3. Improved Temp File Cleanup:
   - Added proper cleanup in worker_initializer
   - Added delay before deletion to ensure files are closed
   - Registered cleanup with atexit

4. Next Steps:
   - Run tests to verify metadata handling
   - Monitor document processing with new thresholds
   - Check downstream impact of metadata changes

---
2024-06-01: Major Integration Milestone
- Successfully tested both PDF and non-PDF extractors in both legacy CLI and ProjectConfig modes.
- All test files processed with zero failures; outputs in both _extracted and low_quality folders were quality checked and found to be robust, well-structured, and fully aligned.
- Metadata normalization and downstream compatibility confirmed.
- This marks the completion of the core extractor integration phase.
- **Known limitations:**
    - ProjectConfig currently only supports standard directory structure; arbitrary input/output paths from YAML are not yet supported.
    - Would-be-nice future features:
        * Support for fully custom input/output directories in ProjectConfig YAML
        * YAML schema validation and error reporting
        * Hot-reloading of config files (watchdog integration)
        * Per-domain or per-task config overrides
        * Enhanced CLI help and config validation
        * Automated test harness for all extractor modes
- Next: Proceed to full pipeline integration, corpus manager/balancer automation, and feedback loop implementation.

---
2024-06-01: Production-Grade Extractor Integration, Multiprocessing, and CLI Refactor

- PDF and non-PDF extractors now expose clean, production-grade APIs (`run_with_project_config`, `run_with_paths`).
- All multiprocessing logic is robust and Windows-safe (no local classes, all worker args pickleable).
- CLI (`crypto_corpus_cli.py`) now calls extractors via the new API, with full error handling and logging.
- ProjectConfig is the single source of truth for all path management; legacy CLI args still supported for backward compatibility.
- Extractors recursively discover and process all files in input directories and subfolders, sorting outputs into correct subfolders (`_extracted`, `low_quality`, etc.).
- Quality checks confirm all outputs are present, metadata is normalized, and directory structure is correct.
- Error handling: clear logging for missing input dirs, file processing errors, and temp file cleanup issues.
- Known limitation: PermissionError on temp file cleanup if files are still open (Windows-specific, non-blocking).
- Next steps: Integrate corpus manager and balancer, automate full pipeline, and begin feedback loop/monitoring features.

---
2025-06-01: ProjectConfig-Based Collector Test (ArxivCollector)
- Successfully tested ArxivCollector with ProjectConfig YAML (project_config_arxiv_test.yaml).
- Output files correctly placed in domain/content-type subfolders (e.g., high_frequency_trading/papers).
- UnicodeEncodeError observed in logging due to non-ASCII author names; does not affect file output or data integrity.
- All files verified present and valid in output directory.
- Confirms backward-compatible collector support for both ProjectConfig and legacy path modes.
- Next: Roll out ProjectConfig support to additional collectors and monitor for encoding/logging issues.

## [2025-06-02] SciDB Collector Modernization

- Fully migrated SciDB DOI collection to enhanced_client.py + enhanced_scidb_collector.py.
- New logic: requests-based download first, Selenium fallback, robust metadata extraction, normalized filenames.
- Successfully tested on DOI 10.1111/cyt.12104 (HTML-only download succeeded).
- Deprecated collect_annas_scidb_search.py; all new SciDB collection should use the new pipeline.
- Improved logging and provenance for all downloads.

## Unified Logging Configuration (2024-03-19)

### Overview
The logging system has been enhanced to support centralized configuration through the master config file. This allows for consistent logging across all components while maintaining flexibility.

### Configuration Structure
```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: "corpus_builder.log"
  max_size: 10485760  # 10MB
  backup_count: 5
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### Key Features
1. **Centralized Control**: Logging configuration is managed through the master config
2. **Flexible Levels**: Each component can have its own log level
3. **Rotation Support**: Automatic log rotation with size limits
4. **Consistent Format**: Standardized log format across all components
5. **Backward Compatibility**: Legacy logging still supported

### Implementation Status
- [x] Master config logging section defined
- [x] Main CLI updated to use config-based logging
- [x] Log rotation implemented
- [ ] All collectors updated to use new logging
- [ ] All extractors updated to use new logging
- [ ] Documentation updated

### Next Steps
1. Update all collectors to use the new logging configuration
2. Update all extractors to use the new logging configuration
3. Add log analysis tools
4. Add log aggregation for distributed runs
5. Update documentation with logging examples

## Logging Configuration (Updated 2024-03-XX)

### Environment-Specific Logging
```
logs/
├── test/                        # Test environment logs
│   ├── corpus_builder.log
│   ├── collectors.log
│   ├── extractors.log
│   └── processors.log
│
└── production/                  # Production environment logs
    ├── corpus_builder.log
    ├── collectors.log
    ├── extractors.log
    └── processors.log
```

### Log Levels
- Test Environment: DEBUG level for detailed debugging
- Production Environment: INFO level for production monitoring

### Log Rotation
- Max file size: 10MB
- Backup count: 5
- Format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

### Component-Specific Logging
- Collectors: Separate log file for each collector type
- Extractors: Separate log file for PDF and non-PDF extraction
- Processors: Separate log file for each processor type

### Cache and Temporary Files
- Cache directories moved to E: drive for better performance
- Temporary files cleaned up automatically
- Log files remain on G: drive for persistence

## [2024-03-19] Processor and Configuration Logging Updates

### Overview
We have enhanced the logging system to provide comprehensive visibility into processor operations and configuration management. This update ensures consistent logging across all components while maintaining backward compatibility.

### Processor Logging

#### QualityControl Processor
```python
[INFO] QualityControl: Initializing with master config
[DEBUG] Loading configuration from processors.quality_control
[INFO] Initializing sub-processors:
  - MachineTranslationDetector
  - LanguageConfidenceDetector
  - CorruptionDetector
[DEBUG] Configuration loaded successfully
[INFO] Processing batch of 10 documents
[DEBUG] Document 1/10: Language confidence 0.95
[DEBUG] Document 2/10: Translation score 0.12
[INFO] Batch complete: 8 passed, 2 failed
```

#### ChartImageExtractor
```python
[INFO] ChartImageExtractor: Starting extraction
[DEBUG] Configuration: dpi=300, ocr_enabled=True
[INFO] Processing file: document.pdf
[DEBUG] Found 3 charts in document.pdf
[INFO] Extracted chart 1/3: size=800x600
[DEBUG] OCR results: 95% confidence
[INFO] Saved chart to: charts/chart_1.png
```

#### FinancialSymbolProcessor
```python
[INFO] FinancialSymbolProcessor: Initializing
[DEBUG] Loading symbol dictionary
[INFO] Processing document: trading_analysis.txt
[DEBUG] Found 15 financial symbols
[INFO] Validated 12 symbols, 3 unknown
[DEBUG] Unknown symbols: ['XYZ', 'ABC', 'DEF']
```

#### DomainClassifier
```python
[INFO] DomainClassifier: Starting classification
[DEBUG] Target domains: ['crypto_derivatives', 'high_frequency_trading']
[INFO] Processing document: market_analysis.pdf
[DEBUG] Domain scores:
  - crypto_derivatives: 0.85
  - high_frequency_trading: 0.65
[INFO] Classified as: crypto_derivatives
```

### Configuration Logging

#### Master Config Loading
```python
[INFO] Loading master configuration
[DEBUG] Environment: production
[DEBUG] Base directories:
  - corpus_dir: /data/production
  - cache_dir: /cache/production
  - log_dir: /logs/production
[INFO] Configuration loaded successfully
```

#### Legacy Config Fallback
```python
[WARNING] processors.quality_control not found in master config
[INFO] Falling back to legacy quality_control configuration
[DEBUG] Legacy config loaded from: config/quality_control.json
```

#### Processing Parameters
```python
[DEBUG] Processing settings:
  - max_workers: 4
  - batch_size: 10
  - timeout: 300
[INFO] Worker pool initialized with 4 workers
```

### Error Logging

#### Configuration Errors
```python
[ERROR] Invalid configuration format
[DEBUG] Expected structure: processors.quality_control.checks
[DEBUG] Received: processors.quality_control
[ERROR] Configuration validation failed
```

#### Processing Errors
```python
[ERROR] Failed to process document: invalid_format.pdf
[DEBUG] Error type: PDFParseError
[DEBUG] Error details: Invalid PDF structure
[INFO] Skipping to next document
```

#### Integration Errors
```python
[ERROR] Pipeline integration failed
[DEBUG] Error in QualityControl processor
[DEBUG] Error in MachineTranslationDetector
[INFO] Attempting recovery...
[ERROR] Recovery failed, stopping pipeline
```

### Log File Structure
```
logs/
├── processors/
│   ├── quality_control.log
│   ├── chart_extractor.log
│   ├── symbol_processor.log
│   └── domain_classifier.log
├── configuration/
│   ├── master_config.log
│   └── legacy_config.log
└── errors/
    ├── processor_errors.log
    └── config_errors.log
```

### Best Practices
1. Always log configuration loading and validation
2. Include debug information for troubleshooting
3. Log all processor operations with appropriate detail
4. Maintain separate error logs for different components
5. Use consistent log formats across all processors
6. Include timing information for performance monitoring
7. Log all fallback operations for legacy support
8. Maintain clear error context for debugging

### Next Steps
1. Implement log rotation and cleanup
2. Add log aggregation for distributed processing
3. Enhance error reporting with stack traces
4. Add performance metrics logging
5. Implement log analysis tools

## Test Logging

### Integration Test Logging
- Logs real download attempts
- Records file operations
- Tracks domain classification
- Monitors metadata generation

### Log Levels in Tests
- INFO: Test progress and setup
- WARNING: Expected test conditions
- ERROR: Test failures and exceptions
- DEBUG: Detailed test execution

### Test Log Files
- Stored in test-specific log directory
- Separate from production logs
- Include test execution timestamps
- Record all file operations