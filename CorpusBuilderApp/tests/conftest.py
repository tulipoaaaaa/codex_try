# File: tests/conftest.py
import sys
import types
import os
import pytest
import tempfile
import shutil
import json

# Ensure repo root is importable when running tests individually
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

# Alias for compatibility with CryptoCorpusBuilder imports
sys.modules.setdefault(
    "CryptoCorpusBuilder",
    types.ModuleType("CryptoCorpusBuilder"),
)
sys.modules.setdefault(
    "CryptoCorpusBuilder.shared_tools",
    __import__("CorpusBuilderApp.shared_tools", fromlist=["dummy"]),
)

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    def load_dotenv(*args, **kwargs):
        pass
    stub = types.ModuleType("dotenv")
    stub.load_dotenv = load_dotenv
    sys.modules.setdefault("dotenv", stub)

# Provide lightweight Qt stubs if requested
if os.environ.get("PYTEST_QT_STUBS") == "1":
    print("Loaded PySide6 stub")

    class _DummySignal:
        def emit(self, *a, **k):
            pass

    class _DummyModuleCore(types.ModuleType):
        def __getattr__(self, name):
            return object

    qtcore = _DummyModuleCore("PySide6.QtCore")
    class _QObject:
        def __init__(self, *a, **k):
            pass

    qtcore.QObject = _QObject
    qtcore.Signal = lambda *a, **k: _DummySignal()
    qtcore.QThread = object
    qtcore.QTimer = object
    qtcore.Slot = lambda *a, **k: (lambda *a, **k: None)
    qtcore.QDir = object
    qtcore.Property = object
    qtcore.Qt = types.SimpleNamespace(
        Orientation=types.SimpleNamespace(Vertical=0, Horizontal=1),
        AlignmentFlag=types.SimpleNamespace(AlignCenter=0),
    )
    qtcore.__version__ = "6.5.0"
    qtcore.qVersion = lambda: "6.5.0"
    qtcore.qDebug = lambda *a, **k: None
    qtcore.qWarning = lambda *a, **k: None
    qtcore.qCritical = lambda *a, **k: None
    qtcore.qFatal = lambda *a, **k: None
    qtcore.qInfo = lambda *a, **k: None
    qtcore.qInstallMessageHandler = lambda *a, **k: None

    class _DummyModuleWidgets(types.ModuleType):
        def __getattr__(self, name):
            return object

    qtwidgets = _DummyModuleWidgets("PySide6.QtWidgets")
    class _QWidget:
        def __init__(self, *a, **k):
            pass

    qtwidgets.QWidget = _QWidget
    qtwidgets.QApplication = type(
        "QApplication",
        (),
        {
            "instance": staticmethod(lambda: None),
            "__init__": lambda self, *a, **k: None,
            "quit": lambda self: None,
        },
    )

    class _DummyGui(types.ModuleType):
        def __getattr__(self, name):
            return object

    qtgui = _DummyGui("PySide6.QtGui")
    qtgui.QIcon = object
    qttest = types.SimpleNamespace(QTest=object, QSignalSpy=object)
    qtmultimedia = types.SimpleNamespace(QSoundEffect=object)
    class _DummyCharts(types.ModuleType):
        def __getattr__(self, name):
            return object
    qtcharts = _DummyCharts("PySide6.QtCharts")

    sys.modules.setdefault("PySide6", types.SimpleNamespace(
        QtCore=qtcore,
        QtWidgets=qtwidgets,
        QtGui=qtgui,
        QtTest=qttest,
        __version__="6.5.0"
    ))
    sys.modules.setdefault("PySide6.QtCore", qtcore)
    sys.modules.setdefault("PySide6.QtWidgets", qtwidgets)
    sys.modules.setdefault("PySide6.QtGui", qtgui)
    sys.modules.setdefault("PySide6.QtTest", qttest)
    sys.modules.setdefault("PySide6.QtMultimedia", qtmultimedia)
    sys.modules.setdefault("PySide6.QtCharts", qtcharts)

# Mock external modules
for mod in [
    "fitz",
    "pytesseract",
    "cv2",
    "numpy",
    "matplotlib",
    "matplotlib.pyplot",
    "seaborn",
    "pandas",
]:
    sys.modules.setdefault(mod, types.ModuleType(mod))

# Mock langdetect
if "langdetect" not in sys.modules:
    langdetect = types.ModuleType("langdetect")
    langdetect.detect_langs = lambda *a, **k: []
    langdetect.LangDetectException = Exception
    sys.modules["langdetect"] = langdetect

# Mock PIL modules
dummy_pil = types.ModuleType("PIL")
dummy_image_mod = types.ModuleType("PIL.Image")
class DummyImage: ...
dummy_image_mod.Image = DummyImage
dummy_enhance_mod = types.ModuleType("PIL.ImageEnhance")
class DummyEnhance: ...
dummy_enhance_mod.ImageEnhance = DummyEnhance
dummy_pil.Image = dummy_image_mod
dummy_pil.ImageEnhance = dummy_enhance_mod
sys.modules.setdefault("PIL", dummy_pil)
sys.modules.setdefault("PIL.Image", dummy_image_mod)
sys.modules.setdefault("PIL.ImageEnhance", dummy_enhance_mod)

# Ensure the CorpusBuilderApp root is on the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDir

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

        def get_logs_dir(self):
            return self.config['directories']['logs']

    cfg = DummyConfig(temp_dir)
    for path in cfg.config['directories'].values():
        os.makedirs(path, exist_ok=True)

    return cfg

@pytest.fixture
def sample_files(temp_dir):
    """Create sample files for testing."""
    files = {}

    text_file = os.path.join(temp_dir, 'sample.txt')
    with open(text_file, 'w') as f:
        f.write("This is a sample text file for testing.")
    files['text'] = text_file

    metadata_file = os.path.join(temp_dir, 'sample_metadata.json')
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
