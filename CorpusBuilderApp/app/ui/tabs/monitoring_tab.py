from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from app.ui.theme.theme_constants import PAGE_MARGIN
from app.ui.widgets.section_header import SectionHeader
from PySide6.QtCore import Slot
from shared_tools.ui_wrappers.processors.monitor_progress_wrapper import MonitorProgressWrapper
from shared_tools.services.system_monitor import SystemMonitor

class MonitoringTab(QWidget):
    def __init__(self, project_config, parent=None):
        super().__init__(parent)
        self.project_config = project_config
        layout = QVBoxLayout(self)
        layout.setContentsMargins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
        layout.setSpacing(PAGE_MARGIN)

        header = SectionHeader("System Monitor")
        layout.addWidget(header)

        # Progress widget provided by the shared wrapper
        self.monitor_widget = MonitorProgressWrapper(self.project_config)
        layout.addWidget(self.monitor_widget)

        # System metrics progress bars
        self.loading_label = QLabel("Loading metrics…")
        self.cpu_bar = QProgressBar()
        self.ram_bar = QProgressBar()
        self.disk_bar = QProgressBar()
        for bar in (self.cpu_bar, self.ram_bar, self.disk_bar):
            bar.setRange(0, 100)

        layout.addWidget(self.loading_label)
        layout.addWidget(self.cpu_bar)
        layout.addWidget(self.ram_bar)
        layout.addWidget(self.disk_bar)

        # Start system monitor
        self.system_monitor = SystemMonitor()
        self.system_monitor.system_metrics.connect(self.update_metrics)
        self.system_monitor.start()

    # ------------------------------------------------------------------
    @Slot(float, float, float)
    def update_metrics(self, cpu: float, ram: float, disk: float) -> None:
        """Update progress bars with the latest system metrics."""
        self.cpu_bar.setValue(int(cpu))
        self.ram_bar.setValue(int(ram))
        self.disk_bar.setValue(int(disk))
        self.loading_label.hide()

    # ------------------------------------------------------------------
    def closeEvent(self, event):
        """Ensure monitoring stops when the tab closes."""
        if hasattr(self, "system_monitor"):
            self.system_monitor.stop()
        super().closeEvent(event)
