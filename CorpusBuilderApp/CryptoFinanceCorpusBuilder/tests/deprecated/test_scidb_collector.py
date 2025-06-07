# DEPRECATED: This file belongs to the legacy CryptoFinanceCorpusBuilder package and should not be used in new modules.
import os
import pytest
from pathlib import Path
from shared_tools.project_config import ProjectConfig
from shared_tools.collectors.enhanced_scidb_collector import SciDBCollector

@pytest.fixture
def test_config():
    """Create test configuration."""
    config_path = os.path.join(os.path.dirname(__file__), '../config/test_config.yaml')
    return ProjectConfig(config_path, environment='test')

@pytest.fixture
def collector(test_config):
    """Create SciDBCollector instance with test configuration."""
    return SciDBCollector(test_config)

def test_collector_initialization(collector, test_config):
    """Test collector initialization with ProjectConfig."""
    assert collector.output_dir == test_config.raw_data_dir
    assert collector.logger is not None

def test_domain_directories_creation(collector, test_config):
    """Test creation of domain-specific directories."""
    for domain in test_config.domain_configs:
        domain_dir = test_config.raw_data_dir / domain
        assert domain_dir.exists()
        for content_type in ['papers', 'reports', 'articles']:
            assert (domain_dir / content_type).exists()

def test_search_by_doi(collector):
    """Test searching for a paper by DOI."""
    doi = "10.1016/j.jbankfin.2021.106159"  # Example DOI
    paper_info = collector._search_by_doi(doi)
    assert paper_info is not None
    assert 'title' in paper_info
    assert 'download_url' in paper_info

def test_determine_domain(collector):
    """Test domain determination from paper info."""
    paper_info = {
        'title': 'Unemployment and aggregate stock returns',
        'doi': '10.1016/j.jbankfin.2021.106159'
    }
    domain = collector._determine_domain(paper_info, None, 'portfolio_construction')
    assert domain == 'portfolio_construction'

def test_download_paper(collector, test_config):
    """Test paper download functionality."""
    paper_info = {
        'title': 'Test Paper',
        'doi': '10.1016/j.jbankfin.2021.106159',
        'domain': 'portfolio_construction'
    }
    filepath = collector._download_paper(paper_info)
    assert filepath is None  # Should be None in test environment without actual download

@pytest.mark.integration
def test_collect_by_doi(collector):
    """Integration test: Test collecting papers by DOI with real download"""
    # Test with a known valid DOI
    doi_list = ["10.1016/j.jbankfin.2021.106159"]  # Example finance paper DOI
    papers = collector.collect_by_doi(doi_list)
    
    assert len(papers) > 0
    assert all('doi' in paper for paper in papers)
    assert all('filepath' in paper for paper in papers)
    assert all(Path(paper['filepath']).exists() for paper in papers)

@pytest.mark.integration
def test_domain_classification_by_doi(collector):
    """Integration test: Test domain classification of papers using DOIs with real download"""
    doi_list = [
        {'doi': '10.1016/j.jbankfin.2021.106159', 'domain': 'portfolio_construction'},
        {'doi': '10.1016/j.jbankfin.2021.106159', 'domain': 'risk_management'},
        {'doi': '10.1016/j.jbankfin.2021.106159', 'domain': 'crypto_derivatives'}
    ]
    
    papers = collector.collect_by_doi(doi_list)
    
    assert len(papers) > 0
    for paper in papers:
        assert 'domain' in paper
        assert paper['domain'] in [
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
    """Integration test: Test PDF file validation with real download"""
    # First collect a paper by DOI
    doi_list = ["10.1016/j.jbankfin.2021.106159"]
    papers = collector.collect_by_doi(doi_list)
    assert len(papers) > 0
    
    # Test file validation
    filepath = papers[0]['filepath']
    assert collector._check_file_validity(filepath)

@pytest.mark.integration
def test_metadata_generation(collector):
    """Integration test: Test metadata generation for collected papers with real download"""
    doi_list = ["10.1016/j.jbankfin.2021.106159"]
    papers = collector.collect_by_doi(doi_list)
    assert len(papers) > 0
    
    paper = papers[0]
    meta_file = Path(paper['filepath']).with_suffix('.meta')
    
    assert meta_file.exists()
    assert all(key in paper for key in ['doi', 'filepath'])

def test_error_handling(collector):
    """Test error handling for invalid inputs"""
    # Test with invalid DOI
    papers = collector.collect_by_doi(["invalid_doi_123"])
    assert len(papers) == 0
    
    # Test with empty DOI list
    papers = collector.collect_by_doi([])
    assert len(papers) == 0

@pytest.mark.integration
def test_cleanup(collector):
    """Integration test: Test cleanup of downloaded files"""
    # Collect some papers by DOI
    doi_list = ["10.1016/j.jbankfin.2021.106159"]
    papers = collector.collect_by_doi(doi_list)
    
    # Clean up
    for paper in papers:
        filepath = Path(paper['filepath'])
        if filepath.exists():
            filepath.unlink()
        meta_file = filepath.with_suffix('.meta')
        if meta_file.exists():
            meta_file.unlink()
    
    # Verify cleanup
    assert not any(Path(paper['filepath']).exists() for paper in papers) 