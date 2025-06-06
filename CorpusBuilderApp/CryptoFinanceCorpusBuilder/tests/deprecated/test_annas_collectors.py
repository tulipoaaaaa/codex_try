import os
import sys
from pathlib import Path

# Add project root and CryptoFinanceCorpusBuilder to Python path
project_root = Path(__file__).parent
sys.path.extend([
    str(project_root),
    str(project_root / "CryptoFinanceCorpusBuilder"),
    str(project_root / "CryptoFinanceCorpusBuilder" / "shared tools")
])

from dotenv import load_dotenv
import logging
import argparse
import json

# Set up logging with proper encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'  # Add explicit encoding
)
logger = logging.getLogger(__name__)

def load_env_file():
    """Try to load .env file from multiple locations"""
    env_locations = [
        project_root / ".env",  # Project root
        project_root / "notebooks" / ".env",  # Notebooks folder
    ]
    
    for env_path in env_locations:
        if env_path.exists():
            logger.info(f"Loading .env from: {env_path}")
            load_dotenv(env_path)
            return True
            
    logger.error("No .env file found in any of the expected locations")
    return False

def validate_cookie(cookie):
    """Validate the cookie format"""
    if not cookie:
        return False
    # Basic format check - adjust based on your cookie format
    if len(cookie) < 10:  # Minimum length check
        return False
    return True

def test_annas_collectors():
    """Test both Annas collectors with enhanced client"""
    
    # Load environment variables
    if not load_env_file():
        return False
        
    account_cookie = os.getenv("AA_ACCOUNT_COOKIE")
    if not account_cookie:
        logger.error("Error: AA_ACCOUNT_COOKIE not found in .env file")
        return False
        
    if not validate_cookie(account_cookie):
        logger.error("Error: Invalid cookie format in AA_ACCOUNT_COOKIE")
        return False

    # Create test directories
    test_dir = Path("test_output/annas_test")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Test 1: Enhanced Client Import
    logger.info("Test 1: Testing enhanced client import...")
    try:
        # Try different import paths
        try:
            from CryptoFinanceCorpusBuilder.shared_tools.collectors.enhanced_client import CookieAuthClient
            logger.info("Imported from CryptoFinanceCorpusBuilder.shared_tools.collectors.enhanced_client")
        except ImportError:
            try:
                from shared_tools.collectors.enhanced_client import CookieAuthClient
                logger.info("Imported from shared_tools.collectors.enhanced_client")
            except ImportError:
                from collectors.enhanced_client import CookieAuthClient
                logger.info("Imported from collectors.enhanced_client")
        logger.info("Successfully imported enhanced client")
    except ImportError as e:
        logger.error(f"Failed to import enhanced client: {e}")
        return False

    # Test 2: Client Initialization
    logger.info("\nTest 2: Testing client initialization...")
    try:
        logger.info("Initializing CookieAuthClient...")
        client = CookieAuthClient(download_dir=str(test_dir), account_cookie=account_cookie)
        
        logger.info("Checking authentication status...")
        if client.is_authenticated:
            logger.info("Successfully initialized and authenticated client")
        else:
            logger.error("Client initialization failed - not authenticated")
            logger.error("Please check your cookie in .env file")
            logger.error(f"Cookie length: {len(account_cookie)}")
            logger.error(f"Cookie first 10 chars: {account_cookie[:10]}...")
            return False
    except Exception as e:
        logger.error(f"Client initialization error: {str(e)}")
        logger.error("Full error details:", exc_info=True)
        return False

    # Test 3: Main Library Collector
    logger.info("\nTest 3: Testing main library collector...")
    try:
        # Try different import paths
        try:
            from CryptoFinanceCorpusBuilder.shared_tools.collectors.collect_annas_main_library import run_annas_main_library_collector
        except ImportError:
            try:
                from shared_tools.collectors.collect_annas_main_library import run_annas_main_library_collector
            except ImportError:
                from collectors.collect_annas_main_library import run_annas_main_library_collector
        
        # Create test arguments
        class TestArgs:
            def __init__(self):
                self.output_dir = str(test_dir / "main_library")
                self.existing_titles = None
        
        args = TestArgs()
        source_config = {}  # Empty config for test
        
        # Run collector with a test book
        test_book = "Mastering Bitcoin Antonopoulos"
        test_json = test_dir / "test_books.json"
        with open(test_json, 'w') as f:
            json.dump([test_book], f)
        
        result = run_annas_main_library_collector(
            args=args,
            source_config=source_config,
            base_dir=args.output_dir,
            batch_json=str(test_json)
        )
        
        if result:
            logger.info("Main library collector test completed successfully")
        else:
            logger.error("Main library collector test failed")
            return False
            
    except Exception as e:
        logger.error(f"Main library collector error: {e}")
        return False

    # Test 4: SCIDB Collector
    logger.info("\nTest 4: Testing SCIDB collector...")
    try:
        # Try different import paths
        try:
            from CryptoFinanceCorpusBuilder.shared_tools.collectors.collect_annas_scidb_search import run_annas_scidb_search_collector
        except ImportError:
            try:
                from shared_tools.collectors.collect_annas_scidb_search import run_annas_scidb_search_collector
            except ImportError:
                from collectors.collect_annas_scidb_search import run_annas_scidb_search_collector
        
        # Create test arguments
        class TestArgs:
            def __init__(self):
                self.output_dir = str(test_dir / "scidb")
                self.scidb_doi = "10.1016/j.jbankfin.2021.106293"  # Example DOI
        
        args = TestArgs()
        source_config = {}  # Empty config for test
        
        # Run collector
        run_annas_scidb_search_collector(
            args=args,
            source_config=source_config,
            base_dir=args.output_dir
        )
        
        # Check if file was downloaded
        scidb_dir = Path(args.output_dir)
        if any(scidb_dir.glob("*.pdf")):
            logger.info("SCIDB collector test completed successfully")
        else:
            logger.error("SCIDB collector test failed - no files downloaded")
            return False
            
    except Exception as e:
        logger.error(f"SCIDB collector error: {e}")
        return False

    logger.info("\nAll tests completed successfully!")
    return True

if __name__ == "__main__":
    success = test_annas_collectors()
    sys.exit(0 if success else 1) 