"""
Module: execute_from_config
Purpose: CLI entry point to run collectors and processors defined in a config.
"""

import argparse
import json
import logging
from typing import List
import yaml
import os
import numpy as np
import datetime

from shared_tools.project_config import ProjectConfig
from shared_tools.ui_wrappers.wrapper_factory import (
    create_collector_wrapper,
    create_processor_wrapper,
)
from shared_tools.ui_wrappers.processors.corpus_balancer_wrapper import CorpusBalancerWrapper
from shared_tools.logging_config import setup_logging

# ---------------------------------------------------------------------------
# Headless Qt bootstrap
# ---------------------------------------------------------------------------
import sys

# When collectors/processors pull in UI wrappers they may instantiate QWidget
# objects.  In a GUI session the QApplication already exists, but when running
# from the CLI it does not, leading to the runtime error:
#   "QWidget: Must construct a QApplication before a QWidget"
# We start a minimal off-screen QApplication so Qt has a valid event loop while
# keeping the CLI fully head-less.

if "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

try:
    from PySide6.QtWidgets import QApplication  # type: ignore

    if QApplication.instance() is None:
        _qt_cli_app = QApplication(sys.argv[:1] or ["cb_cli"])
except Exception:
    # Qt not available or failed to initialize – wrappers that need QWidget
    # will still raise, but we tried.  Safely continue so non-Qt parts work.
    _qt_cli_app = None

logger = logging.getLogger(__name__)


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute pipeline components configured in a ProjectConfig YAML"
    )
    parser.add_argument("--config", required=True, help="Path to ProjectConfig YAML")
    parser.add_argument("--run-all", action="store_true", help="Run collectors, processors and balancer")
    parser.add_argument("--collect", action="store_true", help="Run enabled collectors")
    parser.add_argument("--extract", action="store_true", help="Run enabled processors")
    parser.add_argument("--balance", action="store_true", help="Run corpus balancer")
    parser.add_argument(
        "--preview-only",
        action="store_true",
        help="Preview modules without executing",
    )
    parser.add_argument(
        "--cleanup-empty",
        action="store_true",
        help="Recursively delete empty directories in raw and processed corpus roots after the run",
    )
    parser.add_argument(
        "--validate-corpus",
        action="store_true",
        help="Run corpus directory structure validation and exit (unless other phases also selected)",
    )
    return parser.parse_args(argv)


def load_config(path: str) -> ProjectConfig:
    # First, peek at the YAML to see what environment it specifies
    with open(path, 'r') as f:
        yaml_data = yaml.safe_load(f)
    
    # Use the environment specified in YAML, falling back to env-var or 'test'
    yaml_env = yaml_data.get('environment')
    if isinstance(yaml_env, str):
        # Legacy format: environment: "local"
        env_to_use = yaml_env
    elif isinstance(yaml_env, dict):
        # New format: environment: { active: "local" }
        env_to_use = yaml_env.get('active', 'test')
    else:
        # No environment in YAML, use env-var or default
        env_to_use = None
    
    return ProjectConfig(path, environment=env_to_use)


def enabled_modules(config: ProjectConfig, section: str) -> List[str]:
    modules = config.get(section, {}) or {}
    return [name for name, cfg in modules.items() if isinstance(cfg, dict) and cfg.get("enabled", False)]


def run_collectors(config: ProjectConfig, names: List[str], preview: bool = False):
    if not names:
        raise RuntimeError("No enabled collectors found in configuration")
    for name in names:
        if preview:
            print(f"collector:{name}")
            continue
        logger.info("Running collector: %s", name)
        try:
            wrapper = create_collector_wrapper(name, config)
            # ------------------------------------------------------------------
            # Ensure YAML-specified parameters (e.g. AnnasArchive search_query)
            # are applied when running head-less via CLI.  In the GUI this is
            # done explicitly; replicate the behaviour here so that
            # `execute_from_config --run-all` honours keys under
            # `collectors.<name>` such as search_query, max_attempts, etc.
            # ------------------------------------------------------------------
            if hasattr(wrapper, "refresh_config"):
                try:
                    wrapper.refresh_config()
                except Exception as exc:  # pragma: no cover – defensive
                    logger.warning("%s.refresh_config() failed: %s", name, exc)
        except Exception as e:  # pragma: no cover - simple wrapper creation failure
            raise RuntimeError(f"Failed to create collector wrapper '{name}'") from e
        wrapper.start()
        if getattr(wrapper, "worker", None):
            wrapper.worker.wait()
        logger.info("Collector %s finished", name)


def run_processors(config: ProjectConfig, names: List[str], preview: bool = False):
    if not names:
        raise RuntimeError("No enabled processors found in configuration")
    for name in names:
        wrapper_name = "text" if name in {"nonpdf", "text"} else name
        if preview:
            print(f"processor:{wrapper_name}")
            continue
        logger.info("Running processor: %s", wrapper_name)
        try:
            wrapper = create_processor_wrapper(wrapper_name, config)
        except Exception as e:  # pragma: no cover - simple wrapper creation failure
            raise RuntimeError(f"Failed to create processor wrapper '{wrapper_name}'") from e
        wrapper.start()
        if getattr(wrapper, "worker", None):
            wrapper.worker.wait()
        logger.info("Processor %s finished", wrapper_name)


def run_balancer(config: ProjectConfig, preview: bool = False):
    enabled = config.get("processors.corpus_balancer.enabled", False) or config.get(
        "corpus_balancer.enabled", False
    )
    if not enabled:
        raise RuntimeError("Corpus balancer not enabled in configuration")
    if preview:
        print("balancer:corpus_balancer")
        return
    logger.info("Running corpus balancer")
    logs_dir = config.get_logs_dir()
    logs_dir.mkdir(parents=True, exist_ok=True)
    balancer = CorpusBalancerWrapper(config)
    try:
        stats = balancer.rebalance()
    except AttributeError:
        from shared_tools.processors.corpus_balancer import CorpusBalancer
        stats = CorpusBalancer(config).rebalance()

    if isinstance(stats, dict):
        try:
            def _convert(obj):
                if isinstance(obj, dict):
                    return {str(k): _convert(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [_convert(v) for v in obj]
                if isinstance(obj, (np.integer,)):
                    return int(obj)
                if isinstance(obj, (np.floating,)):
                    return float(obj)
                if isinstance(obj, (datetime.date, datetime.datetime)):
                    return obj.isoformat()
                return obj

            json_path = logs_dir / "corpus_balance.json"
            with open(json_path, "w") as f:
                json.dump(_convert(stats), f, indent=2)
            print(json.dumps(_convert(stats), indent=2))
        except Exception as e:  # pragma: no cover - disk write issues
            logger.error("Failed to save balance results: %s", e)

    logger.info("Corpus balancer completed")


def main(argv: List[str] | None = None):
    args = parse_args(argv)
    setup_logging()
    config = load_config(args.config)

    run_collect = args.run_all or args.collect
    run_extract = args.run_all or args.extract
    run_balance = args.run_all or args.balance
    run_validate = args.validate_corpus
    preview = args.preview_only

    # Decide whether to trigger automatic directory cleanup. If the user passed
    # the flag explicitly we honour it. Otherwise we default to running cleanup
    # only when --run-all is specified so that standalone preview calls remain
    # fast and non-destructive.
    run_cleanup = args.cleanup_empty or args.run_all

    if not any([run_collect, run_extract, run_balance, run_validate]):
        raise RuntimeError("No phases selected to run (use --collect / --extract / --balance / --run-all or --validate-corpus)")

    # ------------------------------------------------------------------
    # Optional pre-flight corpus structure validation (run first)
    # ------------------------------------------------------------------
    if run_validate:
        try:
            from tools.check_corpus_structure import check_corpus_structure

            check_corpus_structure(config, validate_metadata=True, auto_fix=False, check_integrity=False)
        except ModuleNotFoundError:
            logging.warning("check_corpus_structure utility not available; skipping validation")
        if run_validate and not any([run_collect, run_extract, run_balance]):
            # User only wanted validation, so we're done.
            return

    if run_collect:
        collectors = config.get("enabled_collectors") or enabled_modules(config, "collectors")
        run_collectors(config, collectors, preview)

    if run_extract:
        processors = (
            config.get("enabled_processors")
            or enabled_modules(config, "extractors")
            or enabled_modules(config, "processors")
        )
        processors = [p for p in processors if p != "corpus_balancer"]
        run_processors(config, processors, preview)

        # ------------------------------------------------------------------
        # Optional post-extraction organisation – move _extracted into domains
        # ------------------------------------------------------------------
        organise_enabled = config.get('post_extract_organise.enabled', False)
        if organise_enabled and not preview:
            try:
                from shared_tools.processors.post_extract_organiser import organise_extracted
                files_moved, domains = organise_extracted(config)
                logger.info("Post-extract organiser moved %d files into %d domains", files_moved, domains)
            except Exception as exc:  # pragma: no cover – defensive
                logger.error("Post-extract organiser failed: %s", exc)

    if run_balance:
        run_balancer(config, preview)

    # ------------------------------------------------------------------
    # Final housekeeping – remove empty directories created during the run
    # ------------------------------------------------------------------
    if run_cleanup and not preview:
        try:
            from shared_tools.utils.fs_utils import remove_empty_dirs

            targets = {
                config.get_raw_dir(),
                config.get_processed_dir(),
            }

            removed_total = 0
            for path in targets:
                removed_total += len(remove_empty_dirs(path))

            logger.info("Cleanup completed – %d empty directories removed", removed_total)
        except Exception as exc:  # pragma: no cover – defensive guard
            logger.warning("Directory cleanup skipped due to unexpected error: %s", exc)


if __name__ == "__main__":
    main()

# Example usage:
# python cli/execute_from_config.py --config examples/project_config.yaml --run-all
