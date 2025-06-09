import sys
import types
import os
import tempfile
import shutil
import pytest

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
    sys.modules.setdefault("dotenv", stub)

# Ensure the CorpusBuilderApp root is on the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'CorpusBuilderApp'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if os.environ.get("PYTEST_QT_STUBS") == "1":
    print("Loaded PySide6 stub")
    class _Signal:
        def __init__(self, *a, **k):
            self._slots = []
        def connect(self, slot):
            self._slots.append(slot)
        def emit(self, *a, **k):
            for s in self._slots:
                s(*a, **k)

    class _DummyModule(types.ModuleType):
        def __getattr__(self, name):
            obj = type(name, (), {})
            setattr(self, name, obj)
            return obj
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
    class QWidget:
        def __init__(self, *a, **k):
            pass
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
    class QFrame(QWidget):
        pass
    class QScrollArea(QWidget):
        def __init__(self, *a, **k):
            pass
        def setWidget(self, *a, **k):
            pass
    class QMenu(QWidget):
        def __init__(self, *a, **k):
            pass
    class QTableWidgetItem:
        def __init__(self, *a, **k):
            pass
    class QHeaderView:
        ResizeMode = types.SimpleNamespace(ResizeToContents=1, Stretch=2)
    class QLineEdit(QWidget):
        def text(self):
            return ""
        def setText(self, *a, **k):
            pass
    class QDateEdit(QWidget):
        def __init__(self, *a, **k):
            pass
        def setDate(self, *a, **k):
            pass
        def setDisplayFormat(self, *a, **k):
            pass
    class QComboBox(QWidget):
        def __init__(self, *a, **k):
            self._text = ""
        def addItem(self, *a, **k):
            pass
        def currentText(self):
            return self._text
        def setCurrentText(self, t):
            self._text = t
    class QGridLayout:
        def addWidget(self, *a, **k):
            pass
    class QTextEdit(QWidget):
        def toPlainText(self):
            return ""
        def setPlainText(self, *a, **k):
            pass
    class QScrollArea(QWidget):
        def setWidgetResizable(self, *a, **k):
            pass
        def setWidget(self, *a, **k):
            pass
    class QMenu(QWidget):
        def addAction(self, *a, **k):
            pass
        def exec(self, *a, **k):
            pass
    class QTableWidget(QWidget):
        pass
    class QTableWidgetItem:
        def __init__(self, *a, **k):
            pass
    class QTableView(QWidget):
        pass
    class QHeaderView(QWidget):
        class ResizeMode:
            Stretch = 0
        def setSectionResizeMode(self, *a, **k):
            pass
    class QStandardItemModel:
        def __init__(self, *a, **k):
            pass
        def setHorizontalHeaderLabels(self, *a, **k):
            pass
        def rowCount(self):
            return 0
        def insertRow(self, *a, **k):
            pass
        def setItem(self, *a, **k):
            pass
    class QStandardItem:
        def __init__(self, *a, **k):
            pass
        def text(self):
            return ""
    class QFileSystemModel:
        def setReadOnly(self, *a, **k):
            pass
        def setRootPath(self, *a, **k):
            pass
        def index(self, p):
            return p
        def filePath(self, index):
            return index
    class QSortFilterProxyModel:
        def setSourceModel(self, *a, **k):
            pass
        def setFilterCaseSensitivity(self, *a, **k):
            pass
        def setFilterFixedString(self, *a, **k):
            pass
        def mapFromSource(self, index):
            return index
        def mapToSource(self, index):
            return index
    class QDateEdit(QWidget):
        def setDate(self, *a, **k):
            pass
        def date(self):
            return None
    class QSplitter(QWidget):
        pass
    class QMenu: pass
    class QScrollArea(QWidget):
        pass
    class QDateEdit(QWidget):
        def __init__(self, *a, **k):
            pass
    class QTableWidgetItem: pass
    class QInputDialog: pass
    class QSlider(QWidget): pass
    class QFont: pass
    class QSizePolicy: pass
    class QHeaderView: pass
    class QFileSystemModel: pass
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
    class QTableWidgetItem:
        def __init__(self, *a, **k):
            pass
    class QDateEdit(QWidget):
        def setDate(self, *a, **k):
            pass
        def setDisplayFormat(self, *a, **k):
            pass
        def setCalendarPopup(self, *a, **k):
            pass
    class QMenu(QWidget):
        def addAction(self, *a, **k):
            pass
    class QTabWidget(QWidget):
        def addTab(self, *a, **k):
            pass
    class QFileDialog:
        @staticmethod
        def getExistingDirectory(*a, **k):
            return ""
    class QMessageBox: pass
    class QSystemTrayIcon:
        def __init__(self, *a, **k):
            pass
    class QInputDialog(QWidget):
        pass
    class QSlider(QWidget):
        pass
    class QHeaderView(QWidget):
        Stretch = 0
        ResizeToContents = 1
        def setSectionResizeMode(self, *a, **k):
            pass
    class QFont:
        pass
    class QSizePolicy:
        Expanding = 0
        Preferred = 1
    class QFileSystemModel(QWidget):
        pass
    class QDate:
        currentDate = staticmethod(lambda: None)
        def addDays(self, *a):
            return self
    class QDialog(QWidget):
        pass
    class QColor:
        def __init__(self, *a, **k):
            pass
    class QBrush:
        def __init__(self, *a, **k):
            pass
    class QTextCharFormat:
        def __init__(self, *a, **k):
            pass
    class QMargins:
        def __init__(self, *a, **k):
            pass
    class QUrl: pass
    Qt = types.SimpleNamespace(MouseButton=types.SimpleNamespace(LeftButton=1), CaseSensitivity=types.SimpleNamespace(CaseInsensitive=0), AlignmentFlag=types.SimpleNamespace(AlignLeft=0))
    def Slot(*a, **k):
        def decorator(fn):
            return fn
        return decorator
    class _QtCore(types.SimpleNamespace):
        def __getattr__(self, name):
            return object

    qtcore = _QtCore(
        QObject=object,
        Signal=lambda *a, **k: _Signal(),
        QThread=object,
        QTimer=object,
        QDir=QDir,
        Qt=Qt,
        Slot=Slot,
        QMutex=object,
        QModelIndex=object,
        QPoint=object,
        QMimeData=object,
        QUrl=QUrl,
        QDate=QDate,
        QMargins=QMargins,
        qDebug=lambda *a, **k: None,
        qWarning=lambda *a, **k: None,
        qCritical=lambda *a, **k: None,
        qFatal=lambda *a, **k: None,
        qInfo=lambda *a, **k: None,
        qInstallMessageHandler=lambda *a, **k: None,
        Property=object,
        __version__="6.5.0",
        qVersion=lambda: "6.5.0",
    )

    class _QtWidgets(types.SimpleNamespace):
        def __getattr__(self, name):
            return object

    qtwidgets = _QtWidgets(
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
        QFrame=QFrame,
        QLineEdit=QLineEdit,
        QComboBox=QComboBox,
        QGridLayout=QGridLayout,
        QTextEdit=QTextEdit,
        QTableWidget=QTableWidget,
        QTableWidgetItem=QTableWidgetItem,
        QTableView=QTableView,
        QHeaderView=QHeaderView,
        QStandardItemModel=QStandardItemModel,
        QStandardItem=QStandardItem,
        QFileSystemModel=QFileSystemModel,
        QSortFilterProxyModel=QSortFilterProxyModel,
        QScrollArea=QScrollArea,
        QMenu=QMenu,
        QDateEdit=QDateEdit,
        QSplitter=QSplitter,
        QMenu=QMenu,
        QScrollArea=QScrollArea,
        QDateEdit=QDateEdit,
        QTableWidgetItem=QTableWidgetItem,
        QInputDialog=QInputDialog,
        QSlider=QSlider,
        QFont=QFont,
        QSizePolicy=QSizePolicy,
        QHeaderView=QHeaderView,
        QFileSystemModel=QFileSystemModel,
        QFileDialog=QFileDialog,
        QMessageBox=QMessageBox,
        QSystemTrayIcon=QSystemTrayIcon,
        QInputDialog=QInputDialog,
        QSlider=QSlider,
        QHeaderView=QHeaderView,
        QSizePolicy=QSizePolicy,
        QDateEdit=QDateEdit,
        QMenu=QMenu,
        QFileSystemModel=QFileSystemModel,
        QDialog=QDialog,
    )
    class _QtGui(types.SimpleNamespace):
        def __getattr__(self, name):
            return object

    qtgui = _QtGui(QIcon=object, QAction=object, QFont=object, QColor=object,
                   QTextCharFormat=object, QBrush=object, QDragEnterEvent=object,
                   QDropEvent=object)
    qttest = types.SimpleNamespace(QTest=object)
    qtmultimedia = types.SimpleNamespace(QSoundEffect=object)
    sys.modules['PySide6'] = types.SimpleNamespace(
        QtCore=qtcore,
        QtWidgets=qtwidgets,
        QtGui=qtgui,
        QtCharts=qtcharts,
        QtTest=qttest,
        __version__="6.5.0",
    )
    sys.modules['PySide6.QtCore'] = qtcore
    sys.modules['PySide6.QtWidgets'] = qtwidgets
    sys.modules['PySide6.QtGui'] = qtgui
    sys.modules['PySide6.QtCharts'] = qtcharts
    sys.modules['PySide6.QtTest'] = qttest
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
    "bs4",
    "selenium",
    "selenium.webdriver",
    "selenium.webdriver.common",
    "selenium.webdriver.common.by",
    "undetected_chromedriver",
    "selenium.common",
    "selenium.common.exceptions",
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
