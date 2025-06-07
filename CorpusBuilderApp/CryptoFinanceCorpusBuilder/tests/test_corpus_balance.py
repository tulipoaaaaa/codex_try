# DEPRECATED: This file belongs to the legacy CryptoFinanceCorpusBuilder package and should not be used in new modules.
# tests/test_corpus_balancer.py
"""
Comprehensive tests for corpus balancer module.
"""

import unittest
import tempfile
import json
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np

from CryptoFinanceCorpusBuilder.processors.corpus_balancer import (
    CorpusAnalyzer, CorpusRebalancer, CorpusVisualizer, CorpusBalancerCLI
)
from shared_tools.config.balancer_config import BalancerConfig

class TestCorpusAnalyzer(unittest.TestCase):
    """Test cases for CorpusAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.corpus_dir = Path(self.temp_dir)
        
        # Create test directory structure
        (self.corpus_dir / '_extracted').mkdir()
        (self.corpus_dir / 'low_quality').mkdir()
        
        # Create sample metadata files
        self._create_test_metadata()
        
        self.analyzer = CorpusAnalyzer(self.corpus_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_metadata(self):
        """Create sample metadata files for testing."""
        # Domains from test_balancer_config.json
        all_domains = [
            'crypto_derivatives',
            'high_frequency_trading',
            'market_microstructure',
            'risk_management',
            'decentralized_finance',
            'portfolio_construction',
            'valuation_models',
            'regulation_compliance'
        ]
        # Sample metadata for _extracted directory
        extracted_metadata = []
        
        # First add the original varied test cases
        extracted_metadata.extend([
            {
                'domain': 'crypto_derivatives',
                'file_type': 'pdf',
                'token_count': 1500,
                'quality_flag': 'ok',
                'language': 'en',
                'language_confidence': 0.95,
                'file_size': 50000,
                'extraction_date': '2024-01-15T10:30:00',
                'quality_metrics': {
                    'corruption': {'corruption_score_normalized': 85},
                    'machine_translation': {'machine_translated_flag': False},
                    'academic_analysis': {'is_academic_paper': True}
                }
            },
            {
                'domain': 'high_frequency_trading',
                'file_type': 'pdf',
                'token_count': 2000,
                'quality_flag': 'ok',
                'language': 'en',
                'language_confidence': 0.92,
                'file_size': 75000,
                'extraction_date': '2024-01-16T14:20:00',
                'quality_metrics': {
                    'corruption': {'corruption_score_normalized': 90},
                    'machine_translation': {'machine_translated_flag': False},
                    'academic_analysis': {'is_academic_paper': False}
                }
            },
            {
                'domain': 'crypto_derivatives',
                'file_type': 'html',
                'token_count': 800,
                'quality_flag': 'flagged',
                'language': 'en',
                'language_confidence': 0.88,
                'file_size': 25000,
                'extraction_date': '2024-01-17T09:15:00',
                'quality_metrics': {
                    'corruption': {'corruption_score_normalized': 70},
                    'machine_translation': {'machine_translated_flag': True},
                    'academic_analysis': {'is_academic_paper': False}
                }
            }
        ])
        
        # Then add remaining domains with varied data
        remaining_domains = set(all_domains) - {'crypto_derivatives', 'high_frequency_trading'}
        for i, domain in enumerate(remaining_domains):
            extracted_metadata.append({
                'domain': domain,
                'file_type': 'pdf' if i % 2 == 0 else 'html',  # Alternate file types
                'token_count': 1000 + i * 100,
                'quality_flag': 'ok' if i % 3 == 0 else 'flagged',  # Vary quality flags
                'language': 'en',
                'language_confidence': 0.95 - i * 0.01,
                'file_size': 50000 + i * 1000,
                'extraction_date': f'2024-01-{15+i}T10:30:00',
                'quality_metrics': {
                    'corruption': {'corruption_score_normalized': 85 - i},
                    'machine_translation': {'machine_translated_flag': i % 2 == 0},
                    'academic_analysis': {'is_academic_paper': i % 2 == 0}
                }
            })
        
        # Low quality metadata
        low_quality_metadata = [
            {
                'domain': 'unknown',
                'file_type': 'pdf',
                'token_count': 50,
                'quality_flag': 'low_quality',
                'language': 'unknown',
                'language_confidence': 0.3,
                'file_size': 10000,
                'extraction_date': '2024-01-18T16:45:00',
                'quality_metrics': {
                    'corruption': {'corruption_score_normalized': 30},
                    'machine_translation': {'machine_translated_flag': False},
                    'academic_analysis': {'is_academic_paper': False}
                }
            }
        ]
        
        # Write metadata files
        for i, metadata in enumerate(extracted_metadata):
            with open(self.corpus_dir / '_extracted' / f'doc_{i}.json', 'w') as f:
                json.dump(metadata, f)
        for i, metadata in enumerate(low_quality_metadata):
            with open(self.corpus_dir / 'low_quality' / f'low_doc_{i}.json', 'w') as f:
                json.dump(metadata, f)
    
    def test_load_corpus_metadata(self):
        """Test loading corpus metadata from JSON files."""
        df = self.analyzer._load_corpus_metadata()
        
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 10)  # 9 extracted + 1 low quality
        
        # Check required columns exist
        required_columns = ['domain', 'file_type', 'token_count', 'quality_flag']
        for col in required_columns:
            self.assertIn(col, df.columns)
        
        # Check data types and values
        self.assertTrue(df['token_count'].dtype in [np.int64, np.float64, int, float])
        self.assertIn('crypto_derivatives', df['domain'].values)
        self.assertIn('pdf', df['file_type'].values)
    
    def test_analyze_domain_distribution(self):
        """Test domain distribution analysis."""
        df = self.analyzer._load_corpus_metadata()
        result = self.analyzer._analyze_domain_distribution(df)
        
        # Check structure
        self.assertIn('distribution', result)
        self.assertIn('entropy', result)
        self.assertIn('gini_coefficient', result)
        self.assertIn('missing_domains', result)
        
        # Check values
        self.assertIsInstance(result['entropy'], float)
        self.assertGreaterEqual(result['entropy'], 0)
        self.assertIsInstance(result['gini_coefficient'], float)
        self.assertGreaterEqual(result['gini_coefficient'], 0)
        self.assertLessEqual(result['gini_coefficient'], 1)
    
    def test_calculate_gini_coefficient(self):
        """Test Gini coefficient calculation."""
        # Perfect equality
        equal_values = np.array([10, 10, 10, 10])
        gini_equal = self.analyzer._calculate_gini_coefficient(equal_values)
        self.assertAlmostEqual(gini_equal, 0.0, places=2)
        
        # Maximum inequality
        unequal_values = np.array([100, 0, 0, 0])
        gini_unequal = self.analyzer._calculate_gini_coefficient(unequal_values)
        self.assertGreater(gini_unequal, 0.5)
        
        # Empty array
        empty_values = np.array([])
        gini_empty = self.analyzer._calculate_gini_coefficient(empty_values)
        self.assertEqual(gini_empty, 0.0)
    
    def test_detect_imbalances(self):
        """Test imbalance detection."""
        df = self.analyzer._load_corpus_metadata()
        imbalances = self.analyzer._detect_imbalances(df)
        
        # Check structure
        self.assertIn('critical', imbalances)
        self.assertIn('warning', imbalances)
        self.assertIn('info', imbalances)
        
        # All should be lists
        for severity in imbalances.values():
            self.assertIsInstance(severity, list)
    
    def test_analyze_corpus_balance(self):
        """Test full corpus balance analysis."""
        results = self.analyzer.analyze_corpus_balance()
        
        # Check structure
        required_sections = [
            'metadata', 'domain_analysis', 'file_type_analysis',
            'quality_analysis', 'balance_metrics', 'imbalance_detection',
            'recommendations'
        ]
        
        for section in required_sections:
            self.assertIn(section, results)
        
        # Check metadata
        self.assertIn('total_documents', results['metadata'])
        self.assertEqual(results['metadata']['total_documents'], 10)
    
    def test_cache_functionality(self):
        """Test analysis result caching."""
        # First analysis
        results1 = self.analyzer.analyze_corpus_balance()
        
        # Second analysis (should use cache)
        results2 = self.analyzer.analyze_corpus_balance()
        
        # Should be identical
        self.assertEqual(results1['metadata']['analysis_date'], 
                        results2['metadata']['analysis_date'])
        
        # Force refresh
        results3 = self.analyzer.analyze_corpus_balance(force_refresh=True)
        
        # Should have different timestamp
        self.assertNotEqual(results1['metadata']['analysis_date'], 
                           results3['metadata']['analysis_date'])

class TestCorpusRebalancer(unittest.TestCase):
    """Test cases for CorpusRebalancer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.corpus_dir = Path(self.temp_dir)
        
        # Create mock analyzer
        self.mock_analyzer = Mock(spec=CorpusAnalyzer)
        self.rebalancer = CorpusRebalancer(self.mock_analyzer)
        
        # Sample analysis results
        self.sample_analysis = {
            'metadata': {'total_documents': 100},
            'domain_analysis': {
                'distribution': {
                    'crypto_derivatives': 60,
                    'high_frequency_trading': 30,
                    'risk_management': 10
                },
                'entropy': 1.5,
                'gini_coefficient': 0.6
            },
            'quality_analysis': {
                'quality_flag_distribution': {
                    'ok': 70,
                    'flagged': 20,
                    'low_quality': 10
                }
            }
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_create_quality_weighted_plan(self):
        """Test quality-weighted rebalancing plan creation."""
        plan = {
            'strategy': 'quality_weighted',
            'actions': [],
            'created_date': '2024-01-01T00:00:00'
        }
        # Updated sample_analysis to include all domains and make 'risk_management' underrepresented
        sample_analysis = {
            'metadata': {'total_documents': 100},
            'domain_analysis': {
                'distribution': {
                    'crypto_derivatives': 60,
                    'high_frequency_trading': 30,
                    'risk_management': 5,
                    'market_microstructure': 2,
                    'decentralized_finance': 1,
                    'portfolio_construction': 1,
                    'valuation_models': 1,
                    'regulation_compliance': 0
                },
                'entropy': 1.5,
                'gini_coefficient': 0.6,
                'max_entropy': 2.5
            },
            'quality_analysis': {
                'quality_flag_distribution': {
                    'ok': 70,
                    'flagged': 20,
                    'low_quality': 10
                }
            }
        }
        result = self.rebalancer._create_quality_weighted_plan(plan, sample_analysis)
        self.assertEqual(result['strategy'], 'quality_weighted')
        self.assertIsInstance(result['actions'], list)
        # Should have actions for imbalanced domains
        action_domains = [action['domain'] for action in result['actions']]
        self.assertIn('risk_management', action_domains)  # Underrepresented
    
    def test_execute_rebalancing_plan_dry_run(self):
        """Test dry run execution of rebalancing plan."""
        plan = {
            'actions': [
                {
                    'type': 'upsample',
                    'domain': 'risk_management',
                    'current_count': 10,
                    'target_count': 25
                }
            ]
        }
        
        results = self.rebalancer.execute_rebalancing_plan(plan, dry_run=True)
        
        self.assertTrue(results['dry_run'])
        self.assertEqual(len(results['actions_completed']), 1)
        self.assertEqual(len(results['actions_failed']), 0)
        self.assertEqual(len(results['files_modified']), 0)
    
    def test_create_rebalancing_plan_strategies(self):
        """Test different rebalancing strategies."""
        strategies = ['quality_weighted', 'stratified', 'synthetic']
        
        for strategy in strategies:
            plan = self.rebalancer.create_rebalancing_plan(
                self.sample_analysis, strategy
            )
            
            self.assertEqual(plan['strategy'], strategy)
            self.assertIn('actions', plan)
            self.assertIn('implementation_steps', plan)

class TestCorpusVisualizer(unittest.TestCase):
    """Test cases for CorpusVisualizer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir)
        self.visualizer = CorpusVisualizer(self.output_dir)
        
        # Sample analysis results
        self.sample_analysis = {
            'metadata': {
                'total_documents': 100,
                'analysis_date': '2024-01-01T00:00:00'
            },
            'domain_analysis': {
                'distribution': {
                    'crypto_derivatives': 40,
                    'high_frequency_trading': 35,
                    'risk_management': 25
                },
                'entropy': 1.58,
                'gini_coefficient': 0.15,
                'missing_domains': []
            },
            'file_type_analysis': {
                'distribution': {
                    'pdf': 70,
                    'html': 20,
                    'markdown': 10
                }
            },
            'quality_analysis': {
                'quality_flag_distribution': {
                    'ok': 80,
                    'flagged': 15,
                    'low_quality': 5
                },
                'token_statistics': {
                    'mean': 1500,
                    'median': 1200,
                    'std': 800
                }
            },
            'imbalance_detection': {
                'critical': [],
                'warning': ['Some warning'],
                'info': ['Some info']
            },
            'recommendations': [
                {
                    'priority': 'high',
                    'category': 'domain_balance',
                    'description': 'Test recommendation',
                    'implementation': 'Test implementation'
                }
            ]
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    @patch('plotly.graph_objects.Figure.write_html')
    def test_create_balance_dashboard(self, mock_write_html):
        """Test dashboard creation."""
        dashboard_path = self.visualizer.create_balance_dashboard(self.sample_analysis)
        
        # Should return a path
        self.assertIsInstance(dashboard_path, str)
        self.assertTrue(dashboard_path.endswith('.html'))
        
        # Should call write_html
        mock_write_html.assert_called_once()
    
    def test_create_balance_report(self):
        """Test report generation."""
        # Add 'max_entropy' and 'balance_ratio' to sample_analysis['domain_analysis']
        self.sample_analysis['domain_analysis']['max_entropy'] = 2.5
        self.sample_analysis['domain_analysis']['balance_ratio'] = 0.6
        report_path = self.visualizer.create_balance_report(self.sample_analysis)
        # Should create a file
        self.assertTrue(Path(report_path).exists())
        self.assertTrue(report_path.endswith('.md'))
        # Check report content
        with open(report_path, 'r') as f:
            content = f.read()
        self.assertIn('# Corpus Balance Analysis Report', content)
        self.assertIn('**Total Documents:** 100', content)
        self.assertIn('crypto_derivatives', content)

class TestBalancerConfig(unittest.TestCase):
    """Test cases for BalancerConfig class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / 'test_config.json'
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_default_config_loading(self):
        """Test loading default configuration."""
        config = BalancerConfig()
        
        # Check required sections exist
        thresholds = config.get_balance_thresholds()
        self.assertIn('entropy_min', thresholds)
        self.assertIn('gini_max', thresholds)
        
        domain_config = config.get_domain_config()
        self.assertIn('crypto_derivatives', domain_config)
    
    def test_custom_config_loading(self):
        """Test loading custom configuration."""
        custom_config = {
            'balance_thresholds': {
                'entropy_min': 2.5,
                'custom_threshold': 0.8
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(custom_config, f)
        
        config = BalancerConfig(self.config_path)
        thresholds = config.get_balance_thresholds()
        
        # Should have custom value
        self.assertEqual(thresholds['entropy_min'], 2.5)
        # Should retain default values
        self.assertIn('gini_max', thresholds)
        # Should have custom addition
        self.assertEqual(thresholds['custom_threshold'], 0.8)
    
    def test_target_distribution_calculation(self):
        """Test target distribution calculation."""
        config = BalancerConfig()
        target_dist = config.get_target_distribution()
        
        # Should sum to approximately 1.0
        total_weight = sum(target_dist.values())
        self.assertAlmostEqual(total_weight, 1.0, places=2)
        
        # Should include all configured domains
        domain_config = config.get_domain_config()
        for domain in domain_config.keys():
            self.assertIn(domain, target_dist)
    
    def test_config_validation(self):
        """Test configuration validation."""
        config = BalancerConfig()
        issues = config.validate_config()
        
        # Default config should be valid
        self.assertEqual(len(issues), 0)
        
        # Test with invalid config
        config._config['balance_thresholds']['entropy_min'] = 5.0
        config._config['balance_thresholds']['entropy_target'] = 2.0
        
        issues = config.validate_config()
        self.assertGreater(len(issues), 0)
        self.assertTrue(any('entropy_min' in issue for issue in issues))

class TestCorpusBalancerCLI(unittest.TestCase):
    """Test cases for CorpusBalancerCLI class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.corpus_dir = Path(self.temp_dir)
        self.cli = CorpusBalancerCLI()
        
        # Create minimal corpus structure
        (self.corpus_dir / '_extracted').mkdir()
        (self.corpus_dir / 'low_quality').mkdir()
        
        # Create sample metadata file
        sample_metadata = {
            'domain': 'crypto_derivatives',
            'file_type': 'pdf',
            'token_count': 1000,
            'quality_flag': 'ok'
        }
        
        with open(self.corpus_dir / '_extracted' / 'test.json', 'w') as f:
            json.dump(sample_metadata, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    @patch('CryptoFinanceCorpusBuilder.processors.corpus_balancer.CorpusVisualizer')
    def test_analyze_command(self, mock_visualizer):
        """Test analyze command execution."""
        # Mock visualizer methods
        mock_visualizer_instance = Mock()
        mock_visualizer_instance.create_balance_report.return_value = 'test_report.md'
        mock_visualizer_instance.create_balance_dashboard.return_value = 'test_dashboard.html'
        mock_visualizer.return_value = mock_visualizer_instance
        
        result = self.cli.analyze_command(
            corpus_dir=str(self.corpus_dir),
            output_dir=str(self.temp_dir),
            generate_report=True,
            create_dashboard=True
        )
        
        self.assertEqual(result, 0)  # Success
        mock_visualizer_instance.create_balance_report.assert_called_once()
        mock_visualizer_instance.create_balance_dashboard.assert_called_once()
    
    def test_rebalance_command_dry_run(self):
        """Test rebalance command in dry run mode."""
        result = self.cli.rebalance_command(
            corpus_dir=str(self.corpus_dir),
            strategy='quality_weighted',
            dry_run=True,
            output_dir=str(self.temp_dir)
        )
        
        self.assertEqual(result, 0)  # Success

    def test_cli_integration(self):
        """Test CLI integration with realistic corpus."""
        cli = CorpusBalancerCLI()
        # Test analyze command
        result = cli.analyze_command(
            corpus_dir=str(self.corpus_dir),
            output_dir=str(Path(self.temp_dir) / 'reports'),
            generate_report=True,
            create_dashboard=False  # Skip dashboard to avoid plotly dependencies in tests
        )
        self.assertEqual(result, 0)
        # Check that report was generated
        report_files = list((Path(self.temp_dir) / 'reports').glob('*.md'))
        self.assertGreater(len(report_files), 0)
        # Test rebalance command
        result = cli.rebalance_command(
            corpus_dir=str(self.corpus_dir),
            strategy='quality_weighted',
            dry_run=True,
            output_dir=str(Path(self.temp_dir) / 'rebalance_reports')
        )
        self.assertEqual(result, 0)

class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for complete workflows."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.corpus_dir = Path(self.temp_dir)
        self._create_realistic_corpus()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def _create_realistic_corpus(self):
        """Create a realistic corpus for integration testing."""
        # Create directory structure
        (self.corpus_dir / '_extracted').mkdir()
        (self.corpus_dir / 'low_quality').mkdir()
        # Create diverse metadata representing real scenarios
        domains = ['crypto_derivatives', 'high_frequency_trading', 'risk_management']
        file_types = ['pdf', 'html', 'markdown']
        metadata_templates = []
        # Create imbalanced distribution (realistic scenario)
        for i in range(50):  # Crypto derivatives (overrepresented)
            metadata_templates.append({
                'domain': 'crypto_derivatives',
                'file_type': 'pdf',
                'token_count': int(np.random.randint(800, 3000)),
                'quality_flag': str(np.random.choice(['ok', 'flagged'], p=[0.8, 0.2])),
                'language': 'en',
                'language_confidence': float(np.random.uniform(0.8, 1.0)),
                'file_size': int(np.random.randint(20000, 100000)),
                'extraction_date': '2024-01-15T10:30:00',
                'quality_metrics': {
                    'corruption': {'corruption_score_normalized': int(np.random.randint(70, 100))},
                    'machine_translation': {'machine_translated_flag': bool(np.random.choice([True, False]))},
                    'academic_analysis': {'is_academic_paper': bool(np.random.choice([True, False]))}
                }
            })
        for i in range(20):  # HFT (moderate representation)
            metadata_templates.append({
                'domain': 'high_frequency_trading',
                'file_type': str(np.random.choice(['pdf', 'html'])),
                'token_count': int(np.random.randint(500, 2500)),
                'quality_flag': str(np.random.choice(['ok', 'flagged'], p=[0.7, 0.3])),
                'language': 'en',
                'language_confidence': float(np.random.uniform(0.75, 0.95)),
                'file_size': int(np.random.randint(15000, 80000)),
                'extraction_date': '2024-01-16T14:20:00',
                'quality_metrics': {
                    'corruption': {'corruption_score_normalized': int(np.random.randint(60, 95))},
                    'machine_translation': {'machine_translated_flag': bool(np.random.choice([True, False], p=[0.1, 0.9]))},
                    'academic_analysis': {'is_academic_paper': False}
                }
            })
        for i in range(5):  # Risk management (underrepresented)
            metadata_templates.append({
                'domain': 'risk_management',
                'file_type': 'pdf',
                'token_count': int(np.random.randint(1000, 4000)),
                'quality_flag': 'ok',
                'language': 'en',
                'language_confidence': float(np.random.uniform(0.85, 1.0)),
                'file_size': int(np.random.randint(30000, 120000)),
                'extraction_date': '2024-01-17T09:15:00',
                'quality_metrics': {
                    'corruption': {'corruption_score_normalized': int(np.random.randint(80, 100))},
                    'machine_translation': {'machine_translated_flag': False},
                    'academic_analysis': {'is_academic_paper': True}
                }
            })
        # Add some low quality documents
        for i in range(10):
            metadata_templates.append({
                'domain': 'unknown',
                'file_type': 'pdf',
                'token_count': int(np.random.randint(10, 200)),
                'quality_flag': 'low_quality',
                'language': 'unknown',
                'language_confidence': float(np.random.uniform(0.1, 0.5)),
                'file_size': int(np.random.randint(5000, 25000)),
                'extraction_date': '2024-01-18T16:45:00',
                'quality_metrics': {
                    'corruption': {'corruption_score_normalized': int(np.random.randint(10, 50))},
                    'machine_translation': {'machine_translated_flag': bool(np.random.choice([True, False]))},
                    'academic_analysis': {'is_academic_paper': False}
                }
            })
        # Write metadata files
        for i, metadata in enumerate(metadata_templates):
            directory = 'low_quality' if metadata['quality_flag'] == 'low_quality' else '_extracted'
            with open(self.corpus_dir / directory / f'doc_{i:03d}.json', 'w') as f:
                json.dump(metadata, f, indent=2)
    
    def test_complete_analysis_workflow(self):
        """Test complete analysis workflow with realistic data."""
        # Initialize analyzer
        analyzer = CorpusAnalyzer(self.corpus_dir)
        
        # Run analysis
        results = analyzer.analyze_corpus_balance()
        
        # Verify results structure
        self.assertNotIn('error', results)
        self.assertEqual(results['metadata']['total_documents'], 85)
        
        # Check domain imbalance detection
        domain_dist = results['domain_analysis']['distribution']
        self.assertEqual(domain_dist['crypto_derivatives'], 50)  # Overrepresented
        self.assertEqual(domain_dist['risk_management'], 5)     # Underrepresented
        
        # Should detect imbalances
        imbalances = results['imbalance_detection']
        total_issues = sum(len(issues) for issues in imbalances.values())
        self.assertGreater(total_issues, 0)
        
        # Should have recommendations
        self.assertGreater(len(results['recommendations']), 0)
    
    def test_complete_rebalancing_workflow(self):
        """Test complete rebalancing workflow."""
        # Initialize components
        analyzer = CorpusAnalyzer(self.corpus_dir)
        rebalancer = CorpusRebalancer(analyzer)
        # Analyze
        analysis_results = analyzer.analyze_corpus_balance()
        # Create rebalancing plan
        plan = rebalancer.create_rebalancing_plan(analysis_results, 'quality_weighted')
        # Verify plan structure
        self.assertEqual(plan['strategy'], 'quality_weighted')
        self.assertIsInstance(plan['actions'], list)
        # Should have actions for imbalanced domains
        action_types = [action['type'] for action in plan['actions']]
        action_domains = [action['domain'] for action in plan['actions']]
        # Check that at least one underrepresented domain is in the actions
        self.assertTrue(len(action_domains) > 0)
    
    def test_cli_integration(self):
        """Test CLI integration with realistic corpus."""
        cli = CorpusBalancerCLI()
        
        # Test analyze command
        result = cli.analyze_command(
            corpus_dir=str(self.corpus_dir),
            output_dir=str(Path(self.temp_dir) / 'reports'),
            generate_report=True,
            create_dashboard=False  # Skip dashboard to avoid plotly dependencies in tests
        )
        
        self.assertEqual(result, 0)
        
        # Check that report was generated
        report_files = list((Path(self.temp_dir) / 'reports').glob('*.md'))
        self.assertGreater(len(report_files), 0)
        
        # Test rebalance command
        result = cli.rebalance_command(
            corpus_dir=str(self.corpus_dir),
            strategy='quality_weighted',
            dry_run=True,
            output_dir=str(Path(self.temp_dir) / 'rebalance_reports')
        )
        
        self.assertEqual(result, 0)

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)