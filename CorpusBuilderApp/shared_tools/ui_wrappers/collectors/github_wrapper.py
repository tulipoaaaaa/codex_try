from PySide6.QtCore import Signal as pyqtSignal
from ..base_wrapper import BaseWrapper, CollectorWrapperMixin
from shared_tools.collectors.github_collector import GitHubCollector

class GitHubWrapper(BaseWrapper, CollectorWrapperMixin):
    """UI wrapper for GitHub Collector"""
    
    repos_found = pyqtSignal(int)  # Number of repositories found
    repo_cloned = pyqtSignal(str)  # Repository name cloned
    
    def __init__(self, config):
        super().__init__(config)
        self.collector = None
        self.search_terms = []
        self.topic = None
        self.max_repos = 10
        
    def _create_target_object(self):
        """Create GitHub collector instance"""
        if not self.collector:
            self.collector = GitHubCollector(self.config)
        return self.collector
        
    def _get_operation_type(self):
        return "collect"
        
    def set_search_terms(self, terms):
        """Set search terms for repository collection"""
        self.search_terms = terms
        
    def set_topic(self, topic):
        """Set GitHub topic to search for"""
        self.topic = topic
        
    def set_max_repos(self, max_repos):
        """Set maximum number of repositories to collect"""
        self.max_repos = max_repos
        
    def start(self, **kwargs):
        """Override start to pass GitHub-specific parameters"""
        kwargs.update({
            'search_terms': self.search_terms,
            'topic': self.topic,
            'max_repos': self.max_repos
        })
