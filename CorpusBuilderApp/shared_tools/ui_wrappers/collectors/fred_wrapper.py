from PySide6.QtCore import Signal as pyqtSignal
from ..base_wrapper import BaseWrapper, CollectorWrapperMixin
from shared_tools.collectors.fred_collector import FREDCollector

class FREDWrapper(BaseWrapper, CollectorWrapperMixin):
    """UI wrapper for FRED Economic Data Collector"""
    
    series_found = pyqtSignal(int)  # Number of data series found
    
    def __init__(self, config):
        super().__init__(config)
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