import os
import json
from pathlib import Path
from dotenv import load_dotenv
from CryptoFinanceCorpusBuilder.shared_tools.collectors.enhanced_client import CookieAuthClient

def test_annas_main_library_batch():
    """Test downloading a small batch of crypto-finance books from Anna's Archive Main Library"""
    print("===== TESTING ANNA'S ARCHIVE MAIN LIBRARY BATCH DOWNLOAD =====\n")

    # Set up directories
    test_dir = Path("./test_outputs/annas_main_library")
    test_dir.mkdir(parents=True, exist_ok=True)

    # Load cookie from .env
    load_dotenv()
    account_cookie = os.getenv("AA_ACCOUNT_COOKIE")

    if not account_cookie:
        print("ERROR: Please add AA_ACCOUNT_COOKIE to your .env file first")
        return False

    # Initialize client
    client = CookieAuthClient(download_dir=test_dir, account_cookie=account_cookie)

    if not client.is_authenticated:
        print("ERROR: Authentication failed with the provided cookie")
        return False

    # Create a test batch of books
    test_batch = [
        {"title": "The Black Swan: The Impact of the Highly Improbable", "author": "Nassim Nicholas Taleb", "domain": "risk_management", "format": "pdf"},
        {"title": "Options Futures and Other Derivatives", "author": "John Hull", "domain": "crypto_derivatives", "format": "pdf"},
        {"title": "Market Microstructure Theory", "author": "Maureen O'Hara", "domain": "market_microstructure", "format": "pdf"},
        {"title": "Algorithmic Trading and DMA", "author": "Barry Johnson", "domain": "high_frequency_trading", "format": "pdf"},
        {"title": "Decentralized Finance (DeFi)", "author": "Campbell Harvey", "domain": "decentralized_finance", "format": "pdf"}
    ]

    results = {"successful": [], "failed": []}
    for item in test_batch:
        query = item["title"]
        search_results = client.search(query)
        if not search_results:
            results["failed"].append({"item": item, "reason": "No search results"})
            continue
        # Pick the top result
        top_result = search_results[0]
        md5 = top_result.get("md5")
        if not md5:
            results["failed"].append({"item": item, "reason": "No MD5 in search result"})
            continue
        output_path = client.download_file(md5)
        if not output_path:
            print("Falling back to Selenium-based download...")
            output_path = client.download_main_library_file(md5)
        if output_path:
            results["successful"].append({"item": item, "filepath": str(output_path)})
        else:
            results["failed"].append({"item": item, "reason": "Download failed"})

    # Save results
    results_file = test_dir / "test_batch_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    print("\nTest Batch Results:")
    print(f"Total attempted: {len(test_batch)}")
    print(f"Successfully downloaded: {len(results['successful'])}")
    print(f"Failed downloads: {len(results['failed'])}")

    if len(results['successful']) > 0:
        print("\nSuccessfully downloaded:")
        for item in results['successful']:
            print(f"  - {item['item']['title']} by {item['item']['author']} ({item['filepath']})")

    if len(results['failed']) > 0:
        print("\nFailed downloads:")
        for item in results['failed']:
            print(f"  - {item['item']['title']} by {item['item']['author']}: {item['reason']}")

    # Return success based on whether at least one book was downloaded
    return len(results['successful']) > 0

if __name__ == "__main__":
    success = test_annas_main_library_batch()
    if success:
        print("\n✅ Anna's Archive Main Library batch test completed successfully!")
    else:
        print("\n❌ Anna's Archive Main Library batch test failed!") 