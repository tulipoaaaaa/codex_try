import sys
import types
import os
import tempfile
import shutil
import pytest

# Register optional dependency marker so tests can be skipped cleanly
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "optional_dependency: marks tests that require optional packages (PySide6, yaml)",
    )

# Ensure repo root is importable when running tests individually
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)


try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    def load_dotenv(*args, **kwargs):
        pass
    stub = types.ModuleType("dotenv")
    stub.load_dotenv = load_dotenv
    stub.set_key = lambda *a, **k: None
    sys.modules.setdefault("dotenv", stub)

# Ensure the CorpusBuilderApp root is on the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'CorpusBuilderApp'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if "PYTEST_QT_STUBS" not in os.environ:
    try:  # Auto-enable stubs when PySide6 is missing
        import importlib.util
        if importlib.util.find_spec("PySide6") is None:
            os.environ["PYTEST_QT_STUBS"] = "1"
    except Exception:
        os.environ["PYTEST_QT_STUBS"] = "1"

if os.environ.get("PYTEST_QT_STUBS") == "1":
    class _SafeStubModule(types.ModuleType):
        def __getattr__(self, name):
            return type(name, (), {})

    qtwidgets = _SafeStubModule("PySide6.QtWidgets")

    class QApplication:
        _instance = None

        def __init__(self, *a, **k):
            QApplication._instance = self

        @classmethod
        def instance(cls):
            return cls._instance

        def quit(self):
            pass

        def processEvents(self, *a, **k):
            pass

    qtwidgets.QApplication = QApplication
    sys.modules["PySide6.QtWidgets"] = qtwidgets

    qtcore = _SafeStubModule("PySide6.QtCore")
    class Signal:
        def __init__(self, *a, **k):
            pass
        def connect(self, *a, **k):
            pass
    qtcore.Signal = Signal
    qtcore.QObject = type("QObject", (), {})
    qtcore.QThread = type("QThread", (), {})
    qtcore.QTimer = type("QTimer", (), {})
    qtcore.Slot = lambda *a, **k: (lambda *a, **k: None)
    qtcore.qInstallMessageHandler = lambda *a, **k: None
    sys.modules["PySide6.QtCore"] = qtcore

    sys.modules["PySide6.QtGui"] = _SafeStubModule("PySide6.QtGui")
    sys.modules["PySide6.QtCharts"] = _SafeStubModule("PySide6.QtCharts")
    sys.modules["PySide6.QtTest"] = _SafeStubModule("PySide6.QtTest")
    sys.modules["PySide6.QtMultimedia"] = _SafeStubModule("PySide6.QtMultimedia")
    pyside6 = types.ModuleType("PySide6")
    pyside6.QtWidgets = sys.modules["PySide6.QtWidgets"]
    pyside6.QtGui = sys.modules["PySide6.QtGui"]
    pyside6.QtCharts = sys.modules["PySide6.QtCharts"]
    pyside6.QtTest = sys.modules["PySide6.QtTest"]
    pyside6.QtCore = sys.modules["PySide6.QtCore"]
    pyside6.QtMultimedia = sys.modules["PySide6.QtMultimedia"]
    sys.modules["PySide6"] = pyside6

for mod in [
    "fitz",
    "pytesseract",
    "cv2",
    "numpy",
    "matplotlib",
    "matplotlib.pyplot",
    "seaborn",
    "yaml",
    "requests",
    "pandas",
    "plotly",
    "plotly.graph_objects",
    "plotly.express",
    "plotly.subplots",
    "scipy",
    "scipy.stats",
    "bs4",
    "selenium",
    "selenium.webdriver",
    "selenium.webdriver.common",
    "selenium.webdriver.common.by",
    "undetected_chromedriver",
    "selenium.common",
    "selenium.common.exceptions",
    "keyring",
    "cryptography",
    "cryptography.fernet",
    "pydantic",
    "psutil",
]:
    sys.modules.setdefault(mod, types.ModuleType(mod))

bs4_mod = sys.modules.setdefault('bs4', types.ModuleType('bs4'))
setattr(bs4_mod, 'BeautifulSoup', lambda *a, **k: None)

selenium_mod = sys.modules.setdefault('selenium', types.ModuleType('selenium'))
webdriver_mod = sys.modules.setdefault('selenium.webdriver', types.ModuleType('selenium.webdriver'))
setattr(selenium_mod, 'webdriver', webdriver_mod)
chrome_mod = sys.modules.setdefault('selenium.webdriver.chrome', types.ModuleType('selenium.webdriver.chrome'))
options_mod = sys.modules.setdefault('selenium.webdriver.chrome.options', types.ModuleType('selenium.webdriver.chrome.options'))
setattr(options_mod, 'Options', object)
common_mod = sys.modules.setdefault('selenium.webdriver.common', types.ModuleType('selenium.webdriver.common'))
by_mod = sys.modules.setdefault('selenium.webdriver.common.by', types.ModuleType('selenium.webdriver.common.by'))
setattr(by_mod, 'By', object)
selenium_common = sys.modules.setdefault('selenium.common', types.ModuleType('selenium.common'))
exceptions_mod = sys.modules.setdefault('selenium.common.exceptions', types.ModuleType('selenium.common.exceptions'))
setattr(selenium_common, 'exceptions', exceptions_mod)
setattr(exceptions_mod, 'NoSuchElementException', Exception)
np_mod = sys.modules.setdefault('numpy', types.ModuleType('numpy'))
setattr(np_mod, 'ndarray', object)
setattr(np_mod, 'array', lambda *a, **k: None)
pd_mod = sys.modules.setdefault('pandas', types.ModuleType('pandas'))
setattr(pd_mod, 'DataFrame', object)
setattr(pd_mod, 'read_csv', lambda *a, **k: None)
for plot_mod in ['plotly', 'plotly.graph_objects', 'plotly.express', 'plotly.subplots']:
    mod = sys.modules.setdefault(plot_mod, types.ModuleType(plot_mod))
    if plot_mod == 'plotly.subplots':
        setattr(mod, 'make_subplots', lambda *a, **k: None)

scipy_mod = sys.modules.setdefault('scipy', types.ModuleType('scipy'))
scipy_stats_mod = sys.modules.setdefault('scipy.stats', types.ModuleType('scipy.stats'))
setattr(scipy_mod, 'stats', scipy_stats_mod)
setattr(scipy_stats_mod, 'entropy', lambda *a, **k: None)
setattr(scipy_stats_mod, 'chi2_contingency', lambda *a, **k: (None, None, None, None))
cryptography_mod = sys.modules.setdefault('cryptography', types.ModuleType('cryptography'))
fernet_mod = sys.modules.setdefault('cryptography.fernet', types.ModuleType('cryptography.fernet'))
setattr(cryptography_mod, 'fernet', fernet_mod)
setattr(fernet_mod, 'Fernet', type('Fernet', (), {'generate_key': staticmethod(lambda: b"0"*32)}))
setattr(fernet_mod, 'InvalidToken', Exception)
keyring_mod = sys.modules.setdefault('keyring', types.ModuleType('keyring'))
setattr(keyring_mod, 'get_password', lambda *a, **k: None)
setattr(keyring_mod, 'set_password', lambda *a, **k: None)
pydantic_mod = sys.modules.setdefault('pydantic', types.ModuleType('pydantic'))
setattr(pydantic_mod, 'BaseModel', object)
setattr(pydantic_mod, 'validator', lambda *a, **k: (lambda f: f))
setattr(pydantic_mod, 'field_validator', lambda *a, **k: (lambda f: f))
setattr(pydantic_mod, 'Field', lambda *a, **k: None)
setattr(pydantic_mod, 'ValidationError', type('ValidationError', (Exception,), {}))

if "langdetect" not in sys.modules:
    langdetect = types.ModuleType("langdetect")
    langdetect.detect_langs = lambda *a, **k: []
    langdetect.LangDetectException = Exception
    sys.modules["langdetect"] = langdetect

dummy_pil = types.ModuleType("PIL")
dummy_image_mod = types.ModuleType("PIL.Image")

class DummyImage:
    ...

dummy_image_mod.Image = DummyImage
dummy_enhance_mod = types.ModuleType("PIL.ImageEnhance")

class DummyEnhance:
    ...

dummy_enhance_mod.ImageEnhance = DummyEnhance
dummy_pil.Image = dummy_image_mod
dummy_pil.ImageEnhance = dummy_enhance_mod
sys.modules.setdefault("PIL", dummy_pil)
sys.modules.setdefault("PIL.Image", dummy_image_mod)
sys.modules.setdefault("PIL.ImageEnhance", dummy_enhance_mod)


@pytest.fixture(scope="session")
def qapp():
    """Provide a QApplication instance for tests."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture
def mock_project_config(temp_dir):
    """Return a simple project config object with directories."""

    class DummyConfig:
        def __init__(self, base):
            self.base = base
            self.config = {
                "directories": {
                    "corpus_root": base,
                    "raw_data": os.path.join(base, "raw"),
                    "processed_data": os.path.join(base, "processed"),
                    "metadata": os.path.join(base, "metadata"),
                    "logs": os.path.join(base, "logs"),
                }
            }

        def get_directory(self, name):
            return self.config["directories"][name]

        def get_logs_dir(self):
            return self.config["directories"]["logs"]

    cfg = DummyConfig(temp_dir)
    for p in cfg.config["directories"].values():
        os.makedirs(p, exist_ok=True)
    return cfg


@pytest.fixture
def sample_files(temp_dir):
    """Create sample text and metadata files for tests."""
    files = {}
    text_file = os.path.join(temp_dir, "sample.txt")
    with open(text_file, "w") as f:
        f.write("This is a sample text file for testing.")
    files["text"] = text_file

    metadata_file = os.path.join(temp_dir, "sample_metadata.json")
    metadata = {
        "title": "Sample Document",
        "author": "Test Author",
        "year": 2023,
        "domain": "Risk Management",
    }
    import json
    with open(metadata_file, "w") as f:
        json.dump(metadata, f)
    files["metadata"] = metadata_file

    return files
