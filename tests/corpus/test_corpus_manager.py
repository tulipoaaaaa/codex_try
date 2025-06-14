import pytest
from pathlib import Path
import os
import shutil
import json
from datetime import datetime
import logging

@pytest.fixture
def test_data_dir():
    """Fixture to provide test data directory"""
    return Path("G:/data/TEST_CORPUS_MANAGER")

@pytest.fixture
def project_config():
    """Fixture to provide project configuration"""
    class TestProjectConfig:
        def __init__(self):
            self.config = {
                "corpus_manager": {
                    "domains": {
                        "high_frequency_trading": {
                            "path": "high_frequency_trading",
                            "min_documents": 100
                        },
                        "risk_management": {
                            "path": "risk_management",
                            "min_documents": 80
                        },
                        "portfolio_construction": {
                            "path": "portfolio_construction",
                            "min_documents": 70
                        }
                    },
                    "quality_metrics": {
                        "min_token_count": 50,
                        "min_quality_score": 0.6,
                        "max_corruption_score": 0.3
                    }
                }
            }
        
        def get(self, key, default=None):
            return self.config.get(key, default)
        
        def get_processor_config(self, processor_name):
            return self.config.get(processor_name, {})
        
        def get_input_dir(self):
            return Path("G:/data/TEST_CORPUS_MANAGER/input")
        
        def get_logs_dir(self):
            return Path("G:/data/TEST_CORPUS_MANAGER/logs")
    
    return TestProjectConfig()

@pytest.fixture
def corpus_manager():
    """Fixture to provide configured CorpusManager instance"""
    from CorpusBuilderApp.shared_tools.processors.deduplicator import CorpusManager
    return CorpusManager()

def test_corpus_structure_creation(corpus_manager, test_data_dir):
    """Test creation of corpus directory structure"""
    # Create test corpus structure
    corpus_dir = test_data_dir / "test_corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    
    # Create domain directories
    domains = ["high_frequency_trading", "risk_management", "portfolio_construction"]
    for domain in domains:
        domain_dir = corpus_dir / domain
        domain_dir.mkdir(exist_ok=True)
        
        # Create _extracted and low_quality subdirectories
        (domain_dir / "_extracted").mkdir(exist_ok=True)
        (domain_dir / "low_quality").mkdir(exist_ok=True)
        
        # Create sample files
        for subdir in ["_extracted", "low_quality"]:
            for i in range(3):
                file_path = domain_dir / subdir / f"doc_{i}.txt"
                file_path.write_text(f"Test content for {domain} - {subdir} - {i}")
                
                # Create corresponding metadata
                meta_path = domain_dir / subdir / f"doc_{i}.json"
                meta_path.write_text(json.dumps({
                    "domain": domain,
                    "quality_flag": "ok" if subdir == "_extracted" else "low_quality",
                    "token_count": 100,
                    "created_at": datetime.now().isoformat()
                }))
    
    # Verify corpus structure
    assert corpus_dir.exists()
    for domain in domains:
        domain_dir = corpus_dir / domain
        assert domain_dir.exists()
        assert (domain_dir / "_extracted").exists()
        assert (domain_dir / "low_quality").exists()

def test_file_operations(corpus_manager, test_data_dir):
    """Test file operations (copy, move)"""
    # Create source and target directories
    source_dir = test_data_dir / "source"
    target_dir = test_data_dir / "target"
    
    source_dir.mkdir(parents=True, exist_ok=True)
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test files
    test_files = []
    for i in range(3):
        file_path = source_dir / f"test_{i}.txt"
        file_path.write_text(f"Test content {i}")
        test_files.append(str(file_path))
    
    # Test copy operation
    corpus_manager.copy_files(test_files, target_dir)
    for i in range(3):
        assert (target_dir / f"test_{i}.txt").exists()
    
    # Test move operation
    move_dir = test_data_dir / "moved"
    move_dir.mkdir(exist_ok=True)
    corpus_manager.move_files(test_files, move_dir)
    
    # Verify files were moved
    for i in range(3):
        assert not (source_dir / f"test_{i}.txt").exists()
        assert (move_dir / f"test_{i}.txt").exists()

def test_metadata_management(corpus_manager, test_data_dir):
    """Test metadata file operations"""
    # Create test directory with metadata
    meta_dir = test_data_dir / "metadata_test"
    meta_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test files with metadata
    test_data = {
        "doc1.txt": {
            "domain": "high_frequency_trading",
            "quality_flag": "ok",
            "token_count": 150
        },
        "doc2.txt": {
            "domain": "risk_management",
            "quality_flag": "low_quality",
            "token_count": 50
        }
    }
    
    for filename, metadata in test_data.items():
        # Create content file
        file_path = meta_dir / filename
        file_path.write_text(f"Content for {filename}")
        
        # Create metadata file
        meta_path = meta_dir / f"{Path(filename).stem}.json"
        meta_path.write_text(json.dumps(metadata))
    
    # Test metadata operations
    for filename, expected_meta in test_data.items():
        meta_path = meta_dir / f"{Path(filename).stem}.json"
        assert meta_path.exists()
        
        # Verify metadata content
        with open(meta_path, 'r') as f:
            actual_meta = json.load(f)
            assert actual_meta == expected_meta

def test_corpus_validation(corpus_manager, test_data_dir):
    """Test corpus structure validation"""
    # Create valid corpus structure
    valid_corpus = test_data_dir / "valid_corpus"
    valid_corpus.mkdir(parents=True, exist_ok=True)
    
    # Create domain with proper structure
    domain_dir = valid_corpus / "high_frequency_trading"
    domain_dir.mkdir(exist_ok=True)
    (domain_dir / "_extracted").mkdir(exist_ok=True)
    (domain_dir / "low_quality").mkdir(exist_ok=True)
    
    # Create invalid corpus structure
    invalid_corpus = test_data_dir / "invalid_corpus"
    invalid_corpus.mkdir(parents=True, exist_ok=True)
    
    # Create domain with missing required directories
    invalid_domain = invalid_corpus / "risk_management"
    invalid_domain.mkdir(exist_ok=True)
    
    # Test validation
    assert corpus_manager.validate_corpus_structure(valid_corpus)
    assert not corpus_manager.validate_corpus_structure(invalid_corpus)

def test_corpus_statistics(corpus_manager, test_data_dir):
    """Test corpus statistics generation"""
    # Create test corpus with known distribution
    stats_corpus = test_data_dir / "stats_corpus"
    stats_corpus.mkdir(parents=True, exist_ok=True)
    
    # Create domains with different document counts
    domains = {
        "high_frequency_trading": 5,
        "risk_management": 3,
        "portfolio_construction": 2
    }
    
    for domain, count in domains.items():
        domain_dir = stats_corpus / domain
        domain_dir.mkdir(exist_ok=True)
        extracted_dir = domain_dir / "_extracted"
        extracted_dir.mkdir(exist_ok=True)
        
        for i in range(count):
            # Create content file
            file_path = extracted_dir / f"doc_{i}.txt"
            file_path.write_text(f"Content for {domain} - {i}")
            
            # Create metadata
            meta_path = extracted_dir / f"doc_{i}.json"
            meta_path.write_text(json.dumps({
                "domain": domain,
                "quality_flag": "ok",
                "token_count": 100,
                "created_at": datetime.now().isoformat()
            }))
    
    # Generate and verify statistics
    stats = corpus_manager.generate_corpus_statistics(stats_corpus)
    
    assert "total_documents" in stats
    assert stats["total_documents"] == sum(domains.values())
    
    assert "domain_distribution" in stats
    for domain, count in domains.items():
        assert stats["domain_distribution"][domain] == count

    # Keep generated files for inspection; only close log handlers.
    logging.shutdown()
    # If you want to clean up automatically, uncomment the next line.
    # shutil.rmtree(out_dir, ignore_errors=True) 