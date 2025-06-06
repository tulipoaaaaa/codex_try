import json
from pathlib import Path
import argparse

# List of high-priority/problematic document keys (now unused, kept for reference)
HIGH_PRIORITY_KEYS = []


def heal_metadata_fields(metadata_path, corpus_dir, doc_id=None):
    metadata_path = Path(metadata_path)
    corpus_dir = Path(corpus_dir)
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    documents = metadata.get('documents', {})
    updated = 0
    flagged = []
    if doc_id is None:
        print("No --doc_id provided. No documents updated.")
        return
    if doc_id not in documents:
        # Try to infer domain and filename from doc_id
        # Expected doc_id format: domain_filename(without .txt)
        try:
            domain, filename_stem = doc_id.split('_', 1)
        except Exception:
            print(f"Could not infer domain/filename from doc_id: {doc_id}")
            return
        # Try to find the original PDF or source file in the corpus
        pdf_path = corpus_dir / domain / (filename_stem + '.pdf')
        txt_path = corpus_dir / f"{domain}_extracted" / (filename_stem + '.txt')
        doc_info = {
            'priority': 'high',
            'domain': domain,
            'filename': filename_stem + '.pdf' if pdf_path.exists() else filename_stem,
            'path': str(pdf_path) if pdf_path.exists() else '',
            'extracted_text_path': str(txt_path) if txt_path.exists() else '',
        }
        # Try to get token count if .txt exists
        if txt_path.exists():
            try:
                with open(txt_path, 'r', encoding='utf-8', errors='ignore') as ftxt:
                    text = ftxt.read()
                tokens = len(text.split())
                doc_info['token_count'] = tokens
                updated += 1
                if len(text.strip()) < 1000 or tokens < 100:
                    flagged.append((doc_id, str(txt_path), len(text.strip()), tokens))
            except Exception as e:
                flagged.append((doc_id, str(txt_path), f"[ERROR] {e}", 0))
        documents[doc_id] = doc_info
        metadata['documents'] = documents
        updated += 1
        print(f"Added new document entry for {doc_id}.")
    else:
        doc_info = documents[doc_id]
        # Skip if extracted_only and no path
        if doc_info.get("extracted_only") and not doc_info.get("path"):
            print("Document is extracted_only and has no path. Skipping.")
            return
        # Tag as high priority
        doc_info['priority'] = 'high'
        # Use filename if present, else use the stem of the path (handle None safely)
        if 'filename' in doc_info and doc_info['filename']:
            stem = Path(doc_info['filename']).stem
        else:
            path_val = doc_info.get('path') or ''
            stem = Path(path_val).stem
        domain = doc_info.get('domain')
        candidate = corpus_dir / f"{domain}_extracted" / f"{stem}.txt"
        # Fill extracted_text_path if missing
        if not doc_info.get('extracted_text_path') and candidate.exists():
            doc_info['extracted_text_path'] = str(candidate)
            updated += 1
        # Fill filename if missing
        if not doc_info.get('filename'):
            doc_info['filename'] = Path(doc_info.get('path', '')).name
            updated += 1
        # Fill token_count if missing and .txt exists
        if (not doc_info.get('token_count') or doc_info.get('token_count') == 0) and candidate.exists():
            try:
                with open(candidate, 'r', encoding='utf-8', errors='ignore') as ftxt:
                    text = ftxt.read()
                tokens = len(text.split())
                doc_info['token_count'] = tokens
                updated += 1
                # Quality check: flag if file is empty or very short
                if len(text.strip()) < 1000 or tokens < 100:
                    flagged.append((doc_id, str(candidate), len(text.strip()), tokens))
            except Exception as e:
                flagged.append((doc_id, str(candidate), f"[ERROR] {e}", 0))
        # Quality check: flag if .txt exists but is empty or very short
        elif candidate.exists():
            try:
                with open(candidate, 'r', encoding='utf-8', errors='ignore') as ftxt:
                    text = ftxt.read()
                tokens = len(text.split())
                if len(text.strip()) < 1000 or tokens < 100:
                    flagged.append((doc_id, str(candidate), len(text.strip()), tokens))
            except Exception as e:
                flagged.append((doc_id, str(candidate), f"[ERROR] {e}", 0))
    # Save updated metadata
    if updated > 0:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        print(f"Healed/updated {updated} fields in metadata for document: {doc_id}.")
    else:
        print("No missing fields found to heal for this document.")
    # Print flagged files
    if flagged:
        print("\n=== Files needing attention (empty or very short .txt) ===")
        for doc_id, path, length, tokens in flagged:
            print(f"{doc_id}: {path} | Length: {length} | Tokens: {tokens}")
    else:
        print("All checked files passed basic quality checks.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Heal and check corpus_metadata.json by filling missing fields and flagging low-quality files.")
    parser.add_argument('--metadata', default='data/corpus_1/corpus_metadata.json', help='Path to corpus_metadata.json (default: data/corpus_1/corpus_metadata.json)')
    parser.add_argument('--corpus', default='data/corpus_1', help='Path to corpus root directory (default: data/corpus_1)')
    parser.add_argument('--doc_id', required=True, help='Document key to update')
    args = parser.parse_args()
    heal_metadata_fields(args.metadata, args.corpus, args.doc_id) 