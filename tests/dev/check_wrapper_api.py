from tests.dev.discover_wrappers import discover_wrapper_classes
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Signal
import sys
import tempfile
import pathlib
import logging
from pathlib import Path

class DummyProjectConfig:
    """Mock ProjectConfig that mimics the real ProjectConfig interface"""
    
    def __init__(self):
        # Set up basic config structure
        self.config = {
            "environment": {
                "active": "test",
                "python_path": "",
                "venv_path": "",
                "temp_dir": ""
            },
            "environments": {
                "test": {
                    "corpus_root": str(Path.home() / "test_corpus"),
                    "raw_data_dir": str(Path.home() / "test_corpus" / "raw"),
                    "processed_dir": str(Path.home() / "test_corpus" / "processed"),
                    "metadata_dir": str(Path.home() / "test_corpus" / "metadata"),
                    "logs_dir": str(Path.home() / "test_corpus" / "logs")
                }
            },
            "directories": {
                "corpus_root": str(Path.home() / "test_corpus"),
                "raw_data_dir": str(Path.home() / "test_corpus" / "raw"),
                "processed_dir": str(Path.home() / "test_corpus" / "processed"),
                "metadata_dir": str(Path.home() / "test_corpus" / "metadata"),
                "logs_dir": str(Path.home() / "test_corpus" / "logs")
            },
            "domains": {
                "test_domain": {
                    "allocation": 0.5,
                    "min_documents": 10,
                    "priority": "medium",
                    "quality_threshold": 0.7,
                    "target_weight": 0.5,
                    "search_terms": ["test", "example"]
                }
            },
            "processing": {
                "pdf": {
                    "threads": 4,
                    "enable_ocr": True,
                    "enable_formula": True,
                    "enable_tables": True
                },
                "text": {
                    "threads": 4,
                    "enable_language": True,
                    "min_quality": 70,
                    "enable_deduplication": True
                }
            },
            "target_languages": ["en"],  # For MachineTranslationDetector
            "collectors": {},
            "processors": {}
        }
        
        # Set up logger
        self.logger = logging.getLogger("DummyProjectConfig")
        
        # Set up basic attributes that wrappers might access
        self.environment = "test"
        self.domains = []
        self.project_dir = Path.home() / "test_corpus"

    def get(self, key: str, default=None):
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value

    def __getitem__(self, key):
        """Support config['key'] access pattern"""
        return self.get(key)
    
    def __setitem__(self, key, value):
        """Support config['key'] = value pattern"""
        self.set(key, value)

    def set(self, dotted_key: str, value):
        """Set configuration value using dot notation"""
        parts = dotted_key.split('.')
        node = self.config
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = value

    def save(self, path=None):
        """Mock save method"""
        pass

    def reload_from_file(self):
        """Mock reload method"""
        pass

    def revalidate(self):
        """Mock revalidate method"""
        pass

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None

    # Directory helper methods that match ProjectConfig
    def get_corpus_root(self) -> Path:
        return Path(self.get('directories.corpus_root')).expanduser()

    def get_corpus_dir(self) -> Path:
        """Legacy method for backward compatibility"""
        return self.get_corpus_root()

    def get_raw_dir(self) -> Path:
        return Path(self.get('directories.raw_data_dir')).expanduser()

    def get_input_dir(self) -> Path:
        """Legacy helper for compatibility"""
        return self.get_raw_dir()

    def get_processed_dir(self) -> Path:
        return Path(self.get('directories.processed_dir')).expanduser()

    def get_metadata_dir(self) -> Path:
        return Path(self.get('directories.metadata_dir')).expanduser()

    def get_logs_dir(self) -> Path:
        return Path(self.get('directories.logs_dir')).expanduser()

    def get_stats_dir(self) -> Path:
        return self.get_logs_dir() / "stats"

    def get_processor_config(self, processor_name: str):
        """Get processor-specific configuration"""
        return self.get(f'processors.{processor_name}', {})

    def get_collector_config(self, collector_name: str):
        """Get collector-specific configuration"""
        return self.get(f'collectors.{collector_name}', {})

    def __iter__(self):
        """Some wrappers try to iterate config"""
        return iter([])

    # Legacy attributes that some wrappers might access directly
    @property
    def raw_data_dir(self):
        return self.get_raw_dir()

    @property
    def processed_dir(self):
        return self.get_processed_dir()

# Required members and their types
MUST_HAVE = {
    "completed",            # pyqtSignal
    "batch_completed",      # alias signal ok
    "_is_running",          # property/bool
    "file_processed",       # pyqtSignal (may be missing on collectors)
}

# Expected methods that should exist (but might be missing in current state)
EXPECTED_METHODS = {
    "setup_ui",            # UI setup method
    "setup_connections",   # Signal connections setup
    "refresh_config",      # Config refresh method
}

if __name__ == "__main__":
    # Initialize QApplication first
    app = QApplication(sys.argv)
    
    errors = []
    missing_methods = []
    wrapper_paths = discover_wrapper_classes()
    
    for path in wrapper_paths:
        try:
            # Split path into module and class name
            module, cls = path.rsplit('.', 1)
            
            # Import the module and get the class
            wrapper_class = getattr(__import__(module, fromlist=[cls]), cls)
            
            # Skip base classes and abstract classes
            if cls in ['BaseWrapper', 'BaseExtractorWrapper', 'ProcessorMixin', 'CollectorWrapperMixin', 'ProcessorWrapperMixin']:
                continue
            
            # Try to instantiate with dummy config
            try:
                w = wrapper_class(DummyProjectConfig())
                
                # Check for missing required members
                missing = []
                for member in MUST_HAVE:
                    if not hasattr(w, member):
                        missing.append(member)
                
                if missing:
                    errors.append(f"{path} missing required attributes: {', '.join(missing)}")
                
                # Check for missing expected methods (these are production issues)
                missing_methods_for_wrapper = []
                for method in EXPECTED_METHODS:
                    if not hasattr(w, method):
                        missing_methods_for_wrapper.append(method)
                
                if missing_methods_for_wrapper:
                    missing_methods.append(f"{path} missing methods: {', '.join(missing_methods_for_wrapper)}")
                
                # Check signal types for present members
                for name in MUST_HAVE:
                    if hasattr(w, name):
                        # Skip _is_running as it's a property/bool
                        if name == "_is_running":
                            continue
                        
                        # Get the attribute from the class (not instance)
                        attr = getattr(type(w), name, None)
                        if attr is not None and not isinstance(attr, Signal):
                            errors.append(f"{path} {name} is not a Signal")
                
            except Exception as e:
                # This represents the actual production state - wrappers that fail to instantiate
                errors.append(f"{path} failed to instantiate: {repr(e)}")
            
        except Exception as e:
            errors.append(f"{path} failed to import: {repr(e)}")
    
    # Print results
    print("\n" + "="*80)
    print("WRAPPER API CHECK RESULTS")
    print("="*80)
    
    if errors:
        print(f"\n🔴 CRITICAL ERRORS ({len(errors)}):")
        print("These prevent wrappers from being instantiated:")
        for error in errors:
            print(f"  • {error}")
    
    if missing_methods:
        print(f"\n🟡 MISSING METHODS ({len(missing_methods)}):")
        print("These are expected methods that should exist but are missing:")
        for missing in missing_methods:
            print(f"  • {missing}")
    
    if not errors and not missing_methods:
        print("\n✅ All wrappers passed API checks!")
    
    total_issues = len(errors) + len(missing_methods)
    print(f"\nTotal issues found: {total_issues}")
    
    if total_issues > 0:
        print("\n📋 SUMMARY:")
        print("- Critical errors prevent wrapper instantiation (production blockers)")
        print("- Missing methods cause runtime errors when UI tries to call them")
        print("- Both types of issues need to be fixed for proper application functionality") 