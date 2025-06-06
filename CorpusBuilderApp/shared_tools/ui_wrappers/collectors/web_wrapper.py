from PySide6.QtCore import Signal as pyqtSignal
from ..base_wrapper import BaseWrapper, CollectorWrapperMixin
from shared_tools.collectors.web_collector import WebCollector

class WebWrapper(BaseWrapper, CollectorWrapperMixin):
    """UI wrapper for Web Collector"""
    
    pages_found = pyqtSignal(int)  # Number of web pages found
    
    def __init__(self, config):
        super().__init__(config)
        self.collector = None
        self.urls = []
        
    def _create_target_object(self):
        """Create Web collector instance"""
        if not self.collector:
            self.collector = WebCollector(self.config)
        return self.collector
        
    def _get_operation_type(self):
        return "collect"
        
    def set_urls(self, urls):
        """Set URLs to collect from"""
        self.urls = urls
        
    def start(self, **kwargs):
        """Override start to pass web-specific parameters"""
        kwargs.update({
            'urls': self.urls
        })
        super().start(**kwargs)