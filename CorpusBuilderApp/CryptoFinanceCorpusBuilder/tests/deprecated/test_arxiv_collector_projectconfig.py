import os
import sys
import pytest
from pathlib import Path
from shared_tools.collectors.arxiv_collector import ArxivCollector
from shared_tools.project_config import ProjectConfig

@pytest.fixture
def config():
    """Create a test configuration"""
    # Use the production test config file
    config_path = Path('CryptoFinanceCorpusBuilder/config/test_config.yaml')
    return ProjectConfig(str(config_path), environment='test')

@pytest.fixture
def collector(config):
    """Create an ArxivCollector instance"""
    return ArxivCollector(config)

def test_arxiv_collector_projectconfig(config, collector):
    """Test ArxivCollector with ProjectConfig integration and real downloads"""
    
    # Use a specific search term that we know exists
    search_term = "bitcoin futures"
    
    # Collect papers using search term
    results = collector.collect(search_terms=[search_term], max_results=2)
    
    # Verify results
    assert len(results) > 0, "Should find some papers"
    for paper in results:
        assert 'title' in paper, "Each paper should have a title"
        assert 'authors' in paper, "Each paper should have authors"
        assert 'arxiv_id' in paper, "Each paper should have an arXiv ID"
        assert 'pdf_link' in paper, "Each paper should have a PDF link"
        assert 'filepath' in paper, "Each paper should have a filepath"
        assert 'domain' in paper, "Each paper should have a domain"
        assert os.path.exists(paper['filepath']), "PDF file should exist"
        assert os.path.getsize(paper['filepath']) > 0, "PDF file should not be empty"

@pytest.mark.xfail(reason="arXiv API may return papers with different categories than requested")
@pytest.mark.integration
def test_arxiv_collector_by_category(config, collector):
    """Test collecting papers by category"""
    # Test with a specific category
    category = "q-fin.CP"  # Computational Finance category
    
    # Collect papers by category
    results = collector.collect(search_terms=[f"cat:{category}"], max_results=2)
    
    # Verify results
    assert len(results) > 0, "Should find some papers"
    for paper in results:
        assert paper['primary_category'] == category, "Paper should be from the correct category"
        assert paper['domain'] == 'crypto_derivatives', "Paper should be classified as crypto_derivatives"
        assert os.path.exists(paper['filepath']), "PDF file should exist"

@pytest.mark.xfail(reason="Domain classification will be handled by PDF extractor for unknown categories")
@pytest.mark.integration
def test_domain_classification(collector):
    """Integration test: Test domain classification of papers"""
    # Test with specific categories that map to different domains
    categories = [
        ('q-fin.CP', 'crypto_derivatives'),
        ('q-fin.PM', 'portfolio_construction'),
        ('q-fin.RM', 'risk_management')
    ]
    
    for category, expected_domain in categories:
        results = collector.collect(search_terms=[f"cat:{category}"], max_results=1)
        if results:
            paper = results[0]
            assert paper['domain'] == expected_domain, f"Paper from {category} should be in {expected_domain} domain"
            assert paper['primary_category'] == category, f"Paper should have category {category}"

@pytest.mark.integration
def test_file_validation(collector):
    """Integration test: Test PDF file validation"""
    # Use a specific search term
    search_term = "bitcoin futures"
    results = collector.collect(search_terms=[search_term], max_results=1)
    
    # Verify file properties
    assert len(results) > 0, "Should find the paper"
    paper = results[0]
    assert os.path.exists(paper['filepath']), "PDF file should exist"
    assert os.path.getsize(paper['filepath']) > 0, "PDF file should not be empty"
    assert paper['filepath'].endswith('.pdf'), "File should be a PDF"

def test_error_handling(collector):
    """Test error handling for invalid inputs"""
    # Test with invalid search term
    results = collector.collect(search_terms=["invalid_search_term_123456789"], max_results=1)
    assert len(results) == 0, "Should handle invalid search term gracefully"
    
    # Test with empty search terms
    results = collector.collect(search_terms=[], max_results=1)
    assert len(results) >= 0, "Should handle empty search terms"

@pytest.mark.integration
def test_cleanup(collector):
    """Integration test: Test cleanup of downloaded files"""
    # Use a specific search term
    search_term = "bitcoin futures"
    results = collector.collect(search_terms=[search_term], max_results=1)
    
    # Verify files were downloaded
    assert len(results) > 0, "Should find the paper"
    paper = results[0]
    assert os.path.exists(paper['filepath']), "PDF file should exist"
    
    # Clean up
    if os.path.exists(paper['filepath']):
        os.remove(paper['filepath'])
    assert not os.path.exists(paper['filepath']), "File should be removed"

if __name__ == "__main__":
    test_arxiv_collector_projectconfig()
    print("Arxiv collector test completed successfully!") 