# Corpus Balancer Integration Guide

## Overview

The Corpus Balancer module integrates seamlessly with your existing CryptoFinanceCorpusBuilder pipeline, providing comprehensive analysis and rebalancing capabilities for your crypto-finance text corpus.

## Architecture Integration

### Current System Integration Points

The Corpus Balancer integrates with your existing architecture at several key points:

1. **CLI Integration**: Extends `crypto_corpus_cli.py` with new commands
2. **Configuration System**: Uses existing domain configuration from `domain_utils.py`
3. **Metadata Processing**: Works with JSON metadata from existing extractors
4. **Quality Metrics**: Leverages quality scores from existing quality control modules
5. **Logging System**: Uses the same logging infrastructure

### Directory Structure

```
corpusbuilder/
├── processors/
│   ├── corpus_balancer.py          # Core balancer module
│   ├── base_extractor.py           # Existing - unchanged
│   └── ...
├── config/
│   ├── balancer_config.py          # New configuration module
│   └── domain_config.py            # Existing - used by balancer
├── cli/
│   └── crypto_corpus_cli.py        # Extended with balancer commands
└── tests/
    └── test_corpus_balancer.py     # Comprehensive test suite
```

## Installation & Setup

### 1. Add Dependencies

Add these to your `requirements.txt`:

```
plotly>=5.0.0
seaborn>=0.11.0
scipy>=1.7.0
```

### 2. Install Dependencies

```bash
pip install plotly seaborn scipy
```

### 3. Verify Integration

Run the test suite to ensure everything is working:

```bash
python -m pytest tests/test_corpus_balancer.py -v
```

## Usage Examples

### Basic Analysis

```bash
# Analyze corpus balance
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli analyze-balance \
    --corpus-dir /path/to/your/corpus \
    --output-dir ./balance_reports

# Analyze without generating dashboard (faster)
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli analyze-balance \
    --corpus-dir /path/to/your/corpus \
    --output-dir ./balance_reports \
    --no-dashboard

# Force refresh analysis (ignore cache)
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli analyze-balance \
    --corpus-dir /path/to/your/corpus \
    --force-refresh
```

### Rebalancing Operations

```bash
# Create rebalancing plan (dry run)
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli rebalance \
    --corpus-dir /path/to/your/corpus \
    --strategy quality_weighted \
    --output-dir ./rebalance_reports

# Execute rebalancing plan
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli rebalance \
    --corpus-dir /path/to/your/corpus \
    --strategy quality_weighted \
    --execute \
    --output-dir ./rebalance_reports

# Try different strategies
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli rebalance \
    --corpus-dir /path/to/your/corpus \
    --strategy stratified

python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli rebalance \
    --corpus-dir /path/to/your/corpus \
    --strategy synthetic
```

### Programmatic Usage

```python
from CryptoFinanceCorpusBuilder.processors.corpus_balancer import (
    CorpusAnalyzer, CorpusRebalancer, CorpusVisualizer
)
from CryptoFinanceCorpusBuilder.config.balancer_config import BalancerConfig

# Initialize with custom configuration
config = BalancerConfig('path/to/custom_config.json')
analyzer = CorpusAnalyzer('/path/to/corpus', config.get_balance_thresholds())

# Run analysis
results = analyzer.analyze_corpus_balance()

# Check for critical imbalances
critical_issues = results['imbalance_detection']['critical']
if critical_issues:
    print("Critical imbalances found:")
    for issue in critical_issues:
        print(f"  - {issue}")

# Create rebalancing plan
rebalancer = CorpusRebalancer(analyzer)
plan = rebalancer.create_rebalancing_plan(results, 'quality_weighted')

# Execute plan (dry run first)
execution_results = rebalancer.execute_rebalancing_plan(plan, dry_run=True)
print(f"Actions planned: {len(execution_results['actions_completed'])}")

# Generate visualizations
visualizer = CorpusVisualizer('./reports')
dashboard_path = visualizer.create_balance_dashboard(results)
report_path = visualizer.create_balance_report(results, plan)

print(f"Dashboard: {dashboard_path}")
print(f"Report: {report_path}")
```

## Configuration

### Default Configuration

The system uses sensible defaults for crypto-finance corpora:

```python
{
    'balance_thresholds': {
        'entropy_min': 2.0,        # Minimum entropy for balanced corpus
        'gini_max': 0.7,           # Maximum inequality (Gini coefficient)
        'ratio_max': 10.0,         # Maximum class imbalance ratio
        'min_samples': 30          # Minimum samples per domain
    },
    'domain_balance': {
        'crypto_derivatives': {
            'priority': 'high',
            'target_weight': 0.2,   # 20% of corpus
            'min_documents': 100
        },
        # ... other domains
    }
}
```

### Custom Configuration

Create a custom configuration file:

```python
# Create default config file
from CryptoFinanceCorpusBuilder.config.balancer_config import create_default_config_file
create_default_config_file('./my_balancer_config.json')

# Edit the file to customize thresholds, then load it
config = BalancerConfig('./my_balancer_config.json')
```

Example custom configuration:

```json
{
    "balance_thresholds": {
        "entropy_min": 2.5,
        "gini_max": 0.6,
        "min_samples": 50
    },
    "domain_balance": {
        "crypto_derivatives": {
            "priority": "critical",
            "target_weight": 0.3,
            "min_documents": 150
        }
    }
}
```

## Integration with Existing Workflow

### 1. After Data Collection

```bash
# Collect data (existing workflow)
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect \
    --sources arxiv github quantopian \
    --output-dir ./collected_data

# Process data (existing workflow)
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli process \
    --input-dir ./collected_data \
    --output-dir ./processed_corpus

# NEW: Analyze balance
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli analyze-balance \
    --corpus-dir ./processed_corpus \
    --output-dir ./balance_reports
```

### 2. Continuous Monitoring

Set up a monitoring script that runs after each collection cycle:

```python
#!/usr/bin/env python3
"""
Continuous corpus balance monitoring script.
Run this after each data collection/processing cycle.
"""

import sys
from pathlib import Path
from CryptoFinanceCorpusBuilder.processors.corpus_balancer import CorpusAnalyzer

def monitor_corpus_balance(corpus_dir, alert_threshold=5):
    """Monitor corpus and alert if critical imbalances found."""
    analyzer = CorpusAnalyzer(corpus_dir)
    results = analyzer.analyze_corpus_balance()
    
    # Check for critical issues
    critical_issues = results['imbalance_detection']['critical']
    warning_issues = results['imbalance_detection']['warning']
    
    if critical_issues:
        print(f"🚨 CRITICAL: {len(critical_issues)} balance issues found")
        for issue in critical_issues:
            print(f"   - {issue}")
        return 2  # Critical
    
    elif len(warning_issues) >= alert_threshold:
        print(f"⚠️  WARNING: {len(warning_issues)} balance warnings")
        for issue in warning_issues[:3]:  # Show first 3
            print(f"   - {issue}")
        return 1  # Warning
    
    else:
        print("✅ Corpus balance looks good")
        return 0  # OK

if __name__ == "__main__":
    corpus_dir = sys.argv[1] if len(sys.argv) > 1 else "./corpus"
    exit_code = monitor_corpus_balance(corpus_dir)
    sys.exit(exit_code)
```

### 3. Automated Rebalancing

Create a rebalancing automation script:

```python
#!/usr/bin/env python3
"""
Automated corpus rebalancing script.
"""

import logging
from CryptoFinanceCorpusBuilder.processors.corpus_balancer import (
    CorpusAnalyzer, CorpusRebalancer
)

def auto_rebalance(corpus_dir, strategy='quality_weighted', execute=False):
    """Automatically rebalance corpus if needed."""
    
    # Analyze current state
    analyzer = CorpusAnalyzer(corpus_dir)
    results = analyzer.analyze_corpus_balance()
    
    # Check if rebalancing is needed
    critical_issues = results['imbalance_detection']['critical']
    domain_entropy = results['domain_analysis']['entropy']
    
    if not critical_issues and domain_entropy > 2.0:
        logging.info("No rebalancing needed")
        return
    
    # Create and execute rebalancing plan
    rebalancer = CorpusRebalancer(analyzer)
    plan = rebalancer.create_rebalancing_plan(results, strategy)
    
    logging.info(f"Created rebalancing plan with {len(plan['actions'])} actions")
    
    if execute:
        execution_results = rebalancer.execute_rebalancing_plan(plan, dry_run=False)
        logging.info(f"Executed {len(execution_results['actions_completed'])} actions")
    else:
        logging.info("Dry run complete - use execute=True to apply changes")

if __name__ == "__main__":
    import sys
    corpus_dir = sys.argv[1] if len(sys.argv) > 1 else "./corpus"
    execute = "--execute" in sys.argv
    
    auto_rebalance(corpus_dir, execute=execute)
```

## Best Practices

### 1. Regular Analysis

- Run balance analysis after each major data collection
- Set up automated monitoring for continuous collection pipelines
- Review balance reports monthly to identify trends

### 2. Gradual Rebalancing

- Always start with dry runs to understand proposed changes
- Use quality-weighted strategy for most scenarios
- Consider synthetic generation only for severely underrepresented domains

### 3. Quality Preservation

- Set appropriate quality thresholds in configuration
- Monitor quality metrics after rebalancing
- Prefer collecting more high-quality data over synthetic generation

### 4. Domain-Specific Tuning

- Adjust target weights based on research priorities
- Set higher quality thresholds for critical domains (e.g., regulation_compliance)
- Consider domain-specific minimum sample sizes

## Troubleshooting

### Common Issues

**1. "No documents found in corpus"**
- Ensure corpus directory has `_extracted` and/or `low_quality` subdirectories
- Check that JSON metadata files exist in these directories
- Verify file permissions

**2. "High entropy warnings despite apparent balance"**
- Check for many small domains vs. few large ones
- Review domain classification accuracy
- Consider consolidating related domains

**3. "Rebalancing plan has no actions"**
- Corpus may already be well-balanced
- Check if thresholds are too lenient
- Review minimum sample size requirements

**4. "Memory issues with large corpora"**
- Process in batches using pandas chunking
- Increase system memory or use streaming analysis
- Consider sampling for initial analysis

### Debugging

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Your analysis code here
```

Check intermediate results:

```python
analyzer = CorpusAnalyzer('/path/to/corpus')
df = analyzer._load_corpus_metadata()
print(f"Loaded {len(df)} documents")
print(df['domain'].value_counts())
```

## Performance Considerations

### Large Corpora (>100K documents)

- Use analysis caching (enabled by default)
- Consider sampling for exploratory analysis
- Run rebalancing operations during off-peak hours

### Memory Optimization

- Process domains separately for very large corpora
- Use chunked processing for visualization generation
- Monitor memory usage during execution

### Parallel Processing

The system supports parallel processing for:
- Metadata loading and analysis
- Visualization generation  
- Rebalancing operations

Configure worker processes:

```python
analyzer = CorpusAnalyzer(corpus_dir, config={
    'parallel_workers': 8,  # Adjust based on your system
    'chunk_size': 10000     # Documents per chunk
})
```

## Future Enhancements

The modular architecture supports future enhancements:

1. **Real-time Monitoring**: WebSocket-based live dashboard
2. **Advanced Strategies**: ML-based rebalancing optimization
3. **Quality Prediction**: Automated quality scoring for new documents
4. **Multi-corpus Analysis**: Cross-corpus balance comparison
5. **API Integration**: REST API for programmatic access

## Support

For issues or questions:

1. Check the test suite for examples: `tests/test_corpus_balancer.py`
2. Review configuration options in `config/balancer_config.py`
3. Enable debug logging for detailed diagnostics
4. Consider the integration patterns in this guide


Feedback on Corpus Balancer Integration
Thank you for the excellent corpus balancer implementation! After reviewing the code and your integration notes, here's my comprehensive feedback:
Responses to Your Questions
1. Balancer Operation Mode
Answer: Report and Recommend Only ✅

The balancer should NEVER automatically move/delete files
Focus on analysis, reporting, and actionable recommendations
Provide detailed plans that humans can review and execute manually
Include dry-run modes for all operations

2. Processing Mode
Answer: Both Full Corpus + Incremental Support

Primary mode: Full corpus analysis for comprehensive insights
Secondary mode: Incremental updates for new file additions
Include timestamp tracking for efficient incremental processing

3. Ambiguous Domain/File Type Handling
Answer: Graceful Degradation with Reporting

Create an "unknown" category for ambiguous cases
Log all classification failures with context
Provide manual review lists for human classification
Use confidence scores and suggest likely domains

Critical Integration Points to Address
1. Metadata Field Mapping 🔧
python# Need to verify these fields exist in ALL extractors:
REQUIRED_FIELDS = [
    'domain',           # ✅ Exists in most extractors
    'file_type',        # ✅ Exists 
    'quality_flag',     # ⚠️  Sometimes called 'quality_metrics.quality_flag'
    'token_count',      # ⚠️  Sometimes nested in metadata
    'extraction_date',  # ✅ Exists
    'language',         # ⚠️  Sometimes in 'quality_metrics.language_confidence.language'
]
2. Configuration Synchronization ⚙️
The domain definitions need to be perfectly aligned:

domain_config.py defines 8 domains with allocations
balancer_config.py has same 8 domains with different weights
Action Required: Create validation script to ensure consistency

3. CLI Integration Conflicts 🚨
Potential command conflicts to resolve:
bash# Existing CLI commands that might conflict:
python -m crypto_corpus_cli report --corpus-dir ... --output ...

# New balancer commands:
python -m crypto_corpus_cli analyze --corpus-dir ...
python -m crypto_corpus_cli rebalance --corpus-dir ...
Specific Code Review Requests for Dev
A. Placeholder Review Needed 📝
Please review these files for hardcoded placeholders:

corpus_balancer.py - Line ~200-300 range

Check _merge_chunk_results() method
Verify domain mapping logic
Confirm output directory structures


balancer_config.py - Domain weight calculations

Verify the 8 domains match exactly with domain_config.py
Check allocation percentages sum to 1.0
Confirm file type ratios are realistic


CLI Integration - crypto_corpus_cli.py

Search for "TODO" or "PLACEHOLDER" comments
Verify argument parsing doesn't conflict
Check import paths are correct



B. Critical Integration Tests Needed 🧪
python# Test these scenarios:
1. Empty corpus directory
2. Missing metadata fields  
3. Corrupt JSON files
4. Very large corpus (>10k files)
5. Mixed extraction methods (PDF + non-PDF)
Recommended Implementation Plan
Phase 1: Safe Integration (Week 1)

Add balancer as optional CLI command
Run in report-only mode
Test with small corpus subset
Validate metadata field mapping

Phase 2: Full Validation (Week 2)

Test with full corpus
Verify performance with large datasets
Validate all visualization outputs
Test CLI integration thoroughly

Phase 3: Production Ready (Week 3)

Add comprehensive error handling
Create user documentation
Add integration tests
Performance optimization if needed

Specific Technical Concerns
1. Memory Usage 💾
For large corpora (>50k files), consider:
python# Current approach loads all metadata at once
# May need streaming approach for very large corpora
def _load_corpus_metadata_streaming(self, batch_size=1000):
    # Process in chunks instead of loading everything
2. File Path Handling 📁
Ensure cross-platform compatibility:
python# Windows vs Unix path handling
# Relative vs absolute paths in metadata
3. Error Recovery 🔄
Add robust error handling for:

Corrupt JSON metadata files
Missing referenced files
Network timeouts for visualizations
Disk space issues

Questions for Dev Review

Are all file paths in the balancer using our existing domain_utils.py functions?
Does the visualization component handle headless server environments?
Are the quality weight calculations compatible with our existing quality metrics?
Will the rebalancing recommendations work with our current directory structure?
Have you tested the balancer with files from ALL our collectors (arXiv, GitHub, BitMEX, etc.)?

Final Recommendation
The balancer framework is excellent and ready for integration with these modifications:

✅ Keep as report/recommend only
✅ Add incremental processing support
✅ Implement graceful handling of ambiguous classifications
⚠️ Critical: Dev must review all placeholders and test with real corpus data
⚠️ Critical: Verify metadata field consistency across ALL extractors

Next Steps: Please perform the placeholder review and run integration tests with a sample of our actual corpus before merging.

🛠️ If Any Changes Are Required to Fit Our Project
If any extractor/collector is missing a required metadata field:
Do not change the extractor. Instead, handle missing fields in the normalizer with sensible defaults and log a warning.
If config weights do not sum to 1.0:
Document the rationale (e.g., rare domains) in the config validator output, but do not force a change unless it causes analysis errors.
If CLI command names conflict:
Use unique prefixes (e.g., balance-analyze, balance-report) and document them in the CLI help.
✅ Final Implementation Path: Phase 1 (Foundation & Validation)
Day 1: Metadata Audit & Normalization
Create metadata_validator.py
Scans all JSON files in _extracted/ and low_quality/
Reports missing/inconsistent fields
Generates a field mapping report
Create metadata_normalizer.py
Extracts nested quality metrics (e.g., corruption_score, language)
Standardizes field names across all extractors
Handles missing fields with sensible defaults and logs warnings
Add Integration Tests
Use real outputs from each collector type
Verify field consistency post-normalization
Day 2: Configuration Synchronization
Create config_validator.py
Compares domain_config.py vs balancer_config.py
Verifies weight sums and domain consistency
Flags mismatches and provides recommendations
Fix Weight Discrepancy (if needed)
Confirm if regulation_compliance: 0.02 is intentional
Adjust or document as appropriate
Create Unified Domain Reference
Single source of truth for domain definitions
Auto-sync mechanism or validation warnings
Day 3: CLI Integration Safety
CLI Command Audit
Map all existing commands vs new balancer commands
Identify and resolve conflicts (rename if needed)
Backward Compatibility Testing
Ensure all existing CLI functions are unchanged
Test all command combinations
Verify help text and documentation
Error Handling Enhancement
Add graceful degradation for missing dependencies (e.g., Plotly, Matplotlib)
Provide clear error messages for common issues
📝 Next Steps (Preview of Phase 2 and Beyond)
Implement streaming metadata loader and chunked analysis
Add robust error recovery and reporting
Standardize path handling and visualization fallbacks
Expand integration and performance testing
Complete documentation and production readiness

1. Progress Log Entry
Progress Log — Metadata Normalization & Validation
Date: 2024-05-26
Time: 15:45 UTC
Completed:
Developed and tested metadata_validator.py and metadata_normalizer.py utilities.
Successfully validated and normalized metadata for both non-PDF and PDF files in test and production-like directories.
All required fields (domain, file_type, quality_flag, token_count, extraction_date, language) are now present at the top level in all metadata files.
System is ready for robust downstream analytics and balancing.
2. Automation Plan for Final Timeline
Goal:
Ensure all new and existing metadata is always normalized and validated before any downstream processing (balancer, analytics, etc.).
Options for Automation:
A. As a Queued Task:
Integrate normalization/validation as a pre-processing step in your main pipeline (e.g., before running the balancer or analytics).
Use a task queue (e.g., Celery, RQ) or a simple job scheduler (e.g., cron, Windows Task Scheduler) to run normalization on a schedule or trigger.
B. As a CLI Pipeline Command:
Add a new CLI command (e.g., python crypto_corpus_cli.py normalize-metadata --corpus-dir ...) that runs normalization and validation on demand or as part of a batch pipeline.
C. As a Hook in Data Ingestion:
Automatically run normalization/validation whenever new files are added or extracted (e.g., as a post-processing hook in your collector/extractor pipeline).
3. Recommended Structure for Automation (Best Practice for Your System)
Given your modular, CLI-driven, and batch-oriented architecture, the best structure is:
Add a CLI command to your main corpus CLI (e.g., normalize-metadata).
This command will:
Run the normalizer on all relevant directories (all collectors, all _extracted and low_quality subdirs).
Optionally, run the validator and print a summary report.
Be callable as a standalone step or as part of a batch pipeline (e.g., before running the balancer).
Example CLI Integration:
# In your main CLI (crypto_corpus_cli.py)
def normalize_metadata_command(args):
    from CryptoFinanceCorpusBuilder.utils.metadata_normalizer import main as normalize_main
    normalize_main(args.corpus_dir)
    from CryptoFinanceCorpusBuilder.utils.metadata_validator import main as validate_main
    validate_main(args.corpus_dir)

# Add to argparse:
normalize_parser = subparsers.add_parser('normalize-metadata', help='Normalize and validate all metadata')
normalize_parser.add_argument('--corpus-dir', required=True, help='Path to corpus root directory')
normalize_parser.set_defaults(func=normalize_metadata_command)

Usage:
python crypto_corpus_cli.py normalize-metadata --corpus-dir data/test_collect/full_pipeline_short/crypto_derivatives_extracted
This approach:
Keeps your workflow modular and explicit.
Allows for easy automation (can be called from scripts, cron, or as a pipeline step).
Ensures normalization/validation is always performed before analytics.

Summary Table
| Step | When to Run | How to Automate |
|---------------------|---------------------------|--------------------------------|
| Normalize/Validate | Before analytics/balancer | CLI command, scheduled job, or pipeline hook |

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

### 1. **Configuration Synchronization** WE ARE HERE!!
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

FROM HERE IT WENT SOUTH

**You are now ready to move on to configuration synchronization and corpus balancing!**  
If you want a more detailed breakdown or a project management checklist, just let me know!


Here’s a concise **progress log** and **next scheduled steps** for your project:

---

## 📝 **Progress Log**

### 1. **Extractor & Metadata Pipeline**
- **PDF and non-PDF extractors** are robust, modular, and production-ready.
- **Metadata normalization and validation** are fully automated and accessible via CLI.
- **Auto-normalization** is integrated into extractors with a default-on flag, ensuring all output is standardized for downstream analytics.

### 2. **Testing & Validation**
- **Batch extraction** tested on both PDF and non-PDF files.
- **Output directories** and **metadata files** were checked for required fields and structure.
- **Corpus validation** and **summary tools** were run, confirming correct directory structure and file recognition.

### 3. **Configuration Management (Phase 2)**
- **Audit of all config usage**: Identified hardcoded vs. centralized configs.
- **Config loading refactored** in low-risk components (balancer, utils, analytics) to:
  - Load from file if available and valid.
  - Fallback to hardcoded defaults if not.
  - Log all fallback events for auditability.
- **Config validation** added before applying any config.
- **Testing**: Created sample config and metadata files, validated loading, fallback, and summary logic.

### 4. **Boss/Stakeholder Approvals**
- All steps, risk assessments, and implementation strategies were reviewed and approved.
- Mandatory logging, validation, and documentation requirements are in place.

---

## ⏭️ **Next Scheduled Steps**

1. **Complete Documentation**
   - Update docs to reflect new config loading patterns, fallback logic, and CLI usage.

2. **Milestone Review**
   - Report back to stakeholders with:
     - Updated file/component list
     - Example logs of fallback events
     - Test results (validation, summary, fallback)
     - Documentation updates

3. **Extractor Refactor (Phase 3)**
   - After milestone review, begin refactoring extractors to use centralized configs.
   - Maintain all fallback and validation logic.
   - Test thoroughly in non-production before rollout.

4. **Further Automation & Balancer Integration**
   - Integrate config-driven logic into corpus balancer and analytics modules.
   - Schedule regular normalization and validation runs.

5. **Ongoing:**
   - Monitor logs for fallback events.
   - Continue incremental migration of any remaining hardcoded configs.

---

**You are ready for milestone review and documentation. Once approved, you’ll proceed to extractor refactoring and full config centralization.**

Here’s a log entry you can use to document the **Config Sync Phase** progress. This summary is designed so that any developer can pick up where you left off:

---

## **Config Sync Phase: Progress Log**

**Date:** 2025-05-27  
**Project:** CryptoFinanceCorpusBuilder  
**Phase:** Config Synchronization & Validation

---

### **Summary of Actions Completed**

#### **1. Test Corpus Structure**
- Created and used a test corpus with both PDF and non-PDF files.
- Ran extractors to generate metadata and normalized outputs.

#### **2. Domain Config Wrapper**
- Implemented a `DomainConfig` wrapper in `domain_utils.py` for robust, backward-compatible config loading.
- Ensured all extractors use the wrapper for domain info.

#### **3. Balancer Test**
- Ran the corpus balancer on both PDF and non-PDF test corpora.
- Confirmed balancer works with the new config wrapper and produces expected reports.

#### **4. Config Validator Script**
- Created `utils/config_validator.py` to check consistency between `domain_config.py` and `balancer_config.py`.
- Validator checks:
  - All domains in balancer config exist in domain config (balancer is reference).
  - Allocations (`allocation` vs `target_weight`) match.
  - Sums of allocations/weights are exactly 1.0.
  - Domain names are valid Python identifiers.
  - No duplicate domains within each config.
  - Outputs both console and JSON reports.

#### **5. CLI Integration**
- Added `validate-config` command to the main CLI (`crypto_corpus_cli.py`).
- Usage:
  ```powershell
  python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli validate-config --json ./balance_reports/config_validation_report.json
  ```

#### **6. Config Alignment**
- Used project documentation (`README_collectors.md`) as the source of truth for domain allocations.
- Updated `balancer_config.py` so all `target_weight` values match `domain_config.py` and the intended allocations.
- Re-ran validator: all domains match, weights sum to 1.0, no errors or warnings.

#### **7. Linter and Code Quality**
- Fixed linter errors in all new/modified files.
- Improved duplicate domain check logic in the validator.

---

### **Files Created/Modified**

- `utils/config_validator.py` — New config validation script.
- `cli/crypto_corpus_cli.py` — Added `validate-config` CLI command.
- `config/balancer_config.py` — Updated domain weights to match project targets.
- `utils/domain_utils.py` — Added/updated `DomainConfig` wrapper.
- `config/domain_config.py` — (No changes needed; already matched intended allocations.)

---

### **Tests/Validations Performed**

- Ran extractors and balancer on test corpus (PDF and non-PDF).
- Ran config validator (console and JSON output).
- Confirmed all domains and allocations are now fully aligned.
- Confirmed CLI integration for config validation.

---

### **Next Steps**

1. **Implement config sync CLI command** (`sync-config`) to auto-fix mismatches if they ever occur.
2. **Full integration test:** Run the entire pipeline (collect, extract, normalize, balance) on a real corpus.
3. **Document any further changes and update this log.**

---

**Hand-off Note:**  
All config files are now aligned and validated. The validator and CLI integration are in place.  
Any developer can continue by implementing the config sync command or running full integration tests.

---

Would you like to proceed with the config sync command implementation now?

3. What is the next step after this?
Recommended next steps:
Full Integration Test:
Run the entire pipeline (collect, extract, normalize, balance, validate, sync) on a real or large test corpus.
Confirm that all tools work together and produce the expected results.
(Optional) Implement/Enhance Rebalancing Execution:
If you want the balancer to actually move, sample, or generate data, implement the “execute” part of the rebalancing engine.
Documentation & Handoff:
Update documentation and logs so any new developer can pick up seamlessly.
(Optional) UI/Monitoring Integration:
Integrate with a dashboard or monitoring tool for real-time corpus health and balance tracking.




27.5.2025 10:17

Optimized 10-Step Release Plan
Phase 1: Foundation (Week 1-2)
1. Folder Structure + ProjectConfig
• Implement project template generator (CLI or script).
• Build and test the ProjectConfig class for path management and auto-directory creation.
2. Test Auto-Rebalance Loop (CRITICAL)
• Write unit and integration tests for the auto-rebalance command.
• Validate dry-run and execute modes, domain filtering, max-results, and logging.
• Fix any issues before proceeding.
3. Path Robustness Refactor
• Refactor all pipeline components to use ProjectConfig for all file and directory access.
• Ensure all modules validate and create directories as needed.

Phase 2: Core Validation (Week 3)
4. Pipeline Integration Tests
• Test the full pipeline: collect → extract → balance → auto-rebalance.
• Ensure all steps work together with the new path management.
5. CLI Smoke Tests
• Test all CLI commands, edge cases, and both dry-run/execute modes.
• Validate error handling and user feedback.

Phase 3: User Interface (Week 4-5)
6. Dashboard MVP
• Build a web UI for corpus monitoring, report viewing, and manual pipeline triggers.
7. Backend API
• Expose REST endpoints for all major pipeline actions to support the UI.

Phase 4: User Validation (Week 6)
8. UAT + Feedback
• Internal user testing of both CLI and UI.
• Collect feedback, iterate on UX and CLI usability.

Phase 5: Production (Week 7-8)
9. Documentation
• Update README, getting started guide, and API docs.
• Document folder structure, path management, and UI usage.
10. QA + Launch
• Final QA: security, permissions, error handling, edge cases.
• Production deployment and announcement.




Ran tool
Here is a **comprehensive, triple-checked list** of all files that need their imports updated for Batch 1 (utils and storage). This includes every direct and indirect connection, including scripts, tests, and all relevant modules.

---

## **Batch 1: Utils and Storage Import Update Report**

### **A. shared_tools/processors/**
- `deduplicator.py`
  - `from storage.corpus_manager import CorpusManager` → `from shared_tools.storage.corpus_manager import CorpusManager`
- `domain_classifier.py`
  - `from CryptoFinanceCorpusBuilder.utils.domain_utils import ...` → `from shared_tools.utils.domain_utils import ...`
- `corpus_balancer.py`
  - `from CryptoFinanceCorpusBuilder.utils.domain_utils import ...` → `from shared_tools.utils.domain_utils import ...`
  - `from CryptoFinanceCorpusBuilder.utils.extractor_utils import ...` → `from shared_tools.utils.extractor_utils import ...`
- `batch_nonpdf_extractor_enhanced.py`
  - `from CryptoFinanceCorpusBuilder.utils.extractor_utils import ...` → `from shared_tools.utils.extractor_utils import ...`
  - `from CryptoFinanceCorpusBuilder.utils.domain_utils import ...` → `from shared_tools.utils.domain_utils import ...`
  - `from CryptoFinanceCorpusBuilder.utils.metadata_normalizer import ...` → `from shared_tools.utils.metadata_normalizer import ...`
- `base_extractor.py`
  - `from CryptoFinanceCorpusBuilder.utils.extractor_utils import ...` → `from shared_tools.utils.extractor_utils import ...`
- `batch_text_extractor_enhanced_prerefactor.py`
  - `from CryptoFinanceCorpusBuilder.utils.domain_utils import ...` → `from shared_tools.utils.domain_utils import ...`
  - `from CryptoFinanceCorpusBuilder.utils.pdf_safe_open import ...` → `from shared_tools.utils.pdf_safe_open import ...`
  - `from CryptoFinanceCorpusBuilder.utils.metadata_normalizer import ...` → `from shared_tools.utils.metadata_normalizer import ...`

---

### **B. shared_tools/cli/**
- `crypto_corpus_cli.py`
  - `from CryptoFinanceCorpusBuilder.storage.corpus_manager import CorpusManager` → `from shared_tools.storage.corpus_manager import CorpusManager`
  - `from CryptoFinanceCorpusBuilder.utils.metadata_normalizer import ...` → `from shared_tools.utils.metadata_normalizer import ...`
  - `from CryptoFinanceCorpusBuilder.utils.metadata_validator import ...` → `from shared_tools.utils.metadata_validator import ...`
  - `from CryptoFinanceCorpusBuilder.utils import config_validator` → `from shared_tools.utils import config_validator`
  - `from CryptoFinanceCorpusBuilder.utils import config_sync` → `from shared_tools.utils import config_sync`
  - `from CryptoFinanceCorpusBuilder.utils.generate_corpus_report import ...` → `from shared_tools.utils.generate_corpus_report import ...`

---

### **C. tests/**
- `test_extractor_utils.py`
  - `from CryptoFinanceCorpusBuilder.utils.extractor_utils import ...` → `from shared_tools.utils.extractor_utils import ...`
- `test_quality_control_config.py`
  - `from CryptoFinanceCorpusBuilder.utils.extractor_utils import ...` → `from shared_tools.utils.extractor_utils import ...`
- `test_domain_config_wrapper.py`
  - `from CryptoFinanceCorpusBuilder.utils.domain_utils import ...` → `from shared_tools.utils.domain_utils import ...`

---

### **D. cli/**
- `crypto_corpus_cli.py` (if not already updated above)
  - Same as in shared_tools/cli/crypto_corpus_cli.py

---

### **E. processors/**
- `deduplicator.py`
  - `from storage.corpus_manager import CorpusManager` → `from shared_tools.storage.corpus_manager import CorpusManager`
- `domain_classifier.py`
  - `from CryptoFinanceCorpusBuilder.utils.domain_utils import ...` → `from shared_tools.utils.domain_utils import ...`
- `corpus_balancer.py`
  - `from CryptoFinanceCorpusBuilder.utils.domain_utils import ...` → `from shared_tools.utils.domain_utils import ...`
  - `from CryptoFinanceCorpusBuilder.utils.extractor_utils import ...` → `from shared_tools.utils.extractor_utils import ...`
- `batch_nonpdf_extractor_enhanced.py`
  - `from CryptoFinanceCorpusBuilder.utils.extractor_utils import ...` → `from shared_tools.utils.extractor_utils import ...`
  - `from CryptoFinanceCorpusBuilder.utils.domain_utils import ...` → `from shared_tools.utils.domain_utils import ...`
  - `from CryptoFinanceCorpusBuilder.utils.metadata_normalizer import ...` → `from shared_tools.utils.metadata_normalizer import ...`
- `base_extractor.py`
  - `from CryptoFinanceCorpusBuilder.utils.extractor_utils import ...` → `from shared_tools.utils.extractor_utils import ...`
- `batch_text_extractor_enhanced_prerefactor.py`
  - `from CryptoFinanceCorpusBuilder.utils.domain_utils import ...` → `from shared_tools.utils.domain_utils import ...`
  - `from CryptoFinanceCorpusBuilder.utils.pdf_safe_open import ...` → `from shared_tools.utils.pdf_safe_open import ...`
  - `from CryptoFinanceCorpusBuilder.utils.metadata_normalizer import ...` → `from shared_tools.utils.metadata_normalizer import ...`

---

### **F. scripts/**
- All scripts that import `corpus_manager` from storage:
  - Update to `from shared_tools.storage.corpus_manager import CorpusManager`

---

### **G. command_interface.py**
- Update all imports from `storage.corpus_manager` to `shared_tools.storage.corpus_manager`

---

### **H. data/test_collect/** and other test scripts
- Any test or example script that imports from `CryptoFinanceCorpusBuilder.utils` or `storage.corpus_manager` should be updated to use `shared_tools`.

---

### **I. __init__.py files**
- Check for any relative imports of utils or storage and update to use `shared_tools`.

---

## **Next Step**
**I will now proceed to implement these import changes for Batch 1 (utils and storage) in all the files listed above.**  
After this, I will prompt you to run the CLI help command to verify nothing is broken.

**If you have any additional files or folders you want checked, let me know before I start the changes.**  
Otherwise, I will proceed!


Excellent—the CLI loads and all commands are visible, which means the Batch 1 (utils and storage) import updates did **not** break the system. This is a strong indicator that the foundational shared utilities are working as intended.

---

## Next Steps: Batch 2 (Processors) — Plan & Safety Checks

### 1. **What I Will Do**
- Systematically update all imports in the `shared_tools/processors/` directory (and any other processor code that references old paths).
- Triple-check for:
  - Any remaining references to `CryptoFinanceCorpusBuilder.processors` or `CryptoFinanceCorpusBuilder.utils`
  - Any relative imports that should now use `shared_tools`
  - Any cross-processor dependencies (e.g., formula/chart/symbol extractors, quality detectors, etc.)
- Ensure all processor modules are internally consistent and compatible with the new shared structure.

### 2. **Files to be Updated (Batch 2)**
Based on your current structure and the attached files, the following files in `shared_tools/processors/` need their imports updated:
- `batch_text_extractor_enhanced_prerefactor.py`
- `finacial_symbol_processor.py`
- `deduplicator.py`
- `domain_classifier.py`
- `corpus_balancer.py`
- `batch_nonpdf_extractor_enhanced.py`
- `base_extractor.py`
- `quality_control.py`
- Any other processor modules referencing old paths

### 3. **Special Attention**
- **Cross-check all imports for:**
  - `from CryptoFinanceCorpusBuilder.processors...`
  - `from CryptoFinanceCorpusBuilder.utils...`
  - `from processors...`
  - `from utils...`
  - Any direct references to `storage`, `models`, or `config` that should now be `shared_tools`
- **Check for any missed connections to `sources/` or `storage/`** (e.g., `corpus_manager`, `cookieAuthClient`, etc.)

### 4. **Testing After Batch 2**
- After updating, you will run:
  ```
  python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli --help
  ```
  and a simple processor command (e.g., `stats` or `report`) to confirm nothing is broken.

---

## **Proceeding with Batch 2: Processors**
I will now begin updating the imports in the processor files, one by one, with careful attention to all dependencies and cross-links.

**If you have any additional processor files not listed above, please let me know now. Otherwise, I will proceed!**



### Batch 3: Collectors — **Comprehensive Import Review & Fix Plan**

#### **1. What Can Break?**
- **Relative imports** (e.g., `from .foo import bar`) can break if the file is moved or called from a different context.
- **Project-internal absolute imports** (e.g., `from CryptoFinanceCorpusBuilder.utils import ...`) must be updated to `shared_tools` if the code was moved.

---

#### **2. Full File-by-File Import Review**

Below is a **complete list of every file in `shared_tools/collectors/`**, with a summary of import issues found and what needs to be fixed:

---

#### **A. Files with Imports That Need Updating**

- **collect_annas_main_library.py**
  - Uses: `from CookieAuthClient import CookieAuthClient`
  - **Action:** Update to `from shared_tools.collectors.CookieAuthClient import CookieAuthClient`
  - Also, remove any sys.path hacks for local discovery.

- **collect_annas_scidb_search.py**
  - Uses: `from CookieAuthClient import CookieAuthClient`
  - **Action:** Update to `from shared_tools.collectors.CookieAuthClient import CookieAuthClient`
  - Remove sys.path hacks.

- **collect_general_web_corpus.py**
  - Uses: 
    - `from CryptoFinanceCorpusBuilder.sources.specific_collectors.enhanced_client import CookieAuthClient`
    - `from CryptoFinanceCorpusBuilder.config.domain_config import DOMAINS`
  - **Action:** Update to:
    - `from shared_tools.collectors.enhanced_client import CookieAuthClient`
    - `from shared_tools.config.domain_config import DOMAINS`

- **arxiv_collector.py, github_collector.py, fred_collector.py, quantopian_collector.py, new_source_collector.py**
  - All use imports like `from CryptoFinanceCorpusBuilder.sources.api_collector import ApiCollector` or similar.
  - **Action:** Update to `from shared_tools.collectors.api_collector import ApiCollector` (or `repo_collector`, `web_collector`, etc. as appropriate).

- **repo_collector.py, api_collector.py, web_collector.py**
  - Use relative imports like `from .base_collector import BaseCollector`
  - **Action:** These are correct for a package structure and should be left as-is unless you encounter runtime issues. If so, convert to absolute: `from shared_tools.collectors.base_collector import BaseCollector`.

---

#### **B. Files That Are Standalone/Utility (No Project Imports)**
- **collect_bitmex.py, collect_isda.py, CookieAuthClient.py, enhanced_client.py**
  - Only use standard/third-party imports or are self-contained.
  - **Action:** No changes needed.

---

#### **C. `__init__.py`**
- Empty, no imports.
- **Action:** No changes needed.

---

#### **3. Relative Import Check**
- All relative imports (`from .base_collector import ...`) are valid for a package structure. If you encounter issues when running as a script, use absolute imports.

---

#### **4. Next Steps**
- I will now proceed to update all imports in the above files as described.
- After the changes, I will provide a **full report** of what was changed, and you should run the CLI and a collector test to verify.

---

**Proceeding with Batch 3 import fixes now.**


Let me analyze the key differences between the two clients and create a test script. First, let me check the critical differences:

1. **Authentication Handling**:
   - Original `CookieAuthClient`: Basic cookie authentication with simple verification
   - Enhanced Client: More robust authentication with better error handling and session management
   - Risk: Low - Both use the same cookie mechanism, just with better error handling in enhanced

2. **Download Methods**:
   - Original: Direct download with basic retry
   - Enhanced: Multiple download methods (direct, iframe, link-based) with better error recovery
   - Risk: Low - Enhanced actually has more fallback options

3. **Search Capabilities**:
   - Original: Basic search with PDF filter
   - Enhanced: More search parameters (content_type, language) and better result parsing
   - Risk: Low - Enhanced adds features without breaking existing ones

4. **File Validation**:
   - Original: Basic PDF validation
   - Enhanced: More thorough validation and quality checks
   - Risk: Low - Enhanced adds more checks without removing existing ones

Here's a test script to verify the Annas collectors:



The test script will:
1. Test the enhanced client import
2. Test client initialization and authentication
3. Test the main library collector with a sample book
4. Test the SCIDB collector with a sample DOI

Regarding your concerns:

1. **Login Breaking**: The enhanced client is actually safer because:
   - It has better error handling for authentication
   - It verifies the cookie is valid before proceeding
   - It has more robust session management
   - The core authentication mechanism is the same

2. **Database Navigation**: The enhanced client doesn't change how the collectors navigate their specific databases. It only improves:
   - Error handling
   - Download reliability
   - File validation
   - Search capabilities

3. **Other Folders**: You're right about the other folders. We should:
   - Focus on completing the current task first
   - Then do a thorough audit of `scripts/` and `missing files/`
   - Create a proper inventory of all project files
   - Document which files belong to which projects

Would you like me to:
1. Run the test script to verify everything works?
2. Add more specific tests for any particular functionality?
3. Create a plan for auditing the other folders?
