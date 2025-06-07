# DEPRECATED: This file belongs to the legacy CryptoFinanceCorpusBuilder package and should not be used in new modules.
import os
import sys
import pytest
from pathlib import Path
from shared_tools.collectors.general_web_collector import GeneralWebCollector
from shared_tools.project_config import ProjectConfig

@pytest.fixture
def config():
    """Fixture to provide ProjectConfig instance"""
    config_path = os.path.join(os.path.dirname(__file__), '../../config/test_config.yaml')
    return ProjectConfig(config_path, environment='test')

@pytest.fixture
def collector(config):
    """Fixture to provide GeneralWebCollector instance"""
    return GeneralWebCollector(config)

def test_general_web_collector_projectconfig(config, collector):
    """Test GeneralWebCollector with ProjectConfig integration and real downloads"""
    
    # Test search terms from config
    search_terms = []
    for domain, domain_config in config.domain_configs.items():
        search_terms.extend(domain_config.get('search_terms', []))
    
    # Collect web pages with real downloads
    results = collector.collect(
        search_terms=search_terms[:2],  # Limit to 2 terms for testing
        max_results=2  # Limit results for testing
    )
    
    # Verify results
    assert len(results) > 0, "No web pages were collected"
    
    # Check file structure
    for result in results:
        # Verify file exists
        assert Path(result['filepath']).exists(), f"File not found: {result['filepath']}"
        
        # Verify file is in correct domain directory
        file_path = Path(result['filepath'])
        assert file_path.parent.parent.name in config.domain_configs, f"Invalid domain directory: {file_path.parent.parent.name}"
        
        # Verify metadata
        assert 'url' in result, "URL missing from metadata"
        assert 'title' in result, "Title missing from metadata"
        assert 'filepath' in result, "Filepath missing from metadata"
        
        # Verify file size
        file_size = file_path.stat().st_size
        assert file_size > 1000, f"File too small: {file_size} bytes"
        assert file_size < 1000000, f"File too large: {file_size} bytes"

@pytest.mark.integration
def test_general_web_collector_by_url(config, collector):
    """Test collecting specific web pages by URL"""
    urls = [
        "https://example.com/finance/article1",
        "https://example.com/crypto/article2"
    ]
    
    # Collect web pages by URL
    results = collector.collect_by_url(urls)
    
    # Verify results
    assert len(results) > 0, "No web pages were collected"
    
    # Check file structure
    for result in results:
        # Verify file exists
        assert Path(result['filepath']).exists(), f"File not found: {result['filepath']}"
        
        # Verify file is in correct domain directory
        file_path = Path(result['filepath'])
        assert file_path.parent.parent.name in config.domain_configs, f"Invalid domain directory: {file_path.parent.parent.name}"
        
        # Verify metadata
        assert result['url'] in urls, "URL mismatch"
        assert 'title' in result, "Title missing from metadata"
        assert 'filepath' in result, "Filepath missing from metadata"
        
        # Verify file size
        file_size = file_path.stat().st_size
        assert file_size > 1000, f"File too small: {file_size} bytes"
        assert file_size < 1000000, f"File too large: {file_size} bytes"

@pytest.mark.integration
def test_domain_classification(collector):
    """Integration test: Test domain classification of web pages"""
    # Test with known URLs
    urls = [
        {'url': 'https://example.com/portfolio/article1', 'domain': 'portfolio_construction'},
        {'url': 'https://example.com/risk/article2', 'domain': 'risk_management'},
        {'url': 'https://example.com/defi/article3', 'domain': 'decentralized_finance'}
    ]
    
    results = collector.collect_by_url([item['url'] for item in urls])
    
    assert len(results) > 0
    for result in results:
        assert 'domain' in result
        assert result['domain'] in [
            "portfolio_construction",
            "risk_management",
            "regulation_compliance",
            "decentralized_finance",
            "valuation_models",
            "high_frequency_trading",
            "market_microstructure",
            "crypto_derivatives"
        ]

@pytest.mark.integration
def test_file_validation(collector):
    """Integration test: Test file validation"""
    # First collect a web page by URL
    url = "https://example.com/finance/article1"
    results = collector.collect_by_url(url)
    assert len(results) > 0
    
    # Test file validation
    filepath = results[0]['filepath']
    assert collector._check_file_validity(filepath)

@pytest.mark.integration
def test_metadata_generation(collector):
    """Integration test: Test metadata generation for collected web pages"""
    url = "https://example.com/finance/article1"
    results = collector.collect_by_url(url)
    assert len(results) > 0
    
    result = results[0]
    meta_file = Path(result['filepath']).with_suffix('.meta')
    
    assert meta_file.exists()
    assert all(key in result for key in ['url', 'title', 'filepath'])

def test_error_handling(collector):
    """Test error handling for invalid inputs"""
    # Test with invalid URL
    results = collector.collect_by_url(["https://invalid-url-123.com"])
    assert len(results) == 0
    
    # Test with empty URL list
    results = collector.collect_by_url([])
    assert len(results) == 0

@pytest.mark.integration
def test_cleanup(collector):
    """Integration test: Test cleanup of downloaded files"""
    # Collect some web pages by URL
    url = "https://example.com/finance/article1"
    results = collector.collect_by_url(url)
    
    # Clean up
    for result in results:
        filepath = Path(result['filepath'])
        if filepath.exists():
            filepath.unlink()
        meta_file = filepath.with_suffix('.meta')
        if meta_file.exists():
            meta_file.unlink()
    
    # Verify cleanup
    assert not any(Path(result['filepath']).exists() for result in results)

if __name__ == "__main__":
    test_general_web_collector_projectconfig()
    print("General web collector test completed successfully!") 