import json
from pathlib import Path

metadata_files = [
    "data/corpus_1/corpus_metadata.json",
    "data/corpus_1/metadata/corpus_metadata.json"
]
keys_to_remove = [
    "crypto_derivatives_Daemon_Goldsmith_-_Order_Flow_Trading_for_Fun_and_Profit",
    "crypto_derivatives_Binance_Report_why-you-should-care-about-data-availability"
]

for metadata_path in metadata_files:
    path = Path(metadata_path)
    if not path.exists():
        print(f"[SKIP] Metadata file not found: {metadata_path}")
        continue
    with open(metadata_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    docs = data.get("documents", {})
    removed = False
    for key in keys_to_remove:
        if key in docs:
            del docs[key]
            print(f"Removed metadata entry: {key} from {metadata_path}")
            removed = True
    if removed:
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Updated {metadata_path}")
    else:
        print(f"No entries to remove in {metadata_path}")
print("Metadata cleanup complete.") 