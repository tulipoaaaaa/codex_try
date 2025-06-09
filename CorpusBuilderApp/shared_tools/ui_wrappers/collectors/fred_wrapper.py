from PySide6.QtCore import Signal as pyqtSignal
from ..base_wrapper import BaseWrapper, CollectorWrapperMixin
from shared_tools.collectors.fred_collector import FREDCollector

class FREDWrapper(BaseWrapper, CollectorWrapperMixin):
    """UI wrapper for FRED Economic Data Collector"""
    
    series_found = pyqtSignal(int)  # Number of data series found
    
    def __init__(self, config):
        super().__init__(config)
        self.project_config = config
        self.name = "fred"
        self.collector = None
        self.series_ids = []
        
    def _create_target_object(self):
        """Create FRED collector instance"""
        if not self.collector:
            self.collector = FREDCollector(self.config)
        return self.collector
        
    def _get_operation_type(self):
        return "collect"
        
    def set_series_ids(self, series_ids):
        """Set FRED series IDs to collect"""
        self.series_ids = series_ids
        
    def start(self, **kwargs):
        """Override start to pass FRED-specific parameters"""
        kwargs.update({
            'series_ids': self.series_ids
        })
        super().start(**kwargs)

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

