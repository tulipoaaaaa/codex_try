import argparse
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from CryptoFinanceCorpusBuilder.storage.corpus_manager import CorpusManager

def clean_stale_metadata(corpus_dir, metadata_path=None):
    cm = CorpusManager(corpus_dir)
    if metadata_path:
        cm.metadata_file = Path(metadata_path)
        cm._load_metadata()
    stale = []
    for doc_id, doc in list(cm.metadata["documents"].items()):
        file_path = doc.get("path")
        if not file_path or not Path(file_path).exists():
            stale.append(doc_id)
            del cm.metadata["documents"][doc_id]
    cm._save_metadata()
    print(f"🧹 Cleaned {len(stale)} stale entries from metadata.")
    if stale:
        print("Stale doc_ids removed:", stale)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove metadata entries for missing files.")
    parser.add_argument('--corpus', required=True, help='Path to corpus root directory')
    parser.add_argument('--metadata', default=None, help='Path to corpus_metadata.json (optional)')
    args = parser.parse_args()
    clean_stale_metadata(args.corpus, args.metadata) 