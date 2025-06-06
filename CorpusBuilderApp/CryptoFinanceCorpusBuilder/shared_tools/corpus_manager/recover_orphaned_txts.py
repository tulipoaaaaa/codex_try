import argparse
import json
from pathlib import Path
import sys
import shutil

try:
    from CryptoFinanceCorpusBuilder.storage.corpus_manager import CorpusManager
except ImportError:
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from CryptoFinanceCorpusBuilder.storage.corpus_manager import CorpusManager

def recover_orphaned_txts(corpus_dir, metadata_path, priority_stems=None, dry_run=False):
    corpus_dir = Path(corpus_dir)
    cm = CorpusManager(corpus_dir)
    cm.metadata_file = Path(metadata_path)
    cm._load_metadata()
    metadata = cm.metadata
    doc_entries = metadata.get("documents", {})
    # Collect all referenced extracted_text_paths
    referenced_txts = set()
    for doc in doc_entries.values():
        p = doc.get("extracted_text_path")
        if p:
            referenced_txts.add(str(Path(p).resolve()))
    # Find all .txt files in corpus
    all_txt_files = set(str(f.resolve()) for f in corpus_dir.glob('**/*.txt'))
    orphaned_txts = all_txt_files - referenced_txts
    # Prepare new entries
    new_entries = {}
    for txt_path in orphaned_txts:
        txt_file = Path(txt_path)
        stem = txt_file.stem
        # Try to infer domain from parent directory
        parent = txt_file.parent.name
        domain = parent.replace('_extracted', '') if parent.endswith('_extracted') else parent
        # Make extracted_text_path relative to project root
        project_root = Path.cwd()
        extracted_text_path = str(txt_file.resolve().relative_to(project_root))
        entry = {
            "extracted_text_path": extracted_text_path,
            "extracted_only": True,
            "domain": domain,
            "path": None,
        }
        if priority_stems and stem in priority_stems:
            entry["priority"] = "high"
        new_entries[stem] = entry
    print(f"Found {len(orphaned_txts)} orphaned .txt files.")
    if not new_entries:
        print("No new entries to add.")
        return
    print(f"Prepared {len(new_entries)} new metadata entries.")
    for stem, entry in new_entries.items():
        print(f"  - {stem} (priority: {entry.get('priority', 'none')})")
    if dry_run:
        print("[DRY RUN] No changes made. Re-run without --dry-run to apply.")
        return
    # Backup metadata
    backup_path = Path(metadata_path).with_suffix('.json.bak')
    shutil.copy2(metadata_path, backup_path)
    print(f"Backed up metadata to {backup_path}")
    # Add new entries
    for stem, entry in new_entries.items():
        # Avoid overwriting existing entries
        if stem not in doc_entries:
            doc_entries[stem] = entry
    cm._save_metadata()
    print(f"Added {len(new_entries)} new entries to metadata.")

def main():
    parser = argparse.ArgumentParser(description="Recover orphaned .txt files as metadata-only entries.")
    parser.add_argument('--corpus', required=True, help='Path to corpus root directory')
    parser.add_argument('--metadata', required=True, help='Path to corpus_metadata.json')
    parser.add_argument('--priority-stems', default=None, help='Comma-separated list of stems to tag as priority high (optional)')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing to metadata')
    args = parser.parse_args()
    priority_stems = set(s.strip() for s in args.priority_stems.split(",")) if args.priority_stems else None
    recover_orphaned_txts(args.corpus, args.metadata, priority_stems=priority_stems, dry_run=args.dry_run)

if __name__ == "__main__":
    main() 