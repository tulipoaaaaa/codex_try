import argparse
import json
from pathlib import Path
import sys

try:
    from CryptoFinanceCorpusBuilder.storage.corpus_manager import CorpusManager
except ImportError:
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from CryptoFinanceCorpusBuilder.storage.corpus_manager import CorpusManager

def tag_priority_high(corpus_dir, metadata_path, stems=None, titles=None, get_doc_stem=None):
    stems = set(stems or [])
    titles = set(titles or [])
    cm = CorpusManager(corpus_dir)
    cm.metadata_file = Path(metadata_path)
    cm._load_metadata()
    metadata = cm.metadata
    doc_entries = metadata.get("documents", {})
    tagged = 0
    for doc in doc_entries.values():
        match = False
        doc_stem = get_doc_stem(doc) if get_doc_stem else None
        if stems and doc_stem in stems:
            match = True
        if titles and doc.get("title") in titles:
            match = True
        if match:
            doc["priority"] = "high"
            tagged += 1
    cm._save_metadata()
    print(f"✅ Tagged {tagged} documents with priority: high.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tag metadata entries with priority: high by stem or title.")
    parser.add_argument('--corpus', required=True, help='Path to corpus root directory')
    parser.add_argument('--metadata', required=True, help='Path to corpus_metadata.json')
    parser.add_argument('--stems', default=None, help='Comma-separated list of file stems to tag')
    parser.add_argument('--titles', default=None, help='Comma-separated list of titles to tag')
    parser.add_argument('--list-stems', action='store_true', help='List all unique stems in metadata and exit')
    args = parser.parse_args()
    if args.list_stems:
        with open(args.metadata, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        stems = set()
        for doc in metadata["documents"].values():
            p = doc.get("extracted_text_path") or doc.get("path")
            if p:
                stems.add(Path(p).stem)
        for s in sorted(stems):
            print(s)
        sys.exit(0)
    stems = [s.strip() for s in args.stems.split(",")] if args.stems else []
    titles = [t.strip() for t in args.titles.split(",")] if args.titles else []
    def get_doc_stem(doc):
        p = doc.get("extracted_text_path") or doc.get("path")
        return Path(p).stem if p else None
    tag_priority_high(args.corpus, args.metadata, stems=stems, titles=titles, get_doc_stem=get_doc_stem) 