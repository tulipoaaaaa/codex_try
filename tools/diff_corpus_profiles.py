import argparse
import json
import logging
from pathlib import Path
from collections import defaultdict
from typing import Iterable, Dict, Any

logger = logging.getLogger(__name__)


def _token_count(data: Dict[str, Any]) -> int:
    """Return token count from metadata dict."""
    for key in (
        "token_count",
        ("quality_metrics", "token_count"),
        ("quality_metrics", "extraction_quality", "token_count"),
    ):
        if isinstance(key, tuple):
            value = data
            for part in key:
                value = value.get(part, {}) if isinstance(value, dict) else {}
            if isinstance(value, int):
                return value
        else:
            if key in data and isinstance(data[key], int):
                return data[key]
    return 0


def build_profile(corpus_dir: Path) -> Dict[str, Any]:
    """Scan a corpus directory and return summary profile."""
    profile = {
        "domains": defaultdict(lambda: {"txt": 0, "json": 0}),
        "total_files": 0,
        "total_tokens": 0,
        "hashes": set(),
    }

    for txt_file in corpus_dir.rglob("*.txt"):
        rel = txt_file.relative_to(corpus_dir)
        domain = rel.parts[0] if len(rel.parts) > 1 else "root"
        profile["domains"][domain]["txt"] += 1

    for json_file in corpus_dir.rglob("*.json"):
        rel = json_file.relative_to(corpus_dir)
        domain = rel.parts[0] if len(rel.parts) > 1 else "root"
        profile["domains"][domain]["json"] += 1
        try:
            data = json.load(open(json_file, "r", encoding="utf-8"))
            profile["total_tokens"] += _token_count(data)
            sha = data.get("sha256")
            if sha:
                profile["hashes"].add(sha)
        except Exception as exc:  # pragma: no cover - best effort parsing
            logger.warning("Failed reading %s: %s", json_file, exc)

    profile["total_files"] = sum(
        d["txt"] + d["json"] for d in profile["domains"].values()
    )
    profile["hashes"] = sorted(profile["hashes"])
    return profile


def diff_profiles(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    """Return diff information between two profiles."""
    domains = set(before["domains"]) | set(after["domains"])
    domain_table = []
    for d in sorted(domains):
        b = before["domains"].get(d, {"txt": 0, "json": 0})
        a = after["domains"].get(d, {"txt": 0, "json": 0})
        domain_table.append(
            {
                "domain": d,
                "v1_txt": b["txt"],
                "v1_json": b["json"],
                "v2_txt": a["txt"],
                "v2_json": a["json"],
                "delta": (a["txt"] + a["json"]) - (b["txt"] + b["json"]),
            }
        )

    return {
        "domains": domain_table,
        "total_file_delta": after["total_files"] - before["total_files"],
        "total_token_delta": after["total_tokens"] - before["total_tokens"],
        "new_hashes": sorted(set(after["hashes"]) - set(before["hashes"])),
        "removed_hashes": sorted(set(before["hashes"]) - set(after["hashes"])),
    }


def format_report(diff: Dict[str, Any]) -> str:
    lines = []
    lines.append("| Domain | v1 .txt | v1 .json | v2 .txt | v2 .json | Δ |")
    lines.append("|---|---|---|---|---|---|")
    for row in diff["domains"]:
        lines.append(
            f"| {row['domain']} | {row['v1_txt']} | {row['v1_json']} | {row['v2_txt']} | {row['v2_json']} | {row['delta']} |"
        )
    lines.append("")
    lines.append(f"Total file delta: {diff['total_file_delta']}")
    lines.append(f"Total token delta: {diff['total_token_delta']}")
    if diff["new_hashes"]:
        lines.append(f"New hashes: {', '.join(diff['new_hashes'])}")
    if diff["removed_hashes"]:
        lines.append(f"Removed hashes: {', '.join(diff['removed_hashes'])}")
    return "\n".join(lines)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare two corpus snapshots")
    parser.add_argument("--before", required=True, help="Path to earlier corpus")
    parser.add_argument("--after", required=True, help="Path to later corpus")
    parser.add_argument("--save-report", help="Optional path to JSON report")
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO)

    before_profile = build_profile(Path(args.before))
    after_profile = build_profile(Path(args.after))
    diff = diff_profiles(before_profile, after_profile)

    print(format_report(diff))

    if args.save_report:
        report_path = Path(args.save_report)
        with open(report_path, "w", encoding="utf-8") as fh:
            json.dump(diff, fh, indent=2)
        logger.info("Report saved to %s", report_path)


if __name__ == "__main__":
    main()
