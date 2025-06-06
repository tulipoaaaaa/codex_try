# cli/crypto_corpus_cli.py
import argparse
import logging
import json
import sys
import importlib
import concurrent.futures
import time
from CryptoFinanceCorpusBuilder.shared_tools.storage.corpus_manager import CorpusManager
import os
import requests
import zipfile
import io
import shutil
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re as _re
import json as _json
from dotenv import load_dotenv
import traceback
from pathlib import Path
from .collectors.collect_isda import run_isda_collector
from .collectors.collect_bitmex import run_bitmex_collector
from .collectors.collect_annas_main_library import run_annas_main_library_collector
from .collectors.collect_annas_scidb_search import run_annas_scidb_search_collector
from .collectors.collect_general_web_corpus import run_general_web_corpus_collector

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crypto_corpus_builder.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('crypto_corpus_cli')

load_dotenv()

def load_config(config_path):
    """Load configuration from JSON file, trying both the given path and package-relative path."""
    try:
        # Try the given path first
        if Path(config_path).exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        # Try relative to this file's parent (the package root)
        package_root = Path(__file__).parent.parent
        alt_path = package_root / config_path
        if alt_path.exists():
            with open(alt_path, 'r') as f:
                return json.load(f)
        raise FileNotFoundError(f"Config file not found: {config_path} or {alt_path}")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return None

def collect_from_source(source_name, source_config, base_dir, args=None):
    print(f"[DEBUG] collect_from_source called with source_name: {source_name}")
    """Collect data from a specific source"""
    logger.info(f"Collecting from source: {source_name}")
    
    if source_name == 'isda':
        return run_isda_collector(args, source_config, base_dir)

    # Determine source type and import appropriate collector
    source_type = source_config.get('source_type', 'web')
    collector_class = None
    
    try:
        if source_name == 'arxiv':
            from CryptoFinanceCorpusBuilder.sources.specific_collectors.arxiv_collector import ArxivCollector
            # Pass deduplication and search terms if provided
            arxiv_args = {
                'output_dir': base_dir,
                'delay_range': (5, 10),
                'clear_output_dir': getattr(args, 'arxiv_clear_output_dir', False),
                'existing_titles': getattr(args, 'existing_titles', None)
            }
            search_terms = getattr(args, 'arxiv_search_terms', None)
            max_results = getattr(args, 'arxiv_max_results', 1)
            collector = ArxivCollector(**arxiv_args)
            return collector.collect(search_terms=search_terms, max_results=max_results)
        elif source_name == 'github':
            from CryptoFinanceCorpusBuilder.sources.specific_collectors.github_collector import GitHubCollector
            github_args = {
                'output_dir': base_dir,
                'existing_titles': getattr(args, 'existing_titles', None)
            }
            repo_names = getattr(args, 'github_repo_name', None)
            collector = GitHubCollector(**github_args)
            return collector.collect(search_terms=repo_names)
        elif source_name == 'fred':
            from CryptoFinanceCorpusBuilder.sources.specific_collectors.fred_collector import FREDCollector
            collector_class = FREDCollector
        elif source_name == 'quantopian':
            from CryptoFinanceCorpusBuilder.sources.specific_collectors.quantopian_collector import QuantopianCollector
            collector_class = QuantopianCollector
        elif source_name == 'bitmex_research':
            return run_bitmex_collector(args, source_config, base_dir)
        elif source_name == 'annas':
            from CryptoFinanceCorpusBuilder.sources.specific_collectors.annas_archive_client import SimpleAnnaArchiveClient
            # Only reference args.client here
            if hasattr(args, 'client') and args.client == 'simple':
                client = SimpleAnnaArchiveClient(download_dir=args.output_dir)
            elif hasattr(args, 'client') and args.client == 'updated':
                from CryptoFinanceCorpusBuilder.sources.specific_collectors.updated_annas_archive_client import SimpleAnnaArchiveClient as UpdatedClient
                client = UpdatedClient(download_dir=args.output_dir)
            elif hasattr(args, 'client') and args.client == 'cookie':
                from CryptoFinanceCorpusBuilder.sources.specific_collectors.CookieAuthClient import CookieAuthClient
                client = CookieAuthClient(download_dir=args.output_dir)
            elif hasattr(args, 'client') and args.client == 'enhanced':
                from CryptoFinanceCorpusBuilder.sources.specific_collectors.enhanced_client import CookieAuthClient as EnhancedClient
                client = EnhancedClient(download_dir=args.output_dir)
            else:
                logger.error("Unknown Anna's Archive client type")
                return 1
            results = client.search(args.query)
            print(f"Found {len(results)} results.")
            if results:
                first = results[0]
                print(f"Downloading: {first.get('title', 'Unknown Title')}")
                if hasattr(client, 'download_file'):
                    if 'md5' in first:
                        client.download_file(first['md5'], Path(args.output_dir) / f"{first['md5']}.pdf")
                    elif 'url' in first:
                        client.download_file(first['url'], Path(args.output_dir) / f"{first.get('title', 'download')}.pdf")
            return 0
        elif source_name == 'annas_main_library':
            return run_annas_main_library_collector(args, source_config, base_dir, batch_json=getattr(args, 'batch_json', None))
        elif source_name == 'annas_scidb_search':
            return run_annas_scidb_search_collector(args, source_config, base_dir)
        elif source_name == 'general_web_corpus':
            return run_general_web_corpus_collector(args, source_config, base_dir)
        # For other collectors, instantiate and call as before
        if collector_class:
            collector = collector_class(base_dir)
            return collector.collect()
    except Exception as e:
        logger.error(f"Error in collect_from_source: {e}")
        traceback.print_exc()
        return 1
    
    return 0

def normalize_metadata_command(args):
    from CryptoFinanceCorpusBuilder.utils.metadata_normalizer import main as normalize_main
    normalize_main(args.corpus_dir)

def validate_metadata_command(args):
    from CryptoFinanceCorpusBuilder.utils.metadata_validator import main as validate_main
    validate_main(args.corpus_dir)

def validate_config_command(args):
    from CryptoFinanceCorpusBuilder.utils import config_validator
    config_validator.main(json_output_path=args.json)

def add_corpus_balancer_commands(subparsers):
    """Add corpus balancer commands to existing CLI."""
    
    # Analyze command
    analyze_parser = subparsers.add_parser(
        'analyze-balance', 
        help='Analyze corpus balance and generate reports'
    )
    analyze_parser.add_argument(
        '--corpus-dir', 
        required=True, 
        help='Path to corpus directory'
    )
    analyze_parser.add_argument(
        '--output-dir', 
        default='balance_reports',
        help='Output directory for reports and visualizations'
    )
    analyze_parser.add_argument(
        '--no-report', 
        action='store_true',
        help='Skip generating detailed report'
    )
    analyze_parser.add_argument(
        '--no-dashboard', 
        action='store_true',
        help='Skip generating interactive dashboard'
    )
    analyze_parser.add_argument(
        '--force-refresh', 
        action='store_true',
        help='Force re-analysis even if cached results exist'
    )
    analyze_parser.add_argument(
        '--no-recursive',
        action='store_true',
        help='Do NOT recursively aggregate all _extracted/low_quality subfolders (default: recursive ON)'
    )
    analyze_parser.set_defaults(func=handle_analyze_balance)
    
    # Rebalance command
    rebalance_parser = subparsers.add_parser(
        'rebalance', 
        help='Create and execute corpus rebalancing plan'
    )
    rebalance_parser.add_argument(
        '--corpus-dir', 
        required=True, 
        help='Path to corpus directory'
    )
    rebalance_parser.add_argument(
        '--strategy', 
        choices=['quality_weighted', 'stratified', 'synthetic'],
        default='quality_weighted',
        help='Rebalancing strategy to use'
    )
    rebalance_parser.add_argument(
        '--execute', 
        action='store_true',
        help='Execute the plan (default is dry-run only)'
    )
    rebalance_parser.add_argument(
        '--output-dir', 
        default='balance_reports',
        help='Output directory for reports'
    )
    rebalance_parser.add_argument(
        '--no-recursive',
        action='store_true',
        help='Do NOT recursively aggregate all _extracted/low_quality subfolders (default: recursive ON)'
    )
    rebalance_parser.set_defaults(func=handle_rebalance)

def handle_analyze_balance(args):
    """Handle analyze-balance command."""
    from CryptoFinanceCorpusBuilder.processors.corpus_balancer import CorpusBalancerCLI
    balancer_cli = CorpusBalancerCLI()
    return balancer_cli.analyze_command(
        corpus_dir=args.corpus_dir,
        output_dir=args.output_dir,
        generate_report=not args.no_report,
        create_dashboard=not args.no_dashboard,
        recursive=not args.no_recursive
    )

def handle_rebalance(args):
    """Handle rebalance command."""
    from CryptoFinanceCorpusBuilder.processors.corpus_balancer import CorpusBalancerCLI
    balancer_cli = CorpusBalancerCLI()
    return balancer_cli.rebalance_command(
        corpus_dir=args.corpus_dir,
        strategy=args.strategy,
        dry_run=not args.execute,
        output_dir=args.output_dir,
        recursive=not args.no_recursive
    )

def sync_config_command(args):
    from CryptoFinanceCorpusBuilder.utils import config_sync
    config_sync.sync_domains(force_sync=args.force_sync)

def handle_auto_rebalance(args):
    """
    Run corpus balance analysis, parse missing/underrepresented domains, and trigger collectors for those domains.
    Default is dry-run; use --execute to actually run collectors. Logs all actions.
    Supports --max-results and --domains filters. Prints estimated collection time in dry-run.
    """
    import logging
    from CryptoFinanceCorpusBuilder.processors.corpus_balancer import CorpusAnalyzer
    from CryptoFinanceCorpusBuilder.config.domain_config import DOMAINS
    import json
    import sys
    import math
    logger = logging.getLogger('auto_rebalance')
    corpus_dir = args.corpus_dir
    dry_run = not args.execute
    output_dir = getattr(args, 'output_dir', 'balance_reports')
    max_results = getattr(args, 'max_results', 10)
    filter_domains = set([d.strip() for d in getattr(args, 'domains', [])]) if getattr(args, 'domains', None) else None
    print(f"[AUTO-REBALANCE] Starting auto-rebalance for corpus: {corpus_dir}")
    analyzer = CorpusAnalyzer(corpus_dir, recursive=True)
    results = analyzer.analyze_corpus_balance(force_refresh=True)
    if 'error' in results:
        logger.error(f"Analysis failed: {results['error']}")
        print(f"[AUTO-REBALANCE] Analysis failed: {results['error']}")
        return 1
    # Find missing/underrepresented domains from recommendations
    recs = results.get('recommendations', [])
    missing_domains = []
    for rec in recs:
        if rec.get('category') == 'domain_balance' and 'missing domains' in rec.get('description', '').lower():
            desc = rec['description']
            if ':' in desc:
                doms = desc.split(':', 1)[1].strip().split(',')
                missing_domains.extend([d.strip() for d in doms])
    if not missing_domains:
        print("[AUTO-REBALANCE] No missing or underrepresented domains detected. Corpus is balanced.")
        return 0
    # Apply --domains filter if provided
    if filter_domains:
        missing_domains = [d for d in missing_domains if d in filter_domains]
        if not missing_domains:
            print(f"[AUTO-REBALANCE] No missing/underrepresented domains match filter: {filter_domains}")
            return 0
    print(f"[AUTO-REBALANCE] Missing/underrepresented domains to process: {missing_domains}")
    # Estimate collection time (simple heuristic: 2s per result per domain)
    est_time_per_domain = max_results * 2  # seconds
    total_est_time = est_time_per_domain * len(missing_domains)
    est_min = math.ceil(total_est_time / 60)
    if dry_run:
        print(f"[AUTO-REBALANCE] [DRY-RUN] Estimated collection time: ~{est_min} min for {len(missing_domains)} domain(s) (max {max_results} results each)")
    # For each domain, get search terms and trigger collector (dry-run by default)
    for domain in missing_domains:
        if domain not in DOMAINS:
            print(f"[AUTO-REBALANCE] Domain '{domain}' not found in config. Skipping.")
            continue
        search_terms = DOMAINS[domain].get('search_terms', [])
        print(f"[AUTO-REBALANCE] Would collect for domain: {domain}")
        print(f"  Search terms: {search_terms}")
        print(f"  Max results: {max_results}")
        if dry_run:
            print(f"  [DRY-RUN] No collection performed for {domain}.")
        else:
            # Use the existing collect_from_source logic
            source = None
            if 'arxiv' in args.sources:
                source = 'arxiv'
            elif 'bitmex_research' in args.sources:
                source = 'bitmex_research'
            else:
                source = args.sources[0] if args.sources else 'arxiv'
            collector_args = args
            collector_args.arxiv_search_terms = search_terms
            collector_args.arxiv_max_results = max_results
            collector_args.sources = [source]
            collector_args.output_dir = args.output_dir
            print(f"  [EXECUTE] Collecting from source: {source} for domain: {domain}")
            collect_from_source(source, {}, args.output_dir, args=collector_args)
    print("[AUTO-REBALANCE] Done.")
    return 0

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='Crypto-Finance Corpus Builder')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Collect command
    collect_parser = subparsers.add_parser('collect', help='Collect data from sources')
    collect_parser.add_argument('--sources', nargs='+', required=True, help='List of sources to collect from')
    collect_parser.add_argument('--output-dir', required=True, help='Output directory for collected data')
    collect_parser.add_argument('--config', default='CryptoFinanceCorpusBuilder/config/enhanced_sources.json', help='Path to source config JSON')
    # Add collector-specific flags (minimal for test coverage)
    collect_parser.add_argument('--arxiv-clear-output-dir', action='store_true')
    collect_parser.add_argument('--arxiv-max-results', type=int, default=1)
    collect_parser.add_argument('--isda-clear-output-dir', action='store_true')
    collect_parser.add_argument('--isda-max-sources', type=int, default=1)
    collect_parser.add_argument('--bitmex-clear-output-dir', action='store_true')
    collect_parser.add_argument('--bitmex-max-pages', type=int, default=1)
    collect_parser.add_argument('--scidb-doi', type=str)
    collect_parser.add_argument('--scidb-domain', type=str)
    # Deduplication and search term arguments (new)
    collect_parser.add_argument('--existing-titles', type=str, help='Path to deduplication title cache file (optional, for deduplication by normalized title)')
    collect_parser.add_argument('--arxiv-search-terms', nargs='+', help='arXiv search terms (optional)')
    collect_parser.add_argument('--bitmex-keywords', nargs='+', help='BitMEX post keywords (optional)')
    collect_parser.add_argument('--github-repo-name', nargs='+', help='GitHub repo names (optional)')
    # Add batch-json for Anna's Archive and similar collectors
    collect_parser.add_argument('--batch-json', type=str, help="Path to books.json for Anna's Archive batch mode (only used for annas_main_library)")
    # ... add more as needed ...

    # Process command
    process_parser = subparsers.add_parser('process', help='Process collected data')
    process_parser.add_argument('--input-dir', required=True)
    process_parser.add_argument('--output-dir', required=True)
    process_parser.add_argument('--config', default='CryptoFinanceCorpusBuilder/config/enhanced_sources.json')
    process_parser.add_argument('--chunking-mode', type=str, default='page', choices=['page', 'section'], help='Chunking mode for PDF extraction: page or section (default: page)')
    process_parser.add_argument('--chunk-overlap', type=int, default=1, help='Number of sentences to overlap between chunks (default: 1)')
    process_parser.add_argument('--generate-report', action='store_true', help='Generate corpus report after extraction (PDF only)')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show corpus statistics')
    stats_parser.add_argument('--corpus-dir', required=True)
    stats_parser.add_argument('--config', default='CryptoFinanceCorpusBuilder/config/enhanced_sources.json')

    # Add after other subcommands
    report_parser = subparsers.add_parser('report', help='Generate corpus balance and domain distribution report')
    report_parser.add_argument('--corpus-dir', type=str, required=True, help='Path to corpus directory')
    report_parser.add_argument('--output', type=str, required=True, help='Output Markdown report file')
    report_parser.add_argument('--include-stats', action='store_true', help='Include detailed statistics')
    report_parser.add_argument('--include-examples', action='store_true', help='Include example documents')

    # Add normalize-metadata command
    normalize_parser = subparsers.add_parser('normalize-metadata', help='Normalize all metadata in a corpus directory')
    normalize_parser.add_argument('--corpus-dir', required=True, help='Path to corpus root directory')
    normalize_parser.set_defaults(func=normalize_metadata_command)

    # Add validate-metadata command
    validate_parser = subparsers.add_parser('validate-metadata', help='Validate all metadata in a corpus directory')
    validate_parser.add_argument('--corpus-dir', required=True, help='Path to corpus root directory')
    validate_parser.set_defaults(func=validate_metadata_command)

    # Add validate-config command
    validate_config_parser = subparsers.add_parser('validate-config', help='Validate consistency between balancer_config.py and domain_config.py')
    validate_config_parser.add_argument('--json', type=str, help='Path to write JSON report (optional)')
    validate_config_parser.set_defaults(func=validate_config_command)

    # Add corpus balancer commands
    add_corpus_balancer_commands(subparsers)

    # Add sync-config command
    sync_config_parser = subparsers.add_parser('sync-config', help='Sync domain_config.py with balancer_config.py allocations and properties')
    sync_config_parser.add_argument('--force-sync', action='store_true', help='Force replace all properties and search_terms from reference config')
    sync_config_parser.set_defaults(func=sync_config_command)

    # Add auto-rebalance command
    auto_rebalance_parser = subparsers.add_parser('auto-rebalance', help='Auto-collect for missing/underrepresented domains based on balancer analysis')
    auto_rebalance_parser.add_argument('--corpus-dir', required=True, help='Path to corpus directory')
    auto_rebalance_parser.add_argument('--output-dir', default='data', help='Output directory for new collection')
    auto_rebalance_parser.add_argument('--sources', nargs='+', default=['arxiv', 'bitmex_research'], help='Preferred sources to use for collection')
    auto_rebalance_parser.add_argument('--max-results', type=int, default=10, help='Maximum results to collect per domain (default: 10)')
    auto_rebalance_parser.add_argument('--domains', nargs='+', help='Only process these domains (space/comma separated)')
    auto_rebalance_parser.add_argument('--dry-run', action='store_true', help='Dry run (default: True)')
    auto_rebalance_parser.add_argument('--execute', action='store_true', help='Actually run collectors (default: False)')
    auto_rebalance_parser.set_defaults(func=handle_auto_rebalance)

    args = parser.parse_args()

    if args.command == 'collect':
        config = load_config(args.config)
        if not config:
            logger.error('Failed to load configuration')
            return 1
        print(f"[DEBUG] Loaded config sources: {list(config.keys())}")
        print(f"[DEBUG] Requested sources: {args.sources}")
        for source in args.sources:
            source_config = config.get(source, {})
            base_dir = args.output_dir
            collect_from_source(source, source_config, base_dir, args=args)
        return 0
    elif args.command == 'process':
        print('[DEBUG] Process command called')
        input_dir = Path(args.input_dir)
        output_dir = Path(args.output_dir)
        from CryptoFinanceCorpusBuilder.processors.batch_text_extractor import process_pdf_file
        from collections import Counter, defaultdict
        pdf_files = list(input_dir.rglob('*.pdf'))
        all_extracted_metadata = []
        for pdf_path in pdf_files:
            print(f"[INFO] Processing PDF: {pdf_path}")
            results = process_pdf_file(
                pdf_path,
                output_dir,
                chunking_mode=getattr(args, 'chunking_mode', 'page'),
                chunk_overlap=getattr(args, 'chunk_overlap', 1)
            )
            if results:
                all_extracted_metadata.extend(results)
        # Section heading and chunk size reporting (PDF only)
        section_heading_counter = Counter()
        chunk_sizes_by_domain = defaultdict(list)
        for meta in all_extracted_metadata:
            if 'section_heading' in meta and meta['section_heading']:
                section_heading_counter[meta['section_heading']] += 1
            chunk_sizes_by_domain[meta['domain']].append(meta['token_count'])
        print('\nSection Heading Extraction Statistics:')
        for heading, count in section_heading_counter.most_common(10):
            print(f'  {heading}: {count}')
        print('\nAverage Chunk Size by Domain:')
        for domain, sizes in chunk_sizes_by_domain.items():
            avg_size = sum(sizes) / len(sizes) if sizes else 0
            print(f'  {domain}: {avg_size:.1f} tokens')
        print(f"[INFO] Processed {len(pdf_files)} PDF files. Extracted {len(all_extracted_metadata)} chunks.")
        
        # Process non-PDF files
        non_pdf_files = list(input_dir.rglob('*.py')) + list(input_dir.rglob('*.md')) + list(input_dir.rglob('*.json'))
        if non_pdf_files:
            print(f"[INFO] Processing {len(non_pdf_files)} non-PDF files")
            import subprocess
            subprocess.run(['python', '-m', 'CryptoFinanceCorpusBuilder.processors.batch_nonpdf_extractor_enhanced', 
                          '--input-dir', str(input_dir), '--output-dir', str(output_dir)])
        
        if args.generate_report:
            import subprocess
            report_output = Path(args.output_dir) / 'corpus_report.md'
            subprocess.run([
                'python', '-m', 'CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli',
                'report',
                '--corpus-dir', str(args.output_dir),
                '--output', str(report_output),
                '--include-stats',
                '--include-examples'
            ], check=True)
            print(f"[INFO] Corpus report generated: {report_output}")
        return 0
    elif args.command == 'stats':
        print('[DEBUG] Stats command called (placeholder)')
        # Placeholder for stats logic
        return 0
    elif args.command == 'report':
        from CryptoFinanceCorpusBuilder.utils.generate_corpus_report import main as report_main
        report_main(
            corpus_dir=args.corpus_dir,
            output=args.output,
            include_stats=args.include_stats,
            include_examples=args.include_examples
        )
        print(f"[INFO] Corpus report generated: {args.output}")
        return 0
    # Handle new corpus balancer commands
    elif args.command in ['analyze-balance', 'rebalance']:
        return args.func(args)
    elif args.command == 'validate-config':
        return args.func(args)
    elif args.command == 'sync-config':
        return args.func(args)
    elif hasattr(args, 'func'):
        return args.func(args)

if __name__ == '__main__':
    sys.exit(main())