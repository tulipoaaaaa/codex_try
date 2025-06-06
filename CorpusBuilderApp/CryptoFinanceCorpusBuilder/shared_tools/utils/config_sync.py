"""
Config Sync Script
Synchronizes domain_config.py allocations and properties with balancer_config.py target_weights and fields.
Backs up the original domain_config.py before modifying.
Supports safe (default) and force modes.
"""
import sys
import shutil
from pathlib import Path
import pprint
import argparse
import datetime

from CryptoFinanceCorpusBuilder.config import balancer_config, domain_config

REFERENCE_DOMAINS = balancer_config.DOMAIN_BALANCE_CONFIG
EXTRACTOR_DOMAINS = domain_config.DOMAINS

DOMAIN_CONFIG_PATH = Path(__file__).parent.parent / 'config' / 'domain_config.py'
BACKUP_PATH = DOMAIN_CONFIG_PATH.with_suffix('.py.bak')
LOG_PATH = Path(__file__).parent.parent / 'balance_reports' / 'config_sync_log.txt'

LOG = []

def sync_domains(force_sync=False):
    # Backup original file
    shutil.copy(DOMAIN_CONFIG_PATH, BACKUP_PATH)
    LOG.append(f"[INFO] Backed up original domain_config.py to {BACKUP_PATH}")
    timestamp = datetime.datetime.now().isoformat()
    LOG.append(f"[INFO] Sync started at {timestamp}")

    # Prepare new DOMAINS dict
    new_domains = EXTRACTOR_DOMAINS.copy()
    for domain, ref_cfg in REFERENCE_DOMAINS.items():
        if domain not in new_domains:
            LOG.append(f"[ADD] Domain '{domain}' added with properties: {ref_cfg}")
            # Add all properties from reference, add placeholder for search_terms if missing
            new_domains[domain] = dict(ref_cfg)
            if 'search_terms' not in new_domains[domain]:
                new_domains[domain]['search_terms'] = [f"TODO: add search terms for {domain}"]
        else:
            # Sync allocations and additional properties
            for key, value in ref_cfg.items():
                if key not in new_domains[domain]:
                    LOG.append(f"[ADD] Property '{key}' added to domain '{domain}': {value}")
                    new_domains[domain][key] = value
                elif key == 'allocation' or key == 'target_weight':
                    # Always update allocation to match reference
                    if new_domains[domain].get('allocation') != ref_cfg['target_weight']:
                        LOG.append(f"[UPDATE] Domain '{domain}' allocation changed: {new_domains[domain].get('allocation')} -> {ref_cfg['target_weight']}")
                        new_domains[domain]['allocation'] = ref_cfg['target_weight']
                elif force_sync:
                    if new_domains[domain][key] != value:
                        LOG.append(f"[FORCE-REPLACE] Property '{key}' in domain '{domain}' replaced: {new_domains[domain][key]} -> {value}")
                        new_domains[domain][key] = value
            # In force mode, remove properties not in reference (except search_terms)
            if force_sync:
                for key in list(new_domains[domain].keys()):
                    if key not in ref_cfg and key != 'search_terms':
                        LOG.append(f"[FORCE-REMOVE] Property '{key}' removed from domain '{domain}' (not in reference config)")
                        del new_domains[domain][key]
            # In safe mode, preserve existing search_terms and extra fields
            if not force_sync:
                # Only update allocation, add missing properties, never delete or overwrite search_terms
                pass
            # In force mode, replace search_terms if present in reference
            if force_sync and 'search_terms' in ref_cfg:
                if new_domains[domain].get('search_terms') != ref_cfg['search_terms']:
                    LOG.append(f"[FORCE-REPLACE] search_terms in domain '{domain}' replaced.")
                    new_domains[domain]['search_terms'] = ref_cfg['search_terms']
    # Add missing search_terms for new domains
    for domain, props in new_domains.items():
        if 'search_terms' not in props:
            LOG.append(f"[ADD] search_terms placeholder added to domain '{domain}'")
            props['search_terms'] = [f"TODO: add search terms for {domain}"]
    # Remove domains not in balancer_config (optional: comment out to keep extras)
    for domain in list(new_domains.keys()):
        if domain not in REFERENCE_DOMAINS:
            LOG.append(f"[REMOVE] Domain '{domain}' not in balancer_config.py (kept, but consider removing)")
    # Write new domain_config.py
    with open(DOMAIN_CONFIG_PATH, 'w', encoding='utf-8') as f:
        f.write('''"""
CONFIGURATION FILE: EXTRACTOR DOMAIN CONFIGURATION
Purpose: Defines domain classifications and source mappings for extractors
Used by: PDF and Non-PDF extractors, domain classifier
Not used by: Corpus balancer (uses balancer_config.py instead)

This file contains:
1. DOMAINS: Domain definitions with allocations and search terms
2. SOURCES: Source-specific configurations and domain mappings

IMPORTANT: This file is used by extractors through domain_utils.py
DO NOT modify without updating domain_utils.py wrapper
"""

# config/domain_config.py

DOMAINS = \
''')
        pprint.pprint(new_domains, stream=f, width=120)
        f.write('\n\n# (SOURCES section unchanged)\n')
        # Copy the rest of the file (SOURCES etc.)
        with open(BACKUP_PATH, 'r', encoding='utf-8') as orig:
            lines = orig.readlines()
        in_sources = False
        for line in lines:
            if line.strip().startswith('SOURCES ='):
                in_sources = True
            if in_sources:
                f.write(line)
    LOG.append(f"[INFO] domain_config.py updated and synced with balancer_config.py")
    # Write log to file
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, 'a', encoding='utf-8') as logf:
        logf.write(f"\n==== Config Sync Log {timestamp} ====" + "\n")
        for entry in LOG:
            logf.write(entry + "\n")
    LOG.append(f"[INFO] Log written to {LOG_PATH}")
    return LOG

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync domain_config.py with balancer_config.py allocations and properties.")
    parser.add_argument('--force-sync', action='store_true', help='Force replace all properties and search_terms from reference config')
    args = parser.parse_args()
    log = sync_domains(force_sync=args.force_sync)
    for entry in log:
        print(entry) 