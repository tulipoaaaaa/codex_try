import os
import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv
from shared_tools.collectors.fred_collector import FREDCollector
from shared_tools.project_config import ProjectConfig

# Load environment variables from .env file
load_dotenv()

@pytest.fixture
def config():
    """Fixture to provide ProjectConfig instance"""
    config_path = os.path.join(os.path.dirname(__file__), '../../config/test_config.yaml')
    return ProjectConfig(config_path, environment='test')

@pytest.fixture
def collector(config):
    """Fixture to provide FREDCollector instance"""
    api_key = os.getenv("FRED_API_KEY")
    print(f"[DEBUG] FRED_API_KEY loaded from environment: {api_key}")  # Debug print
    if not api_key:
        pytest.skip("FRED_API_KEY not found in environment variables")
    return FREDCollector(config, api_key=api_key)

def test_fred_collector_projectconfig(config, collector):
    """Test FREDCollector with ProjectConfig integration and real downloads"""
    
    # Test search terms from config
    search_terms = []
    for domain, domain_config in config.domain_configs.items():
        if hasattr(domain_config, 'search_terms'):
            search_terms.extend(domain_config.search_terms)
    
    # Collect data with real API calls
    results = collector.collect(
        search_terms=search_terms[:2],  # Limit to 2 terms for testing
        max_results=2  # Limit results for testing
    )
    
    # Verify results
    assert len(results) > 0, "No data was collected"
    
    # Check file structure
    for result in results:
        # Verify file exists
        assert Path(result['filepath']).exists(), f"File not found: {result['filepath']}"
        
        # Verify file is in correct domain directory
        file_path = Path(result['filepath'])
        assert file_path.parent.parent.name in config.domain_configs, f"Invalid domain directory: {file_path.parent.parent.name}"
        
        # Verify metadata
        assert 'series_id' in result, "Series ID missing from metadata"
        assert 'title' in result, "Title missing from metadata"
        assert 'filepath' in result, "Filepath missing from metadata"
        
        # Verify file size
        file_size = file_path.stat().st_size
        assert file_size > 1000, f"File too small: {file_size} bytes"
        assert file_size < 1000000, f"File too large: {file_size} bytes"

@pytest.mark.integration
def test_fred_collector_by_series(config, collector):
    """Test collecting specific data by series ID"""
    series_ids = [
        "GDP",
        "UNRATE"
    ]
    
    # Collect data by series ID
    results = collector.collect_by_series(series_ids)
    
    # Verify results
    assert len(results) > 0, "No data was collected"
    
    # Check file structure
    for result in results:
        # Verify file exists
        assert Path(result['filepath']).exists(), f"File not found: {result['filepath']}"
        
        # Verify file is in correct domain directory
        file_path = Path(result['filepath'])
        assert file_path.parent.parent.name in config.domain_configs, f"Invalid domain directory: {file_path.parent.parent.name}"
        
        # Verify metadata
        assert result['series_id'] in series_ids, "Series ID mismatch"
        assert 'title' in result, "Title missing from metadata"
        assert 'filepath' in result, "Filepath missing from metadata"
        
        # Verify file size
        file_size = file_path.stat().st_size
        assert file_size > 1000, f"File too small: {file_size} bytes"
        assert file_size < 1000000, f"File too large: {file_size} bytes"

@pytest.mark.integration
def test_domain_classification(collector):
    """Integration test: Test domain classification of FRED data"""
    # Test with known series IDs
    series = [
        {'id': 'GDP', 'domain': 'valuation_models'},
        {'id': 'UNRATE', 'domain': 'risk_management'},
        {'id': 'CPIAUCSL', 'domain': 'valuation_models'}
    ]
    
    results = collector.collect_by_series([item['id'] for item in series])
    
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
    # First collect data by series ID
    series_id = "GDP"
    results = collector.collect_by_series(series_id)
    assert len(results) > 0
    
    # Test file validation
    filepath = results[0]['filepath']
    assert collector._check_file_validity(filepath)

@pytest.mark.integration
def test_metadata_generation(collector):
    """Integration test: Test metadata generation for collected data"""
    series_id = "GDP"
    results = collector.collect_by_series(series_id)
    assert len(results) > 0
    
    result = results[0]
    meta_file = Path(result['filepath']).with_suffix('.meta')
    
    assert meta_file.exists()
    assert all(key in result for key in ['series_id', 'title', 'filepath'])

def test_error_handling(collector):
    """Test error handling for invalid inputs"""
    # Test with invalid series ID
    results = collector.collect_by_series(["INVALID-SERIES-123"])
    assert len(results) == 0
    
    # Test with empty series ID list
    results = collector.collect_by_series([])
    assert len(results) == 0

@pytest.mark.integration
def test_cleanup(collector):
    """Integration test: Test cleanup of downloaded files"""
    # Collect some data by series ID
    series_id = "GDP"
    results = collector.collect_by_series(series_id)
    
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
    test_fred_collector_projectconfig()
    print("FRED collector test completed successfully!") 