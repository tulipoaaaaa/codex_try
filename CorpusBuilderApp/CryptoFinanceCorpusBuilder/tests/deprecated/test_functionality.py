import sys
import subprocess
import json
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command and return success status."""
    print(f"\n>>> {description}")
    print(f"Running: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, text=True, 
                              capture_output=True)
        print(f"✅ Success: {description}")
        print(f"Output: {result.stdout[:500]}..." if len(result.stdout) > 500 else f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {description}")
        print(f"Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error output: {e.stderr}")
        return False

def test_basic_functionality():
    """Test the basic functionality of the corpus builder."""
    tests = [
        (
            "python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli --help",
            "Testing CLI help/usage output"
        ),
        (
            "python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources arxiv --output-dir data/test_collect/arxiv --arxiv-clear-output-dir --arxiv-max-results 1",
            "Testing collect command (arxiv, output to data/test_collect/arxiv)"
        ),
        (
            "python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli process --input-dir data/test_collect/arxiv --output-dir data/test_processed",
            "Testing process command (input: data/test_collect/arxiv, output: data/test_processed)"
        ),
        (
            "python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli stats --corpus-dir data/test_collect/arxiv",
            "Testing stats command (on data/test_collect/arxiv)"
        ),
        (
            "python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources isda --output-dir data/test_collect/isda --isda-clear-output-dir --isda-max-sources 1",
            "Testing ISDA modular collector"
        ),
        (
            "python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources bitmex_research --output-dir data/test_collect/bitmex --bitmex-clear-output-dir --bitmex-max-pages 1",
            "Testing BitMEX modular collector"
        ),
        (
            "python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources annas_main_library --output-dir data/test_collect/annas_main_library",
            "Testing Anna's Archive Main Library modular collector"
        ),
        (
            "python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources annas_scidb_search --scidb-doi 10.1016/j.physa.2018.02.169 --output-dir data/test_collect/annas_scidb",
            "Testing Anna's Archive SCIDB modular collector"
        ),
        (
            "python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect --sources general_web_corpus --output-dir data/test_collect/general_web_corpus",
            "Testing General Web Corpus modular collector"
        ),
        # (
        #     'python -m CryptoFinanceCorpusBuilder.cli.crypto_corpus_cli collect_annas --query "Black Swan Taleb" --client simple --output-dir data/test_annas',
        #     'Testing collect_annas command (simple client, output to data/test_annas)'
        # )
    ]
    
    # Run tests sequentially
    results = []
    for cmd, desc in tests:
        success = run_command(cmd, desc)
        results.append((desc, success))
    
    # Print summary
    print("\n=== TEST SUMMARY ===")
    all_passed = all([success for _, success in results])
    
    for desc, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {desc}")
    
    if all_passed:
        print("\n✅ All tests passed!")
    else:
        print("\n⚠️ Some tests failed.")
    
    return all_passed

if __name__ == '__main__':
    sys.exit(0 if test_basic_functionality() else 1) 