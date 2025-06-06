from PySide6.QtCore import Signal as pyqtSignal
from ..base_wrapper import BaseWrapper, CollectorWrapperMixin
from shared_tools.collectors.collect_isda import ISDADocumentationCollector

class ISDAWrapper(BaseWrapper, CollectorWrapperMixin):
    """UI wrapper for ISDA Documentation Collector"""
    
    documents_found = pyqtSignal(int)  # Number of documents found
    
    def __init__(self, config):
        super().__init__(config)
        self.collector = None
        
    def _create_target_object(self):
        """Create ISDA collector instance"""
        if not self.collector:
            self.collector = ISDADocumentationCollector(self.config)
        return self.collector
        
    def _get_operation_type(self):
        return "collect"
        
    def set_search_keywords(self, keywords):
        """Set search keywords for ISDA collection"""
        self.search_keywords = keywords
        
    def set_max_sources(self, max_sources):
        """Set maximum number of sources to process"""
        self.max_sources = max_sources