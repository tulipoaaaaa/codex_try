from PySide6.QtCore import Signal as pyqtSignal
from ..base_wrapper import BaseWrapper, CollectorWrapperMixin
from shared_tools.collectors.collect_bitmex import BitMEXCollector

class BitMEXWrapper(BaseWrapper, CollectorWrapperMixin):
    """UI wrapper for BitMEX Collector"""
    
    data_points_found = pyqtSignal(int)  # Number of data points found
    
    def __init__(self, config):
        super().__init__(config)
        self.project_config = config
        self.name = "bitmex"
        self.collector = None
        
    def _create_target_object(self):
        """Create BitMEX collector instance"""
        if not self.collector:
            self.collector = BitMEXCollector(self.config)
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

