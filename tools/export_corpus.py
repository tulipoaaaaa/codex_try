"""Export corpus data with manifest and ZIP packaging."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterable
import zipfile

logger = logging.getLogger(__name__)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create corpus export archive")
    parser.add_argument(
        "--corpus-root",
        required=True,
        help="Path to corpus root directory",
    )
    parser.add_argument(
        "--output",
        help="Output ZIP file path (default corpus_export_<date>.zip)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without writing files",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def _extract_token_count(meta_path: Path) -> int:
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        token = (
            data.get("token_count")
            or data.get("quality_metrics", {}).get("token_count")
            or data.get("quality_metrics", {})
            .get("extraction_quality", {})
            .get("token_count")
        )
        if isinstance(token, str) and token.isdigit():
            return int(token)
        if isinstance(token, int):
            return token
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed reading %s: %s", meta_path, exc)
    return 0


def build_manifest(corpus_root: Path) -> dict:
    extracted_root = corpus_root / "processed" / "_extracted"
    metadata_root = corpus_root / "metadata"

    domain_names: set[str] = set()
    if extracted_root.exists():
        domain_names.update(
            d.name for d in extracted_root.iterdir() if d.is_dir()
        )
    if metadata_root.exists():
        domain_names.update(d.name for d in metadata_root.iterdir() if d.is_dir())

    stats: dict[str, dict[str, int]] = {}
    total_tokens = 0
    for domain in sorted(domain_names):
        txt_count = len(list((extracted_root / domain).glob("*.txt")))
        json_files = list((extracted_root / domain).glob("*.json"))
        meta_files = list((metadata_root / domain).glob("*.json"))
        json_count = len(json_files) + len(meta_files)
        for meta in meta_files:
            total_tokens += _extract_token_count(meta)
        stats[domain] = {"txt": txt_count, "json": json_count}

    manifest = {
        "corpus_version": datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"),
        "domains": stats,
        "total_tokens": total_tokens,
    }
    return manifest


def create_archive(corpus_root: Path, output: Path, manifest: dict, dry_run: bool) -> None:
    if dry_run:
        logger.info("[DRY RUN] Would create archive %s", output)
        return

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        for rel in ["processed/_extracted", "metadata", "logs"]:
            path = corpus_root / rel
            if not path.exists():
                continue
            for file in path.rglob("*"):
                if file.is_file():
                    zf.write(file, file.relative_to(corpus_root))

    logger.info("Archive written to %s", output)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    corpus_root = Path(args.corpus_root).expanduser().resolve()
    output = (
        Path(args.output)
        if args.output
        else Path(
            f"corpus_export_{datetime.utcnow().strftime('%Y%m%d')}.zip"
        )
    )

    manifest = build_manifest(corpus_root)
    logger.info("Domains found: %s", ", ".join(sorted(manifest["domains"].keys())))
    create_archive(corpus_root, output, manifest, args.dry_run)


if __name__ == "__main__":  # pragma: no cover - manual utility
    main()
