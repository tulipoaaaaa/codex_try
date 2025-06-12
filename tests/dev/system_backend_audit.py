import os
import sys
import importlib
import pkgutil
import traceback
import subprocess
import json
import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

AUDIT_DIR = Path('audit_reports')
AUDIT_DIR.mkdir(exist_ok=True)
TIMESTAMP = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
LOG_FILE = AUDIT_DIR / f'system_backend_audit_{TIMESTAMP}.log'
SUMMARY_FILE = AUDIT_DIR / 'backend_audit_summary.json'

# Helper: log to file
class Logger:
    def __init__(self, log_path):
        self.log_path = log_path
    def log(self, msg):
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
    def log_exc(self, msg):
        self.log(msg + '\n' + traceback.format_exc())

logger = Logger(str(LOG_FILE))

# Helper: DummyProjectConfig fallback
class DummyProjectConfig:
    def get(self, *a, **k):
        return {}
    def get_input_dir(self):
        return '/tmp'
    def get_logs_dir(self):
        return '/tmp'

# 1. Import every module under shared_tools, app/backend, app/cli, etc.
MODULES = []
for pkg_root in ['CorpusBuilderApp/shared_tools', 'CorpusBuilderApp/app']:
    for dirpath, dirnames, filenames in os.walk(pkg_root):
        for fname in filenames:
            if fname.endswith('.py') and fname != '__init__.py':
                mod_path = os.path.relpath(os.path.join(dirpath, fname), '.')
                mod_name = mod_path.replace('/', '.').replace('\\', '.').replace('.py', '')
                MODULES.append(mod_name)

imported_modules = []
for mod in MODULES:
    try:
        imported = importlib.import_module(mod)
        imported_modules.append(mod)
        logger.log(f'IMPORTED: {mod}')
    except Exception as e:
        logger.log_exc(f'FAILED IMPORT: {mod}')

# 2. Instantiate each Collector class and run .collect()
collector_classes = []
collector_results = []
for mod in imported_modules:
    try:
        m = sys.modules[mod]
        for name in dir(m):
            obj = getattr(m, name)
            if isinstance(obj, type) and 'Collector' in name and callable(getattr(obj, 'collect', None)):
                collector_classes.append(f'{mod}.{name}')
                try:
                    with TemporaryDirectory() as tmpdir:
                        inst = obj(DummyProjectConfig())
                        result = inst.collect(tmpdir)
                        collector_results.append((f'{mod}.{name}', 'OK'))
                        logger.log(f'COLLECTOR OK: {mod}.{name}')
                except Exception as e:
                    collector_results.append((f'{mod}.{name}', 'FAIL'))
                    logger.log_exc(f'COLLECTOR FAIL: {mod}.{name}')
    except Exception:
        logger.log_exc(f'COLLECTOR ENUM FAIL: {mod}')

# 3. Instantiate each Processor class and run .process()
processor_classes = []
processor_results = []
for mod in imported_modules:
    try:
        m = sys.modules[mod]
        for name in dir(m):
            obj = getattr(m, name)
            if isinstance(obj, type) and 'Processor' in name and callable(getattr(obj, 'process', None)):
                processor_classes.append(f'{mod}.{name}')
                try:
                    inst = obj()
                    result = inst.process()
                    processor_results.append((f'{mod}.{name}', 'OK'))
                    logger.log(f'PROCESSOR OK: {mod}.{name}')
                except Exception as e:
                    processor_results.append((f'{mod}.{name}', 'FAIL'))
                    logger.log_exc(f'PROCESSOR FAIL: {mod}.{name}')
    except Exception:
        logger.log_exc(f'PROCESSOR ENUM FAIL: {mod}')

# 4. CorpusManager & CorpusBalancer
corpus_results = []
for mod in imported_modules:
    try:
        m = sys.modules[mod]
        for name in dir(m):
            obj = getattr(m, name)
            if name in ['CorpusManager', 'CorpusBalancer'] and isinstance(obj, type):
                try:
                    inst = obj(DummyProjectConfig())
                    for method in ['load_corpus', 'rebalance', 'save_state']:
                        if hasattr(inst, method):
                            getattr(inst, method)()
                    corpus_results.append((f'{mod}.{name}', 'OK'))
                    logger.log(f'CORPUS OK: {mod}.{name}')
                except Exception as e:
                    corpus_results.append((f'{mod}.{name}', 'FAIL'))
                    logger.log_exc(f'CORPUS FAIL: {mod}.{name}')
    except Exception:
        logger.log_exc(f'CORPUS ENUM FAIL: {mod}')

# 5. CLI entry-point
cli_result = None
try:
    env = os.environ.copy()
    env['PYTHONPATH'] = PROJECT_ROOT + os.pathsep + env.get('PYTHONPATH', '')
    proc = subprocess.run([sys.executable, '-m', 'CorpusBuilderApp.cli', '--help'], capture_output=True, text=True, timeout=20, env=env)
    cli_result = {'exit_code': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr}
    logger.log(f'CLI OK: exit {proc.returncode}')
except Exception as e:
    cli_result = {'exit_code': -1, 'stdout': '', 'stderr': str(e)}
    logger.log_exc('CLI FAIL')

# 6. Write JSON summary
summary = {
    'modules_imported': len(imported_modules),
    'collector_classes': len(collector_classes),
    'processor_classes': len(processor_classes),
    'corpus_classes': len(corpus_results),
    'cli_exit_code': cli_result['exit_code'] if cli_result else None,
    'collectors': collector_results,
    'processors': processor_results,
    'corpus': corpus_results,
    'cli': cli_result,
    'log_file': str(LOG_FILE),
}
with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2)

print(f'Backend system audit complete. Log: {LOG_FILE}  Summary: {SUMMARY_FILE}') 