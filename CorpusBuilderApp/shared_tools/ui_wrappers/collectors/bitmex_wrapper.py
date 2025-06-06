from PySide6.QtCore import Signal as pyqtSignal
from ..base_wrapper import BaseWrapper, CollectorWrapperMixin
from shared_tools.collectors.collect_bitmex import BitMEXCollector

class BitMEXWrapper(BaseWrapper, CollectorWrapperMixin):
    """UI wrapper for BitMEX Collector"""
    
    data_points_found = pyqtSignal(int)  # Number of data points found
    
    def __init__(self, config):
        super().__init__(config)
        self.collector = None
        
    def _create_target_object(self):
        """Create BitMEX collector instance"""
        if not self.collector:
            self.collector = BitMEXCollector(self.config)
        return self.collector
        
    def _get_operation_type(self):
        return "collect"