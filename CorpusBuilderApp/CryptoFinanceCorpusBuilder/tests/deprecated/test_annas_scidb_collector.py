import os
from pathlib import Path
from dotenv import load_dotenv
from CryptoFinanceCorpusBuilder.shared_tools.collectors.collect_annas_scidb_search import run_annas_scidb_search_collector

# Example DOI for testing (replace with a real, relevant DOI)
TEST_DOI = "10.1111/prd.12104"

def test_annas_scidb_single():
    """Test downloading a single paper from Anna's Archive SciDB by DOI"""
    print("===== TESTING ANNA'S ARCHIVE SCIDB DOI DOWNLOAD =====\n")

    # Set up directories
    test_dir = Path("./test_outputs/annas_scidb")
    test_dir.mkdir(parents=True, exist_ok=True)

    # Load cookie from .env
    load_dotenv()
    account_cookie = os.getenv("AA_ACCOUNT_COOKIE")

    if not account_cookie:
        print("ERROR: Please add AA_ACCOUNT_COOKIE to your .env file first")
        return False

    # Prepare args for the collector
    class Args:
        scidb_doi = TEST_DOI
        output_dir = str(test_dir)
    args = Args()

    # Run the collector
    run_annas_scidb_search_collector(args, source_config=None, base_dir=str(test_dir))
    print("\n✅ Anna's Archive SciDB DOI test completed (check output directory for PDF).\n")

if __name__ == "__main__":
    test_annas_scidb_single() 