# DEPRECATED: This file belongs to the legacy CryptoFinanceCorpusBuilder package and should not be used in new modules.
import os
import sys
import pytest
from pathlib import Path
from shared_tools.collectors.quantopian_collector import QuantopianCollector
from shared_tools.project_config import ProjectConfig

@pytest.fixture
def config():
    """Fixture to provide ProjectConfig instance"""
    config_path = os.path.join(os.path.dirname(__file__), '../../config/test_config.yaml')
    return ProjectConfig(config_path, environment='test')

@pytest.fixture
def collector(config):
    """Fixture to provide QuantopianCollector instance"""
    return QuantopianCollector(config)

def test_quantopian_collector_projectconfig(config, collector):
    """Test QuantopianCollector with ProjectConfig integration and real downloads"""
    
    # Test search terms from config
    search_terms = []
    for domain, domain_config in config.domain_configs.items():
        search_terms.extend(domain_config.get('search_terms', []))
    
    # Collect algorithms with real downloads
    results = collector.collect(
        search_terms=search_terms[:2],  # Limit to 2 terms for testing
        max_results=2  # Limit results for testing
    )
    
    # Verify results
    assert len(results) > 0, "No algorithms were collected"
    
    # Check file structure
    for result in results:
        # Verify file exists
        assert Path(result['filepath']).exists(), f"File not found: {result['filepath']}"
        
        # Verify file is in correct domain directory
        file_path = Path(result['filepath'])
        assert file_path.parent.parent.name in config.domain_configs, f"Invalid domain directory: {file_path.parent.parent.name}"
        
        # Verify metadata
        assert 'algorithm_id' in result, "Algorithm ID missing from metadata"
        assert 'title' in result, "Title missing from metadata"
        assert 'filepath' in result, "Filepath missing from metadata"
        
        # Verify file size
        file_size = file_path.stat().st_size
        assert file_size > 1000, f"File too small: {file_size} bytes"
        assert file_size < 1000000, f"File too large: {file_size} bytes"

@pytest.mark.integration
def test_quantopian_collector_by_id(config, collector):
    """Test collecting specific algorithms by ID"""
    algorithm_ids = [
        "Q-2023-001",
        "Q-2023-002"
    ]
    
    # Collect algorithms by ID
    results = collector.collect_by_id(algorithm_ids)
    
    # Verify results
    assert len(results) > 0, "No algorithms were collected"
    
    # Check file structure
    for result in results:
        # Verify file exists
        assert Path(result['filepath']).exists(), f"File not found: {result['filepath']}"
        
        # Verify file is in correct domain directory
        file_path = Path(result['filepath'])
        assert file_path.parent.parent.name in config.domain_configs, f"Invalid domain directory: {file_path.parent.parent.name}"
        
        # Verify metadata
        assert result['algorithm_id'] in algorithm_ids, "Algorithm ID mismatch"
        assert 'title' in result, "Title missing from metadata"
        assert 'filepath' in result, "Filepath missing from metadata"
        
        # Verify file size
        file_size = file_path.stat().st_size
        assert file_size > 1000, f"File too small: {file_size} bytes"
        assert file_size < 1000000, f"File too large: {file_size} bytes"

@pytest.mark.integration
def test_domain_classification(collector):
    """Integration test: Test domain classification of algorithms"""
    # Test with known algorithm IDs
    algorithms = [
        {'id': 'Q-2023-001', 'domain': 'portfolio_construction'},
        {'id': 'Q-2023-002', 'domain': 'high_frequency_trading'},
        {'id': 'Q-2023-003', 'domain': 'risk_management'}
    ]
    
    results = collector.collect_by_id([item['id'] for item in algorithms])
    
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
    # First collect an algorithm by ID
    algorithm_id = "Q-2023-001"
    results = collector.collect_by_id(algorithm_id)
    assert len(results) > 0
    
    # Test file validation
    filepath = results[0]['filepath']
    assert collector._check_file_validity(filepath)

@pytest.mark.integration
def test_metadata_generation(collector):
    """Integration test: Test metadata generation for collected algorithms"""
    algorithm_id = "Q-2023-001"
    results = collector.collect_by_id(algorithm_id)
    assert len(results) > 0
    
    result = results[0]
    meta_file = Path(result['filepath']).with_suffix('.meta')
    
    assert meta_file.exists()
    assert all(key in result for key in ['algorithm_id', 'title', 'filepath'])

def test_error_handling(collector):
    """Test error handling for invalid inputs"""
    # Test with invalid algorithm ID
    results = collector.collect_by_id(["INVALID-ID-123"])
    assert len(results) == 0
    
    # Test with empty ID list
    results = collector.collect_by_id([])
    assert len(results) == 0

@pytest.mark.integration
def test_cleanup(collector):
    """Integration test: Test cleanup of downloaded files"""
    # Collect some algorithms by ID
    algorithm_id = "Q-2023-001"
    results = collector.collect_by_id(algorithm_id)
    
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
    pytest.main([__file__, "-v"]) 