Thank you for the reminder and the clear direction.  
**You are absolutely right:**  
- We should only be working with files in `shared_tools` (and not the legacy or duplicate locations).
- **Duplicate code in both `processors/` and `shared_tools/processors/` must be eliminated.**
- All refactoring and ProjectConfig integration should be done only in `shared_tools`.

---

## **Revised Audit: Only `shared_tools`**

### 🔴 **Critical (must be consolidated and refactored first)**
#### 1. `shared_tools/processors/batch_text_extractor_enhanced_prerefactor.py`
- **Current path management:** Uses `os.makedirs`, manual path joins for output directories.
- **Duplication:** There is a duplicate in `processors/`.  
  **Action:** Make `shared_tools/processors/batch_text_extractor_enhanced_prerefactor.py` the canonical version.  
  **Next:** Remove or archive the duplicate in `processors/` and update all imports to use the `shared_tools` version.

#### 2. `shared_tools/processors/batch_nonpdf_extractor_enhanced.py`
- **Current path management:** Uses `os.makedirs`, manual path joins for output directories.
- **Duplication:** There is a duplicate in `processors/`.  
  **Action:** Make `shared_tools/processors/batch_nonpdf_extractor_enhanced.py` the canonical version.  
  **Next:** Remove or archive the duplicate in `processors/` and update all imports to use the `shared_tools` version.

#### 3. `shared_tools/processors/base_extractor.py`
- **Current path management:** Uses `Path`, manual subfolder creation for `_extracted`, `low_quality`.
- **Duplication:** There is a duplicate in `processors/`.  
  **Action:** Make `shared_tools/processors/base_extractor.py` the canonical version.  
  **Next:** Remove or archive the duplicate in `processors/` and update all imports to use the `shared_tools` version.

---

### 🟡 **Important**
#### 4. `shared_tools/cli/crypto_corpus_cli.py`
- **Current path management:** Manual/Path/str, hardcoded subfolder names.
- **Action:** Refactor to accept and use `ProjectConfig` after processor consolidation.

#### 5. `shared_tools/processors/corpus_balancer.py`
- **Current path management:** Path/manual, hardcoded subfolder names.
- **Action:** Refactor after CLI and processor consolidation.

#### 6. `shared_tools/processors/monitor_progress.py`
- **Current path management:** Path/manual mkdir for output_dir and stats files.
- **Action:** Refactor after main pipeline.

---

### 🟢 **Nice-to-have**
#### 7. Utilities, scripts, notebooks in `shared_tools` (if any)
- **Action:** Refactor as needed after core pipeline is stable.

---

## **Immediate Next Step**

**1. List and Consolidate Duplicates in `shared_tools`:**
- Only keep and work with:
  - `shared_tools/processors/batch_text_extractor_enhanced_prerefactor.py`
  - `shared_tools/processors/batch_nonpdf_extractor_enhanced.py`
  - `shared_tools/processors/base_extractor.py`
- Remove/archive the corresponding files in `processors/` (outside `shared_tools`).
- Update all imports in `shared_tools` to use the canonical versions.

---

## **Summary Table (shared_tools only)**

| File/Module                                                      | Path Management         | Duplication? | Action                                  |
|------------------------------------------------------------------|------------------------|--------------|------------------------------------------|
| shared_tools/processors/batch_text_extractor_enhanced_prerefactor.py | os.makedirs/manual     | Yes          | Canonical, remove other, update imports  |
| shared_tools/processors/batch_nonpdf_extractor_enhanced.py       | os.makedirs/manual     | Yes          | Canonical, remove other, update imports  |
| shared_tools/processors/base_extractor.py                        | Path/manual mkdir      | Yes          | Canonical, remove other, update imports  |
| shared_tools/cli/crypto_corpus_cli.py                            | Manual/Path/str        | No           | Refactor after above                     |
| shared_tools/processors/corpus_balancer.py                       | Path/manual            | No           | Refactor after above                     |
| shared_tools/processors/monitor_progress.py                      | Path/manual mkdir      | No           | Refactor after above                     |

---

**Would you like to proceed with the duplicate removal and import update now, or review the list of affected imports first?**

---
2024-05-28: ProjectConfig Integration Milestone
- ProjectConfig integrated into shared_tools/processors/batch_text_extractor_enhanced_prerefactor.py.
- New --project-config argument allows YAML-based config for all paths.
- Maintains backward compatibility: --input-dir/--output-dir still supported if --project-config is not provided.
- All path management now routed through ProjectConfig when available.
- No breaking changes for existing CLI or scripts.
- This is the first step in a phased, incremental rollout of ProjectConfig across all pipeline modules.
- Next: Test thoroughly, then repeat for other critical processors and CLI entry points.

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
2024-06-01: Extractor Integration Complete
- PDF and non-PDF extractors tested in both legacy CLI and ProjectConfig modes.
- All outputs quality checked and confirmed ready for downstream modules.
- This completes the extractor integration phase of the new architecture.
- **Current limitations:**
    - ProjectConfig only supports standard directory structure; arbitrary input/output path support is a future enhancement.
- **Would-be-nice future features:**
    - Arbitrary input/output directory support in ProjectConfig
    - YAML schema validation and error reporting
    - Hot-reloading of config files
    - Per-domain config overrides
    - Automated CLI test harness
- **Next steps:**
    - Full pipeline integration
    - Corpus manager and balancer automation
    - Feedback loop implementation
    - Begin planning for advanced config and monitoring features

---
2024-06-01: Full System Scope Update
- ProjectConfig is now the canonical path/config manager for all pipeline modules.
- PDF and non-PDF extractors use new production-grade APIs, supporting both ProjectConfig and legacy CLI modes.
- Multiprocessing is robust and Windows-safe (no local classes, all worker args pickleable).
- CLI orchestrates the pipeline using the new extractor APIs, with clear error handling and logging.
- Extractors recursively process all files in input directories and subfolders, sorting outputs into correct subfolders.
- Quality checks confirm output completeness, metadata normalization, and correct directory structure.
- Error handling covers missing input dirs, file processing errors, and temp file cleanup (with known Windows PermissionError edge case).
- Next: Integrate corpus manager and balancer, automate full pipeline, and begin work on feedback loop and monitoring features.

---
2025-06-01: ProjectConfig-Based Collector Integration (ArxivCollector)
- ArxivCollector now supports ProjectConfig as well as legacy path mode.
- Test run confirmed correct output structure: domain/content-type subfolders, valid PDF download, and metadata.
- Logging encountered UnicodeEncodeError for non-ASCII author names; does not affect data or output files.
- All outputs present and valid; ready to extend pattern to other collectors.
- Next: Continue incremental rollout and address logging encoding for full Unicode support.

## [2025-06-02] SciDB Collector Modernization

- Fully migrated SciDB DOI collection to enhanced_client.py + enhanced_scidb_collector.py.
- New logic: requests-based download first, Selenium fallback, robust metadata extraction, normalized filenames.
- Successfully tested on DOI 10.1111/cyt.12104 (HTML-only download succeeded).
- Deprecated collect_annas_scidb_search.py; all new SciDB collection should use the new pipeline.
- Improved logging and provenance for all downloads.

## Unified Configuration System (2024-03-19)

### Overview
The system now uses a single master configuration file (`master_config.yaml`) to control the entire pipeline from collection to processing. This unified approach provides several benefits:
- Centralized control of all components
- Consistent configuration across collectors and extractors
- Easy to modify and maintain
- Backward compatibility with legacy systems

### Configuration Structure (Updated 2024-03-XX)

### Directory Structure
```
data/
├── test/
│   ├── raw_data/
│   │   ├── crypto_derivatives/
│   │   │   ├── papers/
│   │   │   └── code/
│   │   ├── high_frequency_trading/
│   │   │   ├── papers/
│   │   │   └── code/
│   │   └── ...
│   ├── extracted/
│   │   ├── crypto_derivatives/
│   │   │   ├── papers/
│   │   │   │   ├── high_quality/
│   │   │   │   └── low_quality/
│   │   │   └── code/
│   │   └── ...
│   ├── processed/
│   │   ├── crypto_derivatives/
│   │   │   ├── papers/
│   │   │   │   ├── quality_checked/
│   │   │   │   └── balanced/
│   │   │   └── code/
│   │   └── ...
│   ├── reports/
│   │   ├── crypto_derivatives/
│   │   │   ├── quality/
│   │   │   └── balance/
│   │   └── ...
│   └── logs/
│       ├── collectors/
│       ├── extractors/
│       └── processors/
│
└── production/
    ├── raw_data/
    │   ├── crypto_derivatives/
    │   │   ├── papers/
    │   │   └── code/
    │   ├── high_frequency_trading/
    │   │   ├── papers/
    │   │   └── code/
    │   └── ...
    ├── extracted/
    │   ├── crypto_derivatives/
    │   │   ├── papers/
    │   │   │   ├── high_quality/
    │   │   │   └── low_quality/
    │   │   └── code/
    │   └── ...
    ├── processed/
    │   ├── crypto_derivatives/
    │   │   ├── papers/
    │   │   │   ├── quality_checked/
    │   │   │   └── balanced/
    │   │   └── code/
    │   └── ...
    ├── reports/
    │   ├── crypto_derivatives/
    │   │   ├── quality/
    │   │   └── balance/
    │   └── ...
    └── logs/
        ├── collectors/
        ├── extractors/
        └── processors/

cache/
├── test/
│   ├── crypto_derivatives/
│   │   ├── papers/
│   │   └── code/
│   └── ...
└── production/
    ├── crypto_derivatives/
    │   ├── papers/
    │   └── code/
    └── ...
```

### Key Features
1. **Domain-Based Organization**: All content is organized by domain first, then by content type
2. **Quality-Based Sorting**: Extracted content is sorted into high_quality and low_quality subdirectories
3. **Processing Stages**: Processed content is organized by processing stage (quality_checked, balanced)
4. **Report Organization**: Reports are organized by domain and report type
5. **Cache Structure**: Cache follows the same domain-based organization for efficient retrieval

### Implementation Status
- [x] Master config file structure defined
- [x] Main CLI updated to support new config
- [x] Backward compatibility maintained
- [ ] All collectors updated to use new config
- [ ] All extractors updated to use new config
- [ ] Documentation updated

### Next Steps
1. Update all collectors to use the new configuration system
2. Update all extractors to use the new configuration system
3. Add validation for configuration values
4. Add configuration migration tools for legacy systems
5. Update documentation with configuration examples

## [2024-03-19] Processor Updates and Configuration Integration

### Overview
We have completed a comprehensive update of all processors to work with the new master configuration system while maintaining backward compatibility. This update ensures a unified approach to configuration management across the entire pipeline.

### Updated Processors
1. **QualityControl Processor**
   - Now checks for `processors.quality_control` in master config
   - Falls back to legacy `quality_control` path if not found
   - Maintains compatibility with old configurations
   - Passes configs to sub-processors (MachineTranslationDetector, LanguageConfidenceDetector, CorruptionDetector)

2. **ChartImageExtractor**
   - Updated to use `processors.specialized.charts` path
   - Falls back to `chart_image_extractor` for legacy support
   - Enhanced default config with processing parameters
   - Improved image extraction and validation

3. **FinancialSymbolProcessor**
   - Now uses `processors.specialized.symbols` path
   - Falls back to `financial_symbol_processor` for legacy support
   - Removed file-based config loading for direct config usage
   - Enhanced symbol processing and validation

4. **DomainClassifier**
   - Updated to use `processors.domain_classifier` path
   - Falls back to `domain_classifier` for legacy support
   - Maintains fallback for DOMAINS configuration
   - Improved domain classification accuracy

### Configuration Structure
```yaml
processors:
  quality_control:
    enabled: true
    checks:
      language:
        min_confidence: 0.8
        target_languages: ["en"]
      corruption:
        min_confidence: 0.7
        checks:
          encoding_errors: true
          garbled_text: true
      duplication:
        min_similarity: 0.85
      translation:
        min_confidence: 0.9
        patterns: ["machine translation", "auto-translated"]
    processing:
      max_workers: 4
      batch_size: 10
      timeout: 300

  specialized:
    charts:
      enabled: true
      dpi: 300
      ocr_enabled: true
      save_images: true
      processing:
        max_workers: 2
        batch_size: 5
        timeout: 150

    symbols:
      enabled: true
      preserve_case: true
      preserve_spacing: true
      validate_tickers: true
      processing:
        max_workers: 2
        batch_size: 5
        timeout: 150

  domain_classifier:
    enabled: true
    min_confidence: 0.7
    domains:
      - crypto_derivatives
      - high_frequency_trading
    processing:
      max_workers: 2
      batch_size: 10
      timeout: 300
```

### Testing Plan

#### 1. Collector Testing
```python
# Test each collector with both new and legacy configs
def test_collector_config_compatibility():
    # Test with master config
    collector = Collector(project_config=master_config)
    results = collector.collect()
    assert results.success
    
    # Test with legacy config
    collector = Collector(config_path="legacy_config.json")
    results = collector.collect()
    assert results.success
```

#### 2. Processor Testing
```python
# Test each processor with both new and legacy configs
def test_processor_config_compatibility():
    # Test with master config
    processor = Processor(project_config=master_config)
    results = processor.process()
    assert results.success
    
    # Test with legacy config
    processor = Processor(config_path="legacy_config.json")
    results = processor.process()
    assert results.success
```

#### 3. Integration Testing
```python
# Test full pipeline with master config
def test_pipeline_integration():
    pipeline = Pipeline(project_config=master_config)
    results = pipeline.run()
    assert results.success
    assert results.quality_metrics.meets_threshold
```

### Test Cases

1. **Configuration Loading**
   - Test loading from master config
   - Test loading from legacy config
   - Test fallback behavior
   - Test invalid config handling

2. **Processor Functionality**
   - Test each processor with valid inputs
   - Test error handling with invalid inputs
   - Test processing parameters (batch size, workers, timeout)
   - Test output validation

3. **Integration Tests**
   - Test collector → processor pipeline
   - Test multiple processors in sequence
   - Test error propagation
   - Test recovery from failures

4. **Performance Tests**
   - Test with large input sets
   - Test concurrent processing
   - Test memory usage
   - Test processing speed

### Next Steps
1. Implement automated test suite
2. Add monitoring and metrics collection
3. Enhance error reporting and recovery
4. Optimize performance based on test results

## Test Architecture

### Test Categories
1. **Unit Tests**
   - Test individual components in isolation
   - No external dependencies
   - Fast execution
   - Examples: collector initialization, domain determination

2. **Integration Tests**
   - Test real-world functionality
   - Marked with `@pytest.mark.integration`
   - Test actual downloads and file operations
   - Examples: DOI collection, file validation, metadata generation

### Test Configuration
- Uses `test_config.yaml` for test environment
- Creates isolated test directories
- Cleans up after test execution

### Test Coverage
- Collector initialization
- Domain directory structure
- DOI search functionality
- Domain classification
- File validation
- Metadata generation
- Error handling
- Cleanup procedures
