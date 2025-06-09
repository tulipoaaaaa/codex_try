import sys
import types

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
        Property=object,
        __version__="6.5.0",
        qVersion=lambda: "6.5.0",
    )
    qtwidgets = types.SimpleNamespace(QApplication=QApplication, QWidget=QWidget, QVBoxLayout=QVBoxLayout, QHBoxLayout=QVBoxLayout, QTabWidget=QTabWidget, QLabel=QLabel, QProgressBar=QProgressBar, QPushButton=QPushButton, QCheckBox=QCheckBox, QSpinBox=QSpinBox, QListWidget=QListWidget, QGroupBox=QGroupBox, QFileDialog=QFileDialog, QMessageBox=QMessageBox, QSystemTrayIcon=QSystemTrayIcon)
    qtgui = types.SimpleNamespace(QIcon=object)
    qttest = types.SimpleNamespace(QTest=object)
    qtmultimedia = types.SimpleNamespace(QSoundEffect=object)
    sys.modules['PySide6'] = types.SimpleNamespace(QtCore=qtcore, QtWidgets=qtwidgets, QtGui=qtgui, QtTest=qttest)
    sys.modules['PySide6.QtCore'] = qtcore
    sys.modules['PySide6.QtWidgets'] = qtwidgets
    sys.modules['PySide6.QtGui'] = qtgui
    sys.modules['PySide6.QtTest'] = qttest
    sys.modules['PySide6.QtMultimedia'] = qtmultimedia
