import pytest
from pathlib import Path
import os
import shutil
import json
from datetime import datetime

@pytest.fixture
def test_data_dir():
    """Fixture to provide test data directory"""
    return Path("G:/data/test_corPUS_balancer")

@pytest.fixture
def project_config():
    """Fixture to provide project configuration"""
    class TestProjectConfig:
        def __init__(self):
            self.config = {
                "corpus_balancer": {
                    "balance_thresholds": {
                        "entropy_min": 2.0,
                        "gini_max": 0.7,
                        "ratio_max": 10.0,
                        "min_samples": 30
                    },
                    "quality_weights": {
                        "token_count": 0.3,
                        "quality_flag": 0.4,
                        "language_confidence": 0.2,
                        "corruption_score": 0.1
                    }
                },
                "domains": {
                    "high_frequency_trading": {
                        "min_documents": 100,
                        "target_weight": 0.4
                    },
                    "risk_management": {
                        "min_documents": 80,
                        "target_weight": 0.3
                    },
                    "portfolio_construction": {
                        "min_documents": 70,
                        "target_weight": 0.3
                    }
                }
            }
        
        def get(self, key, default=None):
            return self.config.get(key, default)
        
        def get_processor_config(self, processor_name):
            return self.config.get(processor_name, {})
        
        def get_input_dir(self):
            return Path("G:/data/test_corPUS_balancer/input")
        
        def get_logs_dir(self):
            return Path("G:/data/test_corPUS_balancer/logs")
    
    return TestProjectConfig()

@pytest.fixture
def corpus_balancer(project_config):
    """Fixture to provide configured CorpusBalancer instance"""
    from CorpusBuilderApp.shared_tools.processors.corpus_balancer import CorpusBalancer
    return CorpusBalancer(project_config)

def test_corpus_analysis(corpus_balancer, test_data_dir):
    """Test corpus analysis functionality"""
    # Create test corpus with known distribution
    corpus_dir = test_data_dir / "analysis_test"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    
    # Create domains with different document counts
    domains = {
        "high_frequency_trading": 50,  # Overrepresented
        "risk_management": 20,         # Underrepresented
        "portfolio_construction": 15    # Underrepresented
    }
    
    for domain, count in domains.items():
        domain_dir = corpus_dir / domain
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
    
    # Run analysis
    analysis = corpus_balancer.analyzer.analyze_corpus_balance()
    
    # Verify analysis results
    assert "domain_analysis" in analysis
    assert "imbalance_detection" in analysis
    assert "recommendations" in analysis
    
    # Check domain distribution
    domain_dist = analysis["domain_analysis"]["distribution"]
    assert domain_dist["high_frequency_trading"] == 50
    assert domain_dist["risk_management"] == 20
    assert domain_dist["portfolio_construction"] == 15
    
    # Verify imbalance detection
    imbalances = analysis["imbalance_detection"]
    assert any("high_frequency_trading" in issue for issue in imbalances.get("severe", []))
    assert any("risk_management" in issue for issue in imbalances.get("moderate", []))
    assert any("portfolio_construction" in issue for issue in imbalances.get("moderate", []))

def test_rebalancing_plan_creation(corpus_balancer, test_data_dir):
    """Test creation of rebalancing plan"""
    # Create imbalanced corpus
    corpus_dir = test_data_dir / "rebalance_test"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    
    # Create domains with imbalance
    domains = {
        "high_frequency_trading": 100,  # Overrepresented
        "risk_management": 30,          # Underrepresented
        "portfolio_construction": 20     # Underrepresented
    }
    
    for domain, count in domains.items():
        domain_dir = corpus_dir / domain
        domain_dir.mkdir(exist_ok=True)
        extracted_dir = domain_dir / "_extracted"
        extracted_dir.mkdir(exist_ok=True)
        
        for i in range(count):
            file_path = extracted_dir / f"doc_{i}.txt"
            file_path.write_text(f"Content for {domain} - {i}")
            
            meta_path = extracted_dir / f"doc_{i}.json"
            meta_path.write_text(json.dumps({
                "domain": domain,
                "quality_flag": "ok",
                "token_count": 100,
                "created_at": datetime.now().isoformat()
            }))
    
    # Run analysis
    analysis = corpus_balancer.analyzer.analyze_corpus_balance()
    
    # Create rebalancing plan
    plan = corpus_balancer.rebalancer.create_rebalancing_plan(analysis, strategy='quality_weighted')
    
    # Verify plan
    assert "actions" in plan
    assert "target_distribution" in plan
    
    # Check that plan includes actions for underrepresented domains
    actions = plan["actions"]
    assert any(action["domain"] == "risk_management" for action in actions)
    assert any(action["domain"] == "portfolio_construction" for action in actions)
    
    # Verify target distribution
    target_dist = plan["target_distribution"]
    assert abs(target_dist["high_frequency_trading"] - 0.4) < 0.1
    assert abs(target_dist["risk_management"] - 0.3) < 0.1
    assert abs(target_dist["portfolio_construction"] - 0.3) < 0.1

def test_rebalancing_execution(corpus_balancer, test_data_dir):
    """Test execution of rebalancing plan"""
    # Create test corpus
    corpus_dir = test_data_dir / "execution_test"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    
    # Create initial state
    domains = {
        "high_frequency_trading": 100,
        "risk_management": 30,
        "portfolio_construction": 20
    }
    
    for domain, count in domains.items():
        domain_dir = corpus_dir / domain
        domain_dir.mkdir(exist_ok=True)
        extracted_dir = domain_dir / "_extracted"
        extracted_dir.mkdir(exist_ok=True)
        
        for i in range(count):
            file_path = extracted_dir / f"doc_{i}.txt"
            file_path.write_text(f"Content for {domain} - {i}")
            
            meta_path = extracted_dir / f"doc_{i}.json"
            meta_path.write_text(json.dumps({
                "domain": domain,
                "quality_flag": "ok",
                "token_count": 100,
                "created_at": datetime.now().isoformat()
            }))
    
    # Run analysis and create plan
    analysis = corpus_balancer.analyzer.analyze_corpus_balance()
    plan = corpus_balancer.rebalancer.create_rebalancing_plan(analysis, strategy='quality_weighted')
    
    # Execute plan (dry run)
    results = corpus_balancer.rebalancer.execute_rebalancing_plan(plan, dry_run=True)
    
    # Verify execution results
    assert "actions_completed" in results
    assert "files_affected" in results
    assert "new_distribution" in results
    
    # Check that the plan would affect the correct number of files
    total_affected = sum(len(action.get("files_affected", [])) for action in results["actions_completed"])
    assert total_affected > 0

def test_collector_config_updates(corpus_balancer, test_data_dir):
    """Test updates to collector configurations based on imbalances"""
    # Create imbalanced corpus
    corpus_dir = test_data_dir / "collector_test"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    
    # Create domains with imbalance
    domains = {
        "high_frequency_trading": 100,
        "risk_management": 20,
        "portfolio_construction": 15
    }
    
    for domain, count in domains.items():
        domain_dir = corpus_dir / domain
        domain_dir.mkdir(exist_ok=True)
        extracted_dir = domain_dir / "_extracted"
        extracted_dir.mkdir(exist_ok=True)
        
        for i in range(count):
            file_path = extracted_dir / f"doc_{i}.txt"
            file_path.write_text(f"Content for {domain} - {i}")
            
            meta_path = extracted_dir / f"doc_{i}.json"
            meta_path.write_text(json.dumps({
                "domain": domain,
                "quality_flag": "ok",
                "token_count": 100,
                "created_at": datetime.now().isoformat()
            }))
    
    # Run analysis and rebalancing
    analysis = corpus_balancer.analyzer.analyze_corpus_balance()
    plan = corpus_balancer.rebalancer.create_rebalancing_plan(analysis, strategy='quality_weighted')
    results = corpus_balancer.rebalancer.execute_rebalancing_plan(plan, dry_run=True)
    
    # Verify that collector configurations would be updated
    assert "collector_updates" in results
    collector_updates = results["collector_updates"]
    
    # Check that underrepresented domains would get more search terms
    for domain in ["risk_management", "portfolio_construction"]:
        assert any(update["domain"] == domain for update in collector_updates)
        assert any(len(update["new_terms"]) > len(update["current_terms"]) 
                  for update in collector_updates if update["domain"] == domain) 