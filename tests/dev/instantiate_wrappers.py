import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from tests.dev.discover_wrappers import discover_wrapper_classes
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Signal
import tempfile
import logging

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

if __name__ == "__main__":
    # Initialize QApplication first
    app = QApplication(sys.argv)
    
    print("="*80)
    print("WRAPPER INSTANTIATION TEST")
    print("="*80)
    print("Testing if wrappers can be instantiated with proper config...")
    
    failures = []
    successes = []
    wrapper_paths = discover_wrapper_classes()
    
    for path in wrapper_paths:
        try:
            # Split path into module and class name
            module, cls = path.rsplit('.', 1)
            
            # Skip base classes and abstract classes
            if cls in ['BaseWrapper', 'BaseExtractorWrapper', 'ProcessorMixin', 'CollectorWrapperMixin', 'ProcessorWrapperMixin']:
                continue
            
            # Import the module and get the class
            wrapper_class = getattr(__import__(module, fromlist=[cls]), cls)
            
            # Try to instantiate with dummy config
            w = wrapper_class(DummyProjectConfig())
            successes.append(path)
            
        except Exception as e:
            failures.append((path, repr(e)))
    
    # Print results
    print(f"\n✅ SUCCESSFUL INSTANTIATIONS ({len(successes)}):")
    if successes:
        for success in successes:
            print(f"  • {success}")
    else:
        print("  None")
    
    print(f"\n🔴 FAILED INSTANTIATIONS ({len(failures)}):")
    if failures:
        for path, error in failures:
            print(f"  • {path}")
            print(f"    Error: {error}")
    else:
        print("  None")
    
    total_tested = len(successes) + len(failures)
    success_rate = (len(successes) / total_tested * 100) if total_tested > 0 else 0
    
    print(f"\n📊 SUMMARY:")
    print(f"  Total wrappers tested: {total_tested}")
    print(f"  Successful: {len(successes)}")
    print(f"  Failed: {len(failures)}")
    print(f"  Success rate: {success_rate:.1f}%")
    
    if failures:
        print(f"\n📋 ANALYSIS:")
        print("These failures represent actual production issues that prevent")
        print("the application from working correctly. Each failed wrapper")
        print("needs to be fixed for the application to function properly.")
    else:
        print(f"\n🎉 All wrappers can be instantiated successfully!") 