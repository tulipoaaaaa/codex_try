from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QDialogButtonBox,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QPushButton,
)
from PySide6.QtCore import Qt

from app.ui.widgets.card_wrapper import CardWrapper
from app.ui.widgets.status_dot import StatusDot
from shared_tools.project_config import ProjectConfig
from shared_tools.ui_wrappers.base_wrapper import BaseWrapper

import inspect
from typing import Any, Callable, Dict


class CollectorConfigDialog(QDialog):
    """Dialog for configuring individual collectors."""

    def __init__(
        self,
        collector_name: str,
        project_config: ProjectConfig,
        wrapper: BaseWrapper,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.collector_name = collector_name
        self.project_config = project_config
        self.wrapper = wrapper
        self.fields: Dict[str, Any] = {}
        self.setters: Dict[str, Callable] = {}

        self.setWindowTitle(f"{collector_name.title()} Configuration")
        self._setup_ui()
        self._create_fields()
        self.load_config()

    # ------------------------------------------------------------------ UI ----
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Status indicator
        self.status_dot = StatusDot(self.collector_name.title(), "info")
        layout.addWidget(self.status_dot)

        # Card container for form
        self.form_card = CardWrapper(title="Settings")
        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(12)
        self.form_card.body_layout.addLayout(self.form_layout)
        layout.addWidget(self.form_card)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)

        self.reset_btn = QPushButton("Reset to Global Config")
        self.reset_btn.clicked.connect(self.reset_to_global)
        buttons.addButton(self.reset_btn, QDialogButtonBox.ButtonRole.ResetRole)

        layout.addWidget(buttons)

    # -------------------------------------------------------------- Helpers ----
    def _create_fields(self) -> None:
        """Inspect wrapper for set_* methods and build form fields."""
        for name, method in inspect.getmembers(self.wrapper, predicate=callable):
            if not name.startswith("set_"):
                continue
            attr = name[4:]
            current = getattr(self.wrapper, attr, None)
            widget = None
            if isinstance(current, bool):
                widget = QCheckBox()
                widget.setChecked(current)
            elif isinstance(current, int):
                widget = QSpinBox()
                widget.setValue(current)
            elif isinstance(current, float):
                widget = QDoubleSpinBox()
                widget.setValue(current)
            elif isinstance(current, str) or current is None:
                widget = QLineEdit(str(current) if current is not None else "")
            else:
                # Unsupported type
                continue

            label = attr.replace("_", " ").title()
            self.form_layout.addRow(label + ":", widget)
            self.fields[attr] = widget
            self.setters[attr] = method

    # -------------------------------------------------------------- Actions ----
    def load_config(self) -> None:
        """Populate fields from project configuration."""
        cfg = self.project_config.get(f"collectors.{self.collector_name}", {})
        if not isinstance(cfg, dict):
            cfg = {}
        for attr, widget in self.fields.items():
            value = cfg.get(attr, getattr(self.wrapper, attr, None))
            if isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                if value is not None:
                    widget.setValue(float(value))
            else:
                widget.setText(str(value) if value is not None else "")

    def save(self) -> None:  # type: ignore[override]
        """Apply values to wrapper and save to config."""
        cfg: Dict[str, Any] = {}
        for attr, widget in self.fields.items():
            if isinstance(widget, QCheckBox):
                value = widget.isChecked()
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                value = widget.value()
                if isinstance(widget, QSpinBox):
                    value = int(value)
            else:
                value = widget.text()
            setter = self.setters.get(attr)
            if setter:
                try:
                    setter(value)
                except Exception as exc:
                    print(f"Failed to set {attr}: {exc}")
            cfg[attr] = value
        self.project_config.set(f"collectors.{self.collector_name}", cfg)
        self.project_config.save()
        self.accept()

    def reset_to_global(self) -> None:
        """Load settings from the global collectors section."""
        global_cfg = self.project_config.get("collectors.global", {})
        if not isinstance(global_cfg, dict):
            return
        for attr, widget in self.fields.items():
            if attr not in global_cfg:
                continue
            value = global_cfg[attr]
            if isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(float(value))
            else:
                widget.setText(str(value))

