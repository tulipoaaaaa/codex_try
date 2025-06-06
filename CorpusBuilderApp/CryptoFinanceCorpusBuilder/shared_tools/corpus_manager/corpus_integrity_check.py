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

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None
    print("[WARNING] PyPDF2 not installed. PDF corruption checks will be skipped.")

def check_integrity(corpus_dir, metadata_path=None):
    corpus_dir = Path(corpus_dir)
    cm = CorpusManager(corpus_dir)
    if metadata_path:
        cm.metadata_file = Path(metadata_path)
        cm._load_metadata()
    metadata = cm.metadata
    doc_entries = metadata.get("documents", {})
    doc_paths = set()
    extracted_paths = set()
    missing_files = []
    orphaned_files = []
    corrupt_pdfs = []
    corrupt_txts = []
    inconsistent_meta = []
    # 1. Collect all referenced files
    for doc_id, doc in doc_entries.items():
        path = doc.get("path")
        extracted = doc.get("extracted_text_path")
        is_extracted_only = doc.get("extracted_only", False)
        if path:
            doc_paths.add(Path(path).resolve())
        if extracted:
            extracted_paths.add(Path(extracted).resolve())
        # Check for required fields
        # Only flag as inconsistent if not extracted_only or if extracted_only but extracted_text_path is missing
        if (not path and not is_extracted_only) or not extracted:
            inconsistent_meta.append(doc_id)
    # 2. Check for missing files
    for p in doc_paths | extracted_paths:
        if not p.exists():
            missing_files.append(str(p))
    # 3. Check for orphaned files
    all_pdf_files = set(f.resolve() for f in corpus_dir.glob('**/*.pdf'))
    all_txt_files = set(f.resolve() for f in corpus_dir.glob('**/*.txt'))
    orphaned_pdfs = all_pdf_files - doc_paths
    orphaned_txts = all_txt_files - extracted_paths
    orphaned_files.extend([str(f) for f in orphaned_pdfs | orphaned_txts])
    # 4. Check for file corruption
    if PdfReader:
        for pdf in doc_paths:
            if pdf.exists():
                try:
                    PdfReader(str(pdf))
                except Exception:
                    corrupt_pdfs.append(str(pdf))
    for txt in extracted_paths:
        if txt.exists():
            try:
                with open(txt, 'r', encoding='utf-8') as f:
                    content = f.read()
                if not content.strip():
                    corrupt_txts.append(str(txt))
            except Exception:
                corrupt_txts.append(str(txt))
    # 5. Report
    print("\n===== CORPUS INTEGRITY REPORT =====")
    print(f"Total metadata entries: {len(doc_entries)}")
    print(f"Missing files referenced in metadata: {len(missing_files)}")
    if missing_files:
        print("  - ", missing_files)
    print(f"Orphaned files on disk (not in metadata): {len(orphaned_files)}")
    if orphaned_files:
        print("  - ", orphaned_files)
    print(f"Corrupt/unreadable PDFs: {len(corrupt_pdfs)}")
    if corrupt_pdfs:
        print("  - ", corrupt_pdfs)
    print(f"Corrupt/empty TXT files: {len(corrupt_txts)}")
    if corrupt_txts:
        print("  - ", corrupt_txts)
    print(f"Metadata entries with missing required fields: {len(inconsistent_meta)}")
    if inconsistent_meta:
        print("  - ", inconsistent_meta)
    print("===== END OF REPORT =====\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check corpus integrity: orphaned/missing/corrupt files and metadata consistency.")
    parser.add_argument('--corpus', required=True, help='Path to corpus root directory')
    parser.add_argument('--metadata', default=None, help='Path to corpus_metadata.json (optional)')
    args = parser.parse_args()
    check_integrity(args.corpus, args.metadata) 