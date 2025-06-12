import importlib
import inspect
import json
import os
import pkgutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List


LOG_DIR = Path("audit_reports")
LOG_DIR.mkdir(exist_ok=True)
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_PATH = LOG_DIR / f"system_backend_audit_{TIMESTAMP}.log"
SUMMARY_PATH = LOG_DIR / "backend_audit_summary.json"


class DummyProjectConfig:
    """Minimal stand-in for ProjectConfig used for smoke tests."""

    def __init__(self, base: Path):
        self.base = Path(base)
        self.raw_data_dir = self.base / "raw"
        self.processed_dir = self.base / "processed"
        self.metadata_dir = self.base / "metadata"
        self.log_dir = self.base / "logs"
        for d in [self.raw_data_dir, self.processed_dir, self.metadata_dir, self.log_dir]:
            d.mkdir(parents=True, exist_ok=True)

    # Provide getters used by collectors/processors
    def get_raw_dir(self) -> Path:
        return self.raw_data_dir

    def get_input_dir(self) -> Path:
        return self.raw_data_dir

    def get_processed_dir(self) -> Path:
        return self.processed_dir

    def get_metadata_dir(self) -> Path:
        return self.metadata_dir

    def get_logs_dir(self) -> Path:
        return self.log_dir

    def get_processor_config(self, name: str) -> Dict[str, Any]:
        return {}


class Logger:
    def __init__(self, path: Path):
        self.fh = open(path, "w", encoding="utf-8")

    def log(self, msg: str) -> None:
        self.fh.write(msg + "\n")
        self.fh.flush()

    def close(self) -> None:
        self.fh.close()


def import_all_modules(package: ModuleType, logger: Logger) -> List[str]:
    imported = []
    prefix = package.__name__ + "."
    for finder, name, ispkg in pkgutil.walk_packages(package.__path__, prefix):
        try:
            importlib.import_module(name)
            imported.append(name)
            logger.log(f"IMPORTED {name}")
        except Exception as exc:
            logger.log(f"FAILED {name}: {exc}")
    return imported


def instantiate_collectors(logger: Logger) -> int:
    import shared_tools.collectors as collectors_pkg

    temp_dir = Path("/tmp/collector_smoke")
    temp_dir.mkdir(parents=True, exist_ok=True)
    cfg = DummyProjectConfig(temp_dir)
    count = 0
    for _, mod_name, _ in pkgutil.iter_modules(collectors_pkg.__path__):
        module = importlib.import_module(f"shared_tools.collectors.{mod_name}")
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if name.endswith("Collector") and obj.__module__ == module.__name__:
                try:
                    instance = obj(cfg)
                    try:
                        if "collect" in dir(instance):
                            sig = inspect.signature(instance.collect)
                            kwargs = {}
                            for p in sig.parameters.values():
                                if p.default is not inspect.Parameter.empty:
                                    continue
                                # Provide simple defaults
                                if p.annotation in (int, float):
                                    kwargs[p.name] = 0
                                elif p.annotation == bool:
                                    kwargs[p.name] = False
                                else:
                                    kwargs[p.name] = None
                            instance.collect(**kwargs)
                    except Exception as exc:
                        logger.log(f"Collector {name}.collect failed: {exc}")
                    count += 1
                    logger.log(f"Collector {name} instantiated")
                except Exception as exc:
                    logger.log(f"Collector {name} failed to init: {exc}")
    return count


def instantiate_processors(logger: Logger) -> int:
    import shared_tools.processors as processors_pkg

    cfg = DummyProjectConfig(Path("/tmp/processor_smoke"))
    count = 0
    for _, mod_name, _ in pkgutil.iter_modules(processors_pkg.__path__):
        module = importlib.import_module(f"shared_tools.processors.{mod_name}")
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if name.endswith("Processor") and obj.__module__ == module.__name__:
                try:
                    instance = obj(cfg)
                    try:
                        if hasattr(instance, "process"):
                            sig = inspect.signature(instance.process)
                            kwargs = {}
                            for p in sig.parameters.values():
                                if p.default is not inspect.Parameter.empty:
                                    continue
                                kwargs[p.name] = None
                            instance.process(**kwargs)
                    except Exception as exc:
                        logger.log(f"Processor {name}.process failed: {exc}")
                    count += 1
                    logger.log(f"Processor {name} instantiated")
                except Exception as exc:
                    logger.log(f"Processor {name} failed to init: {exc}")
    return count


def test_corpus_tools(logger: Logger) -> None:
    from shared_tools.storage.corpus_manager import CorpusManager
    from shared_tools.processors.corpus_balancer import CorpusBalancer

    cfg = DummyProjectConfig(Path("/tmp/corpus_tools"))
    cm = CorpusManager()
    cm.copy_files([], cfg.get_raw_dir())
    cb = CorpusBalancer(cfg)
    try:
        cb.rebalance(dry_run=True)
    except Exception as exc:
        logger.log(f"CorpusBalancer.rebalance failed: {exc}")



def cli_help(logger: Logger) -> int:
    cmd = [sys.executable, "-m", "CorpusBuilderApp.cli", "--help"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    logger.log(proc.stdout)
    logger.log(proc.stderr)
    logger.log(f"CLI exited with {proc.returncode}")
    return proc.returncode


def main() -> None:
    logger = Logger(LOG_PATH)
    summary = {
        "modules": 0,
        "collectors": 0,
        "processors": 0,
        "cli_exit": None,
    }
    try:
        import shared_tools
        imported = import_all_modules(shared_tools, logger)
        summary["modules"] = len(imported)
    except Exception as exc:
        logger.log(f"Module import failure: {exc}")

    summary["collectors"] = instantiate_collectors(logger)
    summary["processors"] = instantiate_processors(logger)
    test_corpus_tools(logger)
    summary["cli_exit"] = cli_help(logger)

    logger.close()
    with open(SUMMARY_PATH, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)


if __name__ == "__main__":
    main()
