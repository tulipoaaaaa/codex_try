from PySide6.QtCore import Signal as pyqtSignal
from ..base_wrapper import BaseWrapper, CollectorWrapperMixin
from shared_tools.collectors.collect_isda import ISDADocumentationCollector

class ISDAWrapper(BaseWrapper, CollectorWrapperMixin):
    """UI wrapper for ISDA Documentation Collector"""
    
    documents_found = pyqtSignal(int)  # Number of documents found
    
    def __init__(self, config):
        super().__init__(config)
        self.project_config = config
        self.name = "isda"
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

