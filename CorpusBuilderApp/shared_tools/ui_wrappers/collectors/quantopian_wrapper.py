from PySide6.QtCore import Signal as pyqtSignal
from ..base_wrapper import BaseWrapper, CollectorWrapperMixin
from shared_tools.collectors.quantopian_collector import QuantopianCollector

class QuantopianWrapper(BaseWrapper, CollectorWrapperMixin):
    """UI wrapper for Quantopian Collector"""
    
    notebooks_found = pyqtSignal(int)  # Number of notebooks found
    
    def __init__(self, config):
        super().__init__(config)
        self.collector = None
        
    def _create_target_object(self):
        """Create Quantopian collector instance"""
        if not self.collector:
            self.collector = QuantopianCollector(self.config)
        return self.collector
        
    def _get_operation_type(self):
        return "collect"
