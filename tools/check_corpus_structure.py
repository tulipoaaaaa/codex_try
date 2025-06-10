"""
Module: check_corpus_structure
Purpose: Utility to validate corpus folder structure for the active ProjectConfig.
"""

import argparse
import logging
from pathlib import Path
from typing import Iterable

from shared_tools.project_config import ProjectConfig

logger = logging.getLogger(__name__)


def _is_writable(path: Path) -> bool:
    """Return True if the given directory is writable."""
    try:
        test_file = path / ".write_test"
        with open(test_file, "w", encoding="utf-8") as fh:
            fh.write("test")
        test_file.unlink()
        return True
    except Exception:
        return False


def _has_contents(path: Path) -> bool:
    """Return True if the directory has any children."""
    try:
        next(path.iterdir())
        return True
    except StopIteration:
        return False
    except Exception:
        return False


def check_corpus_structure(config: ProjectConfig) -> None:
    """Validate corpus directory layout for the active environment."""
    corpus_root = Path(config.get_corpus_dir())
    logger.info("Corpus root: %s", corpus_root)

    required = {
        "raw": Path(config.get_raw_dir()),
        "processed": Path(config.get_processed_dir()),
        "metadata": Path(config.get_metadata_dir()),
        "logs": Path(config.get_logs_dir()),
    }

    domains = list(config.get("domains", {}).keys())

    for name, path in required.items():
        if not path.exists():
            logger.warning("Missing directory %s", path)
            continue
        if not path.is_dir():
            logger.warning("Path is not a directory: %s", path)
            continue
        if not _is_writable(path):
            logger.warning("Directory not writable: %s", path)
        if not _has_contents(path):
            logger.warning("Directory appears empty: %s", path)
        domain_subs = [d for d in path.iterdir() if d.is_dir()]
        if not domain_subs:
            logger.warning("No domain folders found in %s", path)
        else:
            missing = [d for d in domains if not (path / d).exists()]
            if missing:
                logger.warning(
                    "Missing domain directories in %s: %s",
                    path,
                    ", ".join(missing),
                )


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check corpus folder structure")
    parser.add_argument("--config", required=True, help="Path to ProjectConfig YAML")
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    cfg = ProjectConfig.from_yaml(args.config)
    check_corpus_structure(cfg)


if __name__ == "__main__":
    main()

# Example usage:
# python tools/check_corpus_structure.py --config examples/project_config.yaml
