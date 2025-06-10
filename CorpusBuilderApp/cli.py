#!/usr/bin/env python
"""
Crypto Corpus Builder - Project-wide CLI

Usage:
  python cli.py --collector <name> --config <config.yaml> [--args ...]
  python cli.py diff-corpus --profile-a <profile1.json> --profile-b <profile2.json>
  python cli.py export-corpus --corpus-dir <corpus> --output-dir <outdir> [--version-tag v]

Supported collectors:
  fred        - FRED (Federal Reserve Economic Data)
  github      - GitHub repositories
  annas       - Anna's Archive main library
  scidb       - SciDB academic papers
  web         - General Web Corpus

Examples:
  python cli.py --collector fred --config shared_tools/test_config.yaml --series-ids GDP CPI
  python cli.py --collector github --config shared_tools/test_config.yaml --search-terms bitcoin trading
  python cli.py --collector annas --config shared_tools/test_config.yaml --query "Mastering Bitcoin"
  python cli.py diff-corpus --profile-a profile1.json --profile-b profile2.json
  python cli.py export-corpus --corpus-dir data/corpus --output-dir data/exports

All API keys and credentials are loaded from .env or environment variables.
"""
import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parent.parent))
import json

from tools.diff_corpus_profiles import diff_profiles, format_report

# Load .env if present
load_dotenv()

# Import collectors
try:
    from shared_tools.collectors.fred_collector import FREDCollector
    from shared_tools.collectors.github_collector import GitHubCollector
    from shared_tools.collectors.collect_annas_main_library import AnnasMainLibraryCollector
    from shared_tools.collectors.enhanced_scidb_collector import SciDBCollector
    from shared_tools.collectors.collect_general_web_corpus import GeneralWebCorpusCollector
except ImportError as e:
    print(f"[ERROR] Could not import collectors: {e}")
    sys.exit(1)


def _load_profile(path: str) -> dict:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Profile not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def cmd_diff_corpus(args: argparse.Namespace) -> int:
    """Handle the diff-corpus subcommand."""
    try:
        a = _load_profile(args.profile_a)
        b = _load_profile(args.profile_b)
    except Exception as exc:  # pragma: no cover - simple CLI validation
        print(f"[ERROR] {exc}")
        return 2

    diff = diff_profiles(a, b)
    print(format_report(diff))

    differences = (
        diff["total_file_delta"]
        or diff["total_token_delta"]
        or diff["new_hashes"]
        or diff["removed_hashes"]
        or any(row.get("delta") for row in diff["domains"])
    )
    return 1 if differences else 0

def main(argv: list[str] | None = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]

    if argv and argv[0] == "diff-corpus":
        diff_parser = argparse.ArgumentParser(prog="diff-corpus", description="Compare two corpus profiles")
        diff_parser.add_argument("--profile-a", required=True, help="Path to first corpus profile JSON")
        diff_parser.add_argument("--profile-b", required=True, help="Path to second corpus profile JSON")
        diff_args = diff_parser.parse_args(argv[1:])
        return cmd_diff_corpus(diff_args)

    if argv and argv[0] == "export-corpus":
        export_parser = argparse.ArgumentParser(
            prog="export-corpus",
            description="Create versioned corpus export archive",
        )
        export_parser.add_argument("--corpus-dir", required=True, help="Path to corpus root directory")
        export_parser.add_argument("--output-dir", required=True, help="Directory to write export archive")
        export_parser.add_argument("--dry-run", action="store_true", help="Preview actions without writing files")
        export_parser.add_argument("--version-tag", help="Optional version tag for archive filename")
        exp_args = export_parser.parse_args(argv[1:])

        from tools import export_corpus
        name = "corpus_export"
        if exp_args.version_tag:
            name += f"_{exp_args.version_tag}"
        name += ".zip"
        output = Path(exp_args.output_dir) / name
        call_args = ["--corpus-root", exp_args.corpus_dir, "--output", str(output)]
        if exp_args.dry_run:
            call_args.append("--dry-run")
        export_corpus.main(call_args)
        return 0

    parser = argparse.ArgumentParser(description="Crypto Corpus Builder CLI")
    parser.add_argument("--collector", required=True, choices=["fred", "github", "annas", "scidb", "web"], help="Collector to run")
    parser.add_argument("--config", required=True, help="Path to config YAML")
    parser.add_argument("--series-ids", nargs="*", help="FRED: List of series IDs")
    parser.add_argument("--search-terms", nargs="*", help="GitHub: List of search terms")
    parser.add_argument("--query", type=str, help="Annas: Search query")
    parser.add_argument("--topic", type=str, help="GitHub: Topic to search for")
    parser.add_argument("--max-repos", type=int, default=10, help="GitHub: Max repos")
    parser.add_argument("--max-results", type=int, default=100, help="FRED: Max results")
    parser.add_argument("--output-dir", type=str, help="Output directory (for annas, scidb, web)")
    args = parser.parse_args(argv)

    if args.collector == 'fred':
        collector = FREDCollector(args.config)
        results = collector.collect(series_ids=args.series_ids, max_results=args.max_results)
        print(f"[FRED] Collected {len(results)} records.")
        for r in results:
            print(r)
    elif args.collector == 'github':
        collector = GitHubCollector(args.config)
        results = collector.collect(search_terms=args.search_terms, topic=args.topic, max_repos=args.max_repos)
        print(f"[GitHub] Collected {len(results)} repositories.")
        for r in results:
            print(r)
    elif args.collector == 'annas':
        if not args.query:
            print("[ERROR] --query is required for annas collector.")
            sys.exit(1)
        collector = AnnasMainLibraryCollector(args.config)
        results = collector.collect(args.query)
        print(f"[Annas] Collected {len(results)} files.")
        for r in results:
            print(r)
    elif args.collector == 'scidb':
        collector = SciDBCollector(args.config)
        # For simplicity, expects a file 'dois.json' in output-dir or config dir
        dois_path = args.output_dir or os.path.dirname(args.config)
        dois_file = os.path.join(dois_path, 'dois.json')
        if not os.path.exists(dois_file):
            print(f"[ERROR] dois.json not found at {dois_file}")
            sys.exit(1)
        import json
        with open(dois_file, 'r') as f:
            doi_list = json.load(f)
        results = collector.collect_by_doi(doi_list)
        print(f"[SciDB] Collected {len(results)} papers.")
        for r in results:
            print(r)
    elif args.collector == 'web':
        output_dir = args.output_dir or os.path.dirname(args.config)
        collector = GeneralWebCorpusCollector(output_dir)
        results = collector.collect()
        print(f"[Web] Collection complete: {results}")
    else:
        print(f"[ERROR] Unknown collector: {args.collector}")
        sys.exit(1)

    return 0

if __name__ == "__main__":
    sys.exit(main())
