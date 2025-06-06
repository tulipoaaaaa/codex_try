"""
Config Validator Script
Checks consistency between balancer_config.py (reference) and domain_config.py.
Outputs both human-readable and machine-readable (JSON) reports.
"""
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any

# Import configs
sys.path.insert(0, str(Path(__file__).parent.parent / 'config'))
from CryptoFinanceCorpusBuilder.config import balancer_config, domain_config

REFERENCE_DOMAINS = balancer_config.DOMAIN_BALANCE_CONFIG
EXTRACTOR_DOMAINS = domain_config.DOMAINS

REPORT: dict[str, Any] = {
    "missing_in_domain_config": [],
    "allocation_mismatches": [],
    "extra_in_domain_config": [],
    "invalid_names": [],
    "duplicate_domains": [],
    "weight_sum": {},
}

def is_valid_identifier(name: str) -> bool:
    return re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name) is not None

def main(json_output_path=None):
    seen = set()
    # 1. Check for missing domains and allocation mismatches
    for domain, ref_cfg in REFERENCE_DOMAINS.items():
        if domain not in EXTRACTOR_DOMAINS:
            print(f"[ERROR] Domain '{domain}' missing in domain_config.py!")
            REPORT["missing_in_domain_config"].append(domain)
        else:
            # Backward compatibility: check for 'target_weight' or 'allocation'
            alloc = EXTRACTOR_DOMAINS[domain].get("target_weight")
            if alloc is None:
                alloc = EXTRACTOR_DOMAINS[domain].get("allocation")
            target = ref_cfg.get("target_weight")
            if alloc != target:
                print(f"[WARNING] Domain '{domain}' allocation mismatch: domain_config={alloc}, balancer_config={target}")
                REPORT["allocation_mismatches"].append({
                    "domain": domain,
                    "domain_config": alloc,
                    "balancer_config": target
                })
            else:
                print(f"[OK] Domain '{domain}' matches.")
    # 2. Check for extra domains in domain_config.py
    for domain in EXTRACTOR_DOMAINS:
        if domain not in REFERENCE_DOMAINS:
            print(f"[INFO] Domain '{domain}' is extra in domain_config.py (not used by balancer)")
            REPORT["extra_in_domain_config"].append(domain)
    # 3. Validate weight sums
    ref_sum = sum(ref_cfg.get("target_weight", 0) for ref_cfg in REFERENCE_DOMAINS.values())
    # Backward compatibility: sum both 'target_weight' and 'allocation' if present
    ext_sum = 0
    for dom in EXTRACTOR_DOMAINS.values():
        if 'target_weight' in dom:
            ext_sum += dom['target_weight']
        elif 'allocation' in dom:
            ext_sum += dom['allocation']
    REPORT["weight_sum"] = {"balancer_config": ref_sum, "domain_config": ext_sum}
    if abs(ref_sum - 1.0) > 1e-6:
        print(f"[ERROR] balancer_config.py weights sum to {ref_sum} (should be 1.0)")
    else:
        print(f"[OK] balancer_config.py weights sum to 1.0")
    if abs(ext_sum - 1.0) > 1e-6:
        print(f"[ERROR] domain_config.py allocations sum to {ext_sum} (should be 1.0)")
    else:
        print(f"[OK] domain_config.py allocations sum to 1.0")
    # 4. Validate domain names
    for domain in set(list(REFERENCE_DOMAINS.keys()) + list(EXTRACTOR_DOMAINS.keys())):
        if not is_valid_identifier(domain):
            print(f"[ERROR] Invalid domain name: '{domain}' (not a valid Python identifier)")
            REPORT["invalid_names"].append(domain)
    # 5. Check for duplicates within each config
    ref_domains = list(REFERENCE_DOMAINS.keys())
    ext_domains = list(EXTRACTOR_DOMAINS.keys())
    ref_duplicates = set([d for d in ref_domains if ref_domains.count(d) > 1])
    ext_duplicates = set([d for d in ext_domains if ext_domains.count(d) > 1])
    if ref_duplicates:
        print(f"[ERROR] Duplicate domain names in balancer_config.py: {ref_duplicates}")
        REPORT["duplicate_domains"] += list(ref_duplicates)
    if ext_duplicates:
        print(f"[ERROR] Duplicate domain names in domain_config.py: {ext_duplicates}")
        REPORT["duplicate_domains"] += list(ext_duplicates)
    # 6. Output JSON report
    if json_output_path:
        with open(json_output_path, 'w') as f:
            json.dump(REPORT, f, indent=2)
        print(f"[INFO] JSON report written to {json_output_path}")
    return REPORT

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Validate config consistency between balancer_config.py and domain_config.py")
    parser.add_argument('--json', type=str, help='Path to write JSON report (optional)')
    args = parser.parse_args()
    main(json_output_path=args.json) 