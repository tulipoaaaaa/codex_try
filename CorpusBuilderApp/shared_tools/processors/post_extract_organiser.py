from __future__ import annotations

"""shared_tools.processors.post_extract_organiser

Light-weight helper that **moves** the flat outputs written by the PDF / Text
extractors from ``processed/_extracted`` into domain-level sub-folders
``processed/<domain>/``. It uses :pyclass:`shared_tools.storage.corpus_manager.CorpusManager`
for the actual file moves so name collision behaviour stays consistent across
CLI and GUI.

The module exposes a single public function – :pyfunc:`organise_extracted` – so
callers do not need to instantiate classes or think about thread-safety. The
function is intentionally synchronous; the surrounding wrapper / CLI can decide
whether to run it on a background thread if needed.
"""

from pathlib import Path
import json
import logging
from typing import Iterable, Dict, List, Tuple

from shared_tools.storage.corpus_manager import CorpusManager
from shared_tools.utils.fs_utils import remove_empty_dirs
from shared_tools.project_config import ProjectConfig

__all__ = ["organise_extracted"]

logger = logging.getLogger(__name__)


def _bucket_files_by_domain(base: Path, known_domains: set[str]) -> Dict[str, List[Path]]:
    """Return mapping ``domain -> [files]`` found under *base*.

    The helper assumes *base* only contains ``.txt`` and ``.json`` pairs written
    by the extractors. Metadata is expected in the ``.json`` companion file; if
    a metadata file is malformed or the domain missing the entry is bucketed
    under ``"unknown"`` so we never lose data.
    """

    buckets: Dict[str, List[Path]] = {}
    for meta_file in base.glob("*.json"):
        try:
            # Explicit UTF-8 read avoids Windows cp1252 auto-decode errors.
            with meta_file.open("r", encoding="utf-8", errors="strict") as fh:
                meta = json.load(fh)
            domain = (meta.get("domain") or "unknown").lower()
        except UnicodeDecodeError:
            # Fallback – skip undecodable bytes so we still get the domain.
            with meta_file.open("r", encoding="utf-8", errors="ignore") as fh:
                meta = json.load(fh)
            domain = "unknown"
        except json.JSONDecodeError as exc:
            logger.warning("Metadata JSON decode error for %s: %s", meta_file, exc)
            domain = "unknown"

        # If domain still unknown try to infer from filename slug
        if (domain == "unknown" or not domain) and known_domains:
            stem = meta_file.stem.lower()
            # Pick the *longest* matching domain that is a prefix of the stem
            for cand in sorted(known_domains, key=len, reverse=True):
                if stem.startswith(cand + "_"):
                    domain = cand
                    break

        # Ensure bucket initialised even if .txt is missing – keeps behaviour
        # consistent with original ad-hoc script.
        bucket = buckets.setdefault(domain, [])
        bucket.append(meta_file)

        txt_path = meta_file.with_suffix(".txt")
        if txt_path.exists():
            bucket.append(txt_path)
        else:  # pragma: no cover – malformed extractor output
            logger.debug("Missing .txt companion for metadata: %s", meta_file)

    return buckets


def organise_extracted(
    config: ProjectConfig,
    *,
    overwrite: bool = False,
    rename_conflicts: bool = False,
    delete_empty_dirs: bool = True,
) -> Tuple[int, int]:
    """Move files from ``processed/_extracted`` into domain folders.

    Parameters
    ----------
    config:
        Active :pyclass:`ProjectConfig` instance.
    overwrite, rename_conflicts:
        Passed through to :pyfunc:`CorpusManager.move_files`.
    delete_empty_dirs:
        If *True* any empty directories left behind inside *processed* are
        removed via :pyfunc:`shared_tools.utils.fs_utils.remove_empty_dirs`.

    Returns
    -------
    tuple
        ``(files_moved, domains_touched)`` – useful for logging/UI feedback.
    """

    try:
        processed_dir = config.get_processed_dir()
    except Exception:
        # Legacy support – fall back to dict entry
        processed_dir = Path(config.get("environments.local.processed_dir", "."))

    base = processed_dir / "_extracted"
    if not base.exists():
        logger.info("organise_extracted – no _extracted folder found (skipping)")
        return (0, 0)

    logger.info("organise_extracted – starting organisation in %s", base)

    # Known corpus domains from ProjectConfig for filename fallback detection
    try:
        known_domains = {d.lower() for d in (config.get("domains", {}) or {}).keys()}
    except Exception:
        known_domains = set()

    buckets = _bucket_files_by_domain(base, known_domains)
    cm = CorpusManager()

    total_files = 0
    for domain, files in buckets.items():
        target_dir = processed_dir / domain
        try:
            cm.move_files(files, target_dir, overwrite=overwrite, rename_conflicts=rename_conflicts)
            total_files += len(files)
        except Exception as exc:  # pragma: no cover – move failure
            logger.error("Failed to move files for domain '%s': %s", domain, exc)

    # Try to delete _extracted if empty now
    try:
        base.rmdir()
    except OSError:
        logger.debug("organise_extracted – _extracted not empty after move")

    # Optional final cleanup of empty directories underneath processed_dir
    if delete_empty_dirs:
        removed = remove_empty_dirs(processed_dir)
        logger.info("organise_extracted – removed %d empty dirs", len(removed))

    logger.info("organise_extracted – finished (moved %d files across %d domains)", total_files, len(buckets))

    # ------------------------------------------------------------------
    # Second pass: if a residual 'unknown' folder exists beneath processed
    # try to organise its contents as well (helps when organiser is run twice)
    # ------------------------------------------------------------------
    residual_unknown = processed_dir / "unknown"
    if residual_unknown.exists():
        logger.info("organise_extracted – second pass on processed/unknown …")
        buckets2 = _bucket_files_by_domain(residual_unknown, known_domains)
        if len(buckets2) > 1 or "unknown" not in buckets2:
            for dom, files in buckets2.items():
                if dom == "unknown":
                    continue
                try:
                    cm.move_files(files, processed_dir / dom, overwrite=overwrite, rename_conflicts=rename_conflicts)
                    total_files += len(files)
                except Exception as exc:
                    logger.error("Second-pass move failed for '%s': %s", dom, exc)

        # Clean up unknown dir if empty
        try:
            residual_unknown.rmdir()
        except OSError:
            pass

        # Final empty-dir sweep again if we moved more files
        if delete_empty_dirs:
            remove_empty_dirs(processed_dir)

    return (total_files, len(buckets)) 