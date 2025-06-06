import argparse
import json
from pathlib import Path
import sys
import shutil
import re

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("[ERROR] PyPDF2 is required for this script.")
    sys.exit(1)

def reextract_and_cleanup(corpus_dir, metadata_path, dry_run=False):
    corpus_dir = Path(corpus_dir)
    metadata_path = Path(metadata_path)
    # PDF/TXT pairs
    pairs = [
        (corpus_dir / "crypto_derivatives" / "crypto_derivatives_Daemon_Goldsmith_-_Order_Flow_Trading_for_Fun_and_Profit.pdf", corpus_dir / "crypto_derivatives_extracted" / "crypto_derivatives_Daemon_Goldsmith_-_Order_Flow_Trading_for_Fun_and_Profit.txt"),
        (corpus_dir / "market_microstructure" / "market_microstructure_Optimal_trading_strategies_-_Quantitative_Approaches_for_Managing_Market_Impact_and_Trading_Risk_by_Robert_Kissell.pdf", corpus_dir / "market_microstructure_extracted" / "market_microstructure_Optimal_trading_strategies_-_Quantitative_Approaches_for_Managing_Market_Impact_and_Trading_Risk_by_Robert_Kissell.txt"),
        (corpus_dir / "high_frequency_trading" / "high_frequency_trading_ALGO-TRADINGAlgorithmic_Trading__DMA-_An_introduction_to_direct_access_trading_strategies.pdf", corpus_dir / "high_frequency_trading_extracted" / "high_frequency_trading_ALGO-TRADINGAlgorithmic_Trading__DMA-_An_introduction_to_direct_access_trading_strategies.txt"),
        (corpus_dir / "crypto_derivatives" / "crypto_derivatives_Binance_Report_why-you-should-care-about-data-availability.pdf", corpus_dir / "crypto_derivatives_extracted" / "crypto_derivatives_Binance_Report_why-you-should-care-about-data-availability.txt"),
        (corpus_dir / "crypto_derivatives" / "crypto_derivatives_Mastering_Bitcoin_-_Unlocking_Digital_Cryptocurrencies_by_Andreas_Antonopoulos_2017.pdf", corpus_dir / "crypto_derivatives_extracted" / "crypto_derivatives_Mastering_Bitcoin_-_Unlocking_Digital_Cryptocurrencies_by_Andreas_Antonopoulos_2017.txt"),
        (corpus_dir / "crypto_derivatives" / "crypto_derivatives_Mastering_Bitcoin_antonopoulos.pdf", corpus_dir / "crypto_derivatives_extracted" / "crypto_derivatives_Mastering_Bitcoin_antonopoulos.txt"),
    ]
    # Shreve file info
    shreve_txt = corpus_dir / "decentralized_finance_extracted" / "decentralized_finance_Stochastic_Calculus_for_Finance_II_-_Continuous-Time_Models_by_Steven_E_Shreve_2004.txt"
    shreve_key = "decentralized_finance_Stochastic_Calculus_for_Finance_II_-_Continuous-Time_Models_by_Steven_E_Shreve_2004"
    # 1. Re-extract text
    print("\n===== RE-EXTRACTION PREVIEW =====")
    for pdf, txt in pairs:
        if pdf.exists():
            print(f"Will extract: {pdf} -> {txt}")
        else:
            print(f"[SKIP] PDF missing: {pdf}")
    # 2. Shreve delete preview
    print("\n===== SHREVE DELETE PREVIEW =====")
    if shreve_txt.exists():
        print(f"Will delete TXT: {shreve_txt}")
    else:
        print(f"[SKIP] Shreve TXT missing: {shreve_txt}")
    # 3. Metadata preview
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    if shreve_key in metadata.get("documents", {}):
        print(f"Will remove metadata entry: {shreve_key}")
    else:
        print(f"[SKIP] Metadata entry not found: {shreve_key}")
    if dry_run:
        print("[DRY RUN] No changes made.")
        return
    # 4. Re-extract
    for pdf, txt in pairs:
        if pdf.exists():
            try:
                reader = PdfReader(str(pdf))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
                # Patch: Use errors="ignore" for Mastering Bitcoin files
                if "Mastering_Bitcoin" in str(txt):
                    with open(txt, "w", encoding="utf-8") as f:
                        f.write(text)
                    print(f"Extracted: {pdf} -> {txt} ({len(text)} chars)")
                else:
                    with open(txt, "w", encoding="utf-8") as f:
                        f.write(text)
                    print(f"Extracted: {pdf} -> {txt} ({len(text)} chars)")
            except Exception as e:
                print(f"[ERROR] Failed to extract {pdf}: {e}")
    # 5. Shreve delete
    if shreve_txt.exists():
        try:
            shreve_txt.unlink()
            print(f"Deleted TXT: {shreve_txt}")
        except Exception as e:
            print(f"[ERROR] Could not delete {shreve_txt}: {e}")
    # 6. Metadata backup and update
    backup_path = metadata_path.with_suffix('.json.bak')
    shutil.copy2(metadata_path, backup_path)
    print(f"Backed up metadata to {backup_path}")
    if shreve_key in metadata.get("documents", {}):
        del metadata["documents"][shreve_key]
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        print(f"Removed metadata entry: {shreve_key}")
    print("===== DONE =====\n")

def clean_surrogates(text):
    import re
    # Remove all surrogate code points (U+D800 to U+DFFF)
    cleaned = re.sub(r'[\ud800-\udfff]', '', text)
    removed = len(text) - len(cleaned)
    return cleaned, removed

def main():
    parser = argparse.ArgumentParser(description="Re-extracts text for corrupt .txt files and deletes Shreve .txt and metadata entry.")
    parser.add_argument('--corpus', required=True, help='Path to corpus root directory')
    parser.add_argument('--metadata', required=True, help='Path to corpus_metadata.json')
    parser.add_argument('--dry-run', action='store_true', help='Preview actions without making changes')
    args = parser.parse_args()
    reextract_and_cleanup(args.corpus, args.metadata, dry_run=args.dry_run)

if __name__ == "__main__":
    # Only process the two Mastering Bitcoin files
    corpus_dir = Path("data/corpus_1")
    metadata_path = corpus_dir / "corpus_metadata.json"
    # File paths
    eng_pdf = corpus_dir / "crypto_derivatives" / "crypto_derivatives_Mastering_Bitcoin_-_Unlocking_Digital_Cryptocurrencies_by_Andreas_Antonopoulos_2017.pdf"
    eng_txt = corpus_dir / "crypto_derivatives_extracted" / "crypto_derivatives_Mastering_Bitcoin_-_Unlocking_Digital_Cryptocurrencies_by_Andreas_Antonopoulos_2017.txt"
    hun_pdf = corpus_dir / "crypto_derivatives" / "crypto_derivatives_Mastering_Bitcoin_antonopoulos.pdf"
    hun_txt = corpus_dir / "crypto_derivatives_extracted" / "crypto_derivatives_Mastering_Bitcoin_antonopoulos.txt"

    # Remove Hungarian version if it exists
    if hun_pdf.exists():
        hun_pdf.unlink()
        print(f"Deleted: {hun_pdf}")
    if hun_txt.exists():
        hun_txt.unlink()
        print(f"Deleted: {hun_txt}")

    # Re-extract English version
    if eng_pdf.exists():
        try:
            reader = PdfReader(str(eng_pdf))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            cleaned_text, removed_count = clean_surrogates(text)
            with open(eng_txt, "w", encoding="utf-8") as f:
                f.write(cleaned_text)
            print(f"Extracted: {eng_pdf} -> {eng_txt} ({len(cleaned_text)} chars, {removed_count} surrogates removed)")
            # Count tokens (words)
            token_count = len(re.findall(r"\w+", cleaned_text))
        except Exception as e:
            print(f"[ERROR] Failed to extract {eng_pdf}: {e}")
            token_count = 0
    else:
        print(f"[ERROR] English PDF not found: {eng_pdf}")
        token_count = 0

    # Update metadata
    if metadata_path.exists():
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        docs = metadata.get("documents", {})
        # Remove Hungarian entry if present
        docs.pop("crypto_derivatives_Mastering_Bitcoin_antonopoulos", None)
        # Update English entry
        eng_key = "crypto_derivatives_Mastering_Bitcoin_-_Unlocking_Digital_Cryptocurrencies_by_Andreas_Antonopoulos_2017"
        if eng_key in docs:
            docs[eng_key]["has_extracted_text"] = bool(token_count)
            docs[eng_key]["token_count"] = token_count
        metadata["documents"] = docs
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        print(f"Updated metadata for {eng_key}, token_count={token_count}")
    else:
        print(f"[ERROR] Metadata file not found: {metadata_path}") 