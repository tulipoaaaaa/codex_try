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
        """Reload parameters and API credentials from ``self.config``."""
        cfg = self.config.get(f"collectors.{self.name}", {}) or {}
        for key, value in cfg.items():
            method = f"set_{key}"
            if hasattr(self, method):
                try:
                    getattr(self, method)(value)
                except Exception:
                    continue

        if self.collector:
            self.collector.api_key = self.config.get("api_keys.bitmex_key")
            self.collector.api_secret = self.config.get("api_keys.bitmex_secret")

