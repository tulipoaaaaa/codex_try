import sys
import types
import pathlib
import pytest

# Ensure repository modules are importable
BASE = pathlib.Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))
if str(BASE / "CorpusBuilderApp") not in sys.path:
    sys.path.insert(0, str(BASE / "CorpusBuilderApp"))

# Minimal PySide6 stubs if PySide6 not installed
if 'PySide6' not in sys.modules:
    qtcore = types.ModuleType('PySide6.QtCore')
    class Signal:
        def __init__(self, *args, **kwargs):
            self._slots = []
        def connect(self, slot):
            self._slots.append(slot)
        def emit(self, *args, **kwargs):
            for s in list(self._slots):
                s(*args, **kwargs)
    class QObject:
        def __init__(self, *a, **k):
            pass
    class QThread:
        def __init__(self, *a, **k):
            self._running = False
        def start(self):
            self._running = True
            self.run()
        def run(self):
            pass
        def isRunning(self):
            return self._running
        def wait(self):
            pass
        def requestInterruption(self):
            self._running = False
    class QTimer:
        def __init__(self, parent=None):
            self.timeout = Signal()
            self._active = False
            self._interval = 0
        def start(self, interval):
            self._active = True
            self._interval = interval
        def stop(self):
            self._active = False
        def isActive(self):
            return self._active
        def interval(self):
            return self._interval
    qtcore.Signal = Signal
    qtcore.QObject = QObject
    qtcore.QThread = QThread
    qtcore.QTimer = QTimer
    qtcore.__getattr__ = lambda name: type(name, (), {})
    sys.modules['PySide6.QtCore'] = qtcore
    qtwidgets = types.ModuleType('PySide6.QtWidgets')
    class _Any:
        def __init__(self, *a, **k):
            pass
        def __getattr__(self, name):
            return lambda *a, **k: None
    qtwidgets.__getattr__ = lambda name: type(name, (), {})
    class _QWidget:
        def __init__(self, *a, **k):
            pass
    qtwidgets.QWidget = _QWidget
    qtgui = types.ModuleType('PySide6.QtGui')
    qtgui.__getattr__ = lambda name: type(name, (), {})
    qtcharts = types.ModuleType('PySide6.QtCharts')
    qtcharts.__getattr__ = lambda name: type(name, (), {})
    sys.modules['PySide6.QtWidgets'] = qtwidgets
    sys.modules['PySide6.QtGui'] = qtgui
    sys.modules['PySide6.QtCharts'] = qtcharts
    pyside6 = types.ModuleType('PySide6')
    pyside6.QtCore = qtcore
    pyside6.QtWidgets = qtwidgets
    pyside6.QtGui = qtgui
    pyside6.QtCharts = qtcharts
    sys.modules['PySide6'] = pyside6

# Provide psutil stub if missing
if 'psutil' not in sys.modules:
    psutil = types.ModuleType('psutil')
    psutil.cpu_percent = lambda *a, **k: 0.0
    psutil.virtual_memory = lambda: types.SimpleNamespace(percent=0.0)
    psutil.disk_usage = lambda p: types.SimpleNamespace(percent=0.0)
    psutil.cpu_count = lambda: 1
    psutil.boot_time = lambda: 0
    sys.modules['psutil'] = psutil

# Basic stubs for optional heavy deps
sys.modules.setdefault('PyPDF2', types.ModuleType('PyPDF2'))
sys.modules.setdefault('fitz', types.ModuleType('fitz'))
sys.modules.setdefault('pdfminer', types.ModuleType('pdfminer'))
hl = types.ModuleType('pdfminer.high_level')
setattr(hl, 'extract_text', lambda *a, **k: '')
setattr(hl, 'extract_pages', lambda *a, **k: [])
sys.modules.setdefault('pdfminer.high_level', hl)
sys.modules.setdefault('pdfminer.layout', types.ModuleType('pdfminer.layout'))
layout_mod = sys.modules['pdfminer.layout']
for name in ['LTTextContainer','LTChar','LTFigure']:
    setattr(layout_mod, name, type(name, (), {}))
multimedia = types.ModuleType('PySide6.QtMultimedia')
setattr(multimedia, 'QSoundEffect', type('QSoundEffect', (), {}))
sys.modules.setdefault('PySide6.QtMultimedia', multimedia)

# Ensure pydantic has field_validator for compatibility
try:
    import pydantic as _p
    if not hasattr(_p, 'field_validator'):
        setattr(_p, 'field_validator', lambda *a, **k: (lambda f: f))
except Exception:
    _p = types.ModuleType('pydantic')
    _p.field_validator = lambda *a, **k: (lambda f: f)
    _p.BaseModel = type('BaseModel', (), {})
    sys.modules.setdefault('pydantic', _p)

sys.modules.setdefault('yaml', types.ModuleType('yaml'))
dotenv_mod = types.ModuleType('dotenv')
setattr(dotenv_mod, 'load_dotenv', lambda *a, **k: None)
setattr(dotenv_mod, 'set_key', lambda *a, **k: None)
sys.modules.setdefault('dotenv', dotenv_mod)
langdetect_mod = types.ModuleType('langdetect')
setattr(langdetect_mod, 'detect_langs', lambda *a, **k: [])
setattr(langdetect_mod, 'LangDetectException', Exception)
sys.modules.setdefault('langdetect', langdetect_mod)
sys.modules.setdefault('numpy', types.ModuleType('numpy'))
numpy_mod = sys.modules['numpy']
setattr(numpy_mod, 'ndarray', object)
setattr(numpy_mod, 'array', lambda *a, **k: None)
sys.modules.setdefault('camelot', types.ModuleType('camelot'))
sys.modules.setdefault('pandas', types.ModuleType('pandas'))
pandas_mod = sys.modules['pandas']
setattr(pandas_mod, 'DataFrame', lambda *a, **k: None)
sys.modules.setdefault('scipy', types.ModuleType('scipy'))
stats_mod = types.ModuleType('scipy.stats')
setattr(stats_mod, 'entropy', lambda *a, **k: None)
setattr(stats_mod, 'chi2_contingency', lambda *a, **k: (None,None,None,None))
sys.modules.setdefault('scipy.stats', stats_mod)
sys.modules.setdefault('matplotlib', types.ModuleType('matplotlib'))
sys.modules.setdefault('matplotlib.pyplot', types.ModuleType('matplotlib.pyplot'))
sys.modules.setdefault('seaborn', types.ModuleType('seaborn'))
sys.modules.setdefault('plotly', types.ModuleType('plotly'))
sys.modules.setdefault('plotly.graph_objects', types.ModuleType('plotly.graph_objects'))
sys.modules.setdefault('plotly.express', types.ModuleType('plotly.express'))
subplots_mod = types.ModuleType('plotly.subplots')
setattr(subplots_mod, 'make_subplots', lambda *a, **k: None)
sys.modules.setdefault('plotly.subplots', subplots_mod)

# Basic network and data libs stubs
requests_mod = types.ModuleType('requests')
class _Session:
    def __init__(self, *a, **k):
        self.headers = {}
    def get(self, *a, **k):
        class Resp:
            status_code = 200
            text = ''
        return Resp()
    def post(self, *a, **k):
        return self.get()
requests_mod.Session = _Session
sys.modules.setdefault('requests', requests_mod)
sys.modules.setdefault('pandas', types.ModuleType('pandas'))
sys.modules.setdefault('dotenv', types.ModuleType('dotenv'))
selenium_mod = types.ModuleType('selenium')
selenium_mod.webdriver = types.SimpleNamespace(__name__='selenium.webdriver')
sys.modules.setdefault('selenium', selenium_mod)
sys.modules.setdefault('selenium.webdriver', selenium_mod.webdriver)

# Stub BeautifulSoup if bs4 not installed
if 'bs4' not in sys.modules:
    bs4 = types.ModuleType('bs4')
    class _BS:
        def __init__(self, *a, **k):
            pass
        def find_all(self, *a, **k):
            return []
        def find(self, *a, **k):
            return None
    bs4.BeautifulSoup = _BS
    sys.modules['bs4'] = bs4

from pathlib import Path

@pytest.fixture
def tmp_config_path(tmp_path):
    cfg = tmp_path / 'config.yaml'
    cfg.write_text('environment:\n  active: test\n')
    return cfg


class DummyProjectConfig:
    def __init__(self, base: Path):
        self.base = base
        self.raw_data_dir = base / "raw"
        self.processed_dir = base / "processed"
        self.metadata_dir = base / "meta"
        self.log_dir = base / "logs"
        for d in [self.raw_data_dir, self.processed_dir, self.metadata_dir, self.log_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def get_raw_dir(self) -> Path:
        return self.raw_data_dir

    def get_input_dir(self) -> Path:
        return self.raw_data_dir

    def get_processed_dir(self) -> Path:
        return self.processed_dir

    def get_metadata_dir(self) -> Path:
        return self.metadata_dir

    def get_logs_dir(self) -> Path:
        return self.log_dir

    def get_processor_config(self, name: str):
        return {}


@pytest.fixture
def dummy_config(tmp_path):
    return DummyProjectConfig(tmp_path)
