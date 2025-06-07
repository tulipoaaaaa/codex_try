# Crypto-Finance Corpus Builder

This project provides a modular, extensible framework for building, managing, and analyzing a comprehensive corpus of crypto-finance documents from a variety of sources.

---

## Directory Structure

```
corpusbuilder/
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
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources arxiv github --config corpusbuilder/config/enhanced_sources.json --output-dir data/corpus_1
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
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli process --input-dir data/corpus_1 --output-dir data/corpus_1/processed --chunking-mode section --chunk-overlap 2
```

- `--chunking-mode`: Choose between `page` (default) or `section` (semantic chunking by detected headings) for PDF extraction.
- `--chunk-overlap`: Number of sentences to overlap between chunks (default: 1).

**PDF Extraction Features:**
- **Semantic (Section-Based) Chunking:** Extracts text by logical sections/headings (H1-H3, bold, all-caps, numbered, etc.) for more meaningful context, not just by page.
- **Chunk Overlap:** Preserves context across section boundaries by overlapping sentences between chunks.
- **Rich Metadata:** Each chunk includes detailed metadata (original path, language, quality flags, chunk index, section heading, etc.), fully aligned with the non-PDF pipeline.
- **Reporting:** After extraction, the CLI prints statistics on section heading extraction and average chunk size by domain, aiding quality control and analytics.

**Rationale:**
- These features ensure the PDF pipeline matches the modularity, quality control, and metadata standards of the non-PDF pipeline, supporting robust downstream analytics, deduplication, and search.

### Generating Corpus Statistics

```bash
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli stats --corpus-dir data/corpus_1
```

### Corpus Balance Monitoring & Domain Distribution

To monitor and visualize the balance of your corpus (e.g., the 60/40 crypto/traditional finance split), use the CLI report subcommand:

```bash
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli report --corpus-dir data/corpus_1 --output corpus_report.md --include-stats --include-examples
```

- **Aggregates metrics from all extracted files**
- **Tracks domain distribution and calculates the percentage split between crypto-native and traditional finance**
- **Generates a Markdown report** with tables, statistics, and sample documents
- **Optionally includes detailed statistics and example documents**

Or, to generate the report automatically after PDF extraction:

```bash
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli process --input-dir data/corpus_1 --output-dir data/corpus_1/processed --generate-report
```

- This will extract PDFs and then generate a corpus report in the output directory.

**Output:**
- Markdown file (e.g., `corpus_report.md`) with:
  - Total document and size statistics
  - Domain and source distribution tables
  - Traditional vs. crypto-native split (with percentages)
  - Token distribution by domain (if available)
  - Example documents per domain
  - Implementation details and usage recommendations

**Note:**
- This script is the recommended way to track progress toward your corpus balance targets and to generate reports for review or presentation.

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

## Critical Review & Recommendations

### Strengths
- **Modular, Extensible Architecture:** Well-organized CLI, processors, collectors, and config modules. CLI-driven workflow and flexible configuration.
- **Advanced PDF Extraction:** Semantic (section-based) chunking, chunk overlap, and rich, aligned metadata. Quality control with domain-appropriate thresholds.
- **Reporting & Analytics:** Corpus balance monitoring, automated reporting, and detailed statistics/examples.
- **Documentation:** Comprehensive README and usage examples.
- **Testing:** Canonical test suite for PDF extraction.
- **Backward Compatibility:** Non-PDF pipeline remains unaffected by PDF-specific changes.

### Weaknesses / Risks
- **Script Placement:** Some scripts were previously in less discoverable locations (now addressed).
- **Partial Automation:** No single command for end-to-end pipeline; some manual steps remain.
- **UI/Dashboard Not Yet Implemented:** No web interface or real-time monitoring for non-technical users.
- **Testing Coverage:** Edge cases and full pipeline integration not fully tested.
- **Documentation Gaps:** Some submodules lack detailed READMEs or example outputs.
- **Error Handling:** Some error messages are generic or not user-friendly; logging could be more granular.

### Recommendations
- **Broaden Integration Testing:** Use a wider variety of PDFs and domains; validate chunking, overlap, and metadata for edge cases.
- **Automate the Pipeline:** Add a "run-all" CLI command or script for collection → extraction → deduplication → analytics → reporting.
- **Improve Documentation:** Add/update module-specific READMEs and provide more example outputs/reports.
- **Expand Test Suite:** Add tests for edge cases and full pipeline integration.
- **Enhance Error Handling:** Improve error messages and logging granularity.
- **Develop a Web UI/Dashboard (Before Launch):** Build a dashboard for monitoring, reporting, and error management; expose search/filtering and notifications.
- **Continuous Integration:** Set up CI/CD for automated testing and deployment.
- **User Feedback Loop:** Collect feedback from users and reviewers to guide further improvements.

---

## Short-Term Roadmap (2024-05-25)

### Phase 1: Core Improvements
- **Robust Error Handling**
  - Implement partial content saving
  - Add detailed error logging
  - Add recovery mechanisms
  - Add progress tracking

- **Structured Output**
  - Implement unified JSON schema
  - Add content type metadata
  - Add relationship metadata
  - Improve content organization

- **Document Structure**
  - Enhance section detection
  - Add content hierarchy tracking
  - Preserve content relationships
  - Add structure metadata

### Phase 2: Content Type Extraction
- **Table Extraction**
  - Integrate camelot-py
  - Preserve table structures
  - Add table metadata
  - Maintain table relationships

- **Formula Handling**
  - Preserve LaTeX/TeX formulas
  - Add formula context
  - Implement formula metadata
  - Add formula-to-text conversion

- **Visual Content**
  - Extract charts and graphs
  - Preserve image metadata
  - Link captions to content
  - Store visual context

- **Financial Symbols**
  - Create symbol dictionary
  - Implement symbol preservation
  - Add symbol context
  - Improve OCR for symbols

### Phase 3: Quality & Performance
- **Academic Content**
  - Adjust quality thresholds
  - Add paper-specific handling
  - Improve formula detection
  - Enhance table recognition

- **Performance**
  - Add parallel processing
  - Implement content validation
  - Add progress tracking
  - Optimize memory usage

### Phase 4: Non-PDF Alignment
- **Extractor Alignment**
  - Update non-PDF extractor
  - Align metadata structures
  - Share common utilities
  - Maintain compatibility

- **Testing & Validation**
  - Update test suite
  - Add content validation
  - Verify pipeline compatibility
  - Document changes

### Implementation Notes
- All changes must maintain backward compatibility
- Quality standards must be preserved
- Pipeline integration must be seamless
- Documentation must be updated
- Tests must be comprehensive

---

## Roadmap & Next Steps

### Updated Roadmap (UI Before Launch)
1. **Integration Testing & Validation**
   - Run extraction and reporting on a broad PDF set.
   - Validate chunking, overlap, and metadata.
   - Check deduplication and analytics outputs.
2. **Downstream Integration**
   - Test end-to-end pipeline (collection → extraction → deduplication → analytics).
   - Automate extraction if not already.
   - Fix any integration issues.
3. **Documentation & Examples**
   - Update/add module READMEs.
   - Provide sample outputs and reports.
4. **Web UI/Dashboard (Required Before Launch)**
   - Design and implement dashboard.
   - Integrate with backend modules.
5. **Final Review & Launch**
   - Internal review and sign-off.
   - Launch system for production.

---

## NEXT STEPS PLAN

1. **Broaden Integration Testing**
   - Test with a wider variety of PDFs and domains.
   - Validate chunking, overlap, and metadata for edge cases.
   - Run the full pipeline and check for silent failures or data loss.
2. **Automate the Pipeline**
   - Add a "run-all" CLI command or script to orchestrate collection, extraction, deduplication, analytics, and reporting.
   - Optionally, allow for scheduled/triggered runs.
3. **Improve Documentation**
   - Add or update module-specific READMEs.
   - Provide more example outputs and analytics reports.
   - Document error messages and troubleshooting steps.
4. **Expand Test Suite**
   - Add tests for edge cases (large/corrupt PDFs, rare languages, etc.).
   - Add integration tests for the full pipeline.
5. **Enhance Error Handling**
   - Improve error messages and user feedback.
   - Ensure all critical failures are surfaced and logged with context.
6. **Develop Web UI/Dashboard (Before Launch)**
   - Build a dashboard for monitoring, reporting, and error management.
   - Expose search/filtering and milestone notifications.
   - Connect the UI to backend modules (extraction, analytics, reporting).
7. **Continuous Integration**
   - Set up CI/CD for automated testing and deployment.
   - Automate report generation and notifications.
8. **User Feedback Loop**
   - Collect feedback from users and reviewers to guide further improvements.

---

## Step-by-Step Roadmap: From Successful Test to Launch

1. **Confirm Test Success**
   - **What:** Ensure all test PDFs in `data/test_collect/full_pipeline_short/` process cleanly, with correct domain assignment, chunking, and metadata.
   - **How:** Review logs, output files, and analytics (chunk stats, domain balance, etc.).
   - **Why:** This validates the unified pipeline and folder structure.
2. **Finalize Corpus Builder Unification**
   - **What:** Double-check that both PDF and non-PDF extractors output harmonized metadata, quality flags, and directory structure.
   - **How:** Compare a sample of outputs from both pipelines; ensure all required fields and conventions are present.
   - **Why:** This is essential for downstream deduplication, analytics, and search.
3. **Collector Integration (If Needed)**
   - **What:** If you plan to run new collectors (arxiv, github, bitmex, etc.), use the CLI with collector-specific flags and output to isolated test dirs.
   - **How:** Use commands like:
     ```bash
     python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources arxiv --output-dir data/test_collect/arxiv --arxiv-clear-output-dir --arxiv-max-results 2 --arxiv-search-terms "crypto trading"
     ```
   - **Why:** Ensures new data is collected in a safe, testable way, following project rules (no global logic changes).
4. **Full Pipeline Dry Run**
   - **What:** Run the full pipeline (collect → extract → deduplicate) on a larger, but still test-scale, batch.
   - **How:** Use the CLI to process a larger folder, outputting to a new test directory.
   - **Why:** This is your "dress rehearsal" for production.
5. **Deduplication & Analytics**
   - **What:** Run deduplication scripts on the extracted outputs, ensuring `content_hash`, `deduplicated`, and `duplicate_info` fields are present and correct.
   - **How:** Use your deduplication pipeline/scripts, and check the summary logs.
   - **Why:** Ensures your corpus is clean and ready for downstream use.
6. **Documentation & Verification**
   - **What:** Update README, docstrings, and config files to reflect the unified logic and any new CLI options.
   - **How:** Review and edit documentation, run `verify_setup.py` to check dependencies and config.
   - **Why:** Ensures reproducibility and clarity for future users/developers.
7. **Production Launch**
   - **What:** Run the full pipeline on your production-scale data, outputting to a dedicated, versioned directory.
   - **How:** Use the CLI with production paths and settings, monitor logs for errors.
   - **Why:** This is the final step—your unified, robust corpus builder is now live!
8. **Ongoing Monitoring & Maintenance**
   - **What:** Monitor logs, analytics, and output quality. Be ready to patch bugs or add new collectors as needed.
   - **How:** Use log files, summary stats, and periodic manual review.
   - **Why:** Ensures long-term quality and adaptability.

### Key Project Rules to Remember
- **No global logic changes for all collectors:** Always scope changes to the collector block.
- **Test in isolated directories:** Never overwrite production data during testing.
- **CLI/config parity:** All options should be available via CLI and config.
- **Metadata and quality control must be harmonized:** For deduplication and analytics.
- **Document everything:** Update README and configs with every change.

---

## Integration Testing Plan (Step 1 of NEXT STEPS PLAN)

**Objective:** Ensure the pipeline is robust, accurate, and ready for production by testing a wide variety of documents and scenarios.

### What Will Be Tested

1. **PDF Types:**
   - Standard research papers (crypto and traditional finance)
   - Technical whitepapers
   - Presentations and slide decks
   - Scanned/image-based PDFs (if supported)
   - Corrupt or partially damaged PDFs
   - Very large PDFs (100+ pages)
   - Short/low-content PDFs
   - Non-English and mixed-language PDFs

2. **Domains:**
   - Crypto-native finance
   - Traditional finance
   - General technical/scientific
   - Out-of-domain (non-finance) for negative testing

3. **Edge Cases:**
   - PDFs with unusual encodings or fonts
   - PDFs with complex layouts (tables, multi-column, footnotes)
   - PDFs with missing or malformed metadata
   - PDFs with repetitive or formulaic content (to test machine translation/quality heuristics)

### How Results Will Be Validated

- **Chunking:**
  - Are sections/semantic chunks meaningful and correctly split?
  - Is chunk overlap working as intended?
- **Metadata:**
  - Is all required metadata present and accurate for each chunk?
  - Are language and quality flags correct?
- **Quality Control:**
  - Are low-quality and machine-translated chunks correctly flagged?
  - Are false positives minimized for technical content?
- **Deduplication & Analytics:**
  - Are outputs correctly processed by deduplication and analytics modules?
  - Is domain distribution accurately reported?
- **Error Handling:**
  - Are errors surfaced clearly and logged with context?
  - Does the pipeline fail gracefully on corrupt or unsupported files?
- **Performance:**
  - Can the pipeline handle large batches and large files efficiently?

### Implementation Approach

- Prepare a test set covering all the above cases (using existing test PDFs and new samples as needed).
- Run the full pipeline (collection → extraction → deduplication → analytics → reporting) on the test set.
- Review outputs, logs, and reports for each case.
- Document any failures, unexpected results, or areas for improvement.
- Iterate on fixes and retest as needed.

---

## Integration Test Outcomes & Immediate Action Plan

### Outcomes of First Full Pipeline Test (Processing Only)
- **Total PDFs processed:** 382
- **Total chunks extracted:** 78,789
- **Average chunk size:** ~190 tokens
- **Section heading extraction:** Most headings are single characters or numbers (likely page numbers or formula variables)
- **Domain assignment:** All chunks marked as 'unknown'
- **Report quality:** Section heading stats not meaningful; missing breakdowns by language/quality; no error summaries

#### **Critical Issues Identified**
- **Section Heading Detection Problems:**
  - Excessive chunking due to non-meaningful headings
  - Small chunks reduce context and create inefficient overlap
- **Domain Assignment Failure:**
  - All chunks marked as 'unknown', preventing corpus balance monitoring and domain-based analysis
- **Report Quality Issues:**
  - Non-meaningful section heading statistics
  - Missing breakdowns by language and quality metrics
  - No error summaries or quality validation

---

## Multiprocessing Support for PDF Extraction

- The PDF extraction pipeline now supports multiprocessing for efficient batch processing.
- Use the `batch_process_pdfs` function to process many PDFs in parallel.
- Set the number of workers via the `num_workers` argument or the `PDF_NUM_WORKERS` environment variable (default: 1).
- This matches the non-PDF pipeline's batch processing and ensures scalable, fast extraction for large corpora.

**Example usage:**
```python
from CryptoFinanceCorpusBuilder.processors.batch_text_extractor import batch_process_pdfs
results = batch_process_pdfs(pdf_paths, output_dir, num_workers=4)
```
Or set the environment variable:
```bash
set PDF_NUM_WORKERS=4
```

---

## Alignment Note

- The PDF and non-PDF extraction pipelines are now fully aligned in:
  - Chunking logic and configurability
  - Metadata and domain assignment
  - Quality control and flagging
  - Multiprocessing and performance
  - Reporting and analytics

---

## Immediate Action Plan (Post-Integration Test) [UPDATED]

- Multiprocessing is now available for PDF extraction. Use it for all large batch tests and production runs.

---

## Integration Testing Plan (Step 1 of NEXT STEPS PLAN) [UPDATED]

- For all batch tests, enable multiprocessing to ensure efficient processing and realistic performance metrics.

---

## Dependencies

- The PDF extraction pipeline requires the `PyYAML` package for loading the section heading regex config.
- Install it in your environment:

```bash
pip install pyyaml
```

- If you see `ModuleNotFoundError: No module named 'yaml'`, install PyYAML as above.

---

## Next Round of Pipeline Improvements (Boss Recommendations)

### Section Heading Filtering
- Adds a post-filter to remove publisher lines, URLs, copyright, and other non-semantic headings after regex match.
- Only headings with at least two words and reasonable length are used for chunking.

### Robust Domain Assignment
- Uses a multi-strategy approach:
  - Provided mapping (filename → domain)
  - Parent directory if it matches a known domain
  - Content-based classification (if available)
  - Filename heuristics (e.g., "quant", "risk")
  - Fallback to "uncategorized"
- Ensures all domains are referenced as originally designed.

### Chunk Size Optimization
- Merges small chunks and splits large ones to ensure optimal chunk size for downstream use.

### Expanded Analytics & Metrics
- Corpus report now includes:
  - Before/after metrics (chunks per PDF, average chunk size, processing time reduction)
  - Domain, language, and quality flag distributions
  - Machine translation stats
  - Token distribution (min, max, avg)
- Quantifies the impact of improvements for review and validation.

### Alignment Note
- These changes further align the PDF and non-PDF pipelines and directly address all critical issues and recommendations from the boss.

---

## Unified Domain Assignment (PDF & Non-PDF Extraction)

Both the PDF and non-PDF extraction pipelines now use a unified domain assignment utility:
- Domains are loaded from `config/domain_config.py` if available, else a hardcoded list is used.
- Domain assignment order: **parent folder** → **filename prefix** → **keyword matching (filename/text)** → fallback to `uncategorized`.
- To update or add domains, edit the config or the utility in `utils/domain_utils.py`.
- This ensures all extracted files have consistent and correct `domain` metadata for analytics, filtering, and corpus balance.

**No changes are needed in the CLI or extractors to update domains—just update the config or utility.**

---

## Analytics & Corpus Rebalancing

### Current Implementation Status

#### Analytics Features
- **Domain Balance Analysis**
  - Tracks 60/40 crypto/traditional finance split
  - Monitors domain distribution and coverage gaps
  - Generates balance scores and visualizations
  - Calculates Gini coefficient and distribution entropy

- **Quality Metrics**
  - Language confidence detection
  - Mixed language detection
  - Machine translation detection
  - Corruption detection
  - Token count and quality flags

- **Source Diversity**
  - Tracks source distribution
  - Calculates source diversity entropy
  - Monitors source-specific quality metrics

#### Corpus Rebalancing
- **Dynamic Collection Strategy**
  - Automated gap analysis
  - Priority-based collection allocation
  - Traditional finance boost mechanism
  - Continuous balance monitoring

- **Rebalancing Tools**
  - Coverage gap analyzer
  - Domain balance analyzer
  - Collection priority generator
  - Balance score calculator

### Usage Examples

#### Generate Corpus Statistics
```bash
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli stats --corpus-dir data/corpus_1
```

#### Analyze Coverage Gaps
```bash
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli gaps --corpus-dir data/corpus_1 --output gap_analysis.json
```

#### Monitor Corpus Balance
```bash
python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli report --corpus-dir data/corpus_1 --output corpus_report.md --include-stats --include-examples
```

### Output Formats

#### Balance Report
- Total documents and size statistics
- Domain and source distribution tables
- Traditional vs. crypto-native split percentages
- Token distribution by domain
- Example documents per domain
- Implementation details and recommendations

#### Gap Analysis
- Current vs. target domain percentages
- Priority levels for each domain
- Collection allocation recommendations
- Traditional finance boost factors
- Balance score and alignment metrics

### Next Steps

1. **Analytics Enhancement**
   - Implement advanced visualization dashboard
   - Add real-time monitoring capabilities
   - Enhance quality metric tracking
   - Develop predictive balance modeling

2. **Rebalancing Optimization**
   - Improve collection priority algorithms
   - Enhance traditional finance targeting
   - Implement automated rebalancing triggers
   - Add milestone-based notifications

3. **Integration & Testing**
   - End-to-end testing of analytics pipeline
   - Performance optimization
   - Documentation updates
   - User guide creation

If you have any questions or need further guidance, please refer to the code comments, docstrings, or open an issue in your project tracker.

## Comprehensive Development Timeline

### Phase 1: PDF Extractor Testing & Validation (2-3 weeks)

#### Week 1: Core PDF Extraction Testing
1. **Test Environment Setup**
   ```bash
   mkdir -p data/test_collect/full_pipeline_short/{pdf,nonpdf,quality,mt}
   ```

2. **Basic Extraction Test**
   ```bash
   python -m CryptoFinanceCorpusBuilder.processors.batch_text_extractor \
     --input-dir data/test_collect/full_pipeline_short/pdf \
     --output-dir data/test_collect/full_pipeline_short/output \
     --domain crypto_derivatives \
     --relevance-threshold 30 \
     --lang-confidence-threshold 0.70 \
     --mixed-lang-ratio 0.30 \
     --mt-config config/mt_config.json
   ```

3. **Quality Control Test**
   ```bash
   python -m CryptoFinanceCorpusBuilder.processors.batch_text_extractor \
     --input-dir data/test_collect/full_pipeline_short/quality \
     --output-dir data/test_collect/full_pipeline_short/output \
     --domain market_microstructure \
     --relevance-threshold 30 \
     --lang-confidence-threshold 0.80 \
     --mixed-lang-ratio 0.20 \
     --corruption-thresholds config/corruption_thresholds.json
   ```

4. **Machine Translation Test**
   ```bash
   python -m CryptoFinanceCorpusBuilder.processors.batch_text_extractor \
     --input-dir data/test_collect/full_pipeline_short/mt \
     --output-dir data/test_collect/full_pipeline_short/output \
     --domain high_frequency_trading \
     --relevance-threshold 30 \
     --mt-config config/mt_config.json
   ```

#### Week 2: Integration Testing
1. **Test Cases Coverage**
   - Standard research papers (crypto and traditional finance)
   - Technical whitepapers
   - Presentations and slide decks
   - Scanned/image-based PDFs
   - Corrupt or partially damaged PDFs
   - Very large PDFs (100+ pages)
   - Short/low-content PDFs
   - Non-English and mixed-language PDFs

2. **Validation Metrics**
   - Chunking quality and semantic coherence
   - Metadata accuracy and completeness
   - Quality control flagging accuracy
   - Domain assignment correctness
   - Performance under load

3. **Edge Case Testing**
   - PDFs with unusual encodings/fonts
   - Complex layouts (tables, multi-column)
   - Missing/malformed metadata
   - Repetitive/formulaic content

#### Week 3: Performance & Optimization
1. **Multiprocessing Testing**
   - Test with various worker counts
   - Memory usage monitoring
   - CPU utilization analysis
   - I/O bottleneck identification

2. **Batch Processing Validation**
   - Large batch handling
   - Error recovery
   - Progress tracking
   - Resource management

### Phase 2: Analytics & Rebalancing Development (3-4 weeks)

#### Week 4: Analytics Enhancement
1. **Advanced Visualization Dashboard**
   - Real-time corpus balance monitoring
   - Domain distribution visualization
   - Quality metrics dashboard
   - Source diversity tracking

2. **Real-time Monitoring**
   - Live processing statistics
   - Error tracking and alerts
   - Performance metrics
   - Resource utilization

#### Week 5: Rebalancing Implementation
1. **Collection Priority System**
   - Enhanced gap analysis
   - Dynamic allocation algorithms
   - Traditional finance targeting
   - Priority scoring system

2. **Automated Triggers**
   - Balance threshold monitoring
   - Collection initiation rules
   - Quality control triggers
   - Milestone notifications

#### Week 6: Integration & Testing
1. **End-to-End Testing**
   - Full pipeline validation
   - Analytics accuracy verification
   - Rebalancing effectiveness
   - Performance benchmarking

2. **Documentation & Training**
   - User guide creation
   - API documentation
   - Example workflows
   - Troubleshooting guides

### Phase 3: Production Preparation (2 weeks)

#### Week 7: Final Testing & Optimization
1. **Production Scale Testing**
   - Large corpus processing
   - Long-running stability
   - Resource optimization
   - Error handling validation

2. **Performance Tuning**
   - Memory usage optimization
   - CPU utilization improvement
   - I/O efficiency enhancement
   - Cache strategy implementation

#### Week 8: Launch Preparation
1. **Documentation Finalization**
   - README updates
   - API documentation completion
   - Example repository population
   - Troubleshooting guide finalization

2. **Launch Checklist**
   - Environment validation
   - Backup procedures
   - Monitoring setup
   - Rollback procedures

### Success Criteria for Each Phase

#### Phase 1 (PDF Extractor)
- All test cases pass with >95% accuracy
- No critical errors in production-scale testing
- Performance meets or exceeds non-PDF pipeline
- Documentation complete and verified

#### Phase 2 (Analytics & Rebalancing)
- Dashboard provides real-time insights
- Rebalancing maintains 60/40 target ratio
- Automated triggers work reliably
- Documentation and training materials complete

#### Phase 3 (Production)
- System handles production load
- All monitoring systems operational
- Documentation and procedures complete
- Launch checklist items verified

### Risk Mitigation

1. **Technical Risks**
   - Regular backups during testing
   - Isolated test environments
   - Gradual feature rollout
   - Comprehensive error handling

2. **Resource Risks**
   - Clear milestone tracking
   - Regular progress updates
   - Flexible timeline adjustments
   - Resource allocation monitoring

3. **Quality Risks**
   - Automated testing suite
   - Regular code reviews
   - Performance benchmarking
   - User feedback integration

### Post-Launch Monitoring

1. **Performance Monitoring**
   - Processing speed
   - Resource utilization
   - Error rates
   - Quality metrics

2. **Balance Monitoring**
   - Domain distribution
   - Traditional/crypto ratio
   - Source diversity
   - Quality distribution

3. **User Feedback**
   - Feature requests
   - Bug reports
   - Usage patterns
   - Performance feedback

If you have any questions or need further guidance, please refer to the code comments, docstrings, or open an issue in your project tracker. 