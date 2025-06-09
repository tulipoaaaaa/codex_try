from PySide6.QtCore import Signal as pyqtSignal
from ..base_wrapper import BaseWrapper, CollectorWrapperMixin
from shared_tools.collectors.arxiv_collector import ArxivCollector

class ArxivWrapper(BaseWrapper, CollectorWrapperMixin):
    """UI wrapper for arXiv Collector"""
    
    papers_found = pyqtSignal(int)  # Number of papers found
    
    def __init__(self, config):
        super().__init__(config)
        self.project_config = config
        self.name = "arxiv"
        self.collector = None
        self.search_terms = []
        self.max_papers = 50
        
    def _create_target_object(self):
        """Create arXiv collector instance"""
        if not self.collector:
            self.collector = ArxivCollector(self.config)
        return self.collector
        
    def _get_operation_type(self):
        return "collect"
        
    def set_search_terms(self, terms):
        """Set search terms for paper collection"""
        self.search_terms = terms
        
    def set_max_papers(self, max_papers):
        """Set maximum number of papers to collect"""
        self.max_papers = max_papers
        
    def start(self, **kwargs):
        """Override start to pass arXiv-specific parameters"""
        kwargs.update({
            'search_terms': self.search_terms,
            'max_papers': self.max_papers
        })
        super().start(**kwargs)

    def refresh_config(self):
        """Reload parameters from ``self.config`` such as search terms and limits."""
        cfg = self.config.get(f"collectors.{self.name}", {}) or {}
        for key, value in cfg.items():
            method = f"set_{key}"
            if hasattr(self, method):
                try:
                    getattr(self, method)(value)
                except Exception:
                    continue

        if self.collector:
            email = self.config.get("api_keys.arxiv_email")
            if email:
                setattr(self.collector, "email", email)

