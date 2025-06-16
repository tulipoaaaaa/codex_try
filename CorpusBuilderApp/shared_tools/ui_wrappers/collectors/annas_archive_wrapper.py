from PySide6.QtCore import Signal as pyqtSignal
from ..base_wrapper import BaseWrapper, CollectorWrapperMixin
from shared_tools.collectors.collect_annas_main_library import AnnasMainLibraryCollector

class AnnasArchiveWrapper(BaseWrapper, CollectorWrapperMixin):
    """UI wrapper for Anna's Archive Collector"""
    
    books_found = pyqtSignal(int)  # Number of books found
    
    def __init__(self, config):
        super().__init__(config)
        self.project_config = config
        self.name = "annas_archive"
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

    def refresh_config(self):
        """Reload parameters from ``self.config``. Safe to call multiple times."""
        wrapper_cfg = self.config.get(f"collectors.{self.name}", {}) or {}

        for key, value in wrapper_cfg.items():
            method = f"set_{key}"
            if hasattr(self, method):
                try:
                    getattr(self, method)(value)
                except Exception:
                    continue

        if self.collector:
            cookie = self.config.get("api_keys.annas_cookie")
            if cookie:
                setattr(self.collector, "cookie", cookie)

    # ------------------------------------------------------------------
    # Compatibility alias so AutoBalanceDaemon can inject missing domains
    # ------------------------------------------------------------------
    def set_search_terms(self, terms):  # noqa: D401 – simple alias
        """Accept a list of domain names and convert to a single search query.

        This keeps the original API (`set_search_query`) untouched while
        allowing the headless auto-balance daemon—which looks specifically for
        `set_search_terms()`—to bias Anna's Archive searches toward
        under-represented domains.
        """
        if not isinstance(terms, (list, tuple)):
            terms = [str(terms)]
        # Join terms with spaces so the underlying collector performs a broad
        # OR-style search.
        self.search_query = " ".join(str(t) for t in terms if t)

