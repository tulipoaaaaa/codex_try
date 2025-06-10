# -*- coding: utf-8 -*-
# NOTE: Prototype utility script – not used in normal application runtime.
"""Integration audit after refactor.

This script performs a lightweight audit of core service and UI
integrations for the CryptoCorpusBuilder application. It can be run on a
headless system and does not require the full GUI.

Usage::

    python scripts/audit_integration_state.py
"""
from __future__ import annotations

import importlib
import os
import sys
import tempfile
import types
from pathlib import Path


# ---------------------------------------------------------------------------
# Colored output helpers
try:
    from colorama import Fore, Style, init as _color_init

    _color_init()
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    RED = Fore.RED
    RESET = Style.RESET_ALL
except Exception:  # pragma: no cover - colorama optional
    GREEN = YELLOW = RED = RESET = ""


def _pass(msg: str) -> None:
    print(f"{GREEN}✅ {msg}{RESET}")


def _warn(msg: str) -> None:
    print(f"{YELLOW}⚠️ {msg}{RESET}")


def _fail(msg: str) -> None:
    print(f"{RED}❌ {msg}{RESET}")


# ---------------------------------------------------------------------------
# Minimal Qt stubs so modules can be imported without PySide6

def install_qt_stubs() -> bool:
    """Install minimal PySide6 stubs if the real package is missing."""
    try:
        import PySide6  # type: ignore
        return True
    except Exception:
        pass

    class _DummySignal:
        def __init__(self, *a, **k):
            self._slots = []

        def connect(self, slot):
            self._slots.append(slot)

        def emit(self, *a, **k):  # pragma: no cover - runtime helper
            for s in list(self._slots):
                try:
                    s(*a, **k)
                except Exception:
                    pass

    qtcore = types.SimpleNamespace(
        QObject=object,
        Signal=lambda *a, **k: _DummySignal(),
        QThread=object,
        QTimer=object,
        Slot=lambda *a, **k: (lambda func: func),
        Qt=types.SimpleNamespace(),
        QDir=object,
    )
    qtwidgets = types.SimpleNamespace(
        QApplication=type(
            "QApplication",
            (),
            {"instance": staticmethod(lambda: None), "__init__": lambda self, *a, **k: None, "quit": lambda self: None},
        ),
    )
    sys.modules.setdefault("PySide6", types.SimpleNamespace(QtCore=qtcore, QtWidgets=qtwidgets))
    sys.modules.setdefault("PySide6.QtCore", qtcore)
    sys.modules.setdefault("PySide6.QtWidgets", qtwidgets)
    return False


# ---------------------------------------------------------------------------
# Other heavy dependency stubs used by wrappers

def install_extra_stubs() -> None:
    heavy = [
        "fitz",
        "pytesseract",
        "cv2",
        "numpy",
        "matplotlib",
        "matplotlib.pyplot",
        "seaborn",
    ]
    for mod in heavy:
        sys.modules.setdefault(mod, types.ModuleType(mod))

    if "langdetect" not in sys.modules:
        langdetect = types.ModuleType("langdetect")
        langdetect.detect_langs = lambda *a, **k: []
        langdetect.LangDetectException = Exception
        sys.modules["langdetect"] = langdetect

    # Minimal PIL stubs
    dummy_pil = types.ModuleType("PIL")
    dummy_image = types.ModuleType("PIL.Image")
    dummy_enhance = types.ModuleType("PIL.ImageEnhance")
    dummy_pil.Image = dummy_image
    dummy_pil.ImageEnhance = dummy_enhance
    sys.modules.setdefault("PIL", dummy_pil)
    sys.modules.setdefault("PIL.Image", dummy_image)
    sys.modules.setdefault("PIL.ImageEnhance", dummy_enhance)


# ---------------------------------------------------------------------------
# Utility
class DummyConfig:
    def get(self, key: str, default=None):
        return default

    def set(self, key: str, value) -> None:
        pass

    def save(self) -> None:
        pass

    def get_corpus_dir(self):  # For CorpusStatsService
        return os.getcwd()


CONFIG = DummyConfig()


def is_signal(obj: object) -> bool:
    return hasattr(obj, "connect") and hasattr(obj, "emit")


# ---------------------------------------------------------------------------
# Service instantiation checks

def verify_services():
    print("\n== Service Instantiation ==")
    services = [
        ("CorpusStatsService", "shared_tools.services.corpus_stats_service", "CorpusStatsService"),
        ("TaskQueueManager", "shared_tools.services.task_queue_manager", "TaskQueueManager"),
        ("SystemMonitor", "shared_tools.services.system_monitor", "SystemMonitor"),
        ("ActivityLogService", "shared_tools.services.activity_log_service", "ActivityLogService"),
        ("CorpusBalancerWrapper", "shared_tools.ui_wrappers.processors.corpus_balancer_wrapper", "CorpusBalancerWrapper"),
    ]
    for name, module_path, cls_name in services:
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, cls_name)
            try:
                instance = cls(CONFIG)
                _pass(f"{name} instantiated")
            except Exception as exc:
                instance = None
                _warn(f"{name} import but failed to init: {exc}")
            signal_attrs = [a for a in dir(cls) if is_signal(getattr(cls, a))]
            if signal_attrs:
                print(f"   Signals: {', '.join(signal_attrs)}")
        except Exception as exc:
            _fail(f"{name} missing ({exc})")


# ---------------------------------------------------------------------------
# Signal wiring checks (static source inspection)

def verify_signal_wiring(qt_available: bool) -> None:
    print("\n== Signal Wiring ==")
    main_window = Path("CorpusBuilderApp/app/main_window.py")
    dashboard_tab = Path("CorpusBuilderApp/app/ui/tabs/dashboard_tab.py")

    def contains(path: Path, text: str) -> bool:
        if not path.exists():
            return False
        return text in path.read_text(encoding="utf-8")

    checks = [
        (
            "DashboardTab.rebalance_requested connected",
            contains(main_window, "rebalance_requested.connect"),
        ),
        (
            "CorpusBalancerWrapper.balance_completed → on_balance_completed",
            contains(main_window, "balance_completed.connect(self.on_balance_completed"),
        ),
        (
            "CorpusStatsService.stats_updated → DashboardTab.update_overview_metrics",
            contains(dashboard_tab, "stats_updated.connect(self.update_overview_metrics"),
        ),
        (
            "ActivityLogService.activity_added updates RecentActivityWidget",
            contains(dashboard_tab, "activity_added.connect")
            or contains(main_window, "activity_added.connect"),
        ),
    ]

    for desc, ok in checks:
        if ok:
            _pass(desc)
        else:
            _warn(desc + " NOT found")

    if not qt_available:
        _warn("PySide6 unavailable - dynamic signal verification skipped")


# ---------------------------------------------------------------------------
# ProjectConfig round trip

def verify_project_config():
    print("\n== ProjectConfig Round Trip ==")
    try:
        from shared_tools.project_config import ProjectConfig
        tmpdir = tempfile.mkdtemp()
        cfg_path = Path(tmpdir) / "cfg.yaml"
        data = {
            "environment": "test",
            "environments": {"test": {"corpus_dir": tmpdir}},
        }
        import yaml

        with open(cfg_path, "w", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh)

        cfg = ProjectConfig.from_yaml(str(cfg_path))
        cfg.set("audit.test", 42)
        cfg.save()
        reloaded = ProjectConfig.from_yaml(str(cfg_path))
        if reloaded.get("audit.test") == 42:
            _pass("ProjectConfig load/set/save round trip")
        else:
            _fail("ProjectConfig round trip failed")
    except Exception as exc:
        _fail(f"ProjectConfig check failed: {exc}")


# ---------------------------------------------------------------------------
# Wrapper API checks

def verify_wrappers():
    print("\n== Wrapper API Compliance ==")
    wrapper_dirs = [
        Path("CorpusBuilderApp/shared_tools/ui_wrappers/collectors"),
        Path("CorpusBuilderApp/shared_tools/ui_wrappers/processors"),
    ]
    for d in wrapper_dirs:
        for file in d.glob("*_wrapper.py"):
            mod_path = "shared_tools.ui_wrappers." + ".".join(file.relative_to(Path("CorpusBuilderApp/shared_tools/ui_wrappers")).with_suffix("").parts)
            try:
                module = importlib.import_module(mod_path)
            except Exception as exc:
                _fail(f"Failed importing {mod_path}: {exc}")
                continue
            for attr_name in dir(module):
                if attr_name.endswith("Wrapper") and attr_name[0].isupper():
                    cls = getattr(module, attr_name)
                    missing = [m for m in ("start", "stop", "refresh_config") if not hasattr(cls, m)]
                    msg = f"{attr_name}"
                    if missing:
                        _warn(f"{msg} missing methods: {', '.join(missing)}")
                    else:
                        _pass(f"{msg} has start/stop/refresh_config")
                    if hasattr(cls, "set_enabled"):
                        print("   set_enabled available")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    qt_available = install_qt_stubs()
    install_extra_stubs()

    verify_services()
    verify_signal_wiring(qt_available)
    verify_project_config()
    verify_wrappers()
