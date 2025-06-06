import json
from pathlib import Path
import datetime

def heal_all_metadata(metadata_path, corpus_dir, dry_run=False):
    metadata_path = Path(metadata_path)
    corpus_dir = Path(corpus_dir)

    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    documents = metadata.get("documents", {})
    healed_count = 0
    flagged = []
    modified_docs = []

    for doc_id, doc in documents.items():
        updated = False
        domain = doc.get("domain")
        if not domain:
            continue

        is_extracted_only = doc.get("extracted_only", False)

        # Try to guess .txt path
        stem = Path(doc.get("filename", "")).stem if doc.get("filename") else doc_id
        candidate_txt = corpus_dir / f"{domain}_extracted" / f"{stem}.txt"

        # Fill 'filename' even if 'path' is missing, using .txt filename fallback
        if not doc.get("filename"):
            if candidate_txt.exists():
                doc["filename"] = candidate_txt.name
                updated = True

        # Add 'path': None if 'path' is missing
        if "path" not in doc:
            doc["path"] = None
            updated = True

        # Add note if extracted_only and no PDF
        if doc.get("path") is None and is_extracted_only:
            if doc.get("note") != "extracted_only, no PDF":
                doc["note"] = "extracted_only, no PDF"
                updated = True

        # Try to fill extracted_text_path if missing
        if not doc.get("extracted_text_path") and candidate_txt.exists():
            doc["extracted_text_path"] = str(candidate_txt)
            updated = True

        # Fill token count if missing
        if (not doc.get("token_count") or doc["token_count"] == 0) and candidate_txt.exists():
            try:
                text = candidate_txt.read_text(encoding="utf-8", errors="ignore")
                tokens = len(text.split())
                doc["token_count"] = tokens
                updated = True

                if len(text.strip()) < 1000 or tokens < 100:
                    flagged.append((doc_id, str(candidate_txt), len(text.strip()), tokens))
            except Exception as e:
                flagged.append((doc_id, str(candidate_txt), f"[ERROR] {e}", 0))

        # Optional: Add last_updated timestamp
        if updated:
            doc["last_updated"] = datetime.datetime.now().isoformat()
            modified_docs.append(doc_id)
            healed_count += 1

    if dry_run:
        print(f"🟡 DRY RUN: {healed_count} entries would be healed (not saved).")
    else:
        if healed_count > 0:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            print(f"✅ Healed {healed_count} metadata entries.")
        else:
            print("✅ No missing fields detected.")

    if modified_docs:
        print("\n📝 Modified entries:")
        for doc_id in modified_docs:
            print(f" - {doc_id}")

    if flagged:
        print("\n⚠️ Flagged low-quality or short `.txt` files:")
        for doc_id, path, length, tokens in flagged:
            print(f"{doc_id}: {path} | Length: {length} | Tokens: {tokens}")
    else:
        print("✅ All `.txt` files passed basic quality checks.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Heal all corpus metadata entries by filling missing fields.")
    parser.add_argument('--metadata', required=True, help='Path to corpus_metadata.json')
    parser.add_argument('--corpus', required=True, help='Path to corpus directory')
    parser.add_argument('--dry-run', action='store_true', help='Run without saving changes (default: False)')
    args = parser.parse_args()
    heal_all_metadata(args.metadata, args.corpus, dry_run=args.dry_run) 