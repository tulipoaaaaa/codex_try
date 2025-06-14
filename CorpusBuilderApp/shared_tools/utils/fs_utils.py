from __future__ import annotations

"""shared_tools.utils.fs_utils

Utility helpers for interacting with the local filesystem. At the moment this
module only exposes :pyfunc:`remove_empty_dirs`, but it can be extended with
additional helpers in the future.

The implementation purposefully relies only on the Python standard library so
it works in constrained execution environments where third-party dependencies
may be unavailable.
"""

import logging
import os
from pathlib import Path
from typing import List

__all__ = ["remove_empty_dirs"]

logger = logging.getLogger(__name__)


def _is_dir_empty(path: Path) -> bool:
    """Return ``True`` iff *path* contains **no** children.

    The directory is considered empty if ``Path.iterdir`` yields no entries. This
    implies that directories containing only dot-files (e.g. ``.gitkeep``) are
    *not* removed because dot-files are still regular entries.
    """

    try:
        next(path.iterdir())
    except StopIteration:
        return True
    except FileNotFoundError:
        # Directory vanished in between checks; treat as non-existent which is
        # logically equivalent to "empty" for our purposes.
        return True
    except PermissionError:  # pragma: no cover – rare on Windows but worth handling
        logger.warning("Skipping directory due to permission error: %s", path)
        return False
    return False


def remove_empty_dirs(
    root: str | Path,
    *,
    remove_root: bool = False,
    max_depth: int | None = None,
) -> List[Path]:
    """Recursively delete empty directories beneath *root*.

    Parameters
    ----------
    root:
        The top-level directory that will be scanned. It may be provided as a
        string or :class:`~pathlib.Path` instance.
    remove_root:
        If ``True`` the *root* directory itself will also be removed **iff** it
        becomes empty after cleaning up its children. Defaults to ``False`` so
        that the caller retains explicit control over whether the root should
        survive.
    max_depth:
        Optional safety limiter to restrict recursion depth. This counts from
        *root* (depth 0). ``None`` means no explicit limit.

    Returns
    -------
    list[pathlib.Path]
        A list of directories that were actually removed. Useful for logging or
        unit tests.
    """

    root_path = Path(root).expanduser().resolve()
    if not root_path.exists():
        logger.debug("Cleanup – root directory does not exist: %s", root_path)
        return []

    removed: List[Path] = []

    # Walk the tree bottom-up so that child directories are handled before their
    # parents. This mirrors the behaviour of ``os.walk`` when ``topdown=False``.
    for current_dir, dirnames, _ in os.walk(root_path, topdown=False):
        current_path = Path(current_dir)

        # Fast path: if depth exceeded, skip. This is evaluated only if max_depth
        # is provided so we avoid an extra call to ``Path.relative_to`` in the
        # common unlimited case.
        if max_depth is not None:
            try:
                depth = len(current_path.relative_to(root_path).parts)
            except ValueError:
                # Should never happen because ``current_path`` is produced by
                # the walk starting at ``root_path``.
                depth = 0
            if depth > max_depth:
                continue

        # Decide whether to attempt removal.
        if current_path == root_path and not remove_root:
            continue

        if _is_dir_empty(current_path):
            try:
                current_path.rmdir()
                removed.append(current_path)
            except OSError as exc:  # pragma: no cover – dir might become non-empty in between
                logger.debug("Failed to remove directory %s: %s", current_path, exc)

    return removed 