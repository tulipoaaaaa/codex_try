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
## 7. PDF + Non-PDF Extraction Pipeline (2025-06-16)

### 7.1  Runtime environment overrides
Use **session-only** environment variables when running CLI tools locally so production paths stay untouched:

```powershell
$Env:CORPUS_ROOT    = 'G:\codex\codex_try\corpus_1'
$Env:RAW_DATA_DIR   = "$Env:CORPUS_ROOT\raw"
$Env:PROCESSED_DIR  = "$Env:CORPUS_ROOT\processed"
$Env:METADATA_DIR   = "$Env:CORPUS_ROOT\metadata"
$Env:LOGS_DIR       = "$Env:CORPUS_ROOT\logs"
```

### 7.2  Compatibility shim for `ProjectConfig`
`ProjectConfig` now exposes read-only attribute aliases so legacy modules that
reference `project.raw_data_dir` (instead of `get_raw_dir()`) work:

```python
@property
def raw_data_dir(self):
    return self.get_raw_dir()
# processed_dir, metadata_dir, logs_dir same pattern
```

No behaviour change for existing code – just wider compatibility.

### 7.3  Non-PDF extractor crash fix
`batch_nonpdf_extractor_enhanced` raised `NameError: CommentNode` when parsing
Python files.  Added a **one-line fallback** after the logger:

```python
try:
    from typed_ast import ast3 as _ta
    CommentNode = getattr(_ta, 'Comment', None)
except Exception:
    CommentNode = None  # safe fallback
```

All *.py files now process correctly (0 errors in
`corpus_1/logs/batch_nonpdf_extractor.log`).

### 7.4  Output structure: `_extracted` folder
Both extractors currently write to
`processed/_extracted/{file}.{txt|json}` regardless of domain.  The domain is
stored inside each JSON, so downstream components work, but UI tabs that rely
on per-domain folders appear empty.

**Options to organise into `processed/<domain>/…`:**
1. Run the metadata normaliser with auto-move enabled (or patch it to do so).
2. Use `CorpusManager.move_files()` in a small script to move pairs based on
the `domain` field.

### 7.5  Corpus Manager quick reference
`shared_tools.storage.corpus_manager.CorpusManager` helper methods:
- `copy_files(list, target_dir)`
- `move_files(list, target_dir)`
- `rename_files(list, pattern)` – e.g. `{index}_{original}`
- `organize_files(list, criteria='extension'|'date')`
All emit Qt signals for GUI progress bars, but work fine head-less.

### 7.6  Corpus Balancer dry-run recipe
```powershell
python - <<PY
from shared_tools.project_config import ProjectConfig
from shared_tools.processors.corpus_balancer import CorpusBalancer
cfg = ProjectConfig('CorpusBuilderApp/configs/local_corpus.yaml')
report = CorpusBalancer(cfg).rebalance(strategy='quality_weighted', dry_run=True)
print(report['analysis']['domain_analysis'])
PY
```
If happy with the plan, rerun with `dry_run=False` to execute copy/move actions.

---
## 8. Corpus maintenance pipeline – deduplication → quality-control → balancer

### 8.1  Components
| Stage | Entry-point class | YAML key | CLI auto-run | Purpose |
|-------|------------------|----------|--------------|---------|
| Deduplicator | `shared_tools.processors.deduplicator.Deduplicator` | n/a (invoked ad-hoc or via wrapper) | no | Builds an index (`deduplication_index.json`) and detects duplicates by SHA-256, file hash, normalised title and MinHash similarity. |
| Quality-control | `shared_tools.processors.quality_control.QualityControl` | `processors.quality_control` | yes (when `--extract` or `--run-all`) | Flags low-quality text (language, corruption, MT, duplication) and moves rejects to `low_quality/`. Successful files go to `processed/quality_checked/<domain>`. |
| Corpus balancer | `shared_tools.processors.corpus_balancer.CorpusBalancer` | `processors.corpus_balancer` | yes (`--balance` or `--run-all`) | Down-samples/upsamples `processed/quality_checked` to hit domain-ratio targets; writes to `processed/balanced`. |

### 8.2  Testing plan (CI or local)
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

### 8.3  Environment variables for OCR tables (recap)
`TESSERACT_OCR_TABLE_CONFIG`, `TESSERACT_OCR_TABLE_CONFIG_WIDE`, `TESSERACT_OCR_NUMERIC_CONFIG` override the hard-coded defaults in `image_table_extractor.py`. They are **optional** – leave unset for the tuned defaults.

---
## 9. *shared_tools/services* and *shared_tools/utils* – current usage map

*Services* are long-running or orchestrating helpers that sit **outside** the main collector/processor pipeline. Today only two are actively triggered by the UI layer:

| Service | Used by | Function |
|---------|---------|----------|
| `auto_balance_service.AutoBalanceService` | UI "Corpus" tab | Periodically calls the balancer wrapper every N minutes. |
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

Below is a concise "mini-audit" of every module that lives in  

  `CorpusBuilderApp/shared_tools/services`   and  `CorpusBuilderApp/shared_tools/utils`.

For each file you get  
• what it is meant to do (from code & doc-strings)  
• whether it is actually imported anywhere in today's pipeline / UI  
• an opinion on readiness (✓ works, ⚠︎ stub / needs love)  
• how you could integrate it if it makes sense.

─────────────────────────────
A.  services/  (orchestrators & long-running helpers)
─────────────────────────────
✓ = actively used ⚠︎ = partial / unused ✗ = empty placeholder

| Service file | Current consumer | Audit & integration notes |
|--------------|------------------|---------------------------|
| **auto_balance_service.py** | Electron UI "Corpus" tab & `CorpusBuilderApp/app/ui/tabs/corpus_manager_tab.py` | ✓  Starts a timer; when enabled it calls the balancer wrapper every N minutes. Implementation is clean: uses `ProjectConfig`, signals progress, log file. Nothing to do. |
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
C.  Are they "written properly"?  
I spot-checked the non-used services:

• They import the right ProjectConfig helpers, follow the same logging pattern, and raise no flake8 issues, but most lack unit tests and a hook point. Functionally they'll run, they're just not called.

─────────────────────────────
D.  How to integrate dormant services if useful  

1. **corpus_validator_service** – call it at the start of `cli/execute_from_config.py` when `--run-all` is set; abort if structure invalid.

2. **activity_log_service** – instantiate once in your Electron preload and emit `service.log_action("event", payload)` whenever a user runs collectors/processors.

3. **task_queue_manager / task_history_service** – wrap them in a lightweight scheduler (e.g. Windows service or daemon thread) and enqueue nightly "rebalance", "export", "diff profiles" jobs.

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

# Integration Notes – Local vs. Production Corpus Paths

## 1. Background
Crypto-Finance Corpus tools rely on a single `ProjectConfig` object that merges **three** sources of configuration (highest priority first):

1. **OS environment variables** (e.g. `CORPUS_ROOT`, `RAW_DATA_DIR`, …).
2. **Values passed programmatically** (e.g. `ProjectConfig(path, environment="local")`).
3. **Entries in the YAML config file** (`environment:` & `environments:` sections).

If a variable such as `CORPUS_ROOT` is present in the environment, it **overrides** whatever is specified in the YAML file – even when the active environment is set to `local`.

## 2. Symptom Observed
```
INFO  tools.check_corpus_structure: Corpus root: G:\data\production
```
While running:
```powershell
python cli/execute_from_config.py --config CorpusBuilderApp/configs/local_corpus.yaml --validate-corpus
```
… the validator reported production paths although the YAML contained:
```yaml
environment: local
environments:
  local:
    corpus_root: "G:/codex/codex_try/corpus_1"
```

## 3. Root Cause
+### Why `CORPUS_ROOT` is so disruptive
+
+`ProjectConfig` performs a *deep merge* where anything found in the OS environment completely overrides the same key from the YAML.  In particular:
+
+```python
+env_dirs = {}
+if 'CORPUS_ROOT' in os.environ:
+    env_dirs['corpus_root'] = os.environ['CORPUS_ROOT']
+# … RAW_DATA_DIR, PROCESSED_DIR, etc.
+self._deep_merge(config, {'directories': env_dirs})
+```
+
+1. The mere presence of `CORPUS_ROOT` injects **`directories.corpus_root`** into the configuration, regardless of which environment (local/test/prod) is active.
+2. Later, helper methods like `get_raw_dir()` resolve paths by first looking at the *active environment section* (`environments.local.raw_data_dir`) **but fall back to `directories.raw_data_dir`**.  If that key is missing, they derive it by appending `/raw` to the *effective* `corpus_root`.
+3. Result: once `CORPUS_ROOT` is set to `G:\data\production`, every helper (`get_raw_dir`, `get_processed_dir`, etc.) silently gravitates back to production paths—even though `environment.active` is still `local`.
+
+In other words, **`CORPUS_ROOT` acts as a single-point override that drags the whole directory tree with it.**  Clearing that variable (or redefining it) is therefore essential before any local run.
+
```

## 4. Resolution Steps (PowerShell)
```powershell
# 1. Inspect overrides
Get-ChildItem Env:CORPUS_ROOT,Env:RAW_DATA_DIR,Env:PROCESSED_DIR,Env:METADATA_DIR,Env:LOGS_DIR

# 2. Remove or redefine as needed
Remove-Item Env:CORPUS_ROOT      -ErrorAction SilentlyContinue
Remove-Item Env:RAW_DATA_DIR     -ErrorAction SilentlyContinue
Remove-Item Env:PROCESSED_DIR    -ErrorAction SilentlyContinue
Remove-Item Env:METADATA_DIR     -ErrorAction SilentlyContinue
Remove-Item Env:LOGS_DIR         -ErrorAction SilentlyContinue

# 3. Re-run validation / pipeline
python cli/execute_from_config.py --config CorpusBuilderApp/configs/local_corpus.yaml --validate-corpus
```
Expected log:
```
INFO  tools.check_corpus_structure: Corpus root: G:\codex\codex_try\corpus_1
```
No production paths should appear.

## 5. Cross-Shell equivalents
Bash / Zsh:
```bash
unset CORPUS_ROOT RAW_DATA_DIR PROCESSED_DIR METADATA_DIR LOGS_DIR
```

## 6. Recommended Practices
1. **Never export production paths globally** in your user environment.
2. For local workflows, either:
   * rely solely on the YAML (`environment: local`), **or**
   * use a per-project `.env` file loaded automatically by `ProjectConfig` (same variable names).
3. If you must switch frequently, create helper scripts:
   * `env\set_local.ps1` – sets variables for local corpus.
   * `env\set_production.ps1` – sets variables for production corpus.
4. Remove ad-hoc debug prints after resolving issues (`DEBUG: YAML environment …`).

## 7. Directory Skeleton for a New Corpus
```
corpus_1/
├─ raw/           # raw input files
├─ processed/     # generated by processors
├─ metadata/
│   └─ corpus_metadata.json  # domain, author, year, etc.
└─ logs/
```

A minimal `corpus_metadata.json`:
```json
{
  "domain": "my_domain",
  "author": "Your Name",
  "year": 2025
}
```

---
_Last updated: 2025-06-14_

---
## 10. End-to-End Pipeline Checklist (tested 2025-06-16)

### 10.1  Logical flow
```
Collectors (fred / github / annas / …)
        │  raw/<domain>/
        ▼
PDF batch extractor (batch_text_extractor_enhanced_prerefactor)
        │  – writes txt+json
        │  – calls internal normalize_metadata_in_directory()
        ▼
Non-PDF batch extractor (batch_nonpdf_extractor_enhanced)
        │  – writes txt+json
        │  – calls utils.metadata_normalizer.main()
        ▼
processed/_extracted/*.txt|*.json   ← flat layout after both extractors
        │
        ├─ optional: Metadata Normaliser / CorpusManager move to processed/<domain>/
        │
        ├─ optional: DeduplicateNonPDFOutputs
        │
        └─ QualityControl (processors.quality_control)
               │  – flags low_quality & writes to processed/low_quality
               ▼
CorpusBalancer (dry-run ⇒ analyse, real ⇒ move/copy docs in raw/)
        ▼
CorpusStatsService / dashboards / visualisers
```

### 10.2  Commands we have verified
1. **Extractors**  (session overrides set first)
   ```powershell
   # PDF
   python -m CorpusBuilderApp.shared_tools.processors.batch_text_extractor_enhanced_prerefactor \
          --config CorpusBuilderApp/configs/local_corpus.yaml --verbose
   # Non-PDF
   python -m CorpusBuilderApp.shared_tools.processors.batch_nonpdf_extractor_enhanced \
          --config CorpusBuilderApp/configs/local_corpus.yaml --verbose
   ```

2. **Structure & integrity check**
   ```powershell
   python CorpusBuilderApp/cli.py check-corpus --config CorpusBuilderApp/configs/local_corpus.yaml \
          --auto-fix --validate-metadata --check-integrity
   ```

3. **Corpus balance analysis (dry-run)**
   ```powershell
   python -c "from shared_tools.project_config import ProjectConfig\nfrom shared_tools.processors.corpus_balancer import CorpusAnalyzer\nimport pprint\ncfg = ProjectConfig('CorpusBuilderApp/configs/local_corpus.yaml')\nanalysis = CorpusAnalyzer(cfg.get_processed_dir(), recursive=True).analyze_corpus_balance()\npprint.pprint(analysis['domain_analysis'])"
   ```

4. **Corpus balancer execution (when ready)**
   ```python
   from shared_tools.project_config import ProjectConfig
   from shared_tools.processors.corpus_balancer import CorpusBalancer
   cfg = ProjectConfig('CorpusBuilderApp/configs/local_corpus.yaml')
   CorpusBalancer(cfg).rebalance(strategy='quality_weighted', dry_run=False)
   ```

### 10.3  Next tests to run
1. **QualityControl processor** – enable in YAML and run via
   `execute_from_config.py --extract` to label low-quality docs.
2. **DeduplicateNonPDFOutputs** – if needed, enable and run to remove
   near-duplicate outputs.
3. **CorpusVisualizer dashboard** – generate HTML with
   `CorpusVisualizer().create_balance_dashboard(analysis)` after the
   balancer.

After these, the full local pipeline mirrors production expectations.

---
## 11. Post-extract Organiser (NEW – 2025-06-16)

### 11.1  What it does
* Moves the flat outputs produced by the PDF and Non-PDF batch extractors from
  `processed/_extracted/` into per-domain folders `processed/<domain>/` based on
  the `domain` field inside each JSON metadata file.
* Deletes `processed/_extracted` if it becomes empty and prunes any **empty**
  directories left behind across `processed/` (calls `utils.fs_utils.remove_empty_dirs`).
* Uses `CorpusManager.move_files()` under the hood so name-clash rules remain
  identical across GUI, CLI and ad-hoc scripts.

### 11.2  Enabling it
Add the flag below to **any** ProjectConfig YAML (it lives at the root level):

```yaml
post_extract_organise:
  enabled: true
```
If omitted or set to `false` nothing changes – CI and legacy runs stay untouched.

### 11.3  Pipeline integration points
| Layer | When it runs | Notes |
|-------|--------------|-------|
| **CLI** (`cli/execute_from_config.py`) | Immediately after the extractor loop (`--extract` or `--run-all`), *before* any balancer step | Honour `--preview-only`; skipped during previews. |
| **GUI – Non-PDF wrapper** | After `batch_completed` signal fires | Appends a one-liner to the log pane: `Organised N files into D domain folders.` |
| **GUI – PDF wrapper** | Inside `_on_finished` callback | Logs via the shared logger; nothing displayed in UI unless log tab is open. |
| **Standalone** | Import & call `organise_extracted(ProjectConfig(...))` | Replaces the previous `scripts\organize_extracted.py`. |

### 11.4  Manual one-liner for existing corpora
```powershell
python - <<'PY'
from shared_tools.project_config import ProjectConfig
from shared_tools.processors.post_extract_organiser import organise_extracted
cfg = ProjectConfig('CorpusBuilderApp/configs/local_corpus.yaml')
organise_extracted(cfg)
PY
```
(Output will say how many files/domains were moved and how many empty
directories were pruned.)

### 11.5  Why keep it optional?
* CI jobs and fast unit tests may assert against the **flat** layout.
* Some downstream tools still scan `_extracted/` directly; those can migrate at
  their own pace.

_Last updated: 2025-06-16_

---
## 12. Lightweight Quality-Control Pass (2025-06-16)

The *full* QC detectors are still WIP, but we now have a pragmatic pass that
reuses the metrics already stored by the extractors.

### 12.1  How it works
* **Processor updated:** `shared_tools.processors.quality_control.QualityControl`
  now contains `process_directory()`.
* It walks `processed/<domain>/*.json`, reads the `quality_metrics` /
  `quality_score` already present, applies relaxed thresholds (score ≥ 0.4,
  token_count ≥ 50).
* Pairs that pass are **copied** to
  `processed/quality_checked/<domain>/`; those that fail go to
  `processed/low_quality/<domain>/`.
* A summary line is appended to `logs/quality_control.log`.

### 12.2  Running it
```powershell
python cli/execute_from_config.py --config CorpusBuilderApp/configs/local_corpus.yaml --extract
```
(as long as `processors.quality_control.enabled: true` in the YAML).  No extra
flags required.

### 12.3  Tunable thresholds
Edit the root-level block or per-run override:
```yaml
processors:
  quality_control:
    enabled: true
    min_quality_score: 0.4   # extractor default was 0.7
    min_token_count:   50
    checks:
      translation:
        enabled: false        # skip MT detector for now
```

### 12.4  What's next
When the language, corruption and MT detector classes are
fully implemented they can be plugged in without changing callers; tighten the
thresholds and re-run QC to re-evaluate the corpus.

---
## 13. Production config alignment (2025-06-16)

* **Deduplicator processor** now included in `shared_tools/master_config.yaml` with the same relaxed `0.70` similarity threshold and `move_instead_of_copy: true`.
* **CorpusBalancer** path keys simplified — `input_dir` / `output_dir` replaced by a single `corpus_dir: "{corpus_dir}/processed"`.
* **Post-extract organiser** flag added at root level (`post_extract_organise.enabled: true`) in both local and master configs so production clusters will automatically tidy `processed/_extracted` into per-domain folders.

No code changes were required for these YAML edits; they take effect on the next run.

---
## 14. Headless Auto-Balance Daemon (2025-06-16)

A new module `shared_tools/services/auto_balance_daemon.py` allows the
balancing/collection feedback loop to run on servers **without** the GUI.

Usage examples:

```powershell
# Single analyse → collect cycle, preview-only
python -m shared_tools.services.auto_balance_daemon \
       --config CorpusBuilderApp/shared_tools/master_config.yaml \
       --once --preview-only

# Continuous loop (every 15 min as per YAML)
python -m shared_tools.services.auto_balance_daemon \
       --config CorpusBuilderApp/shared_tools/master_config.yaml
```

Behaviour:
1. Loads `auto_balance.*` thresholds from the YAML (dominance_ratio, min_entropy,
   check_interval, start_balancing).
2. Runs the balancer in **dry-run** mode each cycle.
3. If imbalance detected, triggers all enabled collectors with missing domains
   appended to their search terms (only collectors that implement
   `set_search_terms`).
4. If `auto_balance.start_balancing: true`, executes the balancer in
   non-dry-run mode after collection.
5. Writes a summary JSON to `logs/auto_balance_last_result.json` and maintains a
   PID lock file `logs/auto_balance.pid`.

GUI interaction:
* The existing Qt-based `AutoBalanceService` is unchanged, but both GUI and
  daemon now share the **same underlying balancer logic**, so metrics and
  thresholds stay consistent.

Safe-by-default:
* Production YAML still has `auto_balance.enabled: false`; start the daemon
  manually in staging first, then flip the flag when ready.

---
_Last updated: 2025-06-14_

---
## 15. Checklist – settings you MUST change before first production run

The default repo keeps most "dangerous" features turned **off**.  Before the
pipeline can run unattended in production review and, where needed, flip the
following YAML flags (usually in `shared_tools/master_config.yaml`).

| Setting | Default | When to change |
|---------|---------|----------------|
| `auto_balance.enabled` | `false` | Set **true** to let the daemon or GUI loop start; leave false while you stage-test. |
| `auto_balance.start_balancing` | `false` | Switch to **true** once you're confident the collectors are running correctly and you want the balancer to begin moving/copying files. |
| `auto_balance.rest_enabled` | `false` | Set **true** (or pass `--rest` flag) if you need the REST `/status` & `/control` endpoints. Requires the `flask` package. |
| `auto_balance.rest_port` | `8799` | Only change if that port is occupied on your server. |
| `auto_balance.auth_token` | *(empty)* | Provide any string to demand an `X-AUTH-TOKEN` header on REST calls. |
| `post_extract_organise.enabled` | `false` in earlier configs; now **true** in master | Keep at **true** unless you still rely on the flat `_extracted/` layout. |
| `processors.deduplicator.enabled` | `true` in master | Flip to **false** if disk space is limited and you want to skip dedup. |
| `processors.corpus_balancer.dry_run` | `true` | Set **false** only after a manual review of a dry-run plan; this causes real file moves. |

Remember to `pip install flask` inside the venv if you plan to enable the REST
endpoint.

### Correct PowerShell command examples

Bash-style backslashes cause errors in PowerShell.  Use back-ticks (`` ` ``) or
write the command on **one line**.

```powershell
# One-off preview, single line
python -m shared_tools.services.auto_balance_daemon --config CorpusBuilderApp\configs\local_corpus.yaml --once --preview-only

# Multi-line with back-ticks (PowerShell continuation character)
python -m shared_tools.services.auto_balance_daemon `
    --config CorpusBuilderApp\configs\local_corpus.yaml `
    --rest `
    --preview-only
```

---
## 16. Collector wrappers – domain-bias capability audit (2025-06-16)

When the Auto-Balance daemon sees missing domains it tries to pass the domain
names into collectors via a `set_search_terms()` method. Here's the current
coverage:

| Collector wrapper | Domain-bias supported? | Method | Notes |
|-------------------|------------------------|--------|-------|
| GitHubWrapper     | ✅ Yes                | `set_search_terms(list)` | Works out of the box. |
| ArxivWrapper      | ✅ Yes                | `set_search_terms(list)` | Works out of the box. |
| ISDAWrapper       | ⚠️ Partial           | `set_search_keywords(list)` | Daemon **will not** auto-inject yet (different method name). |
| AnnasArchiveWrapper | ⚠️ Partial        | `set_search_query(str)`→ plus new alias `set_search_terms(list)` | Added alias 2025-06-16 so daemon can inject domains. |
| FREDWrapper       | N/A (series-id based) | `set_series_ids(list)`   | Not domain driven; usually static list. |
| BitMEXWrapper     | 🚫 No                 | n/a   | Scrapes predefined categories. |
| QuantopianWrapper | 🚫 No                 | n/a   | Uses fixed endpoints. |
| SciDBWrapper      | 🚫 No                 | n/a   | Category list hard-coded. |
| WebWrapper        | 🚫 No                 | `set_urls(list)` but not based on domain.

What this means:
* Missing-domain signals will automatically bias GitHub and arXiv collectors.
* Other collectors will still run but won't target specific domains until we
  extend them with a compatible setter.

_No changes made yet; this is just the audit._

---
## 17. REST API security & production switch (2025-06-16)

* In any environment where port 8799 is reachable from outside the host, set
  an authentication token in YAML:
  ```yaml
  auto_balance:
    auth_token: "PLEASE_CHANGE_ME"
  ```
  Then call the API with a header:
  ```powershell
  curl -H "X-AUTH-TOKEN: PLEASE_CHANGE_ME" http://<host>:8799/status
  ```

* Production defaults to:
  ```yaml
  auto_balance:
    enabled: true       # daemon is expected to run as a service
    rest_enabled: true  # expose /status and /control
    start_balancing: false  # keep safe until operator flips via REST/GUI
  ```
  Flip `start_balancing` to `true` once you trust the moves.

* Local `configs/local_corpus.yaml` test tweaks (min_entropy, check_interval)
  have been reset to normal values (2.0 entropy, 15-minute interval).

* `auth_token` placeholder (`PLEASE_CHANGE_ME`) has been inserted into both
  `configs/local_corpus.yaml` and `shared_tools/master_config.yaml`. Replace with
  a real secret before opening port 8799 to other hosts.



  Right—that's the right order.

What's already covered  
• All individual collectors were smoke-tested against their remote sources.  
• Every processor (text/PDF extractors, deduplicator, QC, corpus balancer) has run at least once in isolation.  
• The corpus manager can move finished artefacts into the final tree, and the balancer respects allow_downsampling = false.  
• The new headless Auto-Balance daemon runs, writes JSON summaries, and its REST endpoints are reachable with token auth.

What still needs attention

1. End-to-end pipeline rehearsal  
   a. Use a trimmed config (e.g. your `local_corpus.yaml`) that exercises the full chain:  
      collectors → processors → corpus_manager → deduplicator → balancer.  
   b. First run with `--preview-only` so nothing is written, then a real run on a small test corpus.  
   c. Check:  
      • exit code 0, no stack-traces in logs  
      • expected files appear in `corpus_1/processed/...`  
      • balancer report shows only up-sampling, never down-sampling  
      • deduplicator summary lists removed duplicates (or "0" if none)  
      • JSON status file and REST `/status` agree.

2. Automated integration test  
   • Wrap the above in a pytest (or invoke-task) so CI can replay it with `pytest -m e2e`.  
   • Use a few tiny fixtures (one PDF, one TXT) committed in `tests/assets/`.

3. GUI wiring pass  
   a. Settings panel: expose new YAML flags  
      • allow_downsampling (checkbox, defaults to off/disabled)  
      • start_balancing (toggle or button that hits REST `/control`)  
   b. Auto-Balance tab: live status indicator (poll `/status` every N sec), start/stop button.  
   c. Add read-only field showing current auth-token state (red warning if still "PLEASE_CHANGE_ME").  
   d. Make sure the new deduplicator block appears in the processor list and can be re-ordered.  
   e. Smoke-test the Qt event loop: open/close the tab, quit the app, relaunch—no stray threads or zombie daemon.

4. Documentation & housekeeping  
   • Final pass on `INTEGRATION_NOTES.md` to include GUI steps.  
   • Update screenshots if you keep them.  
   • Replace the placeholder auth token before any public or shared deployment.  
   • Bump version/CHANGELOG.

5. Optional stretch items  
   • Finish domain-bias setters for the remaining collectors.  
   • Add CI job that starts GUI in headless mode (`QT_QPA_PLATFORM=offscreen`) and ensures it loads.  
   • Dockerfile or `launch_app.bat` update so the daemon can run as a Windows service.

If the end-to-end rehearsal is green and the GUI controls work, you can cut the release/merge the feature branch.

---
## 18. 2025-06-16 End-to-end rehearsal fixes
1. **Balancing directory** – `corpus_balancer.corpus_dir` must point to the *parent* `processed/` directory, not `processed/_extracted`.  All production configs (`master_config.yaml`, `local_corpus.yaml`) already use the correct path; only the new `e2e_trial.yaml` was updated.
2. **Processor ordering** – keep `corpus_balancer` as the last item in `enabled_processors` so it executes after the post-extract organiser has moved files into their domain folders.
3. **Content-similarity dedup** – install `datasketch>=1.6.5` in the venv to enable LSH duplicate detection and silence runtime warnings.
4. **Fast test runs** – for smoke tests only, disable heavy PDF features:

```yaml
processors:
  pdf_batch:
    features:
      ocr:    false   # skip Tesseract
      tables: false   # skip Camelot table scan
      images: false   # skip chart/image detection
```
Production configs keep all three features enabled.



  Right—that's the right order.

What's already covered  
• All individual collectors were smoke-tested against their remote sources.  
• Every processor (text/PDF extractors, deduplicator, QC, corpus balancer) has run at least once in isolation.  
• The corpus manager can move finished artefacts into the final tree, and the balancer respects allow_downsampling = false.  
• The new headless Auto-Balance daemon runs, writes JSON summaries, and its REST endpoints are reachable with token auth.

What still needs attention

1. End-to-end pipeline rehearsal  
   a. Use a trimmed config (e.g. your `local_corpus.yaml`) that exercises the full chain:  
      collectors → processors → corpus_manager → deduplicator → balancer.  
   b. First run with `--preview-only` so nothing is written, then a real run on a small test corpus.  
   c. Check:  
      • exit code 0, no stack-traces in logs  
      • expected files appear in `corpus_1/processed/...`  
      • balancer report shows only up-sampling, never down-sampling  
      • deduplicator summary lists removed duplicates (or "0" if none)  
      • JSON status file and REST `/status` agree.

2. Automated integration test  
   • Wrap the above in a pytest (or invoke-task) so CI can replay it with `pytest -m e2e`.  
   • Use a few tiny fixtures (one PDF, one TXT) committed in `tests/assets/`.

3. GUI wiring pass  
   a. Settings panel: expose new YAML flags  
      • allow_downsampling (checkbox, defaults to off/disabled)  
      • start_balancing (toggle or button that hits REST `/control`)  
   b. Auto-Balance tab: live status indicator (poll `/status` every N sec), start/stop button.  
   c. Add read-only field showing current auth-token state (red warning if still "PLEASE_CHANGE_ME").  
   d. Make sure the new deduplicator block appears in the processor list and can be re-ordered.  
   e. Smoke-test the Qt event loop: open/close the tab, quit the app, relaunch—no stray threads or zombie daemon.

4. Documentation & housekeeping  
   • Final pass on `INTEGRATION_NOTES.md` to include GUI steps.  
   • Update screenshots if you keep them.  
   • Replace the placeholder auth token before any public or shared deployment.  
   • Bump version/CHANGELOG.

5. Optional stretch items  
   • Finish domain-bias setters for the remaining collectors.  
   • Add CI job that starts GUI in headless mode (`QT_QPA_PLATFORM=offscreen`) and ensures it loads.  
   • Dockerfile or `launch_app.bat` update so the daemon can run as a Windows service.

If the end-to-end rehearsal is green and the GUI controls work, you can cut the release/merge the feature branch.

---