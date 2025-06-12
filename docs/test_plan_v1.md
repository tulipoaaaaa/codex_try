# Test Plan v1

This document outlines the initial test coverage approach for the backend components.

| Component | Objective | Fixtures Needed | Sample Command | Edge Cases |
|-----------|-----------|----------------|---------------|-----------|
| Collectors | Ensure each collector can be instantiated and run in dry-run mode | Temporary directory with DummyProjectConfig | `python -m CorpusBuilderApp.cli collect --preview-only` | Missing network, invalid auth |
| Processors | Validate processors handle minimal input without errors | Temporary files for inputs | `processor.process()` | Empty input, corrupt data |
| CorpusManager | Verify file operations on temp corpus | Temp corpus directory | `CorpusManager.copy_files([...])` | Missing files |
| CorpusBalancer | Confirm balancing logic runs with dummy config | Temp corpus with few files | `CorpusBalancer.rebalance(dry_run=True)` | No documents, extreme ratios |
| End-to-End | Smoke test pipeline via CLI | Sample config YAML | `python -m CorpusBuilderApp.cli run --dry-run` | Invalid config, missing deps |
