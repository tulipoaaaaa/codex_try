from PySide6.QtCore import Signal as pyqtSignal
from ..base_wrapper import BaseWrapper, CollectorWrapperMixin
from shared_tools.collectors.collect_annas_main_library import AnnasMainLibraryCollector

class AnnasArchiveWrapper(BaseWrapper, CollectorWrapperMixin):
    """UI wrapper for Anna's Archive Collector"""
    
    books_found = pyqtSignal(int)  # Number of books found
    
    def __init__(self, config):
        super().__init__(config)
        self.collector = None
        self.search_query = ""
        self.max_attempts = 5
        
    def _create_target_object(self):
        """Create Anna's Archive collector instance"""
        if not self.collector:
            self.collector = AnnasMainLibraryCollector(self.config)
        return self.collector
        
    def _get_operation_type(self):
        return "collect"
        
    def set_search_query(self, query):
        """Set search query for book collection"""
        self.search_query = query
        
    def set_max_attempts(self, max_attempts):
        """Set maximum number of download attempts"""
        self.max_attempts = max_attempts
        
    def start(self, **kwargs):
        """Override start to pass search query"""
        kwargs.update({
            'search_query': self.search_query,
            'max_attempts': self.max_attempts
        })
        super().start(**kwargs)
