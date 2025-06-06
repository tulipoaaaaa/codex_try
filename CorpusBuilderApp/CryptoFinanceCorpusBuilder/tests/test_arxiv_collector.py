import os
import pytest
from pathlib import Path
from shared_tools.collectors.arxiv_collector import ArxivCollector
from shared_tools.project_config import ProjectConfig

# Test configuration
TEST_CONFIG = {
    "environment": "test",
    "environments": {
        "test": {
            "corpus_dir": "data/test_output",
            "cache_dir": "data/test_output/cache",
            "log_dir": "data/test_output/logs"
        }
    }
}

@pytest.fixture
def test_config():
    """Create a test configuration"""
    config = ProjectConfig.from_dict(TEST_CONFIG)
    return config

@pytest.fixture
def collector(test_config):
    """Create an arXiv collector instance"""
    output_dir = Path(test_config.get_corpus_dir()) / "arxiv_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    return ArxivCollector(output_dir)

def test_collect_by_category(collector):
    """Test collecting papers by category"""
    categories = ["q-fin.CP", "q-fin.PM"]  # Computational Finance and Portfolio Management
    papers = collector.collect_by_category(categories, max_results=2)
    
    assert len(papers) > 0
    assert all('arxiv_id' in paper for paper in papers)
    assert all('title' in paper for paper in papers)
    assert all('filepath' in paper for paper in papers)
    assert all(Path(paper['filepath']).exists() for paper in papers)

def test_collect_by_search(collector):
    """Test collecting papers by search terms"""
    search_terms = ["cryptocurrency trading strategies"]
    papers = collector.collect_by_search(search_terms, max_results=2)
    
    assert len(papers) > 0
    assert all('title' in paper for paper in papers)
    assert all('filepath' in paper for paper in papers)
    assert all(Path(paper['filepath']).exists() for paper in papers)

def test_metadata_extraction(collector):
    """Test metadata extraction from arXiv papers"""
    papers = collector.collect_by_category(["q-fin.CP"], max_results=1)
    assert len(papers) > 0
    
    paper = papers[0]
    assert all(key in paper for key in [
        'arxiv_id',
        'title',
        'authors',
        'abstract',
        'categories',
        'published_date',
        'updated_date'
    ])

def test_pdf_download(collector):
    """Test PDF download functionality"""
    papers = collector.collect_by_category(["q-fin.CP"], max_results=1)
    assert len(papers) > 0
    
    paper = papers[0]
    filepath = Path(paper['filepath'])
    
    assert filepath.exists()
    assert filepath.suffix == '.pdf'
    assert filepath.stat().st_size > 0

def test_error_handling(collector):
    """Test error handling for invalid inputs"""
    # Test with invalid category
    papers = collector.collect_by_category(["invalid-category"])
    assert len(papers) == 0
    
    # Test with empty search term
    papers = collector.collect_by_search([""])
    assert len(papers) == 0

def test_rate_limiting(collector):
    """Test rate limiting functionality"""
    import time
    start_time = time.time()
    
    # Collect multiple papers to test rate limiting
    papers = collector.collect_by_category(["q-fin.CP"], max_results=3)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Should take at least 3 seconds due to rate limiting
    assert duration >= 3
    assert len(papers) > 0

def test_cleanup(collector):
    """Test cleanup of test files"""
    # Collect some papers
    papers = collector.collect_by_category(["q-fin.CP"], max_results=1)
    
    # Clean up
    for paper in papers:
        filepath = Path(paper['filepath'])
        if filepath.exists():
            filepath.unlink()
    
    # Verify cleanup
    assert not any(Path(paper['filepath']).exists() for paper in papers) 