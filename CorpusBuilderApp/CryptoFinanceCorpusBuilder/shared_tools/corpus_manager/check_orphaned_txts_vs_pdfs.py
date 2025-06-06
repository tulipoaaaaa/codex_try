import argparse
from pathlib import Path
import sys
import os

try:
    from CryptoFinanceCorpusBuilder.storage.corpus_manager import CorpusManager
except ImportError:
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from CryptoFinanceCorpusBuilder.storage.corpus_manager import CorpusManager

def check_orphaned_txts_vs_pdfs(corpus_dir, metadata_path=None):
    corpus_dir = Path(corpus_dir)
    cm = CorpusManager(corpus_dir)
    if metadata_path:
        cm.metadata_file = Path(metadata_path)
        cm._load_metadata()
    metadata = cm.metadata
    doc_entries = metadata.get("documents", {})
    extracted_paths = set()
    for doc in doc_entries.values():
        extracted = doc.get("extracted_text_path")
        if extracted:
            extracted_paths.add(Path(extracted).resolve())
    # Find all .txt files in _extracted folders
    all_txt_files = set(f.resolve() for f in corpus_dir.glob('**/*_extracted/*.txt'))
    orphaned_txts = all_txt_files - extracted_paths
    print("\n===== ORPHANED TXT vs PDF CHECK =====")
    for txt_path in sorted(orphaned_txts):
        stem = txt_path.stem
        domain = txt_path.parent.name.replace("_extracted", "")
        pdf_path_guess = txt_path.parent.parent / domain / f"{stem}.pdf"
        print(f"TXT: {txt_path}")
        print(f"  Guessed PDF: {pdf_path_guess}")
        print(f"  PDF exists: {pdf_path_guess.exists()}")
    print("===== END OF REPORT =====\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check if orphaned .txt files have corresponding PDFs in the corpus.")
    parser.add_argument('--corpus', required=True, help='Path to corpus root directory')
    parser.add_argument('--metadata', default=None, help='Path to corpus_metadata.json (optional)')
    args = parser.parse_args()
    check_orphaned_txts_vs_pdfs(args.corpus, args.metadata) 