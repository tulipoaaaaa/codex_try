"""Utility helpers for UI tests."""
from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any

try:
    from PySide6.QtWidgets import QWidget
except Exception:  # pragma: no cover - PySide6 stubs may be used
    QWidget = object  # type: ignore


class DummySignal:
    """Simple signal object storing connected slots."""

    def __init__(self) -> None:
        self._slots: list[callable] = []

    def connect(self, slot) -> None:
        self._slots.append(slot)

    def emit(self, *args, **kwargs) -> None:
        for slot in list(self._slots):
            slot(*args, **kwargs)


class MockProjectConfig:
    """Lightweight project config used in tests."""

    def __init__(self, base: str | Path = ".") -> None:
        self.base = Path(base)

    def get(self, key: str, default: Any = None) -> Any:
        return default

    def set(self, key: str, value: Any) -> None:  # pragma: no cover - dummy
        pass

    def save(self) -> None:  # pragma: no cover - dummy
        pass

    def get_logs_dir(self) -> str:
        return str(self.base / "logs")


_definitions = {
    "shared_tools.ui_wrappers.processors.corpus_balancer_wrapper": (
        "CorpusBalancerWrapper",
        {"balance_completed": DummySignal()},
    ),
    "shared_tools.services.activity_log_service": (
        "ActivityLogService",
        {
            "activity_added": DummySignal(),
            "log": lambda self, *a, **k: None,
            "load_recent": lambda self, n=20: [],
        },
    ),
    "shared_tools.services.corpus_stats_service": (
        "CorpusStatsService",
        {"stats_updated": DummySignal(), "refresh_stats": lambda self: None},
    ),
}


def _install_service_stubs() -> None:
    for module_name, (cls_name, attrs) in _definitions.items():
        if module_name in sys.modules:
            continue
        mod = types.ModuleType(module_name)
        stub_cls = type(cls_name, (), {"__init__": lambda self, *a, **k: None, **attrs})
        setattr(mod, cls_name, stub_cls)
        sys.modules[module_name] = mod


def make_mock_tab(project_config: MockProjectConfig | None = None) -> QWidget:
    """Return a simple tab instance with heavy services mocked."""
    _install_service_stubs()
    cfg = project_config or MockProjectConfig()

    class SimpleTab(QWidget):
        def __init__(self, config) -> None:
            super().__init__()
            self.project_config = config
            from shared_tools.services.activity_log_service import ActivityLogService
            from shared_tools.ui_wrappers.processors.corpus_balancer_wrapper import (
                CorpusBalancerWrapper,
            )

            self.activity_log_service = ActivityLogService()
            self.balancer = CorpusBalancerWrapper(config)

    return SimpleTab(cfg)

