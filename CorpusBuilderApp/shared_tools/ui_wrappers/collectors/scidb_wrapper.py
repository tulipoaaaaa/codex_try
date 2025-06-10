from PySide6.QtCore import Signal as pyqtSignal
from ..base_wrapper import BaseWrapper, CollectorWrapperMixin
from shared_tools.collectors.enhanced_scidb_collector import SciDBCollector

class SciDBWrapper(BaseWrapper, CollectorWrapperMixin):
    """UI wrapper for SciDB Collector"""
    
    papers_found = pyqtSignal(int)  # Number of papers found
    
    def __init__(self, config):
        super().__init__(config)
        self.project_config = config
        self.name = "scidb"
        self.collector = None
        
    def _create_target_object(self):
        """Create SciDB collector instance"""
        if not self.collector:
            self.collector = SciDBCollector(self.config)
        return self.collector
        
    def _get_operation_type(self):
        return "collect"

    def refresh_config(self):
        """Reload collector options from configuration."""
        cfg = self.config.get(f"collectors.{self.name}", {}) or {}
        for key, value in cfg.items():
            method = f"set_{key}"
            if hasattr(self, method):
                try:
                    getattr(self, method)(value)
                except Exception:
                    continue

