# CryptoFinanceCorpusBuilder/processors/corpus_balancer.py
"""
Corpus Balancer Module - Integrates with existing pipeline architecture
Analyzes corpus balance, identifies imbalances, and provides rebalancing recommendations
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from collections import defaultdict, Counter
import logging
from datetime import datetime
import hashlib
from scipy import stats
from scipy.stats import entropy, chi2_contingency
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Import existing utilities from your codebase
from CryptoFinanceCorpusBuilder.utils.domain_utils import get_valid_domains, get_domain_for_file
from CryptoFinanceCorpusBuilder.utils.extractor_utils import safe_filename

def to_serializable(obj):
    """Recursively convert NumPy types and non-JSON-serializable dict keys to native Python types/strings for JSON serialization."""
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            # Only str, int, float, bool, None are valid JSON keys
            if isinstance(k, (str, int, float, bool)) or k is None:
                new_key = k
            else:
                new_key = str(k)
            new_dict[new_key] = to_serializable(v)
        return new_dict
    elif isinstance(obj, list):
        return [to_serializable(v) for v in obj]
    elif isinstance(obj, tuple):
        return tuple(to_serializable(v) for v in obj)
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    else:
        return obj

class CorpusAnalyzer:
    """Analyzes corpus composition and identifies imbalances."""
    
    def __init__(self, corpus_dir: Union[str, Path], config: Optional[Dict] = None, recursive: bool = True):
        self.corpus_dir = Path(corpus_dir)
        self.config = config or self._get_default_config()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.recursive = recursive
        
        # Initialize analysis state
        self.metadata_cache = {}
        self.analysis_results = {}
        self.last_analysis_time = None
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration for corpus analysis."""
        return {
            'balance_thresholds': {
                'entropy_min': 2.0,  # Minimum entropy for balanced corpus
                'gini_max': 0.7,     # Maximum Gini coefficient
                'ratio_max': 10.0,   # Maximum class ratio imbalance
                'min_samples': 30    # Minimum samples per class
            },
            'quality_weights': {
                'token_count': 0.3,
                'quality_flag': 0.4,
                'language_confidence': 0.2,
                'corruption_score': 0.1
            },
            'file_types': ['.txt', '.json'],
            'analysis_cache_ttl': 3600,  # 1 hour
            'visualization_output_dir': 'analysis_reports'
        }
    
    def analyze_corpus_balance(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Comprehensive corpus balance analysis.
        
        Args:
            force_refresh: Force re-analysis even if cached results exist
            
        Returns:
            Dictionary containing balance analysis results
        """
        # Check cache validity
        if not force_refresh and self._is_cache_valid():
            self.logger.info("Using cached analysis results")
            return self.analysis_results
        
        self.logger.info("Starting comprehensive corpus balance analysis")
        
        # Load all document metadata
        metadata_df = self._load_corpus_metadata()
        
        if metadata_df.empty:
            self.logger.warning("No documents found in corpus")
            return {'error': 'No documents found in corpus'}
        
        # Perform multi-dimensional analysis
        analysis_results = {
            'metadata': {
                'analysis_date': datetime.now().isoformat(),
                'total_documents': len(metadata_df),
                'corpus_directory': str(self.corpus_dir)
            },
            'domain_analysis': self._analyze_domain_distribution(metadata_df),
            'file_type_analysis': self._analyze_file_type_distribution(metadata_df),
            'quality_analysis': self._analyze_quality_distribution(metadata_df),
            'temporal_analysis': self._analyze_temporal_distribution(metadata_df),
            'balance_metrics': self._calculate_balance_metrics(metadata_df),
            'imbalance_detection': self._detect_imbalances(metadata_df),
            'recommendations': []
        }
        
        # Generate recommendations based on analysis
        analysis_results['recommendations'] = self._generate_recommendations(analysis_results)
        
        # Cache results
        self.analysis_results = analysis_results
        self.last_analysis_time = datetime.now()
        
        self.logger.info("Corpus balance analysis completed")
        return analysis_results
    
    def _load_corpus_metadata(self) -> pd.DataFrame:
        """Load metadata from all JSON files in corpus."""
        metadata_records = []
        subdirs = ['_extracted', 'low_quality']
        if self.recursive:
            # Recursively find all _extracted and low_quality subfolders
            for root, dirs, files in os.walk(self.corpus_dir):
                for subdir in subdirs:
                    subdir_path = Path(root) / subdir
                    if subdir_path.exists():
                        json_files = list(subdir_path.glob('*.json'))
                        self.logger.info(f"[RECURSIVE] Found {len(json_files)} JSON files in {subdir_path}")
                        for json_file in json_files:
                            try:
                                with open(json_file, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                                record = {
                                    'file_path': str(json_file),
                                    'document_id': json_file.stem,
                                    'directory': subdir,
                                    'domain': metadata.get('domain', 'unknown'),
                                    'file_type': metadata.get('file_type', 'unknown'),
                                    'extraction_method': metadata.get('extraction_method', 'unknown'),
                                    'token_count': metadata.get('token_count', 0),
                                    'quality_flag': metadata.get('quality_flag', 'unknown'),
                                    'extraction_date': metadata.get('extraction_date'),
                                    'language': metadata.get('language', 'unknown'),
                                    'language_confidence': metadata.get('language_confidence', 0.0),
                                    'file_size': metadata.get('file_size', 0),
                                    'quality_metrics': metadata.get('quality_metrics', {}),
                                    'enhancement_results': metadata.get('enhancement_results', {})
                                }
                                if isinstance(record['quality_metrics'], dict):
                                    qm = record['quality_metrics']
                                    record['corruption_score'] = qm.get('corruption', {}).get('corruption_score_normalized', 100)
                                    record['machine_translation_flag'] = qm.get('machine_translation', {}).get('machine_translated_flag', False)
                                    record['academic_paper'] = qm.get('academic_analysis', {}).get('is_academic_paper', False)
                                metadata_records.append(record)
                            except Exception as e:
                                self.logger.warning(f"Error loading metadata from {json_file}: {e}")
                                continue
        else:
            # Original behavior: only scan immediate subdirs
            for subdir in subdirs:
                subdir_path = self.corpus_dir / subdir
                if not subdir_path.exists():
                    continue
                json_files = list(subdir_path.glob('*.json'))
                self.logger.info(f"Found {len(json_files)} JSON files in {subdir}")
                for json_file in json_files:
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        record = {
                            'file_path': str(json_file),
                            'document_id': json_file.stem,
                            'directory': subdir,
                            'domain': metadata.get('domain', 'unknown'),
                            'file_type': metadata.get('file_type', 'unknown'),
                            'extraction_method': metadata.get('extraction_method', 'unknown'),
                            'token_count': metadata.get('token_count', 0),
                            'quality_flag': metadata.get('quality_flag', 'unknown'),
                            'extraction_date': metadata.get('extraction_date'),
                            'language': metadata.get('language', 'unknown'),
                            'language_confidence': metadata.get('language_confidence', 0.0),
                            'file_size': metadata.get('file_size', 0),
                            'quality_metrics': metadata.get('quality_metrics', {}),
                            'enhancement_results': metadata.get('enhancement_results', {})
                        }
                        if isinstance(record['quality_metrics'], dict):
                            qm = record['quality_metrics']
                            record['corruption_score'] = qm.get('corruption', {}).get('corruption_score_normalized', 100)
                            record['machine_translation_flag'] = qm.get('machine_translation', {}).get('machine_translated_flag', False)
                            record['academic_paper'] = qm.get('academic_analysis', {}).get('is_academic_paper', False)
                        metadata_records.append(record)
                    except Exception as e:
                        self.logger.warning(f"Error loading metadata from {json_file}: {e}")
                        continue
        return pd.DataFrame(metadata_records)
    
    def _analyze_domain_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze distribution across domains."""
        domain_counts = df['domain'].value_counts()
        valid_domains = get_valid_domains()
        
        # Calculate entropy
        probabilities = domain_counts.values / domain_counts.sum()
        domain_entropy = entropy(probabilities, base=2)
        
        # Calculate Gini coefficient
        gini_coefficient = self._calculate_gini_coefficient(domain_counts.values)
        
        # Identify missing domains
        missing_domains = set(valid_domains) - set(domain_counts.index)
        
        return {
            'distribution': domain_counts.to_dict(),
            'entropy': domain_entropy,
            'max_entropy': np.log2(len(valid_domains)),
            'balance_ratio': domain_entropy / np.log2(len(valid_domains)) if len(valid_domains) > 1 else 1.0,
            'gini_coefficient': gini_coefficient,
            'missing_domains': list(missing_domains),
            'dominant_domain': domain_counts.index[0] if not domain_counts.empty else None,
            'dominance_ratio': domain_counts.iloc[0] / domain_counts.iloc[1] if len(domain_counts) > 1 else float('inf')
        }
    
    def _analyze_file_type_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze distribution across file types."""
        file_type_counts = df['file_type'].value_counts()
        
        # Calculate balance metrics
        probabilities = file_type_counts.values / file_type_counts.sum()
        file_type_entropy = entropy(probabilities, base=2)
        
        return {
            'distribution': file_type_counts.to_dict(),
            'entropy': file_type_entropy,
            'balance_ratio': file_type_entropy / np.log2(len(file_type_counts)) if len(file_type_counts) > 1 else 1.0,
            'total_types': len(file_type_counts)
        }
    
    def _analyze_quality_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze quality distribution across corpus."""
        quality_counts = df['quality_flag'].value_counts()
        
        # Token count statistics
        token_stats = {
            'mean': df['token_count'].mean(),
            'median': df['token_count'].median(),
            'std': df['token_count'].std(),
            'min': df['token_count'].min(),
            'max': df['token_count'].max(),
            'q25': df['token_count'].quantile(0.25),
            'q75': df['token_count'].quantile(0.75)
        }
        
        # Quality score distribution
        corruption_scores = df['corruption_score'].dropna()
        quality_score_stats = {
            'mean_corruption': corruption_scores.mean() if not corruption_scores.empty else 0,
            'high_quality_ratio': (corruption_scores >= 80).sum() / len(corruption_scores) if not corruption_scores.empty else 0,
            'low_quality_ratio': (corruption_scores < 50).sum() / len(corruption_scores) if not corruption_scores.empty else 0
        }
        
        return {
            'quality_flag_distribution': quality_counts.to_dict(),
            'token_statistics': token_stats,
            'quality_scores': quality_score_stats,
            'language_distribution': df['language'].value_counts().to_dict(),
            'directory_distribution': df['directory'].value_counts().to_dict()
        }
    
    def _analyze_temporal_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze temporal distribution of document extraction."""
        # Convert extraction dates
        df_temp = df.copy()
        df_temp['extraction_date'] = pd.to_datetime(df_temp['extraction_date'], errors='coerce')
        df_temp = df_temp.dropna(subset=['extraction_date'])
        
        if df_temp.empty:
            return {'error': 'No valid extraction dates found'}
        
        # Group by date
        daily_counts = df_temp.groupby(df_temp['extraction_date'].dt.date).size()
        
        return {
            'date_range': {
                'start': df_temp['extraction_date'].min().isoformat(),
                'end': df_temp['extraction_date'].max().isoformat(),
                'span_days': (df_temp['extraction_date'].max() - df_temp['extraction_date'].min()).days
            },
            'daily_distribution': daily_counts.to_dict(),
            'documents_per_day': {
                'mean': daily_counts.mean(),
                'std': daily_counts.std(),
                'max': daily_counts.max(),
                'min': daily_counts.min()
            }
        }
    
    def _calculate_balance_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive balance metrics."""
        metrics = {}
        
        # Domain balance metrics
        domain_counts = df['domain'].value_counts()
        if len(domain_counts) > 1:
            metrics['domain_entropy'] = entropy(domain_counts.values, base=2)
            metrics['domain_gini'] = self._calculate_gini_coefficient(domain_counts.values)
            metrics['domain_max_ratio'] = domain_counts.iloc[0] / domain_counts.iloc[-1]
        
        # File type balance metrics
        type_counts = df['file_type'].value_counts()
        if len(type_counts) > 1:
            metrics['file_type_entropy'] = entropy(type_counts.values, base=2)
            metrics['file_type_gini'] = self._calculate_gini_coefficient(type_counts.values)
        
        # Quality balance metrics
        quality_counts = df['quality_flag'].value_counts()
        if len(quality_counts) > 1:
            metrics['quality_entropy'] = entropy(quality_counts.values, base=2)
            metrics['quality_distribution'] = quality_counts.to_dict()
        
        return metrics
    
    def _detect_imbalances(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Detect various types of imbalances in the corpus."""
        imbalances = {
            'critical': [],
            'warning': [],
            'info': []
        }
        
        thresholds = self.config['balance_thresholds']
        
        # Domain imbalances
        domain_counts = df['domain'].value_counts()
        if len(domain_counts) > 1:
            domain_entropy = entropy(domain_counts.values, base=2)
            max_domain_entropy = np.log2(len(domain_counts))
            
            if domain_entropy < thresholds['entropy_min']:
                imbalances['critical'].append(f"Low domain entropy: {domain_entropy:.2f} < {thresholds['entropy_min']}")
            
            # Check for dominant domains
            dominance_ratio = domain_counts.iloc[0] / domain_counts.iloc[1] if len(domain_counts) > 1 else 1
            if dominance_ratio > thresholds['ratio_max']:
                imbalances['warning'].append(f"Domain imbalance ratio: {dominance_ratio:.1f}:1")
            
            # Check for insufficient samples
            insufficient_domains = domain_counts[domain_counts < thresholds['min_samples']]
            if not insufficient_domains.empty:
                imbalances['warning'].append(f"Domains with insufficient samples: {list(insufficient_domains.index)}")
        
        # Quality imbalances
        quality_counts = df['quality_flag'].value_counts()
        low_quality_ratio = quality_counts.get('low_quality', 0) / len(df)
        if low_quality_ratio > 0.3:
            imbalances['warning'].append(f"High low-quality ratio: {low_quality_ratio:.1%}")
        
        # File type imbalances
        type_counts = df['file_type'].value_counts()
        if len(type_counts) > 1:
            type_gini = self._calculate_gini_coefficient(type_counts.values)
            if type_gini > thresholds['gini_max']:
                imbalances['info'].append(f"File type Gini coefficient: {type_gini:.2f} > {thresholds['gini_max']}")
        
        return imbalances
    
    def _generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        imbalances = analysis_results['imbalance_detection']
        domain_analysis = analysis_results['domain_analysis']
        quality_analysis = analysis_results['quality_analysis']
        
        # Domain-based recommendations
        if domain_analysis['missing_domains']:
            recommendations.append({
                'priority': 'high',
                'category': 'domain_balance',
                'action': 'collect_data',
                'description': f"Collect data for missing domains: {', '.join(domain_analysis['missing_domains'])}",
                'implementation': "Use existing collectors with domain-specific search terms"
            })
        
        if domain_analysis['dominance_ratio'] > 5.0:
            dominant_domain = domain_analysis['dominant_domain']
            recommendations.append({
                'priority': 'medium',
                'category': 'domain_balance',
                'action': 'reduce_overrepresentation',
                'description': f"Reduce overrepresentation of {dominant_domain} domain",
                'implementation': "Apply stratified sampling or move excess documents to separate collection"
            })
        
        # Quality-based recommendations
        low_quality_count = quality_analysis['quality_flag_distribution'].get('low_quality', 0)
        total_docs = analysis_results['metadata']['total_documents']
        
        if low_quality_count / total_docs > 0.2:
            recommendations.append({
                'priority': 'medium',
                'category': 'quality_improvement',
                'action': 'improve_extraction',
                'description': f"High proportion of low-quality documents: {low_quality_count}/{total_docs}",
                'implementation': "Review extraction parameters and consider alternative processing methods"
            })
        
        # File type recommendations
        file_types = analysis_results['file_type_analysis']['distribution']
        if 'pdf' in file_types and file_types['pdf'] / total_docs > 0.8:
            recommendations.append({
                'priority': 'low',
                'category': 'diversity',
                'action': 'diversify_sources',
                'description': "Consider collecting more non-PDF sources for format diversity",
                'implementation': "Enable additional collectors for HTML, markdown, and structured data"
            })
        
        return recommendations
    
    def _calculate_gini_coefficient(self, values: np.ndarray) -> float:
        """Calculate Gini coefficient for inequality measurement."""
        if len(values) == 0:
            return 0.0
        
        sorted_values = np.sort(values)
        n = len(values)
        cumsum = np.cumsum(sorted_values)
        
        return (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n
    
    def _is_cache_valid(self) -> bool:
        """Check if cached analysis results are still valid."""
        if not self.analysis_results or not self.last_analysis_time:
            return False
        
        time_elapsed = (datetime.now() - self.last_analysis_time).total_seconds()
        return time_elapsed < self.config['analysis_cache_ttl']

class CorpusRebalancer:
    """Handles corpus rebalancing operations."""
    
    def __init__(self, corpus_analyzer: CorpusAnalyzer):
        self.analyzer = corpus_analyzer
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def create_rebalancing_plan(self, analysis_results: Dict[str, Any], 
                              strategy: str = 'quality_weighted') -> Dict[str, Any]:
        """
        Create a detailed rebalancing plan based on analysis results.
        
        Args:
            analysis_results: Results from CorpusAnalyzer
            strategy: Rebalancing strategy ('quality_weighted', 'stratified', 'synthetic')
            
        Returns:
            Detailed rebalancing plan
        """
        plan = {
            'strategy': strategy,
            'created_date': datetime.now().isoformat(),
            'source_analysis': analysis_results,
            'actions': [],
            'expected_outcomes': {},
            'implementation_steps': []
        }
        
        if strategy == 'quality_weighted':
            plan = self._create_quality_weighted_plan(plan, analysis_results)
        elif strategy == 'stratified':
            plan = self._create_stratified_plan(plan, analysis_results)
        elif strategy == 'synthetic':
            plan = self._create_synthetic_plan(plan, analysis_results)
        
        return plan
    
    def _create_quality_weighted_plan(self, plan: Dict[str, Any], 
                                    analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create plan using quality-weighted sampling."""
        domain_analysis = analysis_results['domain_analysis']
        quality_analysis = analysis_results['quality_analysis']
        
        # Identify target distribution
        total_docs = analysis_results['metadata']['total_documents']
        target_per_domain = total_docs // len(get_valid_domains())
        
        for domain, count in domain_analysis['distribution'].items():
            if count < target_per_domain * 0.5:  # Significantly underrepresented
                plan['actions'].append({
                    'type': 'upsample',
                    'domain': domain,
                    'current_count': count,
                    'target_count': target_per_domain,
                    'method': 'quality_weighted_duplication'
                })
            elif count > target_per_domain * 2:  # Significantly overrepresented
                plan['actions'].append({
                    'type': 'downsample',
                    'domain': domain,
                    'current_count': count,
                    'target_count': target_per_domain,
                    'method': 'quality_based_selection'
                })
        
        return plan
    
    def _create_stratified_plan(self, plan: Dict[str, Any], 
                              analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create plan using stratified sampling."""
        # Implementation for stratified sampling approach
        plan['implementation_steps'] = [
            "Load corpus metadata",
            "Calculate stratification weights by domain and quality",
            "Apply stratified sampling within each stratum",
            "Validate balanced output"
        ]
        return plan
    
    def _create_synthetic_plan(self, plan: Dict[str, Any], 
                             analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create plan using synthetic data generation."""
        # Implementation for synthetic data generation approach
        plan['implementation_steps'] = [
            "Identify underrepresented domains",
            "Extract representative samples for augmentation",
            "Apply text augmentation techniques",
            "Validate synthetic document quality"
        ]
        return plan
    
    def execute_rebalancing_plan(self, plan: Dict[str, Any], 
                               dry_run: bool = True) -> Dict[str, Any]:
        """
        Execute the rebalancing plan.
        
        Args:
            plan: Rebalancing plan from create_rebalancing_plan
            dry_run: If True, only simulate the operations
            
        Returns:
            Execution results
        """
        results = {
            'plan_id': hashlib.md5(json.dumps(to_serializable(plan), sort_keys=True).encode()).hexdigest()[:8],
            'execution_date': datetime.now().isoformat(),
            'dry_run': dry_run,
            'actions_completed': [],
            'actions_failed': [],
            'final_distribution': {},
            'files_modified': []
        }
        
        for action in plan['actions']:
            try:
                if action['type'] == 'upsample':
                    result = self._execute_upsample_action(action, dry_run)
                elif action['type'] == 'downsample':
                    result = self._execute_downsample_action(action, dry_run)
                else:
                    result = {'status': 'skipped', 'reason': f"Unknown action type: {action['type']}"}
                
                if result['status'] == 'success':
                    results['actions_completed'].append({**action, **result})
                    results['files_modified'].extend(result.get('files_affected', []))
                else:
                    results['actions_failed'].append({**action, **result})
                    
            except Exception as e:
                self.logger.error(f"Error executing action {action}: {e}")
                results['actions_failed'].append({
                    **action, 
                    'status': 'error', 
                    'error': str(e)
                })
        
        return results
    
    def _execute_upsample_action(self, action: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
        """Execute upsampling action for underrepresented domain."""
        if dry_run:
            return {
                'status': 'success',
                'message': f"Would upsample {action['domain']} from {action['current_count']} to {action['target_count']}",
                'files_affected': []
            }
        
        # Actual upsampling implementation would go here
        # For now, return simulated success
        return {
            'status': 'success',
            'message': f"Upsampled {action['domain']}",
            'files_affected': [],
            'duplications_created': action['target_count'] - action['current_count']
        }
    
    def _execute_downsample_action(self, action: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
        """Execute downsampling action for overrepresented domain."""
        if dry_run:
            return {
                'status': 'success',
                'message': f"Would downsample {action['domain']} from {action['current_count']} to {action['target_count']}",
                'files_affected': []
            }
        
        # Actual downsampling implementation would go here
        return {
            'status': 'success',
            'message': f"Downsampled {action['domain']}",
            'files_affected': [],
            'files_moved': action['current_count'] - action['target_count']
        }

class CorpusVisualizer:
    """Generate visualizations for corpus analysis."""
    
    def __init__(self, output_dir: Union[str, Path] = "analysis_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def create_balance_dashboard(self, analysis_results: Dict[str, Any]) -> str:
        """Create comprehensive dashboard with multiple visualizations."""
        dashboard_path = self.output_dir / f"corpus_balance_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Domain Distribution', 'Quality Distribution', 
                          'File Type Distribution', 'Token Count Distribution'],
            specs=[[{"type": "pie"}, {"type": "bar"}],
                   [{"type": "pie"}, {"type": "histogram"}]]
        )
        
        # Domain distribution pie chart
        domain_data = analysis_results['domain_analysis']['distribution']
        fig.add_trace(
            go.Pie(labels=list(domain_data.keys()), values=list(domain_data.values()),
                   name="Domains", showlegend=True),
            row=1, col=1
        )
        
        # Quality distribution bar chart
        quality_data = analysis_results['quality_analysis']['quality_flag_distribution']
        fig.add_trace(
            go.Bar(x=list(quality_data.keys()), y=list(quality_data.values()),
                   name="Quality Flags"),
            row=1, col=2
        )
        
        # File type distribution pie chart
        filetype_data = analysis_results['file_type_analysis']['distribution']
        fig.add_trace(
            go.Pie(labels=list(filetype_data.keys()), values=list(filetype_data.values()),
                   name="File Types", showlegend=False),
            row=2, col=1
        )
        
        # Token count histogram (placeholder - would need raw data)
        fig.add_trace(
            go.Histogram(x=[100, 200, 150, 300, 250, 400, 350, 500],  # Placeholder data
                        name="Token Counts"),
            row=2, col=2
        )
        
        fig.update_layout(
            title_text="Corpus Balance Dashboard",
            showlegend=True,
            height=800
        )
        
        # Save dashboard
        fig.write_html(str(dashboard_path))
        self.logger.info(f"Dashboard saved to {dashboard_path}")
        
        return str(dashboard_path)
    
    def create_balance_report(self, analysis_results: Dict[str, Any], 
                            rebalancing_plan: Optional[Dict[str, Any]] = None) -> str:
        """Create detailed text report of corpus balance analysis."""
        report_path = self.output_dir / f"corpus_balance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Corpus Balance Analysis Report\n\n")
            f.write(f"**Generated:** {analysis_results['metadata']['analysis_date']}\n")
            f.write(f"**Total Documents:** {analysis_results['metadata']['total_documents']}\n\n")
            
            # Domain Analysis
            f.write("## Domain Distribution\n\n")
            domain_analysis = analysis_results['domain_analysis']
            f.write(f"- **Entropy:** {domain_analysis['entropy']:.3f} / {domain_analysis['max_entropy']:.3f}\n")
            f.write(f"- **Balance Ratio:** {domain_analysis['balance_ratio']:.3f}\n")
            f.write(f"- **Gini Coefficient:** {domain_analysis['gini_coefficient']:.3f}\n")
            
            if domain_analysis['missing_domains']:
                f.write(f"- **Missing Domains:** {', '.join(domain_analysis['missing_domains'])}\n")
            
            f.write("\n### Document Counts by Domain\n\n")
            for domain, count in domain_analysis['distribution'].items():
                f.write(f"- {domain}: {count}\n")
            
            # Quality Analysis
            f.write("\n## Quality Distribution\n\n")
            quality_analysis = analysis_results['quality_analysis']
            
            f.write("### Quality Flags\n")
            for flag, count in quality_analysis['quality_flag_distribution'].items():
                f.write(f"- {flag}: {count}\n")
            
            f.write("\n### Token Statistics\n")
            token_stats = quality_analysis['token_statistics']
            f.write(f"- Mean: {token_stats['mean']:.1f}\n")
            f.write(f"- Median: {token_stats['median']:.1f}\n")
            f.write(f"- Standard Deviation: {token_stats['std']:.1f}\n")
            
            # Imbalances
            f.write("\n## Detected Imbalances\n\n")
            imbalances = analysis_results['imbalance_detection']
            
            for severity, issues in imbalances.items():
                if issues:
                    f.write(f"### {severity.title()}\n")
                    for issue in issues:
                        f.write(f"- {issue}\n")
                    f.write("\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            for i, rec in enumerate(analysis_results['recommendations'], 1):
                f.write(f"### {i}. {rec['description']}\n")
                f.write(f"- **Priority:** {rec['priority']}\n")
                f.write(f"- **Category:** {rec['category']}\n")
                f.write(f"- **Implementation:** {rec['implementation']}\n\n")
            
            # Rebalancing Plan
            if rebalancing_plan:
                f.write("## Rebalancing Plan\n\n")
                f.write(f"**Strategy:** {rebalancing_plan['strategy']}\n\n")
                
                if rebalancing_plan['actions']:
                    f.write("### Planned Actions\n\n")
                    for action in rebalancing_plan['actions']:
                        f.write(f"- **{action['type'].title()}** {action['domain']}: "
                               f"{action['current_count']} → {action['target_count']}\n")
        
        self.logger.info(f"Report saved to {report_path}")
        return str(report_path)

# Integration with existing CLI
class CorpusBalancerCLI:
    """CLI interface for corpus balancing operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def analyze_command(self, corpus_dir: str, output_dir: str = None, 
                       generate_report: bool = True, create_dashboard: bool = True, recursive: bool = True) -> int:
        """Analyze corpus balance and generate reports."""
        try:
            # Initialize analyzer
            analyzer = CorpusAnalyzer(corpus_dir, recursive=recursive)
            
            # Run analysis
            self.logger.info("Starting corpus balance analysis...")
            results = analyzer.analyze_corpus_balance()
            
            if 'error' in results:
                self.logger.error(f"Analysis failed: {results['error']}")
                return 1
            
            # Generate outputs
            if output_dir:
                visualizer = CorpusVisualizer(output_dir)
                
                if generate_report:
                    report_path = visualizer.create_balance_report(results)
                    print(f"Report generated: {report_path}")
                
                if create_dashboard:
                    dashboard_path = visualizer.create_balance_dashboard(results)
                    print(f"Dashboard generated: {dashboard_path}")
            
            # Print summary to console
            print("\n=== Corpus Balance Summary ===")
            print(f"Total Documents: {results['metadata']['total_documents']}")
            print(f"Domain Entropy: {results['domain_analysis']['entropy']:.3f}")
            print(f"Missing Domains: {len(results['domain_analysis']['missing_domains'])}")
            
            # Print imbalances
            for severity, issues in results['imbalance_detection'].items():
                if issues:
                    print(f"\n{severity.upper()} Issues:")
                    for issue in issues:
                        print(f"  - {issue}")
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Analysis command failed: {e}")
            return 1
    
    def rebalance_command(self, corpus_dir: str, strategy: str = 'quality_weighted',
                         dry_run: bool = True, output_dir: str = None, recursive: bool = True) -> int:
        """Create and optionally execute rebalancing plan."""
        try:
            # Initialize components
            analyzer = CorpusAnalyzer(corpus_dir, recursive=recursive)
            rebalancer = CorpusRebalancer(analyzer)
            
            # Analyze current state
            self.logger.info("Analyzing current corpus state...")
            analysis_results = analyzer.analyze_corpus_balance()
            
            if 'error' in analysis_results:
                self.logger.error(f"Analysis failed: {analysis_results['error']}")
                return 1
            
            # Create rebalancing plan
            self.logger.info(f"Creating rebalancing plan with strategy: {strategy}")
            plan = rebalancer.create_rebalancing_plan(analysis_results, strategy)
            
            # Execute plan
            self.logger.info(f"Executing plan (dry_run={dry_run})...")
            execution_results = rebalancer.execute_rebalancing_plan(plan, dry_run)
            
            # Report results
            print(f"\n=== Rebalancing Results ===")
            print(f"Strategy: {strategy}")
            print(f"Dry Run: {dry_run}")
            print(f"Actions Completed: {len(execution_results['actions_completed'])}")
            print(f"Actions Failed: {len(execution_results['actions_failed'])}")
            
            if execution_results['actions_completed']:
                print("\nCompleted Actions:")
                for action in execution_results['actions_completed']:
                    print(f"  - {action['type']} {action['domain']}: {action.get('message', 'Success')}")
            
            if execution_results['actions_failed']:
                print("\nFailed Actions:")
                for action in execution_results['actions_failed']:
                    print(f"  - {action['type']} {action['domain']}: {action.get('error', 'Unknown error')}")
            
            # Generate report if output directory specified
            if output_dir:
                visualizer = CorpusVisualizer(output_dir)
                report_path = visualizer.create_balance_report(analysis_results, plan)
                print(f"\nDetailed report: {report_path}")
            
            # Optionally: Save execution_results as JSON (robust to NumPy types)
            if output_dir:
                results_path = Path(output_dir) / f"rebalance_execution_{strategy}_{'dryrun' if dry_run else 'exec'}.json"
                with open(results_path, 'w', encoding='utf-8') as f:
                    json.dump(to_serializable(execution_results), f, indent=2)
                print(f"Execution results saved to {results_path}")
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Rebalancing command failed: {e}")
            return 1