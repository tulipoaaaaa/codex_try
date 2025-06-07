# File: tests/conftest.py

import pytest
import sys
import os
import types

# Provide lightweight PySide6 stubs for headless test environments
if 'PySide6' not in sys.modules:
    class _Signal:
        def __init__(self):
            self._slots = []
        def connect(self, slot):
            self._slots.append(slot)
        def emit(self, *args, **kwargs):
            for s in list(self._slots):
                s(*args, **kwargs)

    qtcore = types.SimpleNamespace(
        QObject=object,
        QDir=type('QDir', (), {'homePath': staticmethod(lambda: "/tmp")}),
        Signal=lambda *a, **k: _Signal()
    )
    qtwidgets = types.SimpleNamespace(
        QApplication=type('QApplication', (), {
            'instance': classmethod(lambda cls: None),
            '__init__': lambda self, *a, **k: None,
            'quit': lambda self: None,
        })
    )
    qtgui = types.SimpleNamespace(QGuiApplication=type('QGuiApplication', (), {}))
    sys.modules.setdefault('PySide6', types.SimpleNamespace(QtCore=qtcore, QtWidgets=qtwidgets, QtGui=qtgui))
    sys.modules.setdefault('PySide6.QtCore', qtcore)
    sys.modules.setdefault('PySide6.QtWidgets', qtwidgets)
    sys.modules.setdefault('PySide6.QtGui', qtgui)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDir
import tempfile
import shutil

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def mock_project_config(temp_dir):
    """Create a mock project configuration for testing."""
    class DummyConfig:
        def __init__(self, base):
            self.base = base
            self.config = {
                'directories': {
                    'corpus_root': base,
                    'raw_data': os.path.join(base, 'raw'),
                    'processed_data': os.path.join(base, 'processed'),
                    'metadata': os.path.join(base, 'metadata'),
                    'logs': os.path.join(base, 'logs'),
                }
            }

        def get_directory(self, name):
            return self.config['directories'][name]

    cfg = DummyConfig(temp_dir)

    for path in cfg.config['directories'].values():
        os.makedirs(path, exist_ok=True)

    return cfg

@pytest.fixture
def sample_files(temp_dir):
    """Create sample files for testing."""
    files = {}
    
    # Create a sample text file
    text_file = os.path.join(temp_dir, 'sample.txt')
    with open(text_file, 'w') as f:
        f.write("This is a sample text file for testing.")
    files['text'] = text_file
    
    # Create a sample JSON metadata file
    metadata_file = os.path.join(temp_dir, 'sample_metadata.json')
    import json
    metadata = {
        'title': 'Sample Document',
        'author': 'Test Author',
        'year': 2023,
        'domain': 'Risk Management'
    }
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f)
    files['metadata'] = metadata_file
    
    return files
