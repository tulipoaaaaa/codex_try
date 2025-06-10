from __future__ import annotations

import logging
import threading
from typing import Optional, Dict, Any

from PySide6.QtCore import QObject, QThread, Signal as pyqtSignal

from shared_tools.ui_wrappers.processors.corpus_balancer_wrapper import CorpusBalancerWrapper
from shared_tools.project_config import ProjectConfig


class AutoBalanceThread(QThread):
    """Background thread that monitors corpus balance."""

    progress = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(
        self,
        wrapper: CorpusBalancerWrapper,
        thresholds: Dict[str, float],
        check_interval: int = 900,
        start_balancing: bool = False,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.wrapper = wrapper
        self.thresholds = thresholds
        self.check_interval = check_interval
        self.start_balancing = start_balancing
        self._stop = threading.Event()

    # ------------------------------------------------------------------
    def stop(self) -> None:
        """Request the thread to stop."""
        self._stop.set()

    # ------------------------------------------------------------------
    def _wait_for_collectors(self) -> None:
        """Wait for all attached collectors to finish if they expose a finished signal."""
        wrappers = getattr(self.wrapper, "collector_wrappers", {}) or {}
        events: list[threading.Event] = []
        for wrap in wrappers.values():
            sig = (
                getattr(wrap, "collection_finished", None)
                or getattr(wrap, "finished", None)
                or getattr(wrap, "completed", None)
            )
            if sig is None or not hasattr(sig, "connect"):
                continue
            ev = threading.Event()
            sig.connect(lambda *a, _e=ev: _e.set())
            events.append(ev)
        for ev in events:
            while not ev.is_set() and not self._stop.is_set():
                self.msleep(50)

    # ------------------------------------------------------------------
    def run(self) -> None:  # pragma: no cover - thread loop
        while not self._stop.is_set():
            try:
                results: Dict[str, Any] = self.wrapper.analyze_corpus()
            except Exception as exc:  # pragma: no cover - defensive
                logging.getLogger(self.__class__.__name__).warning(
                    "analysis failed: %s", exc
                )
                break

            domain = results.get("domain_analysis", {}) if isinstance(results, dict) else {}
            missing = domain.get("missing_domains", []) or []
            ratio = float(domain.get("dominance_ratio", 1))

            if missing or ratio > self.thresholds.get("dominance_ratio", 5.0):
                self.progress.emit("Collecting for missing domains")
                try:
                    self.wrapper.collect_for_missing_domains()
                    self._wait_for_collectors()
                except Exception:  # pragma: no cover - defensive
                    pass
                if self.start_balancing:
                    try:
                        self.progress.emit("Balancing corpus")
                        self.wrapper.start_balancing()
                    except Exception:  # pragma: no cover - defensive
                        pass
            else:
                # Balanced - stop loop
                break

            for _ in range(int(self.check_interval * 10)):
                if self._stop.is_set():
                    break
                self.msleep(100)

        self.finished.emit()


class AutoBalanceService(QObject):
    """Service that manages the auto-balance thread."""

    loop_started = pyqtSignal()
    loop_stopped = pyqtSignal()
    progress = pyqtSignal(str)

    def __init__(
        self,
        balancer: CorpusBalancerWrapper,
        project_config: ProjectConfig,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.balancer = balancer
        self.config = project_config
        self._thread: AutoBalanceThread | None = None
        self.logger = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------
    def _thresholds(self) -> Dict[str, float]:
        return {
            "dominance_ratio": float(self.config.get("auto_balance.dominance_ratio", 5.0)),
            "check_interval": int(self.config.get("auto_balance.check_interval", 900)),
        }

    # ------------------------------------------------------------------
    def start(self) -> bool:
        """Start the auto-balance loop if not already running."""
        if self._thread and self._thread.isRunning():
            return False
        thres = self._thresholds()
        self._thread = AutoBalanceThread(
            self.balancer,
            thres,
            check_interval=int(thres.get("check_interval", 900)),
            start_balancing=bool(self.config.get("auto_balance.start_balancing", False)),
            parent=self,
        )
        self._thread.progress.connect(self.progress.emit)
        self._thread.finished.connect(self._on_finished)
        self.loop_started.emit()
        self._thread.start()
        return True

    # ------------------------------------------------------------------
    def _on_finished(self) -> None:
        self.loop_stopped.emit()
        self._thread = None

    # ------------------------------------------------------------------
    def stop(self) -> None:
        if self._thread and self._thread.isRunning():
            self._thread.stop()
            self._thread.wait()
            self._thread = None
            self.loop_stopped.emit()
