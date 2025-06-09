#!/usr/bin/env python
"""
Crypto Corpus Builder - Project-wide CLI

Usage:
  python cli.py --collector <name> --config <config.yaml> [--args ...]

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

All API keys and credentials are loaded from .env or environment variables.
"""
import argparse
import os
import sys
from dotenv import load_dotenv

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

def main():
    parser = argparse.ArgumentParser(description="Crypto Corpus Builder CLI")
    parser.add_argument('--collector', required=True, choices=['fred', 'github', 'annas', 'scidb', 'web'], help='Collector to run')
    parser.add_argument('--config', required=True, help='Path to config YAML')
    parser.add_argument('--series-ids', nargs='*', help='FRED: List of series IDs')
    parser.add_argument('--search-terms', nargs='*', help='GitHub: List of search terms')
    parser.add_argument('--query', type=str, help="Annas: Search query")
    parser.add_argument('--topic', type=str, help='GitHub: Topic to search for')
    parser.add_argument('--max-repos', type=int, default=10, help='GitHub: Max repos')
    parser.add_argument('--max-results', type=int, default=100, help='FRED: Max results')
    parser.add_argument('--output-dir', type=str, help='Output directory (for annas, scidb, web)')
    args = parser.parse_args()

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

if __name__ == "__main__":
    main() 