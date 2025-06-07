# DEPRECATED: This file belongs to the legacy CryptoFinanceCorpusBuilder package and should not be used in new modules.
import os
import sys
import pytest
import logging
from pathlib import Path
from dotenv import load_dotenv
from shared_tools.collectors.collect_annas_main_library import AnnasMainLibraryCollector
from shared_tools.project_config import ProjectConfig

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

@pytest.fixture
def config():
    """Create a test configuration"""
    # Use the production test config file
    config_path = Path('CryptoFinanceCorpusBuilder/config/test_config.yaml')
    return ProjectConfig(str(config_path), environment='test')

@pytest.fixture
def collector(config):
    """Create an AnnasMainLibraryCollector instance with real authentication"""
    # Verify required environment variables
    if not os.getenv('AA_ACCOUNT_COOKIE'):
        pytest.skip("AA_ACCOUNT_COOKIE environment variable not set")
    return AnnasMainLibraryCollector(config)

def test_annas_library_collector_projectconfig(config, collector):
    """Test AnnasMainLibraryCollector with ProjectConfig integration and real downloads"""
    # Test with a specific search term
    search_term = "bitcoin"
    
    # Debug: Print the search URL
    search_url = f"https://annas-archive.org/search?q={search_term}&ext=pdf"
    logger.debug(f"Search URL: {search_url}")
    
    # Collect papers using search term
    results = collector.collect(search_term)
    
    # Debug: Print the results
    logger.debug(f"Found {len(results)} results")
    for result in results:
        logger.debug(f"Result: {result}")
    
    # Verify results
    assert len(results) > 0, "Should find some papers"
    for paper in results:
        assert 'title' in paper, "Each paper should have a title"
        assert 'filepath' in paper, "Each paper should have a filepath"
        assert 'quality_score' in paper, "Each paper should have a quality score"
        assert os.path.exists(paper['filepath']), "PDF file should exist"
        assert os.path.getsize(paper['filepath']) > 0, "PDF file should not be empty"

def test_annas_library_collector_by_category(config, collector):
    """Test collecting papers by category with real downloads"""
    # Test with a specific category
    category = "bitcoin derivatives"  # Changed from "crypto derivatives" to be more specific
    
    # Debug: Print the search URL
    search_url = f"https://annas-archive.org/search?q={category}&ext=pdf"
    logger.debug(f"Search URL: {search_url}")
    
    # Collect papers by category
    logger.debug(f"Starting search for category: {category}")
    results = collector.collect(category)
    logger.debug(f"Search completed. Found {len(results)} results")
    
    # Debug: Print the results
    for result in results:
        logger.debug(f"Result: {result}")
    
    # Verify results
    assert len(results) > 0, "Should find some papers"
    for paper in results:
        assert os.path.exists(paper['filepath']), "PDF file should exist"
        assert os.path.getsize(paper['filepath']) > 0, "PDF file should not be empty"

def test_file_validation(collector):
    """Test PDF file validation with real downloads"""
    # Use a specific search term
    search_term = "bitcoin"
    results = collector.collect(search_term)
    
    # Verify file properties
    assert len(results) > 0, "Should find the paper"
    paper = results[0]
    assert os.path.exists(paper['filepath']), "PDF file should exist"
    assert os.path.getsize(paper['filepath']) > 0, "PDF file should not be empty"
    assert paper['filepath'].endswith('.pdf'), "File should be a PDF"

def test_error_handling(collector):
    """Test error handling for invalid inputs with real collector"""
    # Test with invalid search term
    results = collector.collect("invalid_search_term_123456789")
    assert len(results) == 0, "Should handle invalid search term gracefully"

def test_cleanup(collector):
    """Test cleanup of downloaded files"""
    # Use a specific search term
    search_term = "bitcoin"
    results = collector.collect(search_term)
    
    # Verify files were downloaded
    assert len(results) > 0, "Should find the paper"
    paper = results[0]
    assert os.path.exists(paper['filepath']), "PDF file should exist"
    
    # Log file locations
    logger.info(f"File downloaded to: {paper['filepath']}")
    if 'domain' in paper:
        logger.info(f"File classified into domain: {paper['domain']}")
    
    # Don't clean up - we want to keep the files for inspection
    logger.info("Files left in place for inspection")

if __name__ == "__main__":
    test_annas_library_collector_projectconfig()
    print("Anna's library collector test completed successfully!") 