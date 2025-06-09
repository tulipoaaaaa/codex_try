import sys
import types
import os
import tempfile
import shutil
import pytest

# Ensure app and shared_tools packages are importable
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(base_dir, 'CorpusBuilderApp'))
sys.path.insert(0, os.path.join(base_dir, 'CorpusBuilderApp', 'shared_tools'))

if 'PySide6' not in sys.modules:
    class _Signal:
        def __init__(self, *a, **k):
            self._slots = []
        def connect(self, slot):
            self._slots.append(slot)
        def emit(self, *a, **k):
            for s in self._slots:
                s(*a, **k)
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
    class QDir:
        @staticmethod
        def homePath():
            import os
            return os.path.expanduser('~')
        @staticmethod
        def rootPath():
            return '/'
    class QPushButton:
        def __init__(self, *a, **k):
            self.clicked = _Signal()
    class QLabel:
        def __init__(self, *a, **k):
            self._text = ''
        def setText(self, t):
            self._text = t
        def text(self):
            return self._text
        def setObjectName(self, n):
            pass
    class QProgressBar:
        def __init__(self, *a, **k):
            self._value = 0
        def setRange(self, a, b):
            pass
        def setValue(self, v):
            self._value = v
    class QCheckBox:
        def __init__(self, *a, **k):
            self._checked = False
        def setChecked(self, v):
            self._checked = v
        def isChecked(self):
            return self._checked
    class QWidget: pass
    class QVBoxLayout:
        def __init__(self, *a, **k):
            pass
        def addWidget(self, *a, **k):
            pass
        def addLayout(self, *a, **k):
            pass
    class QGroupBox(QWidget):
        def __init__(self, *a, **k):
            pass
    class QSpinBox:
        def __init__(self, *a, **k):
            self._value = 0
        def setRange(self, a, b):
            pass
        def setValue(self, v):
            self._value = v
        def value(self):
            return self._value
    class QListWidget(QWidget):
        def __init__(self, *a, **k):
            self._items = []
        def addItem(self, item):
            self._items.append(item)
        def clear(self):
            self._items = []
        def count(self):
            return len(self._items)
        def item(self, i):
            return types.SimpleNamespace(text=lambda: self._items[i], isSelected=lambda: True)
    class QTreeView(QWidget):
        pass
    class QTabWidget(QWidget):
        def addTab(self, *a, **k):
            pass
    class QFileDialog: pass
    class QMessageBox: pass
    class QSystemTrayIcon:
        def __init__(self, *a, **k):
            pass
    class QUrl: pass
    Qt = types.SimpleNamespace(MouseButton=types.SimpleNamespace(LeftButton=1), CaseSensitivity=types.SimpleNamespace(CaseInsensitive=0), AlignmentFlag=types.SimpleNamespace(AlignLeft=0))
    def Slot(*a, **k):
        def decorator(fn):
            return fn
        return decorator
    qtcore = types.SimpleNamespace(
        QObject=object,
        Signal=lambda *a, **k: _Signal(),
        QThread=object,
        QTimer=object,
        QDir=QDir,
        Qt=Qt,
        Slot=Slot,
        QMutex=object,
        QUrl=QUrl,
        qDebug=lambda *a, **k: None,
        qWarning=lambda *a, **k: None,
        qCritical=lambda *a, **k: None,
        qFatal=lambda *a, **k: None,
        qInfo=lambda *a, **k: None,
        qInstallMessageHandler=lambda *a, **k: None,
        Property=object,
    )
    qtwidgets = types.SimpleNamespace(
        QApplication=QApplication,
        QWidget=QWidget,
        QVBoxLayout=QVBoxLayout,
        QHBoxLayout=QVBoxLayout,
        QTabWidget=QTabWidget,
        QLabel=QLabel,
        QProgressBar=QProgressBar,
        QPushButton=QPushButton,
        QCheckBox=QCheckBox,
        QSpinBox=QSpinBox,
        QListWidget=QListWidget,
        QTreeView=QTreeView,
        QGroupBox=QGroupBox,
        QFileDialog=QFileDialog,
        QMessageBox=QMessageBox,
        QSystemTrayIcon=QSystemTrayIcon,
    )
    qtgui = types.SimpleNamespace(QIcon=object)
    qtmultimedia = types.SimpleNamespace(QSoundEffect=object)
    qttest = types.SimpleNamespace(QTest=object)
    sys.modules['PySide6'] = types.SimpleNamespace(
        QtCore=qtcore,
        QtWidgets=qtwidgets,
        QtGui=qtgui,
        QtTest=qttest,
    )
    sys.modules['PySide6.QtCore'] = qtcore
    sys.modules['PySide6.QtWidgets'] = qtwidgets
    sys.modules['PySide6.QtGui'] = qtgui
    sys.modules['PySide6.QtMultimedia'] = qtmultimedia
    sys.modules['PySide6.QtTest'] = qttest

for mod in [
    "fitz",
    "pytesseract",
    "cv2",
    "numpy",
    "matplotlib",
    "matplotlib.pyplot",
    "seaborn",
]:
    sys.modules.setdefault(mod, types.ModuleType(mod))

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
