import json
from pathlib import Path
import shutil
import time
import difflib

def tag_high_priority_and_canonical(metadata_path, dry_run=False):
    metadata_path = Path(metadata_path)
    # Backup
    if not dry_run:
        backup_path = metadata_path.with_suffix('.json.bak')
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path_ts = metadata_path.with_name(f"{metadata_path.stem}_{timestamp}.bak")
        shutil.copy2(metadata_path, backup_path)
        shutil.copy2(metadata_path, backup_path_ts)
        print(f"🗂️  Backed up metadata to {backup_path} and {backup_path_ts}")

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    documents = metadata.get("documents", {})
    canonical_tagged = 0
    # Tag all high-priority docs as canonical if not already
    for doc_id, doc in documents.items():
        if doc.get("priority") == "high" and not doc.get("canonical"):
            if not dry_run:
                doc["canonical"] = True
            canonical_tagged += 1
    # Specifically tag the Kissell book as high and canonical
    kissell_key = "market_microstructure_Optimal_trading_strategies_-_Quantitative_Approaches_for_Managing_Market_Impact_and_Trading_Risk_by_Robert_Kissell"
    if kissell_key in documents:
        doc = documents[kissell_key]
        changed = False
        if doc.get("priority") != "high":
            if not dry_run:
                doc["priority"] = "high"
            changed = True
        if not doc.get("canonical"):
            if not dry_run:
                doc["canonical"] = True
            changed = True
        if changed:
            print(f"Tagged '{kissell_key}' as high priority and canonical.")
    else:
        print(f"[WARNING] Kissell book key not found in metadata.")
    if not dry_run:
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        print(f"🏷️  Tagged {canonical_tagged} high-priority docs as canonical.")
    else:
        print(f"[DRY RUN] Would tag {canonical_tagged} high-priority docs as canonical.")

def print_high_and_canonical(metadata_path):
    metadata_path = Path(metadata_path)
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    documents = metadata.get("documents", {})
    print("Documents with priority='high' and canonical=True:")
    for doc_id, doc in documents.items():
        if doc.get("priority") == "high" and doc.get("canonical") == True:
            print(doc_id)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Tag all high-priority docs as canonical in corpus metadata. Optionally print all high+canonical docs.")
    parser.add_argument('--metadata', required=True, help='Path to corpus_metadata.json')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing to file')
    parser.add_argument('--print-high-canonical', action='store_true', help='Print all docs with priority=high and canonical=True')
    args = parser.parse_args()
    tag_high_priority_and_canonical(args.metadata, dry_run=args.dry_run)
    if args.print_high_canonical:
        print_high_and_canonical(args.metadata)

if __name__ == "__main__":
    main()