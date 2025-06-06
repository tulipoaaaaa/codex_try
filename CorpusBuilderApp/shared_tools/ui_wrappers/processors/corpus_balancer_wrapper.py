from PySide6.QtCore import Signal as pyqtSignal, QThread
from ..base_wrapper import BaseWrapper, ProcessorWrapperMixin
from shared_tools.processors.corpus_balancer import CorpusAnalyzer as CorpusBalancer
from typing import Dict, Any, List

class CorpusBalancerWorker(QThread):
    """Worker thread for Corpus Balancing"""
    progress = pyqtSignal(int, int, str)  # current, total, message
    error = pyqtSignal(str)
    finished = pyqtSignal(dict)
    domain_processed = pyqtSignal(str, int, int)  # domain, current, target
    
    def __init__(self, balancer, domains_to_balance, **kwargs):
        super().__init__()
        self.balancer = balancer
        self.domains = domains_to_balance
        self.kwargs = kwargs
        self._should_stop = False
        
    def run(self):
        """Run corpus balancing operations"""
        try:
            # First analyze corpus
            self.progress.emit(0, 100, "Analyzing corpus distribution...")
            corpus_stats = self.balancer.analyze_corpus()
            
            # Calculate balance operations
            self.progress.emit(25, 100, "Calculating balance operations...")
            balance_operations = self.balancer.calculate_balance_operations()
            
            # Execute balance operations
            total_domains = len(balance_operations)
            for i, (domain, operations) in enumerate(balance_operations.items()):
                if self._should_stop:
                    break
                
                self.progress.emit(25 + (i * 75 // total_domains), 100, 
                                   f"Balancing domain: {domain}")
                
                # Execute operations for this domain
                domain_stats = self.balancer.execute_domain_operations(domain, operations)
                
                # Emit domain-specific progress
                current = domain_stats.get('current_count', 0)
                target = domain_stats.get('target_count', 0)
                self.domain_processed.emit(domain, current, target)
            
            # Final analysis after balancing
            final_stats = self.balancer.analyze_corpus()
            
            # Prepare results
            results = {
                "initial_stats": corpus_stats,
                "balance_operations": balance_operations,
                "final_stats": final_stats
            }
            
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(str(e))
            
    def stop(self):
        """Stop processing"""
        self._should_stop = True

class CorpusBalancerWrapper(BaseWrapper, ProcessorWrapperMixin):
    """UI wrapper for Corpus Balancer"""
    
    domain_processed = pyqtSignal(str, int, int)  # domain, current, target
    balance_completed = pyqtSignal(dict)  # Balance results
    
    def __init__(self, config):
        super().__init__(config)
        self.balancer = None
        self.target_allocations = {}
        
    def _create_target_object(self):
        """Create Corpus Balancer instance"""
        if not self.balancer:
            self.balancer = CorpusBalancer(
                corpus_dir=self.config.corpus_dir,
                config=self.config
            )
        return self.balancer
        
    def _get_operation_type(self):
        return "balance_corpus"
        
    def set_target_allocations(self, allocations: Dict[str, float]):
        """Set target allocations for domains"""
        self.target_allocations = allocations
        
    def start_balancing(self, domains_to_balance=None):
        """Start corpus balancing"""
        if self._is_running:
            self.status_updated.emit("Balancing already in progress")
            return
            
        self._is_running = True
        self.status_updated.emit("Starting corpus balancing...")
        
        # Create balancer instance
        balancer = self._create_target_object()
        
        # Set target allocations if provided
        if self.target_allocations:
            balancer.set_target_allocations(self.target_allocations)
        
        # Create worker thread
        self.worker = CorpusBalancerWorker(
            balancer,
            domains_to_balance or list(balancer.get_domains())
        )
        
        # Connect signals
        self.worker.progress.connect(self._on_progress)
        self.worker.error.connect(self._on_error)
        self.worker.finished.connect(self._on_finished)
        self.worker.domain_processed.connect(self.domain_processed)
        
        # Start worker
        self.worker.start()
        
    def _on_finished(self, results: Dict[str, Any]):
        """Handle completion"""
        self._is_running = False
        self.completed.emit(results)
        self.balance_completed.emit(results)
        self.status_updated.emit("Corpus balancing completed successfully")
        
    def analyze_corpus(self):
        """Analyze corpus without balancing"""
        balancer = self._create_target_object()
        return balancer.analyze_corpus()
        
    def get_domain_stats(self):
        """Get statistics for each domain"""
        balancer = self._create_target_object()
        return balancer.get_domain_stats()

    def collect_for_missing_domains(self):
        """Analyze corpus and trigger collection for missing/underrepresented domains."""
        balancer = self._create_target_object()
        analysis = balancer.analyze_corpus()
        recommendations = analysis.get('recommendations', [])
        missing_domains = []
        for rec in recommendations:
            if rec.get('action') == 'collect_data' and 'missing domains' in rec.get('description', ''):
                # Extract domains from description string
                desc = rec['description']
                if ':' in desc:
                    domains_str = desc.split(':', 1)[1]
                    missing_domains = [d.strip() for d in domains_str.split(',')]
        if missing_domains:
            print("[CorpusBalancerWrapper] Would trigger collectors for: {}".format(missing_domains))
            # TODO: Actually trigger collectors here
        else:
            print("[CorpusBalancerWrapper] No missing domains found for collection.")
