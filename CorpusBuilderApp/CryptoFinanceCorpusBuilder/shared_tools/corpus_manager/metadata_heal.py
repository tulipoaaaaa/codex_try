import json
from pathlib import Path
import argparse

def heal_metadata(metadata_path, corpus_dir):
    metadata_path = Path(metadata_path)
    corpus_dir = Path(corpus_dir)
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    documents = metadata.get('documents', {})
    updated = 0
    missing = 0
    for doc_id, doc_info in documents.items():
        # Use filename if present, else use the stem of the path
        if 'filename' in doc_info and doc_info['filename']:
            stem = Path(doc_info['filename']).stem
        else:
            stem = Path(doc_info.get('path', '')).stem
        domain = doc_info.get('domain')
        candidate = corpus_dir / f"{domain}_extracted" / f"{stem}.txt"
        if 'extracted_text_path' not in doc_info or not doc_info['extracted_text_path']:
            if candidate.exists():
                doc_info['extracted_text_path'] = str(candidate)
                updated += 1
            else:
                print(f"[MISSING] {doc_id}: expected {candidate} (from domain={domain}, stem={stem})")
                missing += 1
    if updated > 0:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        print(f"Healed {updated} documents in metadata.")
    else:
        print("No missing extracted_text_path fields found.")
    print(f"Total missing extracted text files: {missing}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Heal corpus_metadata.json by backfilling extracted_text_path fields.")
    parser.add_argument('--metadata', required=True, help='Path to corpus_metadata.json')
    parser.add_argument('--corpus', required=True, help='Path to corpus root directory')
    args = parser.parse_args()
    heal_metadata(args.metadata, args.corpus) 