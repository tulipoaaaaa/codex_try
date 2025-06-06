# cli/crypto_corpus_cli.py
import argparse
import logging
import json
import sys
import importlib
import concurrent.futures
import time
from CryptoFinanceCorpusBuilder.shared_tools.storage.corpus_manager import CorpusManager
from CryptoFinanceCorpusBuilder.shared_tools.project_config import ProjectConfig
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
from CryptoFinanceCorpusBuilder.shared_tools.collectors.collect_isda import run_isda_collector
from CryptoFinanceCorpusBuilder.shared_tools.collectors.collect_bitmex import run_bitmex_collector
from CryptoFinanceCorpusBuilder.shared_tools.collectors.collect_annas_main_library import run_annas_main_library_collector
from CryptoFinanceCorpusBuilder.shared_tools.collectors.collect_general_web_corpus import run_general_web_corpus_collector

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
    """Load configuration from YAML file."""
    try:
        return ProjectConfig(config_path)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return None

def collect_from_source(source_name, source_config, config: ProjectConfig, args=None):
    print(f"[DEBUG] collect_from_source called with source_name: {source_name}")
    """Collect data from a specific source"""
    logger.info(f"Collecting from source: {source_name}")
    
    if source_name == 'isda':
        return run_isda_collector(args, source_config, config)

    # Determine source type and import appropriate collector
    source_type = source_config.get('source_type', 'web')
    collector_class = None
    
    try:
        if source_name == 'arxiv':
            from CryptoFinanceCorpusBuilder.sources.specific_collectors.arxiv_collector import ArxivCollector
            # Pass deduplication and search terms if provided
            arxiv_args = {
                'output_dir': config.raw_data_dir,
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
                'output_dir': config.raw_data_dir,
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
            return run_bitmex_collector(args, source_config, config)
        elif source_name == 'annas':
            from CryptoFinanceCorpusBuilder.sources.specific_collectors.annas_archive_client import SimpleAnnaArchiveClient
            # Only reference args.client here
            if hasattr(args, 'client') and args.client == 'simple':
                client = SimpleAnnaArchiveClient(download_dir=config.raw_data_dir)
            elif hasattr(args, 'client') and args.client == 'updated':
                from CryptoFinanceCorpusBuilder.sources.specific_collectors.updated_annas_archive_client import SimpleAnnaArchiveClient as UpdatedClient
                client = UpdatedClient(download_dir=config.raw_data_dir)
            elif hasattr(args, 'client') and args.client == 'cookie':
                from CryptoFinanceCorpusBuilder.sources.specific_collectors.CookieAuthClient import CookieAuthClient
                client = CookieAuthClient(download_dir=config.raw_data_dir)
            elif hasattr(args, 'client') and args.client == 'enhanced':
                from CryptoFinanceCorpusBuilder.sources.specific_collectors.enhanced_client import CookieAuthClient as EnhancedClient
                client = EnhancedClient(download_dir=config.raw_data_dir)
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
                        client.download_file(first['md5'], Path(config.raw_data_dir) / f"{first['md5']}.pdf")
                    elif 'url' in first:
                        client.download_file(first['url'], Path(config.raw_data_dir) / f"{first.get('title', 'download')}.pdf")
            return 0
        elif source_name == 'annas_main_library':
            return run_annas_main_library_collector(args, source_config, config, batch_json=getattr(args, 'batch_json', None))
        elif source_name == 'general_web_corpus':
            return run_general_web_corpus_collector(args, source_config, config)
        # For other collectors, instantiate and call as before
        if collector_class:
            collector = collector_class(config.raw_data_dir)
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
        execute=args.execute,
        output_dir=args.output_dir,
        recursive=not args.no_recursive
    )

def sync_config_command(args):
    """Handle sync-config command."""
    from CryptoFinanceCorpusBuilder.utils.config_sync import sync_config
    sync_config(args.config)

def handle_auto_rebalance(args):
    """Handle auto-rebalance command."""
    from CryptoFinanceCorpusBuilder.processors.corpus_balancer import CorpusBalancerCLI
    balancer_cli = CorpusBalancerCLI()
    return balancer_cli.auto_rebalance_command(
        corpus_dir=args.corpus_dir,
        min_ratio=args.min_ratio,
        max_ratio=args.max_ratio,
        strategy=args.strategy,
        output_dir=args.output_dir,
        recursive=not args.no_recursive
    )

def setup_logging(config=None) -> None:
    """Set up logging configuration."""
    log_level = logging.INFO
    if config and hasattr(config, 'logging'):
        log_level = getattr(logging, config.logging.get('level', 'INFO').upper())
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('crypto_corpus_builder.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Crypto Finance Corpus Builder CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Collect command
    collect_parser = subparsers.add_parser('collect', help='Collect data from sources')
    collect_parser.add_argument('--source', required=True, help='Source to collect from')
    collect_parser.add_argument('--output-dir', required=True, help='Output directory')
    collect_parser.add_argument('--config', required=True, help='Path to YAML config file')
    collect_parser.add_argument('--batch-json', help='Path to batch JSON file')
    collect_parser.add_argument('--client', choices=['simple', 'updated', 'cookie', 'enhanced'], help='Client type for Anna\'s Archive')
    collect_parser.add_argument('--query', help='Search query')
    collect_parser.add_argument('--arxiv-search-terms', help='Arxiv search terms')
    collect_parser.add_argument('--arxiv-max-results', type=int, help='Maximum number of results for Arxiv')
    collect_parser.add_argument('--arxiv-clear-output-dir', action='store_true', help='Clear output directory before collecting')
    collect_parser.add_argument('--github-repo-name', help='GitHub repository name')
    collect_parser.add_argument('--existing-titles', help='Path to file with existing titles')
    
    # Normalize metadata command
    normalize_parser = subparsers.add_parser('normalize-metadata', help='Normalize metadata in corpus')
    normalize_parser.add_argument('--corpus-dir', required=True, help='Path to corpus directory')
    
    # Validate metadata command
    validate_parser = subparsers.add_parser('validate-metadata', help='Validate metadata in corpus')
    validate_parser.add_argument('--corpus-dir', required=True, help='Path to corpus directory')
    
    # Validate config command
    validate_config_parser = subparsers.add_parser('validate-config', help='Validate configuration file')
    validate_config_parser.add_argument('--json', required=True, help='Path to JSON config file')
    
    # Add corpus balancer commands
    add_corpus_balancer_commands(subparsers)
    
    # Auto-rebalance command
    auto_rebalance_parser = subparsers.add_parser('auto-rebalance', help='Automatically rebalance corpus')
    auto_rebalance_parser.add_argument('--corpus-dir', required=True, help='Path to corpus directory')
    auto_rebalance_parser.add_argument('--min-ratio', type=float, default=0.8, help='Minimum ratio for rebalancing')
    auto_rebalance_parser.add_argument('--max-ratio', type=float, default=1.2, help='Maximum ratio for rebalancing')
    auto_rebalance_parser.add_argument('--strategy', choices=['quality_weighted', 'stratified', 'synthetic'], default='quality_weighted', help='Rebalancing strategy to use')
    auto_rebalance_parser.add_argument('--output-dir', default='balance_reports', help='Output directory for reports')
    auto_rebalance_parser.add_argument('--no-recursive', action='store_true', help='Do NOT recursively aggregate all _extracted/low_quality subfolders (default: recursive ON)')
    auto_rebalance_parser.set_defaults(func=handle_auto_rebalance)
    
    # Sync config command
    sync_config_parser = subparsers.add_parser('sync-config', help='Synchronize configuration')
    sync_config_parser.add_argument('--config', required=True, help='Path to config file')
    sync_config_parser.set_defaults(func=sync_config_command)
    
    args = parser.parse_args()
    
    if args.command == 'collect':
        config = load_config(args.config)
        if not config:
            logger.error('Failed to load configuration')
            return 1
        setup_logging(config)
        return collect_from_source(args.source, config.domain_configs.get(args.source, {}), config, args)
    elif args.command == 'normalize-metadata':
        return normalize_metadata_command(args)
    elif args.command == 'validate-metadata':
        return validate_metadata_command(args)
    elif args.command == 'validate-config':
        return validate_config_command(args)
    elif hasattr(args, 'func'):
        return args.func(args)
    else:
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(main())