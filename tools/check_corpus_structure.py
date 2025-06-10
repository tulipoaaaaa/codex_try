"""
Module: check_corpus_structure
Purpose: Utility to validate corpus folder structure for the active ProjectConfig.
"""

import argparse
import logging
import json
from pathlib import Path
from typing import Iterable

from shared_tools.processors.corruption_detector import CorruptionDetector

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


def validate_metadata_files(cfg: ProjectConfig) -> None:
    """Validate JSON metadata files under ``cfg.get_metadata_dir()``."""
    meta_root = Path(cfg.get_metadata_dir())
    required = {"domain", "author", "year"}
    if not meta_root.exists():
        logger.warning("Metadata directory missing: %s", meta_root)
        return

    for meta_file in meta_root.rglob("*.json"):
        try:
            with open(meta_file, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("Invalid metadata JSON %s: %s", meta_file, exc)
            continue

        missing = [k for k in required if k not in data]
        if missing:
            logger.warning(
                "Metadata file %s missing fields: %s",
                meta_file,
                ", ".join(missing),
            )


def check_corpus_structure(
    config: ProjectConfig,
    *,
    validate_metadata: bool = False,
    auto_fix: bool = False,
    check_integrity: bool = False,
) -> None:
    """Validate corpus directory layout for the active environment.

    Parameters
    ----------
    config:
        Active :class:`ProjectConfig` instance.
    validate_metadata:
        When ``True`` also run :func:`validate_metadata_files`.
    auto_fix:
        When ``True`` create any missing directories before logging warnings.
    check_integrity:
        When ``True`` sample domain files with :class:`CorruptionDetector`.
    """
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
            if auto_fix:
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    logger.info("Created missing directory %s", path)
                except Exception as exc:  # pragma: no cover - best effort
                    logger.warning("Failed to create %s: %s", path, exc)
            logger.warning("Missing directory %s", path)
            if not path.exists():
                # could not create
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
                if auto_fix:
                    for d in missing:
                        try:
                            (path / d).mkdir(parents=True, exist_ok=True)
                            logger.info("Created missing domain %s in %s", d, path)
                        except Exception as exc:  # pragma: no cover - best effort
                            logger.warning("Failed to create domain %s in %s: %s", d, path, exc)
                logger.warning(
                    "Missing domain directories in %s: %s",
                    path,
                    ", ".join(missing),
                )

        if check_integrity and path.name in {"raw", "processed"}:
            detector = CorruptionDetector()
            for domain_dir in domain_subs:
                samples = [f for f in domain_dir.iterdir() if f.is_file()][:3]
                for sample in samples:
                    try:
                        text = sample.read_text(errors="ignore")
                        result = detector.detect(text)
                        if result.get("is_corrupted"):
                            logger.warning("File appears corrupted: %s", sample)
                    except Exception as exc:  # pragma: no cover - best effort
                        logger.warning("Integrity check failed for %s: %s", sample, exc)

    if validate_metadata:
        validate_metadata_files(config)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check corpus folder structure")
    parser.add_argument("--config", required=True, help="Path to ProjectConfig YAML")
    parser.add_argument(
        "--validate-metadata",
        action="store_true",
        help="Also validate metadata JSON files",
    )
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Create missing directories before checking",
    )
    parser.add_argument(
        "--check-integrity",
        action="store_true",
        help="Sample files with CorruptionDetector",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    cfg = ProjectConfig.from_yaml(args.config)
    check_corpus_structure(
        cfg,
        validate_metadata=args.validate_metadata,
        auto_fix=args.auto_fix,
        check_integrity=args.check_integrity,
    )


if __name__ == "__main__":
    main()

# Example usage:
# python tools/check_corpus_structure.py --config examples/project_config.yaml
