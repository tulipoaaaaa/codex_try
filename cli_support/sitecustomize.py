"""sitecustomize – executed automatically by the Python interpreter on startup

Purpose
-------
Provide a lightweight stub replacement for PySide6 so that server-side / head-less
executions of the CorpusBuilderApp **do not require a full Qt installation**.

How it works
~~~~~~~~~~~~
1. If the environment variable ``ENABLE_QT`` is **set** (to any value), we leave
   the import mechanism unchanged – the real PySide6 will be imported later.
2. Otherwise we *attempt* to import PySide6.  If that succeeds, nothing further
   happens.  If the import raises any exception (module missing, DLL load
   failure, etc.) we inject a tiny stub module hierarchy into ``sys.modules``
   under the names used throughout the codebase (``PySide6``,
   ``PySide6.QtCore``, ``PySide6.QtWidgets``).

The stubs expose just enough surface area for the non-GUI parts of the
application: ``QObject``, ``Signal``, ``QThread``, ``QTimer``, plus on the
Widgets side a dynamic fallback so *any* attribute access yields an empty class
(so ``QLabel``, ``QVBoxLayout`` and friends all exist but do nothing).

This keeps the GUI build 100 % intact (launch with ``ENABLE_QT=1`` or simply
have PySide6 installed) while letting CLI / test environments run without
installing or linking Qt.
"""

from __future__ import annotations

import os
import sys
import types
from typing import Any, Callable

print('[sitecustomize] loaded', file=sys.stderr)

# ---------------------------------------------------------------------------
# Decide whether to enable the stub
# ---------------------------------------------------------------------------
if os.getenv("ENABLE_QT"):
    # GUI / test environments explicitly want the full Qt stack; do nothing.
    # If PySide6 is missing they'll get a normal ImportError.
    pass
else:
    # ----------------------------------------------------------------------
    # Head-less mode: install stub BEFORE any attempt to import PySide6.
    # We don't try to probe the real PySide6 – even if it is partially
    # present it may crash the interpreter when its native libraries are
    # missing.  The real modules will still be available when ENABLE_QT=1.
    # ----------------------------------------------------------------------
    # Build minimal stub hierarchy
    # ----------------------------------------------------------------------
    pyside6_stub = types.ModuleType("PySide6")

    # ---------------- QtCore module ----------------------------------
    qtcore_stub = types.ModuleType("PySide6.QtCore")

    class QObject:  # noqa: D401 – simple placeholder
        """No-op replacement for QtCore.QObject"""
        def __init__(self, *args, **kwargs):
            super().__init__()

    # Qt's Signal implementation needs connect/emit. Provide tiny copy.
    class _Signal:  # noqa: D401 – behaves like a stub signal instance
        def __init__(self):
            self._slots: list[Callable[..., Any]] = []

        def connect(self, slot: Callable[..., Any]) -> None:  # pragma: no cover
            self._slots.append(slot)

        def emit(self, *args, **kwargs):  # pragma: no cover
            for s in list(self._slots):
                try:
                    s(*args, **kwargs)
                except Exception:  # noqa: BLE001 – suppress downstream
                    pass

    def Signal(*_types, **_kwargs):  # noqa: D401
        return _Signal()

    import threading
    import time as _time

    class QThread(threading.Thread):
        """Lightweight stand-in for QtCore.QThread"""

        def __init__(self):
            super().__init__(daemon=True)

        def wait(self, timeout: float | None = None):  # noqa: D401
            self.join(timeout)

    class QTimer:  # noqa: D401 – only singleShot used in codebase
        @staticmethod
        def singleShot(msec: int, func: Callable[[], None]):  # noqa: N802
            _time.sleep(msec / 1000.0)
            func()

    # Export core symbols
    qtcore_stub.QObject = QObject  # type: ignore[attr-defined]
    qtcore_stub.Signal = Signal  # type: ignore[attr-defined]
    qtcore_stub.QThread = QThread  # type: ignore[attr-defined]
    qtcore_stub.QTimer = QTimer  # type: ignore[attr-defined]

    # ---------------- QtWidgets module --------------------------------
    qtwidgets_stub = types.ModuleType("PySide6.QtWidgets")

    # Common empty base class for all widget types referenced in imports
    class _WidgetBase:  # noqa: D401 – placeholder for QWidget & co.
        def __init__(self, *args, **kwargs):
            pass

    # Pre-declare the names we know are imported explicitly; anything else
    # will fall back to __getattr__ (below).
    for _name in (
        "QWidget",
        "QVBoxLayout",
        "QHBoxLayout",
        "QPushButton",
        "QLabel",
        "QProgressBar",
        "QTextEdit",
        "QFileDialog",
        "QCheckBox",
        "QSpinBox",
        "QGroupBox",
        "QGridLayout",
        "QMessageBox",
        "QInputDialog",
        "QAbstractTableModel",
        "QModelIndex",
        "QDir",
        "QSortFilterProxyModel",
        "QMimeData",
        "QUrl",
    ):
        setattr(qtwidgets_stub, _name, type(_name, (_WidgetBase,), {}))

    # Dynamic fallback so *any* missing attr returns an empty class.
    def _qtwidgets_getattr(name):  # noqa: D401
        cls = type(name, (_WidgetBase,), {})
        setattr(qtwidgets_stub, name, cls)
        return cls

    qtwidgets_stub.__getattr__ = _qtwidgets_getattr  # type: ignore[attr-defined]

    # ---------------- integrate into sys.modules ----------------------
    pyside6_stub.QtCore = qtcore_stub  # type: ignore[attr-defined]
    pyside6_stub.QtWidgets = qtwidgets_stub  # type: ignore[attr-defined]

    sys.modules.setdefault("PySide6", pyside6_stub)
    sys.modules.setdefault("PySide6.QtCore", qtcore_stub)
    sys.modules.setdefault("PySide6.QtWidgets", qtwidgets_stub) 