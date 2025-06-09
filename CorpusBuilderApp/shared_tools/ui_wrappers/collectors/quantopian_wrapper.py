from PySide6.QtCore import Signal as pyqtSignal
from ..base_wrapper import BaseWrapper, CollectorWrapperMixin
from shared_tools.collectors.quantopian_collector import QuantopianCollector

class QuantopianWrapper(BaseWrapper, CollectorWrapperMixin):
    """UI wrapper for Quantopian Collector"""
    
    notebooks_found = pyqtSignal(int)  # Number of notebooks found
    
    def __init__(self, config):
        super().__init__(config)
        self.project_config = config
        self.name = "quantopian"
        self.collector = None
        
    def _create_target_object(self):
        """Create Quantopian collector instance"""
        if not self.collector:
            self.collector = QuantopianCollector(self.config)
        return self.collector
        
    def _get_operation_type(self):
        return "collect"

    def refresh_config(self):
        """Re-apply configuration values from :class:`ProjectConfig`. Safe to call at any time."""
        config = self.project_config.get(f"collectors.{self.name}", {})
        for key, value in config.items():
            method = f"set_{key}"
            if hasattr(self, method):
                try:
                    getattr(self, method)(value)
                except Exception:
                    pass


