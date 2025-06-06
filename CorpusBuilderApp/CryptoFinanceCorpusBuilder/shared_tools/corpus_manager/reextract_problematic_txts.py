import argparse
from pathlib import Path
from PyPDF2 import PdfReader

def safe_extract(pdf_path, txt_path, dry_run=False):
    if dry_run:
        print(f"[DRY RUN] Would extract: {pdf_path} -> {txt_path}")
        return
    try:
        reader = PdfReader(str(pdf_path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        with open(txt_path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(text)
        print(f"Extracted: {pdf_path} -> {txt_path} ({len(text)} chars)")
    except Exception as e:
        print(f"[ERROR] {pdf_path}: {e}")

files = [
    ("data/corpus_1/high_frequency_trading/high_frequency_trading_ALGO-TRADINGAlgorithmic_Trading__DMA-_An_introduction_to_direct_access_trading_strategies.pdf",
     "data/corpus_1/high_frequency_trading_extracted/high_frequency_trading_ALGO-TRADINGAlgorithmic_Trading__DMA-_An_introduction_to_direct_access_trading_strategies.txt"),
    ("data/corpus_1/crypto_derivatives/crypto_derivatives_Daemon_Goldsmith_-_Order_Flow_Trading_for_Fun_and_Profit.pdf",
     "data/corpus_1/crypto_derivatives_extracted/crypto_derivatives_Daemon_Goldsmith_-_Order_Flow_Trading_for_Fun_and_Profit.txt"),
    ("data/corpus_1/crypto_derivatives/crypto_derivatives_Binance_Report_why-you-should-care-about-data-availability.pdf",
     "data/corpus_1/crypto_derivatives_extracted/crypto_derivatives_Binance_Report_why-you-should-care-about-data-availability.txt"),
    ("data/corpus_1/market_microstructure/market_microstructure_Optimal_trading_strategies_-_Quantitative_Approaches_for_Managing_Market_Impact_and_Trading_Risk_by_Robert_Kissell.pdf",
     "data/corpus_1/market_microstructure_extracted/market_microstructure_Optimal_trading_strategies_-_Quantitative_Approaches_for_Managing_Market_Impact_and_Trading_Risk_by_Robert_Kissell.txt"),
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Re-extracts 4 problematic .txt files with errors=ignore. Use --dry-run to preview actions.")
    parser.add_argument('--dry-run', action='store_true', help='Preview actions without making changes')
    args = parser.parse_args()
    for pdf, txt in files:
        if Path(pdf).exists():
            safe_extract(pdf, txt, dry_run=args.dry_run)
        else:
            print(f"[SKIP] PDF missing: {pdf}") 