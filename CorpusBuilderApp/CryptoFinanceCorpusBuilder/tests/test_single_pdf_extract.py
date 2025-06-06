import sys
from pathlib import Path

# Add the project root to sys.path
sys.path.append(str(Path(__file__).parent / "CryptoFinanceCorpusBuilder"))

from processors.text_extractor import TextExtractor

pdf_path = "data/corpus_1/crypto_derivatives/crypto_derivatives_trading_multiple_mean_reversion.pdf"
extractor = TextExtractor(num_workers=1)
result = extractor.extract(pdf_path)
print(f"Extraction result for {pdf_path}:")
print(result) 