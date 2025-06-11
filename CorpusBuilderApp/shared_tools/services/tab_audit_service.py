from __future__ import annotations

import logging
from typing import List, Tuple

from PySide6.QtCore import QObject


OPTIONAL_TABS = {"balancer_tab", "corpus_manager_tab"}


class TabAuditService(QObject):
    """Runtime audit of main tab connections."""

    def __init__(self, main_window: QObject, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.main_window = main_window
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tab_registry = getattr(main_window, "tab_registry", {})

    # ------------------------------------------------------------------
    def _signal_receivers(self, signal: object) -> int:
        """Return number of connected slots for a Qt signal."""
        if signal is None:
            return 0
        if hasattr(signal, "receivers"):
            try:
                return signal.receivers()  # type: ignore[attr-defined]
            except Exception:  # pragma: no cover - best effort
                return 0
        if hasattr(signal, "_slots"):
            return len(getattr(signal, "_slots", []))
        return 0

    # ------------------------------------------------------------------
    def _check_connection(self, obj: object, signal_name: str, description: str, issues: List[str]) -> None:
        signal = getattr(obj, signal_name, None)
        if signal is None:
            issues.append(f"{obj.__class__.__name__} missing signal {signal_name}")
            return
        if self._signal_receivers(signal) == 0:
            issues.append(f"{obj.__class__.__name__}.{signal_name} not connected ({description})")

    # ------------------------------------------------------------------
    def audit(self) -> List[str]:
        """Perform the tab connection audit and log any issues."""
        mw = self.main_window
        issues: List[str] = []

        registry = getattr(self, "tab_registry", getattr(mw, "tab_registry", {}))
        tabs = list(registry.keys())

        for attr in tabs:
            tab_obj = registry.get(attr)
            if tab_obj is None and attr not in OPTIONAL_TABS:
                issues.append(f"{attr} missing")

        # Expected cross-tab signal connections
        collectors_tab = registry.get("collectors_tab")
        if collectors_tab:
            self._check_connection(collectors_tab, "collection_started", "on_collection_started", issues)
            self._check_connection(collectors_tab, "collection_finished", "on_collection_finished", issues)

        processors_tab = registry.get("processors_tab")
        if processors_tab:
            self._check_connection(processors_tab, "processing_started", "on_processing_started", issues)
            self._check_connection(processors_tab, "processing_finished", "on_processing_finished", issues)

        dashboard_tab = registry.get("dashboard_tab")
        if dashboard_tab:
            self._check_connection(dashboard_tab, "view_all_activity_requested", "show_full_activity_tab", issues)
            self._check_connection(dashboard_tab, "rebalance_requested", "on_rebalance_requested", issues)

        configuration_tab = registry.get("configuration_tab")
        if configuration_tab:
            self._check_connection(configuration_tab, "configuration_saved", "config.save", issues)

        balancer_tab = registry.get("balancer_tab")
        balancer = getattr(balancer_tab, "balancer", None)
        if balancer:
            self._check_connection(balancer, "balance_completed", "on_balance_completed", issues)
        else:
            issues.append("balancer tab missing balancer")

        full_activity_tab = registry.get("full_activity_tab")
        if full_activity_tab and not hasattr(full_activity_tab, "task_source"):
            issues.append("FullActivityTab missing task source")

        if issues:
            for msg in issues:
                self.logger.warning(msg)
        else:
            self.logger.info("Tab audit passed with no issues")

        return issues

