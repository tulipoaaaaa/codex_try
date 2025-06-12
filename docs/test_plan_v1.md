# Test Plan v1

## Test Matrix

| Component        | Objective                                      | Fixtures Needed         | Sample Cmd / Call                                      | Edge Cases / Notes                                  |
|-----------------|------------------------------------------------|------------------------|--------------------------------------------------------|-----------------------------------------------------|
| Collectors      | Ensure each Collector can run `.collect()` on a temp dir and produce expected output | Temp dir, DummyProjectConfig | pytest tests/collectors/test_<collector>.py           | Network errors, empty dir, permission denied        |
| Processors      | Ensure each Processor can run `.process()` with minimal input and not crash | Minimal input, DummyProjectConfig | pytest tests/processors/test_<processor>.py           | Malformed input, missing config, large input        |
| CorpusManager   | Validate corpus loading, saving, and state transitions | DummyProjectConfig, temp dir | pytest tests/corpus/test_corpus_manager.py             | Corrupt state, missing files, concurrent access     |
| CorpusBalancer  | Validate rebalancing and state persistence      | DummyProjectConfig, temp dir | pytest tests/corpus/test_corpus_balancer.py            | No data, unbalanced input, repeated rebalance       |
| E2E Pipeline    | Run full pipeline via CLI with --dry-run/--preview-only | DummyProjectConfig, temp dir | pytest tests/e2e/test_pipeline_run.py                  | CLI arg errors, missing dependencies, GPU required  |

## Notes
- All tests should use fixtures in `tests/conftest.py` for temp dirs and dummy configs.
- Use `pytest.skip` if GPU is required but unavailable.
- Each test should run in <30s.
- Extend edge cases as new bugs are found. 

Absolutely! Here’s a **detailed review and critique** of each test file, with recommendations to ensure they truly reflect production usage and are robust for your codebase.

---

## 1. **Collectors Test (`tests/collectors/test_collectors.py`)**

### **What it does:**
- Dynamically finds all Collector classes in `CorpusBuilderApp.shared_tools.collectors`.
- Instantiates each with a `DummyProjectConfig`.
- Calls `.collect(temp_dir)` on each, using a temporary directory.

### **Strengths:**
- **Dynamic discovery**: Will catch new collectors automatically.
- **Isolated temp dir**: Prevents side effects.
- **Catches exceptions**: Fails the test if `.collect()` raises.

### **Potential Issues & Recommendations:**
- **Production-like config**: `DummyProjectConfig` is minimal. If collectors expect real config values (API keys, endpoints), they may fail or not test real logic.
  - **Recommendation**: Use a fixture that can be extended to provide realistic config values, or parametrize with real/simulated configs.
- **No output validation**: Only checks for exceptions, not for correct output or side effects.
  - **Recommendation**: After `.collect()`, check the temp dir for expected files or data.
- **No network mocking**: If collectors hit real APIs, tests may be flaky or slow.
  - **Recommendation**: Use `pytest`'s monkeypatch or `requests-mock` to simulate network responses.

---

## 2. **Processors Test (`tests/processors/test_processors.py`)**

### **What it does:**
- Dynamically finds all Processor classes in `CorpusBuilderApp.shared_tools.processors`.
- Instantiates each (no config passed).
- Calls `.process()`.

### **Strengths:**
- **Dynamic discovery**.
- **Catches exceptions**.

### **Potential Issues & Recommendations:**
- **No input provided**: Most processors likely require input data (file, text, etc.).
  - **Recommendation**: Use fixtures to provide minimal valid input for each processor type.
- **No output validation**: Only checks for exceptions.
  - **Recommendation**: Assert on the return value or side effects.
- **No config**: If processors require config, this will fail.
  - **Recommendation**: Pass `dummy_config` or a real config if required.

---

## 3. **CorpusManager Test (`tests/corpus/test_corpus_manager.py`)**

### **What it does:**
- Imports `CorpusManager`.
- Instantiates with `DummyProjectConfig`.
- Calls `load_corpus()` and `save_state()` if available.

### **Strengths:**
- **Covers key methods**.
- **Uses temp dir**.

### **Potential Issues & Recommendations:**
- **No corpus data**: If `load_corpus()` expects files, it may fail or do nothing.
  - **Recommendation**: Place a minimal valid corpus file in the temp dir before calling.
- **No output validation**: Only checks for exceptions.
  - **Recommendation**: Assert that state is loaded/saved as expected.

---

## 4. **CorpusBalancer Test (`tests/corpus/test_corpus_balancer.py`)**

### **What it does:**
- Imports `CorpusBalancer`.
- Instantiates with `DummyProjectConfig`.
- Calls `rebalance()` and `save_state()` if available.

### **Strengths:**
- **Covers key methods**.
- **Uses temp dir**.

### **Potential Issues & Recommendations:**
- **No corpus data**: If `rebalance()` expects data, it may do nothing or fail.
  - **Recommendation**: Place a minimal valid corpus file in the temp dir before calling.
- **No output validation**: Only checks for exceptions.
  - **Recommendation**: Assert that the corpus is rebalanced as expected.

---

## 5. **E2E Pipeline Test (`tests/e2e/test_pipeline_run.py`)**

### **What it does:**
- Runs the CLI with `--dry-run` in a subprocess.
- Asserts exit code is 0 or help is shown.

### **Strengths:**
- **Simulates real CLI usage**.
- **Isolated temp dir**.

### **Potential Issues & Recommendations:**
- **No real pipeline data**: If the CLI expects input files, it may not test the full pipeline.
  - **Recommendation**: Place a minimal valid input in the temp dir and pass it to the CLI.
- **No output validation**: Only checks for exit code/help.
  - **Recommendation**: Parse CLI output for expected messages or results.

---

## **General Recommendations for All Tests**

1. **Fixtures for Realistic Data**:  
   Use `tests/conftest.py` to provide minimal but valid input files/configs for each component.

2. **Output/Side-Effect Validation**:  
   Don’t just check for exceptions—assert that the expected files, logs, or data are produced.

3. **Network/Filesystem Mocking**:  
   Use `pytest` plugins to mock external dependencies for reliability and speed.

4. **Parametrize for Edge Cases**:  
   Test with empty, malformed, and large inputs.

5. **Skip or xfail for Unavailable Resources**:  
   Use `pytest.skip` or `pytest.xfail` if a GPU or network is required but unavailable.

---

## **Summary Table**

| Test File                        | Instantiates | Runs Key Methods | Uses Realistic Input | Validates Output | Handles Edge Cases | Mocks External? |
|----------------------------------|--------------|------------------|---------------------|------------------|-------------------|-----------------|
| test_collectors.py               | Yes          | Yes              | No                  | No               | No                | No              |
| test_processors.py               | Yes          | Yes              | No                  | No               | No                | No              |
| test_corpus_manager.py           | Yes          | Yes              | No                  | No               | No                | No              |
| test_corpus_balancer.py          | Yes          | Yes              | No                  | No               | No                | No              |
| test_pipeline_run.py             | Yes (CLI)    | Yes              | No                  | No               | No                | No              |

---

## **Actionable Next Steps**

- **Add/extend fixtures** to provide minimal valid input for each test.
- **Add assertions** to check output, not just for exceptions.
- **Mock network/filesystem** where needed.
- **Parametrize for edge cases**.

---

**Would you like me to propose or implement these improvements, or proceed with the current tests as-is?**

Ran tool
Here’s a **plan and approach** for creating robust, production-like, individual tests for each collector, extractor, corpus manager, and corpus balancer, as you requested. This will ensure each test matches how the component is actually used in production.

---

## **Collectors: Individual Test Design**

### **How to proceed:**
1. **Enumerate all concrete collector classes** (not just base classes).
2. **For each collector:**
   - Read its constructor and main methods (especially `.collect()`).
   - Identify required config, environment variables, and input arguments.
   - Create a dedicated test file:  
     `tests/collectors/test_<collector_name>.py`
   - Use realistic config and input (mocking network/filesystem as needed).
   - Assert on both output and side effects (files, logs, etc.).

### **Example: ArxivCollector**
- **Constructor:** Needs config, delay_range, clear_output_dir, existing_titles.
- **Production call:** `.collect(query, max_items=100)`
- **Test:** Provide a minimal config, a sample query, and check that output files are created or results are returned.

### **Example: AnnasMainLibraryCollector**
- **Constructor:** Needs config, account_cookie (from .env).
- **Production call:** `.collect(search_query, max_attempts=5)`
- **Test:** Mock the CookieAuthClient if needed, provide a sample search query, and check for downloaded files.

### **Example: RepoCollector**
- **Constructor:** config, delay_range, clone_depth.
- **Production call:** `.clone_repo(repo_url, ...)`
- **Test:** Use a public repo URL, check that the repo is cloned to the temp dir.

---

## **Extractors (PDF/Non-PDF): Individual Test Design**

- **PDF Extractor:**  
  - Test with a real or sample PDF file.
  - Assert that extracted data matches expectations.
- **Non-PDF Extractor:**  
  - Test with a sample text or HTML file.
  - Assert on output structure and content.

---

## **CorpusManager & CorpusBalancer: Individual Test Design**

- **CorpusManager:**  
  - Test `load_corpus`, `save_state`, and any transformation methods.
  - Use a temp dir with a minimal corpus structure.
- **CorpusBalancer:**  
  - Test `rebalance`, `save_state`.
  - Use a temp dir with a minimal, intentionally unbalanced corpus.

---

## **E2E Pipeline:**
- Simulate a real pipeline run with all steps, using the CLI and a temp corpus.
- Assert on final output, logs, and exit code.

---

## **Batching & Memory**
- I will proceed in batches (e.g., all collectors first, then extractors, etc.).
- I will keep track of which components have been covered and ensure all are done.

---

## **Next Steps:**
1. **Batch 1:**  
   - Create individual test files for each working collector in `tests/collectors/`.
   - Each test will:
     - Use realistic config and input.
     - Mock network/filesystem as needed.
     - Assert on output and side effects.
2. **Report progress and await your review before moving to extractors.**

---

**Would you like to review the proposed test for one collector first, or proceed with the full batch for all collectors?**  
Let me know if you want a specific collector prioritized, or if you want to see the test template before I proceed!

Ran tool
Here is a list of **all concrete collector classes** in your codebase that need individual, production-like tests:

---

## **Collectors to Test (with their main methods/usage):**

1. **BaseCollector** (abstract, do not test directly)
2. **ApiCollector** (base, do not test directly)
3. **ArxivCollector**
   - `.collect(query, max_items=100)`
4. **AnnasMainLibraryCollector**
   - `.collect(search_query, max_attempts=5)`
5. **GeneralWebCorpusCollector**
   - `.collect(max_total=20, max_retries=3, rate_limit=5)`
6. **RepoCollector**
   - `.clone_repo(repo_url, target_dir=None, branch=None)`
   - `.extract_archive(archive_path, target_dir=None)`
7. **GitHubCollector**
   - `.collect(query, max_items=100)` (inherits from ApiCollector)
   - `._search_by_term(term, max_repos=10)`
   - `._clone_repo(clone_url, target_dir)`
8. **SciDBCollector**
   - `.collect(...)` (details depend on config and authentication)
9. **WebCollector**
   - `.download_file(url, filename, subfolder=None)`
   - (May have a `.collect()` in a subclass)
10. **ISDADocumentationCollector** (if present, similar to above)
11. **Any other concrete collector classes found in `collect_*.py` files**

---

### **Collectors NOT to test directly:**
- `BaseCollector`, `ApiCollector`, and other abstract/base classes.

---

## **Next Step:**
**I will start with `ArxivCollector` and create a dedicated test file for it, using realistic config and input, and checking for expected output.**

After that, I will proceed one by one with the rest.

---

**Would you like to review the test for `ArxivCollector` before I proceed to the next, or should I continue in sequence and report after each?**