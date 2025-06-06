import json
from pathlib import Path

# List of flagged .txt files (from previous script output)
flagged_txts = [
    "data/corpus_1/crypto_derivatives_extracted/crypto_derivatives_Binance_Report_AI-Crypto-Exploring-Use-Cases-and-Possibilities-.txt",
    "data/corpus_1/crypto_derivatives_extracted/crypto_derivatives_Binance_Report_a-new-era-for-bitcoin.txt",
    "data/corpus_1/crypto_derivatives_extracted/crypto_derivatives_Binance_Report_financialization-of-nfts.txt",
    "data/corpus_1/crypto_derivatives_extracted/crypto_derivatives_Binance_Report_institutional-custody-in-crypto--.txt",
    "data/corpus_1/crypto_derivatives_extracted/crypto_derivatives_Binance_Report_the-zkevm-world-an-overview-of-zksync.txt",
    "data/corpus_1/market_microstructure_extracted/market_microstructure_Binance_Report_monthly-market-insights-2023-03-.txt",
    "data/corpus_1/market_microstructure_extracted/market_microstructure_Binance_Report_monthly-market-insights-2023-04.txt",
    "data/corpus_1/market_microstructure_extracted/market_microstructure_Binance_Report_monthly-market-insights-2023-05.txt",
]

# Derive PDF paths and metadata keys from TXT paths
pdfs_and_keys = []
for txt_path in flagged_txts:
    txt = Path(txt_path)
    # PDF is in the parent directory, with same stem but .pdf extension
    if "_extracted" in txt.parent.name:
        pdf_dir = txt.parent.parent / txt.parent.name.replace("_extracted", "")
    else:
        pdf_dir = txt.parent
    pdf_path = pdf_dir / (txt.stem + ".pdf")
    # Metadata key is the stem
    key = txt.stem
    pdfs_and_keys.append((txt_path, str(pdf_path), key))

# Delete files and update metadata
def batch_delete(metadata_path):
    metadata_path = Path(metadata_path)
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    docs = metadata.get("documents", {})
    for txt_path, pdf_path, key in pdfs_and_keys:
        for path in [txt_path, pdf_path]:
            p = Path(path)
            if p.exists():
                p.unlink()
                print(f"Deleted: {p}")
        if key in docs:
            del docs[key]
            print(f"Removed metadata entry: {key}")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print("Batch delete and metadata cleanup complete.")

if __name__ == "__main__":
    batch_delete("data/corpus_1/corpus_metadata.json") 