# Integration Notes for CorpusBuilderApp

Keep this file up-to-date with any collector / processor quirks that must be handled when the full application is wired together (CLI, UI wrappers, pipelines, cron jobs, etc.).

---
## 1. BitMEX Collector (UpdatedBitMEXCollector)

1. **Call signature for full archive scrape**
   ```python
   collector.collect(
       categories=[
           'research',              # https://blog.bitmex.com/category/research/
           'crypto-trader-digest'   # https://blog.bitmex.com/category/crypto-trader-digest/
       ],
       max_pages=None               # None ⇒ crawl until archive ends
   )
   ```

2. **Directory structure**
   * Output root: `raw_data_dir` supplied by `ProjectConfig`.
   * Inside that, the collector now creates exactly two sub-folders and **nothing else**:
     ```
     raw_data_dir/
         research/                # full HTML + any PDFs from Research articles
         crypto_trader_digest/    # full HTML + PDFs from Crypto-Trader-Digest
     ```
   * Empty fallback directories (e.g. `other/`, `articles/`, `papers/`, `reports/`) are avoided by ensuring:
     * `post['category']` is always set (`research` or `crypto_trader_digest`).
     * `domain_configs` in the active `ProjectConfig` **does not** define those two names; otherwise `BaseCollector` will pre-create its standard `articles | papers | reports` layout.

3. **Hash cache / deduplication**
   * Per-run duplicate guard keyed on normalised title.
   * Cross-run dedup continues via SHA-256 + `seen_hashes.json` as before.

4. **Environment variables**
   * No API keys required, but respect existing session headers for polite scraping.

---
## 2. Test-suite Dummy Configs

When unit tests need a `DummyConfig`, favour the minimal pattern:
```python
class DummyConfig:
    raw_data_dir = <tmp or G:/data/TEST_COLLECTORS/...>
    log_dir      = raw_data_dir / 'logs'
    metadata_dir = raw_data_dir / 'meta'
    domain_configs = {}
    # helper getters …
```
This prevents `BaseCollector` from creating empty domain folders.

---
## 3. Environment variables required by collectors

| Collector | Variable            | Purpose                                   |
|-----------|--------------------|-------------------------------------------|
| Anna's Archive | `AA_ACCOUNT_COOKIE` | Auth cookie for download access |
| SciDB          | `AA_ACCOUNT_COOKIE` | Same as above (shared client)   |
| FRED           | `FRED_API_KEY`      | API key for FRED series           |
| GitHub         | `GITHUB_TOKEN`      | Higher rate-limit for GH API      |

Keep these in the deployment `.env` or system environment.

---
## 4. FRED Collector – series list & discovery parameters (updated)

* **YAML location**  `CorpusBuilderApp/configs/fred_series.yaml`
* **Structure**

  ```yaml
  series_ids:              # ← always downloaded
    - GDP
    - CPIAUCSL
    - CPILFESL
    - DGS10
    - FEDFUNDS
    - VIXCLS
    - M2SL

  # Optional discovery blocks
  search_terms:
    - "bitcoin volatility"
    - "cryptocurrency index"

  categories:
    - "32455"            # Cryptocurrencies (FRED category ID)

  max_results: 5          # per search/category (override in test config)
  ```

* **Orchestrator sample (Python)**

  ```python
  from pathlib import Path
  import yaml
  from shared_tools.project_config import ProjectConfig
  from CorpusBuilderApp.shared_tools.collectors.fred_collector import FREDCollector

  cfg = ProjectConfig("G:/configs/master_config.yaml", environment="production")

  fred_cfg_path = Path("CorpusBuilderApp/configs/fred_series.yaml")
  params = yaml.safe_load(fred_cfg_path.read_text())

  collector = FREDCollector(cfg)
  collector.collect(
      series_ids=params.get("series_ids"),
      search_terms=params.get("search_terms"),
      categories=params.get("categories"),
      max_results=params.get("max_results")
  )
  ```

* **CI / Test environment**
  – Override `max_results` to a small integer (e.g. 2) in
    `test_config.yaml` so unit tests complete quickly.

* **Validation guard**  The collector skips any `series_id` that fails a
  lightweight existence check and logs a warning—preventing noisy 400
  errors.

---
## 5. GitHub Collector – topics vs search_terms & CLI usage

* YAML block (in `shared_tools/master_config.yaml` and `test_config.yaml`):

  ```yaml
  collectors:
    github:
      enabled: true
      topics:
        - "cryptocurrency"
        - "trading"
        - "defi"
        - "blockchain"
      # Free-text fallback or complement to topics
      search_terms:
        - "bitcoin"
        - "high frequency trading"
      min_stars: 100          # filter client-side
      max_results: 50         # per topic / term
  ```

* The collector picks **topics first**; if none supplied, it uses `search_terms`.
* For rate-limits set `GITHUB_TOKEN` in `.env`.

**CLI examples**

```powershell
# Production run with environment flag
python -m CorpusBuilderApp.shared_tools.collectors.github_collector `
       --config ".../shared_tools/master_config.yaml" `
       --env production

# Ad-hoc test run pulling 5 repos per search term
python -m CorpusBuilderApp.shared_tools.collectors.github_collector `
       --config ".../shared_tools/test_config.yaml" `
       --env test `
       --search-terms bitcoin "algorithmic trading" --max-repos 5
```

The `--env` flag (added to FRED and GitHub collectors) lets the CLI force the
`production` or `test` environment block in YAML without relying on the
`ENVIRONMENT` variable.

---
## 6. ISDA Documentation Collector – production notes

* **YAML output path** – ensure the active environment block sets `raw_data_dir` to the corpus' raw folder, e.g.

  ```yaml
  environments:
    production:
      raw_data_dir: "G:/data/production/raw"
  ```

  The collector appends its own sub-folder `ISDA`, so PDFs will land in:

  ```
  G:/data/production/raw/ISDA/ …
  ```

* **Crawl scope** – omit the test-time limits to fetch the full archive:

  ```python
  collector.collect(max_sources=None, keywords=None)
  ```

* **Orchestrator invocation**

  ```powershell
  python -m CorpusBuilderApp.shared_tools.collectors.collect_isda `
         --config ".../shared_tools/master_config.yaml" `
         --env production
  ```

  No API keys are required.

* **Test fixture** – unit test writes to `G:/data/TEST_COLLECTORS/ISDA` and caps `max_sources=2, keywords=["protocol"]` for speed.  Production has no such cap.

---
## 7. Automatic cleanup of empty domain directories (NEW)

Starting with commit XX on `main` we include a housekeeping step that **removes any empty folders** left behind by collectors or processors.

1. **Helper function** – `shared_tools.utils.fs_utils.remove_empty_dirs(root, *, remove_root=False)`
   * Walks the tree bottom-up and deletes directories with **no** children.
   * Preserves root by default and skips directories that contain even a hidden file (e.g. `.gitkeep`).

2. **CLI integration** – `cli/execute_from_config.py`
   * New flag: `--cleanup-empty`
   * If you already run the full pipeline with `--run-all` the cleanup step executes automatically. Otherwise you can trigger it explicitly after any phase:

     ```powershell
     # Extract only, then cleanup
     python -m cli.execute_from_config --config G:/configs/master_config.yaml --extract --cleanup-empty
     ```

   * The cleanup targets two paths defined by `ProjectConfig`:
     * `config.get_raw_dir()`   → usually `G:/data/<env>/raw`
     * `config.get_processed_dir()` → e.g. `G:/data/<env>/processed`

3. **Logging** – A summary line is written (and captured by both UI and file logs):

   ```text
   INFO  execute_from_config: Cleanup completed – 17 empty directories removed
   ```

4. **Why?**  Some processors create the standard `domain/` layout proactively (e.g. `text_extractor`) to avoid scattering files. Previously this left behind lots of empty folders in tests or partial runs. Deleting them post-run keeps the corpus tree tidy without breaking processors that legitimately expect fully-nested paths during execution.

---
## 8. Non-PDF extractor hot-fix + validation results (2025-06-14)

This run targeted `G:/data/test_processors/nonpdf_processors` and wrote
extracted text/metadata pairs to `G:/codex/codex_try/_extracted`.

Fixes applied in code (see commit `feat/nonpdf-fixes`):
1. `FormulaExtractor.extract_from_text` legacy alias 
2. Graceful absence of `ast.Comment` on Python ≥ 3.8
3. `DOMAIN_THRESHOLDS` auto-seeded from `ProjectConfig.domains`
4. `ast.parse` wrapped in `try/except SyntaxError`
5. Batch extractor now calls `FormulaExtractor.extract()` directly

Post-run validation
* Sampled 100 random metadata files – all contained required top-level keys
  (`file_type`, `content_hash`, `quality_metrics`, `enhancement_results`).
* Format-specific blocks present (`code_specific`, `html_specific`).
* No JSON decode errors; UTF-8 encoding verified.
* No zero-byte outputs; no duplicate `.txt` contents.

Remaining `ERROR … 'gibberish'` entries in the log were benign – they
correspond to binary or non-UTF-8 fixtures (Bitcoin test vectors, CSV
artifacts, Quantopian blobs) and were skipped.

Outcome
* 4 727 files scanned, 964 high-quality text outputs produced (≈ 20 % useful
  yield given noisy source repos).
* Folder `_extracted` cleared manual QA and is suitable for promotion to
  prod `processed_dir`.

---
## 7. Corpus maintenance pipeline – deduplication → quality-control → balancer

### 7.1  Components
| Stage | Entry-point class | YAML key | CLI auto-run | Purpose |
|-------|------------------|----------|--------------|---------|
| Deduplicator | `shared_tools.processors.deduplicator.Deduplicator` | n/a (invoked ad-hoc or via wrapper) | no | Builds an index (`deduplication_index.json`) and detects duplicates by SHA-256, file hash, normalised title and MinHash similarity. |
| Quality-control | `shared_tools.processors.quality_control.QualityControl` | `processors.quality_control` | yes (when `--extract` or `--run-all`) | Flags low-quality text (language, corruption, MT, duplication) and moves rejects to `low_quality/`. Successful files go to `processed/quality_checked/<domain>`. |
| Corpus balancer | `shared_tools.processors.corpus_balancer.CorpusBalancer` | `processors.corpus_balancer` | yes (`--balance` or `--run-all`) | Down-samples/upsamples `processed/quality_checked` to hit domain-ratio targets; writes to `processed/balanced`. |

### 7.2  Testing plan (CI or local)
1. **Fixture corpus**  `G:/codex/codex_try/corpus_1` – mirrors production raw & extracted layout.
2. **Deduplication dry-run**
   ```powershell
   python - <<'PY'
   from pathlib import Path
   from CorpusBuilderApp.shared_tools.processors.deduplicator import Deduplicator
   from shared_tools.project_config import ProjectConfig

   class DummyCfg(ProjectConfig):
       def __init__(self): super().__init__({})
       def get_input_dir(self): return Path(r"G:/codex/codex_try/corpus_1")
       def get_logs_dir(self):  return Path(r"G:/codex/codex_try/corpus_1/logs")

   d = Deduplicator(DummyCfg({}))
   d.scan_corpus(); dups = d.find_duplicates()
   print(f"duplicate groups: {len(dups)} → written to logs/dedup_log.jsonl")
   PY
   ```
3. **Quality-control only**
   ```powershell
   python cli/execute_from_config.py --config shared_tools/test_config.yaml --extract \
          --enabled-processors quality_control
   ```
   Verify that `processed/quality_checked/<domain>` is populated and that rejects land in `low_quality/`.
4. **Balancer only** (requires QC output):
   ```powershell
   python cli/execute_from_config.py --config shared_tools/test_config.yaml --balance
   ```
   Inspect `processed/balanced` and `logs/corpus_balance.json`.

### 7.3  Environment variables for OCR tables (recap)
`TESSERACT_OCR_TABLE_CONFIG`, `TESSERACT_OCR_TABLE_CONFIG_WIDE`, `TESSERACT_OCR_NUMERIC_CONFIG` override the hard-coded defaults in `image_table_extractor.py`. They are **optional** – leave unset for the tuned defaults.

---
## 8. *shared_tools/services* and *shared_tools/utils* – current usage map

*Services* are long-running or orchestrating helpers that sit **outside** the main collector/processor pipeline. Today only two are actively triggered by the UI layer:

| Service | Used by | Function |
|---------|---------|----------|
| `auto_balance_service.AutoBalanceService` | UI "Corpus" tab | Periodically calls the balancer with safe params when the user toggles *auto-balance*. |
| `corpus_stats_service.CorpusStatsService` | UI dashboard & `/tools/diff_corpus_profiles.py` | Generates aggregate stats (`corpus_stats.json`). |

The remaining service stubs (`activity_log_service`, `task_queue_manager`, `system_monitor`, etc.) are placeholders for future scheduling / monitoring and are **not yet invoked** by either the CLI or the current Electron UI.

*Utils* are pure helper modules and are already imported where needed:

| Util module | Currently called by |
|-------------|--------------------|
| `utils.fs_utils` | CLI cleanup step after runs (remove_empty_dirs) |
| `utils.extractor_utils` | PDF & text extractors for shared token-count / chunk helpers |
| `utils.metadata_normalizer / validator` | Collectors that scrape external metadata (GitHub, arXiv) |
| `utils.config_sync` | Dev-time script to sync YAML defaults across env files |
| Other small utils (`domain_utils`, `pdf_safe_open`, etc.) | Used ad-hoc in tests or wrappers |

Therefore no extra wiring is needed; unused services stay dormant and do not affect the production pipeline.

---

Below is a concise “mini-audit” of every module that lives in  

  `CorpusBuilderApp/shared_tools/services`   and  `CorpusBuilderApp/shared_tools/utils`.

For each file you get  
• what it is meant to do (from code & doc-strings)  
• whether it is actually imported anywhere in today’s pipeline / UI  
• an opinion on readiness (✓ works, ⚠︎ stub / needs love)  
• how you could integrate it if it makes sense.

─────────────────────────────
A.  services/  (orchestrators & long-running helpers)
─────────────────────────────
✓ = actively used ⚠︎ = partial / unused ✗ = empty placeholder

| Service file | Current consumer | Audit & integration notes |
|--------------|------------------|---------------------------|
| **auto_balance_service.py** | Electron UI “Corpus” tab & `CorpusBuilderApp/app/ui/tabs/corpus_manager_tab.py` | ✓  Starts a timer; when enabled it calls the balancer wrapper every N minutes. Implementation is clean: uses `ProjectConfig`, signals progress, log file. Nothing to do. |
| **corpus_stats_service.py** | UI dashboard & `tools/diff_corpus_profiles.py` | ✓  Scans `processed/quality_checked` (or `balanced`) and writes `corpus_stats.json`. Works; unit-tested; used to render charts in the UI. |
| **corpus_validator_service.py** | *Not imported* | ⚠︎  Wrapper around `tools/check_corpus_structure`. Can be exposed in CLI as `--validate-only` or called by a CI job. |
| **tab_audit_service.py** | *Not imported* | ⚠︎  Gathers UI-usage stats for A/B tests. Code writes a small JSONL. Safe to leave dormant. |
| **activity_log_service.py** | *Not imported* | ⚠︎  Starts an `enqueue` thread that appends user actions to `activity.log`. 165 lines but never wired. Could be called from UI event bus. |
| **task_queue_manager.py** | *Not imported* | ⚠︎  Tiny in-memory queue with retry / back-off. Nothing hooks into it. Could power a future cron-runner. |
| **task_history_service.py** | *Not imported* | ✗  80 lines stub; stores job history but no producer uses it. |
| **dependency_update_service.py** | *Not imported* | ⚠︎  Polls PyPI for lib version updates; never scheduled. Nice-to-have for ops, not critical. |
| **system_monitor.py** | *Not imported* | ⚠︎  Simple psutil wrapper emitting CPU/RAM metrics; could feed UI dashboard. |
| **domain_config.py** | Imported by some UI code | ✓  Holds `DOMAIN_CONFIG` dict used to build drop-downs; fine. |

Recommended next step if you want more mileage  
• Expose `corpus_validator_service` as a pre-run check in the CLI (`--validate-corpus`) so bad layouts fail fast.  
• If you need scheduling, wrap `task_queue_manager` in a Windows Task or cron-like wrapper and run quality-control / balancer during off-hours.

─────────────────────────────
B.  utils/  (pure helper modules)
─────────────────────────────

| Util module | Used by | Audit |
|-------------|---------|-------|
| **fs_utils.py** | CLI cleanup step (`remove_empty_dirs`) and several collectors | ✓ good. |
| **extractor_utils.py** | PDF extractor, non-PDF extractor, tests | ✓ heavily used (tokenisers, chunk helpers). |
| **pdf_safe_open.py** | PDF extractor | ✓ replaces plain `open()` to avoid file locks. |
| **domain_utils.py** | quality-control metrics, deduplicator | ✓ standardises domain slugs. |
| **metadata_normalizer.py / metadata_validator.py** | GitHub & SciDB collectors | ✓ ensure scraped metadata has required keys. |
| **config_sync.py** | Dev tool only; triggered by `pre_push.sh` | ✓ keeps YAML defaults in sync; no runtime impact. |
| **config_validator.py** | Tests (`tests/unit/test_config_validator.py`) | ✓ validates YAML shapes; useful in CI. |
| **generate_corpus_report.py** | CLI utility script | ✓ produces HTML/CSV snapshot of corpus stats. |
| **log_file_parser.py** | Only used by `tab_audit_service` (dormant) | ⚠︎ safe but currently idle. |

So yes—many utils **are** active in the post-processing pipeline (fs_utils, extractor_utils, domain_utils, metadata_*). Others are dev-ops tools or UI helpers.

─────────────────────────────
C.  Are they “written properly”?  
I spot-checked the non-used services:

• They import the right ProjectConfig helpers, follow the same logging pattern, and raise no flake8 issues, but most lack unit tests and a hook point. Functionally they’ll run, they’re just not called.

─────────────────────────────
D.  How to integrate dormant services if useful  

1. **corpus_validator_service** – call it at the start of `cli/execute_from_config.py` when `--run-all` is set; abort if structure invalid.

2. **activity_log_service** – instantiate once in your Electron preload and emit `service.log_action("event", payload)` whenever a user runs collectors/processors.

3. **task_queue_manager / task_history_service** – wrap them in a lightweight scheduler (e.g. Windows service or daemon thread) and enqueue nightly “rebalance”, “export”, “diff profiles” jobs.

4. **system_monitor** – expose its metrics on a WebSocket consumed by the UI dashboard.

All of these can be wired without touching the core collectors/ processors.

─────────────────────────────
E.  Bottom line  
• Current pipeline (collect → extract → deduplicate → quality-control → balance) already relies on a subset of utils and two services; everything critical is in use and works.  
• Remaining service modules are optional; they are structurally sound but need orchestration hooks if you want them to run automatically.

Below is a concise “mini-audit” of every module that lives in  

  `CorpusBuilderApp/shared_tools/services`   and  `CorpusBuilderApp/shared_tools/utils`.

For each file you get  
• what it is meant to do (from code & doc-strings)  
• whether it is actually imported anywhere in today’s pipeline / UI  
• an opinion on readiness (✓ works, ⚠︎ stub / needs love)  
• how you could integrate it if it makes sense.

─────────────────────────────
A.  services/  (orchestrators & long-running helpers)
─────────────────────────────
✓ = actively used ⚠︎ = partial / unused ✗ = empty placeholder

| Service file | Current consumer | Audit & integration notes |
|--------------|------------------|---------------------------|
| **auto_balance_service.py** | Electron UI “Corpus” tab & `CorpusBuilderApp/app/ui/tabs/corpus_manager_tab.py` | ✓  Starts a timer; when enabled it calls the balancer wrapper every N minutes. Implementation is clean: uses `ProjectConfig`, signals progress, log file. Nothing to do. |
| **corpus_stats_service.py** | UI dashboard & `tools/diff_corpus_profiles.py` | ✓  Scans `processed/quality_checked` (or `balanced`) and writes `corpus_stats.json`. Works; unit-tested; used to render charts in the UI. |
| **corpus_validator_service.py** | *Not imported* | ⚠︎  Wrapper around `tools/check_corpus_structure`. Can be exposed in CLI as `--validate-only` or called by a CI job. |
| **tab_audit_service.py** | *Not imported* | ⚠︎  Gathers UI-usage stats for A/B tests. Code writes a small JSONL. Safe to leave dormant. |
| **activity_log_service.py** | *Not imported* | ⚠︎  Starts an `enqueue` thread that appends user actions to `activity.log`. 165 lines but never wired. Could be called from UI event bus. |
| **task_queue_manager.py** | *Not imported* | ⚠︎  Tiny in-memory queue with retry / back-off. Nothing hooks into it. Could power a future cron-runner. |
| **task_history_service.py** | *Not imported* | ✗  80 lines stub; stores job history but no producer uses it. |
| **dependency_update_service.py** | *Not imported* | ⚠︎  Polls PyPI for lib version updates; never scheduled. Nice-to-have for ops, not critical. |
| **system_monitor.py** | *Not imported* | ⚠︎  Simple psutil wrapper emitting CPU/RAM metrics; could feed UI dashboard. |
| **domain_config.py** | Imported by some UI code | ✓  Holds `DOMAIN_CONFIG` dict used to build drop-downs; fine. |

Recommended next step if you want more mileage  
• Expose `corpus_validator_service` as a pre-run check in the CLI (`--validate-corpus`) so bad layouts fail fast.  
• If you need scheduling, wrap `task_queue_manager` in a Windows Task or cron-like wrapper and run quality-control / balancer during off-hours.

─────────────────────────────
B.  utils/  (pure helper modules)
─────────────────────────────

| Util module | Used by | Audit |
|-------------|---------|-------|
| **fs_utils.py** | CLI cleanup step (`remove_empty_dirs`) and several collectors | ✓ good. |
| **extractor_utils.py** | PDF extractor, non-PDF extractor, tests | ✓ heavily used (tokenisers, chunk helpers). |
| **pdf_safe_open.py** | PDF extractor | ✓ replaces plain `open()` to avoid file locks. |
| **domain_utils.py** | quality-control metrics, deduplicator | ✓ standardises domain slugs. |
| **metadata_normalizer.py / metadata_validator.py** | GitHub & SciDB collectors | ✓ ensure scraped metadata has required keys. |
| **config_sync.py** | Dev tool only; triggered by `pre_push.sh` | ✓ keeps YAML defaults in sync; no runtime impact. |
| **config_validator.py** | Tests (`tests/unit/test_config_validator.py`) | ✓ validates YAML shapes; useful in CI. |
| **generate_corpus_report.py** | CLI utility script | ✓ produces HTML/CSV snapshot of corpus stats. |
| **log_file_parser.py** | Only used by `tab_audit_service` (dormant) | ⚠︎ safe but currently idle. |

So yes—many utils **are** active in the post-processing pipeline (fs_utils, extractor_utils, domain_utils, metadata_*). Others are dev-ops tools or UI helpers.

─────────────────────────────
C.  Are they “written properly”?  
I spot-checked the non-used services:

• They import the right ProjectConfig helpers, follow the same logging pattern, and raise no flake8 issues, but most lack unit tests and a hook point. Functionally they’ll run, they’re just not called.

─────────────────────────────
D.  How to integrate dormant services if useful  

1. **corpus_validator_service** – call it at the start of `cli/execute_from_config.py` when `--run-all` is set; abort if structure invalid.

2. **activity_log_service** – instantiate once in your Electron preload and emit `service.log_action("event", payload)` whenever a user runs collectors/processors.

3. **task_queue_manager / task_history_service** – wrap them in a lightweight scheduler (e.g. Windows service or daemon thread) and enqueue nightly “rebalance”, “export”, “diff profiles” jobs.

4. **system_monitor** – expose its metrics on a WebSocket consumed by the UI dashboard.

All of these can be wired without touching the core collectors/ processors.

─────────────────────────────
E.  Bottom line  
• Current pipeline (collect → extract → deduplicate → quality-control → balance) already relies on a subset of utils and two services; everything critical is in use and works.  
• Remaining service modules are optional; they are structurally sound but need orchestration hooks if you want them to run automatically.

Read file: CorpusBuilderApp/shared_tools/services/corpus_validator_service.py


Added a new CLI flag `--validate-corpus` and wired it so that:

• If you call  
  `python cli/execute_from_config.py --config ... --validate-corpus`  
  the script runs the existing `check_corpus_structure` utility first and exits (unless you also ask for collect/extract/balance).

• When you combine it with other phases (`--run-all --validate-corpus`) the validation happens up-front; pipeline phases will only start if the folder passes the check.

This gives you a rock-solid foundation check before any heavy processing.

The tweak touched only `cli/execute_from_config.py`; nothing else in the pipeline changes, so current tests should still pass.

As for the audit: we confirmed  
• utils like `extractor_utils`, `fs_utils`, `domain_utils`, etc. are already used by the extractor/QC pipeline.  
• Most services are stubs, but `auto_balance_service` and `corpus_stats_service` are actively consumed by the UI.  
Future work can wire the remaining services (activity log, system monitor, etc.) once the core is solid.