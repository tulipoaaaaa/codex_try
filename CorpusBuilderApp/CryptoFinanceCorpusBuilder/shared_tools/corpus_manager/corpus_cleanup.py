import argparse
import json
from pathlib import Path
import sys
import os

try:
    from CryptoFinanceCorpusBuilder.storage.corpus_manager import CorpusManager
except ImportError:
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from CryptoFinanceCorpusBuilder.storage.corpus_manager import CorpusManager

def cleanup_corpus(corpus_dir, metadata_path=None, dry_run=False):
    corpus_dir = Path(corpus_dir)
    cm = CorpusManager(corpus_dir)
    if metadata_path:
        cm.metadata_file = Path(metadata_path)
        cm._load_metadata()
    metadata = cm.metadata
    doc_entries = metadata.get("documents", {})
    doc_paths = set()
    extracted_paths = set()
    # 1. Collect all referenced files
    for doc_id, doc in doc_entries.items():
        path = doc.get("path")
        extracted = doc.get("extracted_text_path")
        if path:
            doc_paths.add(Path(path).resolve())
        if extracted:
            extracted_paths.add(Path(extracted).resolve())
    # 2. Find orphaned files
    all_pdf_files = set(f.resolve() for f in corpus_dir.glob('**/*.pdf'))
    all_txt_files = set(f.resolve() for f in corpus_dir.glob('**/*.txt'))
    orphaned_pdfs = all_pdf_files - doc_paths
    orphaned_txts = all_txt_files - extracted_paths
    orphaned_files = list(orphaned_pdfs | orphaned_txts)
    # 3. Find corrupt/empty TXT files
    corrupt_txts = []
    for txt in extracted_paths:
        if txt.exists():
            try:
                with open(txt, 'r', encoding='utf-8') as f:
                    content = f.read()
                if not content.strip():
                    corrupt_txts.append(str(txt))
            except Exception:
                corrupt_txts.append(str(txt))
    # 4. Find metadata entries with missing required fields
    to_remove = []
    for doc_id, doc in list(doc_entries.items()):
        missing_fields = []
        if not doc.get('path'):
            missing_fields.append('path')
        if not doc.get('extracted_text_path'):
            missing_fields.append('extracted_text_path')
        if missing_fields:
            to_remove.append((doc_id, missing_fields))
    # 5. Report
    print("\n===== CORPUS CLEANUP PREVIEW =====")
    print(f"Orphaned files (not in metadata): {len(orphaned_files)}")
    for f in orphaned_files:
        print(f"  - {f} [orphaned {'PDF' if str(f).endswith('.pdf') else 'TXT'}]")
    print(f"Corrupt/empty TXT files: {len(corrupt_txts)}")
    for f in corrupt_txts:
        print(f"  - {f} [corrupt/empty TXT]")
    print(f"Metadata entries with missing required fields: {len(to_remove)}")
    for doc_id, fields in to_remove:
        print(f"  - {doc_id} [missing: {', '.join(fields)}]")
    print("===== END OF PREVIEW =====\n")
    if dry_run:
        print("[DRY RUN] No files or metadata were deleted. Review the above and re-run without --dry-run to apply cleanup.")
        return
    # 6. Delete orphaned files
    deleted_orphans = []
    for f in orphaned_files:
        try:
            os.remove(f)
            deleted_orphans.append(str(f))
        except Exception:
            pass
    # 7. Delete corrupt/empty TXT files
    deleted_txts = []
    for f in corrupt_txts:
        try:
            os.remove(f)
            deleted_txts.append(str(f))
        except Exception:
            pass
    # 8. Remove metadata entries with missing required fields
    for doc_id, _ in to_remove:
        if doc_id in doc_entries:
            del doc_entries[doc_id]
    cm._save_metadata()
    # 9. Final report
    print("\n===== CORPUS CLEANUP REPORT =====")
    print(f"Deleted orphaned files: {len(deleted_orphans)}")
    if deleted_orphans:
        print("  - ", deleted_orphans)
    print(f"Deleted corrupt/empty TXT files: {len(deleted_txts)}")
    if deleted_txts:
        print("  - ", deleted_txts)
    print(f"Removed metadata entries with missing required fields: {len(to_remove)}")
    if to_remove:
        print("  - ", [doc_id for doc_id, _ in to_remove])
    print("===== END OF REPORT =====\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean up orphaned/corrupt files and metadata in the corpus.")
    parser.add_argument('--corpus', required=True, help='Path to corpus root directory')
    parser.add_argument('--metadata', default=None, help='Path to corpus_metadata.json (optional)')
    parser.add_argument('--dry-run', action='store_true', help='Preview what would be deleted/removed, but do not actually delete anything.')
    args = parser.parse_args()
    cleanup_corpus(args.corpus, args.metadata, dry_run=args.dry_run) 