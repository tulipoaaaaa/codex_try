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
    
    def __init__(self, config, test_mode: bool = False):
        super().__init__(config, test_mode=test_mode)
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
        if not missing_domains:
            self.status_updated.emit("No missing domains found for collection.")
            return

        started: list[str] = []
        wrappers: dict[str, Any] = getattr(self, "collector_wrappers", {})

        for name, wrapper in wrappers.items():
            try:
                if hasattr(wrapper, "set_search_terms"):
                    existing = getattr(wrapper, "search_terms", []) or []
                    for dom in missing_domains:
                        if dom not in existing:
                            existing.append(dom)
                    wrapper.set_search_terms(existing)
                wrapper.start()
                started.append(name)
            except Exception:
                continue

        if started:
            self.status_updated.emit("Triggered collectors: " + ", ".join(started))
        else:
            self.status_updated.emit("No collectors available to trigger")

    def balance_corpus(self):
        """Analyze domain imbalance and update collector configurations."""

        # Placeholder target counts per domain
        domain_targets = {"ai": 300, "finance": 200, "eth": 250}

        # Attempt to get current domain distribution from an attached corpus manager
        current_counts = {}
        if hasattr(self, "_corpus_manager") and hasattr(self._corpus_manager, "get_domain_distribution"):
            try:
                current_counts = self._corpus_manager.get_domain_distribution()
            except Exception:
                current_counts = {}

        # Fallback placeholder distribution if none available
        if not current_counts:
            current_counts = {key: 0 for key in domain_targets}

        # Iterate through collectors and adjust search terms for underrepresented domains
        collectors_cfg = self.config.get("collectors", {}) or {}
        for domain, target in domain_targets.items():
            current = current_counts.get(domain, 0)
            if current < target:
                for name, cfg in collectors_cfg.items():
                    terms: List[str] = cfg.get("search_terms", []) or []
                    if domain not in terms:
                        terms.append(domain)
                        self.config.set(f"collectors.{name}.search_terms", terms)

        # Persist configuration changes
        self.config.save()

        # Notify the UI about updates
        self.status_updated.emit("Updated collector configs based on imbalance analysis")

    def refresh_config(self):
        """Reload parameters from ``self.config``."""
        cfg = {}
        if hasattr(self.config, 'get_processor_config'):
            cfg = self.config.get_processor_config('corpus_balancer') or {}
        for k, v in cfg.items():
            method = f'set_{k}'
            if hasattr(self, method):
                try:
                    getattr(self, method)(v)
                    continue
                except Exception:
                    self.logger.debug('Failed to apply %s via wrapper', k)
            if hasattr(self.processor, method):
                try:
                    getattr(self.processor, method)(v)
                    continue
                except Exception:
                    self.logger.debug('Failed to apply %s via processor', k)
            if hasattr(self.processor, k):
                setattr(self.processor, k, v)
            elif hasattr(self, k):
                setattr(self, k, v)
        if cfg and hasattr(self, 'configuration_changed'):
            self.configuration_changed.emit(cfg)
