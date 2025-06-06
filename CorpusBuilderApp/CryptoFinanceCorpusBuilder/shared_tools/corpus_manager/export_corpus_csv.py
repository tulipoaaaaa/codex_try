import csv
import json
from pathlib import Path
import argparse

def export_corpus_csv(metadata_path, output_path, high_output_path=None):
    metadata_path = Path(metadata_path)
    output_path = Path(output_path)
    high_output_path = Path(high_output_path) if high_output_path else None

    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    documents = metadata.get("documents", {})

    # Define columns
    columns = [
        "id", "domain", "filename", "token_count", "priority", "extracted_only",
        "extracted_text_path", "path", "note", "source"
    ]

    # Write all entries to main CSV
    with open(output_path, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        for doc_id, doc in documents.items():
            row = {col: doc.get(col, "") for col in columns}
            row["id"] = doc_id
            writer.writerow(row)
    print(f"✅ Exported {len(documents)} entries to {output_path}")

    # Write high-priority entries to high_output_path if requested
    if high_output_path:
        high_count = 0
        with open(high_output_path, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
            for doc_id, doc in documents.items():
                if doc.get("priority") == "high":
                    row = {col: doc.get(col, "") for col in columns}
                    row["id"] = doc_id
                    writer.writerow(row)
                    high_count += 1
        print(f"✅ Exported {high_count} high-priority entries to {high_output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export corpus metadata to CSV (all and high-priority entries)")
    parser.add_argument('--metadata', required=True, help='Path to corpus_metadata.json')
    parser.add_argument('--output', required=True, help='Path to output CSV for all entries')
    parser.add_argument('--high-output', help='Path to output CSV for high-priority entries')
    args = parser.parse_args()
    export_corpus_csv(args.metadata, args.output, args.high_output) 